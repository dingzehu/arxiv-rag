import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from google import genai

from app.config import settings
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.db import Chunk, Paper

TEST_TOPICS = [
    "transformer architecture",
    "attention mechanism",
    "BERT pre-training",
    "reinforcement learning from human feedback",
    "diffusion models"
    ]

CHUNK_PROMPT = """Generate exactly 2 questions whose answers are clearly stated in
this text.
Include exactly 1 medium-difficulty question and 1 easy or hard question.
Return ONLY a valid JSON array — no markdown, no explanation:
[
    {{
        "question": "...",
        "expected_answer": "...",
        "difficulty": "easy|medium|hard"
    }}
]
{chunk_text}"""

NEGATIVE_PROMPT = """Generate exactly 2 questions about {topic} in machine learning
research that CANNOT be answered from the papers published before 2025 or from the
following 5 core topics: transformer architecture, attention mechanism,
BERT pre-training, reinforcement learning from human feedback, diffusion models.
    
Use these strategies — choose 2 from 3:
1. Temporal cutoff: ask about benchmarks or results only available after 2024
2. Adjacent uncovered entities: ask about real models or papers outside the 5 topics
above
3. Overly specific implementation detail: ask about an internal detail not covered
in survey-level papers
        
The expected_answer must always be exactly:
"The indexed papers do not contain enough information to answer this question."
Return ONLY a valid JSON array — no markdown, no explanation:
[
    {{
    "question": "...",
    "expected_answer": "...",
    "difficulty": "negative"
    }}
]"""

async def fetch_random_chunks(n: int) -> list[tuple]:
    """Fetch random n (chunk_text, paper_title) pairs for prompt seeding."""

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Chunk.chunk_text, Paper.title)
            .join(Paper, Chunk.paper_id == Paper.id)
            .order_by(func.random())
            .limit(n)
        )

        return result.all()
        
def generate_pairs_for_chunk(
    client, chunk_text: str, paper_title: str
    ) -> list[dict]:
    """Calls Gemini to generate chunk_based question-answer pair."""
    
    chunk_prompt = CHUNK_PROMPT.format(chunk_text=chunk_text)

    results = client.models.generate_content(
        model=settings.gemini_model,
        contents=chunk_prompt,
    )

    pairs = json.loads(results.text)
    for pair in pairs:
        pair["paper_title"] = paper_title

    return pairs


def generate_negative_for_topic(client, test_topic: str) -> list[dict]:
    """Calls Gemini to generate negative question-answer pair."""

    negative_prompt = NEGATIVE_PROMPT.format(topic=test_topic)

    results = client.models.generate_content(
        model=settings.gemini_model,
        contents=negative_prompt,
    )

    return json.loads(results.text)


def main():
    client = genai.Client(api_key=settings.gemini_api_key)

    random_chunks = asyncio.run(fetch_random_chunks(10))

    all_pairs = []

    for chunk_text, paper_title in random_chunks:
        try:
            positive_pairs = generate_pairs_for_chunk(client, chunk_text, paper_title)
            all_pairs.extend(positive_pairs)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Chunk '{chunk_text}' from paper '{paper_title}' skipped: {e}")
            continue

    for topic in TEST_TOPICS:
        try:
            negative_pairs = generate_negative_for_topic(client, topic)
            all_pairs.extend(negative_pairs)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Skipped topic '{topic}': {e}")
            continue

    for i, pair in enumerate(all_pairs, start=1):
        pair["id"] = i

    OUTPUT_PATH = Path(__file__).resolve().parent / "golden_test_set.json"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, indent=2)
    
    print(f"{len(all_pairs)} pairs written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

