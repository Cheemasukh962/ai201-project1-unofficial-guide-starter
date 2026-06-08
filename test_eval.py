"""Test the top 5 evaluation questions end-to-end through the full RAG pipeline."""
from query import ask

questions = [
    "What ARC course satisfies PSC 001 General Psychology at UC Davis?",
    "What ARC course satisfies CHE 129A Organic Chemistry Laboratory at UC Davis?",
    "What ARC course counts for ANT 001 Introduction to Anthropology at UC Davis?",
    "What ARC course transfers as SOC 001 Introduction to Sociology at UC Davis?",
    "What ARC course counts for MAT 021A Calculus at UC Davis?",
    # Failure case — genuinely vague query with no good match
    "Does ARC have an English composition course that transfers to UC Davis?",
]

for i, q in enumerate(questions, 1):
    print(f"\n{'='*60}")
    print(f"Q{i}: {q}")
    print("="*60)
    result = ask(q)
    print(f"Answer:\n{result['answer']}")
    print(f"\nSources: {', '.join(result['sources'])}")
