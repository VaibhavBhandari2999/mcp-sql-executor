# summarizer.py
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

MODEL = os.getenv("OPENAI_MODEL")


def summarize(question: str, rows: List[Dict[str, Any]]) -> str:
    system = (
        "You are a helpful assistant that answers questions based solely on the provided database rows. "
        "Respond with required context from question and database rows and do not hallucinate."
    )

    user_content = (
        f"Question: {question}\n\n"
        f"Rows:\n{rows}\n\n"
        "Use only these rows to answer. If the answer is not present, say so."
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )

    return resp.choices[0].message.content.strip()
