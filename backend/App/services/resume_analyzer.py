from collections import Counter
import math
import re

from .skill_extractor import extract_skills

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "with",
}
WORD_PATTERN = re.compile(r"[a-z0-9][a-z0-9+#.]*", re.IGNORECASE)


def _tokenize(text):
    """Return meaningful terms for the lightweight TF-IDF similarity score."""
    return [
        word.lower()
        for word in WORD_PATTERN.findall(text)
        if word.lower() not in STOP_WORDS
    ]


def calculate_similarity(resume_text, job_description):
    if not resume_text.strip() or not job_description.strip():
        return 0

    documents = [_tokenize(resume_text), _tokenize(job_description)]
    if not documents[0] or not documents[1]:
        return 0

    document_frequency = Counter()
    for document in documents:
        document_frequency.update(set(document))

    vectors = []
    for document in documents:
        counts = Counter(document)
        document_length = len(document)
        vectors.append(
            {
                term: (count / document_length)
                * (math.log((1 + len(documents)) / (1 + document_frequency[term])) + 1)
                for term, count in counts.items()
            }
        )

    first, second = vectors
    dot_product = sum(weight * second.get(term, 0) for term, weight in first.items())
    first_magnitude = math.sqrt(sum(weight ** 2 for weight in first.values()))
    second_magnitude = math.sqrt(sum(weight ** 2 for weight in second.values()))
    if not first_magnitude or not second_magnitude:
        return 0

    return round((dot_product / (first_magnitude * second_magnitude)) * 100, 2)


def analyze_resume(resume_text, job_description):
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)

    matched_skills = [skill for skill in job_skills if skill in resume_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]

    if job_skills:
        skill_score = (len(matched_skills) / len(job_skills)) * 100
    else:
        skill_score = 0

    similarity_score = calculate_similarity(resume_text, job_description)
    overall_score = (skill_score * 0.6) + (similarity_score * 0.4)

    recommendations = [
        f"Consider adding {skill} if you have experience with it."
        for skill in missing_skills
    ]

    if not recommendations:
        recommendations.append("Your resume matches the required skills well.")

    return {
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_score": round(skill_score, 2),
        "similarity_score": similarity_score,
        "overall_score": round(overall_score, 2),
        "recommendations": recommendations,
    }
