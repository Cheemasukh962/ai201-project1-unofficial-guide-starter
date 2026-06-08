"""
query.py -- Retrieve relevant chunks and generate a grounded answer via Groq.

Usage:
  python query.py  (interactive CLI)
  from query import ask
"""

import os
from groq import Groq
from dotenv import load_dotenv
from embed import retrieve

load_dotenv()

CLIENT = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL  = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a California community college transfer advisor.
Answer the student's question using ONLY the course articulation information provided below.
Do not use any outside knowledge — if the answer is not in the provided documents, say so.
Always cite which source document(s) your answer comes from."""

def ask(question: str, cc_name: str = "American River College",
        uc_name: str = "UC Davis", k: int = 5) -> dict:
    """
    Retrieve top-k chunks then generate a grounded answer.
    Returns: {answer, sources, chunks}
    """
    chunks = retrieve(question, k=k, cc_name=cc_name, uc_name=uc_name)

    if not chunks:
        return {
            "answer":  "I could not find any relevant articulation data for that question.",
            "sources": [],
            "chunks":  [],
        }

    # Build context block from retrieved chunks
    context = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}"
        for c in chunks
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"Context documents:\n{context}\n\n"
            f"Student question: {question}"
        )},
    ]

    response = CLIENT.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.1,   # low temperature = more factual
        max_tokens=512,
    )

    answer  = response.choices[0].message.content
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # deduplicated, ordered

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    print("ASSIST Transfer Chatbot — ARC -> UC Davis")
    print("Type 'quit' to exit\n")
    while True:
        q = input("Your question: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        result = ask(q)
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}\n")
        print("-" * 60)
