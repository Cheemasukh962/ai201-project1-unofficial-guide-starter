"""
embed.py -- Embed all chunks with all-MiniLM-L6-v2 and store in ChromaDB.

Run once to build the vector store:
  python embed.py

Then import retrieve() from this module in query.py:
  from embed import retrieve
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from chunk import load_chunks

CHROMA_DIR  = os.path.join("data", "chroma")
COLLECTION  = "assist_articulations"
MODEL_NAME  = "all-MiniLM-L6-v2"
BATCH_SIZE  = 256   # embed this many chunks at a time to avoid memory spikes

# ── Build (or rebuild) the vector store ───────────────────────────────────────

def build_vector_store():
    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading chunks ...")
    chunks = load_chunks()
    print(f"  {len(chunks)} chunks from {len(set(c['source'] for c in chunks))} files")

    print(f"Connecting to ChromaDB at {CHROMA_DIR} ...")
    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    # Delete existing collection so re-runs start fresh
    try:
        client.delete_collection(COLLECTION)
        print("  Deleted existing collection")
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)

    print(f"Embedding and storing in batches of {BATCH_SIZE} ...")
    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        batch  = chunks[start : start + BATCH_SIZE]
        texts  = [c["text"]    for c in batch]
        ids    = [f"chunk_{start + i}" for i in range(len(batch))]
        metas  = [{
            "cc_name": c["cc_name"],
            "uc_name": c["uc_name"],
            "major":   c["major"],
            "source":  c["source"],
        } for c in batch]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metas)

        end = min(start + BATCH_SIZE, total)
        print(f"  [{end:4d}/{total}] stored")

    print(f"\nDone. {total} chunks embedded into ChromaDB collection '{COLLECTION}'")
    return collection, model

# ── Retrieve top-k chunks for a query ─────────────────────────────────────────

def retrieve(query: str, k: int = 5,
             cc_name: str = None, uc_name: str = None):
    """
    Embed the query and return the top-k most relevant chunks.

    Args:
        query:   natural language question
        k:       number of results to return
        cc_name: optional filter (e.g. "American River College")
        uc_name: optional filter (e.g. "UC Davis")

    Returns:
        list of dicts: {text, source, major, distance}
    """
    model      = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query]).tolist()

    # Build optional metadata filter
    where = {}
    if cc_name and uc_name:
        where = {"$and": [{"cc_name": {"$eq": cc_name}},
                           {"uc_name": {"$eq": uc_name}}]}
    elif cc_name:
        where = {"cc_name": {"$eq": cc_name}}
    elif uc_name:
        where = {"uc_name": {"$eq": uc_name}}

    kwargs = dict(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    docs   = results["documents"][0]
    metas  = results["metadatas"][0]
    dists  = results["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        output.append({
            "text":     doc,
            "source":   meta.get("source", ""),
            "major":    meta.get("major", ""),
            "distance": round(dist, 4),
        })
    return output

# ── Lazy singletons (avoid re-loading on every retrieve() call) ───────────────

_model      = None
_collection = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _get_collection():
    global _collection
    if _collection is None:
        client      = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION)
    return _collection

# ── CLI: embed + run retrieval test ───────────────────────────────────────────

if __name__ == "__main__":
    collection, model = build_vector_store()

    # Quick retrieval test with 3 of the 5 evaluation queries
    test_queries = [
        "Does MATH 400 at ARC satisfy MAT 021B Calculus at UC Davis?",
        "What ARC course satisfies ECS 020 Discrete Mathematics at UC Davis?",
        "Is there an ARC course equivalent to ECS 036A Programming at UC Davis?",
    ]

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        results = retrieve(query, k=5,
                           cc_name="American River College",
                           uc_name="UC Davis")
        for r in results:
            print(f"  [{r['distance']:.4f}] {r['text']}")
            print(f"           source: {r['source']}")
