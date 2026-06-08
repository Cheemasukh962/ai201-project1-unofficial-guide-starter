"""Test a set of candidate questions and show top retrieval result for each."""
from embed import retrieve

candidates = [
    # Calculus
    "What ARC course counts for MAT 021A Calculus at UC Davis?",
    "What ARC course transfers as MATH 401 Calculus II to UC Davis?",
    # Biology
    "Does ARC have a course for BIS 002A Introduction to Biology at UC Davis?",
    "What ARC biology course satisfies BIS 002C Biodiversity at UC Davis?",
    # Chemistry
    "What ARC course satisfies CHE 129A Organic Chemistry at UC Davis?",
    "Does ARC have an equivalent to CHE 002A General Chemistry at UC Davis?",
    # Computer Science
    "What ARC course counts for ECS 020 Discrete Mathematics at UC Davis?",
    "Does ARC offer anything equivalent to ECS 050 Computer Organization?",
    "What ARC course satisfies ECS 036B Object Oriented Programming at UC Davis?",
    # Physics
    "What ARC course satisfies PHY 009A Physics at UC Davis?",
    "Does ARC have a course for MAT 021C Calculus at UC Davis?",
    # Other
    "What ARC course counts for CMN 001 Public Speaking at UC Davis?",
    "What ARC course satisfies POL 001 American Government at UC Davis?",
    "Does ARC have an English composition course that transfers to UC Davis?",
    "What ARC course satisfies PHIL 001 Introduction to Philosophy at UC Davis?",
    "What ARC course transfers as SOC 001 Introduction to Sociology?",
    "Does ARC have a statistics course that counts at UC Davis?",
    "What ARC course satisfies PSC 001 General Psychology at UC Davis?",
    "What ARC course counts for ANT 001 Introduction to Anthropology?",
]

results = []
for q in candidates:
    top = retrieve(q, k=1, cc_name="American River College", uc_name="UC Davis")
    if top:
        r = top[0]
        results.append((r["distance"], q, r["text"]))

results.sort()
print("Questions ranked by retrieval distance (lower = better match)\n")
for dist, q, text in results:
    print(f"[{dist:.4f}] {q}")
    print(f"         -> {text[:90]}")
    print()
