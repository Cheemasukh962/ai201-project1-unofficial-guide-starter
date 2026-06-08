from query import ask

questions = [
    "What ARC course satisfies ECS 036B Object Oriented Programming in C++ at UC Davis?",
    "What ARC course counts for CMN 001 Introduction to Public Speaking at UC Davis?",
    "What ARC course satisfies PHI 001 Introduction to Philosophy at UC Davis?",
    "What ARC course transfers as ANT 001 Human Evolutionary Biology at UC Davis?",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print("="*60)
    result = ask(q)
    print(result["answer"])
    print(f"\nSources: {result['sources'][0] if result['sources'] else 'none'}")
