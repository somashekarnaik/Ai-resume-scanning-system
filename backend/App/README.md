## Career AI Assistant setup

The assistant uses the OpenAI API to answer career-related questions. Create `backend/.env`
from `backend/.env.example` and set `OPENAI_API_KEY` to your own API key. You can
optionally set `OPENAI_MODEL`; it defaults to `gpt-4o-mini`.

Install the backend dependencies with `pip install -r requirements.txt`, then restart
the FastAPI server. Keep the API key in the backend environment only; never add it to
frontend code or commit the `.env` file.

The assistant works without an uploaded resume and politely redirects unrelated
questions back to career topics. If a resume has been analyzed, it also
receives detected skills, the selected and recommended roles, match score, and
format-review findings to personalize relevant career advice. It does not receive the
original resume file. Questions and recent chat history are sent to OpenAI, as disclosed
in the chat panel. Without a valid API key or network access, the assistant cannot
generate answers; the API returns an explicit configuration or service error.