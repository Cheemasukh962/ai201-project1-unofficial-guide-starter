from embed import retrieve

queries = [
    "Does MATH 400 at ARC satisfy MAT 021B Calculus at UC Davis?",
    "What ARC course satisfies ECS 020 Discrete Mathematics at UC Davis?",
    "Is there an ARC course equivalent to ECS 036A Programming at UC Davis?",
]

for q in queries:
    print(f"QUERY: {q}")
    results = retrieve(q, k=5, cc_name="American River College", uc_name="UC Davis")
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")
        print(f"           source: {r['source']}")
    print()
