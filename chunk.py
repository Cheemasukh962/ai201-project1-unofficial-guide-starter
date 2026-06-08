"""
chunk.py -- Split raw ASSIST .txt files into one chunk per course equivalency pair.

Each chunk is a dict with keys:
  text     -- the human-readable pair text
  cc_name  -- "American River College"
  uc_name  -- "UC Davis"
  major    -- e.g. "Computer Science B.S."
  source   -- filename (for attribution)

Usage:
  from chunk import load_chunks
  chunks = load_chunks()
"""

import os
import re

RAW_DIR = os.path.join("data", "raw")

CC_NAME = "American River College"
UC_NAME = "UC Davis"


def load_chunks(raw_dir=RAW_DIR, skip_all_majors=True):
    """
    Load all .txt files in raw_dir and return a flat list of chunk dicts.
    Chunk strategy: one pair per chunk (UC course line + CC course line).
    No overlap — pairs are independent facts.

    skip_all_majors: exclude All_Majors.txt which duplicates pairs from
    every individual major file and floods retrieval results.
    """
    all_chunks = []
    seen_texts = set()   # deduplicate by text content

    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith(".txt"):
            continue
        if skip_all_majors and "All_Majors" in filename:
            continue

        filepath = os.path.join(raw_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            text = f.read()

        major = _extract_major(text, filename)
        pairs = _extract_pairs(text)

        for pair_text in pairs:
            if pair_text in seen_texts:
                continue
            seen_texts.add(pair_text)

            all_chunks.append({
                "text":    pair_text,
                "cc_name": CC_NAME,
                "uc_name": UC_NAME,
                "major":   major,
                "source":  filename,
            })

    return all_chunks


def _extract_major(text, filename):
    """Pull the major name from the 'Major: ...' header line, or fall back to filename."""
    m = re.search(r"^Major:\s*(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Fallback: derive from filename
    # e.g. American_River_College_UC_Davis_Computer_Science_B.S..txt
    name = filename.replace("American_River_College_UC_Davis_", "").replace(".txt", "")
    return name.replace("_", " ")


def _extract_pairs(text):
    """
    Split document text into course equivalency pairs.
    A pair is two consecutive non-empty lines:
      UC course:  ...
      CC course:  ...
    Blank lines separate pairs.
    Returns list of strings like "UC course: X\nCC course: Y".
    """
    pairs = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("UC course:"):
            uc_line = line
            # Look for the CC course on the very next non-empty line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith("CC course:"):
                cc_line = lines[j].strip()
                pairs.append(f"{uc_line}\n{cc_line}")
                i = j + 1
                continue
        i += 1

    return pairs


if __name__ == "__main__":
    import random

    chunks = load_chunks()
    print(f"Total chunks loaded: {len(chunks)}")
    print(f"Files processed: {len(set(c['source'] for c in chunks))}")
    print()

    # Print 5 random chunks for inspection
    print("=== 5 random chunks (spot-check) ===")
    samples = random.sample(chunks, min(5, len(chunks)))
    for i, chunk in enumerate(samples, 1):
        print(f"\n--- Chunk {i} (source: {chunk['source']}, major: {chunk['major']}) ---")
        print(chunk["text"])

    # Quality checks
    print("\n=== Quality checks ===")
    empty = [c for c in chunks if not c["text"].strip()]
    print(f"Empty chunks:          {len(empty)}")

    no_uc = [c for c in chunks if "UC course:" not in c["text"]]
    print(f"Missing UC course:     {len(no_uc)}")

    no_cc = [c for c in chunks if "CC course:" not in c["text"]]
    print(f"Missing CC course:     {len(no_cc)}")

    lens = [len(c["text"]) for c in chunks]
    print(f"Avg chunk length:      {sum(lens)//len(lens)} chars")
    print(f"Min chunk length:      {min(lens)} chars")
    print(f"Max chunk length:      {max(lens)} chars")

    if len(chunks) < 50:
        print("\nWARNING: fewer than 50 chunks — check that raw files have content")
    elif len(chunks) > 5000:
        print("\nNOTE: more than 5000 chunks — retrieval may need a higher top-k")
    else:
        print(f"\nChunk count looks good ({len(chunks)} total)")
