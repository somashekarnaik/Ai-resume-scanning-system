import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from App.schemas import CareerAssistantMessage, CareerAssistantRequest
from App.services.career_assistant import (
    CareerAssistantConfigurationError,
    answer_career_question,
)


class CareerAssistantTests(unittest.IsolatedAsyncioTestCase):
    async def test_answers_without_resume_and_includes_catalog(self):
        data = CareerAssistantRequest(
            question="How should I prepare for a software developer interview?",
            history=[
                CareerAssistantMessage(role="user", content="I am a new graduate."),
                CareerAssistantMessage(
                    role="assistant",
                    content="I can tailor suggestions for an entry-level role.",
                ),
            ],
        )
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Practice explaining a project and solving problems aloud."
                    )
                )
            ]
        )

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch("App.services.career_assistant.AsyncOpenAI") as openai_client,
        ):
            openai_client.return_value.chat.completions.create = AsyncMock(
                return_value=response
            )
            answer = await answer_career_question(data)

        self.assertIn("Practice explaining", answer)
        request_messages = (
            openai_client.return_value.chat.completions.create.await_args.kwargs[
                "messages"
            ]
        )
        self.assertIn("built_in_job_role_catalog", request_messages[0]["content"])
        self.assertIn("untrusted data", request_messages[0]["content"])
        self.assertEqual(request_messages[-1]["content"], data.question)
        self.assertEqual(
            [message["role"] for message in request_messages[1:3]],
            ["user", "assistant"],
        )

    async def test_redirects_questions_unrelated_to_careers(self):
        question = "Why does the Moon appear to change shape?"
        data = CareerAssistantRequest(question=question)
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="I can help with career-related questions. What would "
                        "you like to know about your career or job search?"
                    )
                )
            ]
        )

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch("App.services.career_assistant.AsyncOpenAI") as openai_client,
        ):
            openai_client.return_value.chat.completions.create = AsyncMock(
                return_value=response
            )
            answer = await answer_career_question(data)

        self.assertIn("career-related questions", answer)
        request_messages = (
            openai_client.return_value.chat.completions.create.await_args.kwargs[
                "messages"
            ]
        )
        self.assertIn("answer unrelated questions", request_messages[0]["content"])
        self.assertIn("career-related question", request_messages[0]["content"])
        self.assertEqual(request_messages[-1]["content"], question)

    async def test_reports_missing_api_key(self):
        data = CareerAssistantRequest(question="How do I prepare for an interview?")

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": ""}),
            patch("App.services.career_assistant.AsyncOpenAI") as openai_client,
        ):
            with self.assertRaises(CareerAssistantConfigurationError):
                await answer_career_question(data)

        openai_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
