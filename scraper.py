"""
scraper.py -- Fetch ARC -> UC Davis articulation agreements from ASSIST.org.

Uses Playwright to navigate the ASSIST UI and intercept API responses.
Clicking each major in the list triggers the articulation detail API call.
Saves one .txt file per major to data/raw/.

Run: python scraper.py  (~5-8 minutes for all 120 ARC->UCD agreements)
"""

import json
import os
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Constants ─────────────────────────────────────────────────────────────────

SENDING_ID   = 27   # American River College
RECEIVING_ID = 89   # UC Davis
YEAR_ID      = 75   # 2024-25

LIST_URL = (
    f"https://assist.org/transfer/results"
    f"?year={YEAR_ID}&institution={SENDING_ID}"
    f"&agreement={RECEIVING_ID}&agreementType=to&view=agreement"
)

OUTPUT_DIR = os.path.join("data", "raw")

# ── Parse articulation JSON into course pair text ─────────────────────────────

def parse_agreement(result_obj, major_name):
    """
    result_obj: the 'result' dict inside the articulation API response.
    articulations is a double-encoded JSON string inside result_obj.
    Returns (lines, pair_count).
    """
    lines = [
        f"Major: {major_name}",
        "CC: American River College -> UC: UC Davis",
        "",
    ]

    raw = result_obj.get("articulations", "[]")
    try:
        articulations = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        articulations = []

    pair_count = 0
    for item in articulations:
        art    = item.get("articulation", {})
        uc_str = _fmt_course(art.get("course", {}))
        cc_str = _fmt_sending(art.get("sendingArticulation", {}))

        if uc_str and cc_str:
            lines.append(f"UC course:  {uc_str}")
            lines.append(f"CC course:  {cc_str}")
            lines.append("")
            pair_count += 1
        elif uc_str and art.get("sendingArticulation", {}).get("noArticulationReason"):
            lines.append(f"UC course:  {uc_str}")
            lines.append(f"CC course:  No articulation")
            lines.append("")
            pair_count += 1

    return lines, pair_count


def _fmt_course(c):
    prefix = c.get("prefix", "")
    number = c.get("courseNumber", "")
    title  = (c.get("courseTitle") or "").strip()
    if not (prefix or number or title):
        return ""
    return f"{prefix} {number} - {title}".strip()


def _fmt_sending(sending):
    groups = sending.get("items", [])
    group_strs = []
    for group in groups:
        courses = group.get("items", [])
        conj    = (group.get("courseConjunction") or "And").lower()
        sep     = " AND " if conj == "and" else " OR "
        parts   = [_fmt_course(c) for c in courses]
        parts   = [p for p in parts if p]
        if parts:
            group_strs.append(sep.join(parts))
    return " / ".join(group_strs)


def save_file(lines, major_name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe = (major_name.replace(" ", "_")
                      .replace("/", "-")
                      .replace(",", "")
                      .replace("(", "").replace(")", "")
                      .replace("&", "and"))
    path = os.path.join(OUTPUT_DIR, f"American_River_College_UC_Davis_{safe}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting ASSIST scraper (Playwright navigate-and-intercept mode)")
    print(f"ARC (id={SENDING_ID}) -> UC Davis (id={RECEIVING_ID}), year {YEAR_ID}")

    captured_list = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()

        # --- Step 1: load the list page, intercept agreements list ----------
        def on_response(response):
            if ("/api/agreements" in response.url
                    and "categoryCode=major" in response.url
                    and response.status == 200):
                try:
                    captured_list["data"] = response.json()
                except Exception:
                    pass

        page.on("response", on_response)
        print("Navigating to ARC -> UC Davis list ...")
        page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        if "data" not in captured_list:
            print("ERROR: failed to capture agreements list")
            browser.close()
            return

        all_entries = (captured_list["data"].get("reports", [])
                       + captured_list["data"].get("allReports", []))
        print(f"Found {len(all_entries)} agreements to scrape\n")

        # --- Step 2: click each major to trigger the articulation API call --
        saved   = []
        skipped = []

        for i, entry in enumerate(all_entries):
            key   = entry.get("key", "")
            label = entry.get("label", key)

            print(f"[{i+1:3d}/{len(all_entries)}] {label}", end="", flush=True)

            try:
                # Wait for the articulation response while clicking the major
                with page.expect_response(
                    lambda r, k=key: (
                        "/api/articulation/Agreements" in r.url
                        and k in r.url
                        and r.status == 200
                    ),
                    timeout=15000
                ) as resp_info:
                    # Click the major by its label text
                    el = page.query_selector(f"text={label}")
                    if not el:
                        # Try partial match
                        truncated = label[:30]
                        el = page.query_selector(f"text={truncated}")
                    if not el:
                        print(f" -- element not found, skipping")
                        skipped.append(label)
                        continue
                    el.click()

                detail_data = resp_info.value.json()
                result_obj  = detail_data.get("result", {})
                lines, n    = parse_agreement(result_obj, label)
                path        = save_file(lines, label)
                saved.append(path)
                print(f" -- {n} pairs")

                # Navigate back to list for the next click
                page.goto(LIST_URL, wait_until="networkidle", timeout=20000)
                time.sleep(0.5)

            except PlaywrightTimeout:
                print(f" -- timeout (no API response)")
                skipped.append(label)
                page.goto(LIST_URL, wait_until="networkidle", timeout=20000)
                time.sleep(0.5)
            except Exception as e:
                print(f" -- error: {e}")
                skipped.append(label)
                try:
                    page.goto(LIST_URL, wait_until="networkidle", timeout=20000)
                    time.sleep(0.5)
                except Exception:
                    pass

        browser.close()

    print(f"\nSaved: {len(saved)} files  |  Skipped: {len(skipped)}")
    if skipped:
        print("Skipped:", skipped[:10])

    if saved:
        print(f"\nPreview of {os.path.basename(saved[0])} (first 25 lines):")
        with open(saved[0], encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 25:
                    break
                print(line, end="")


if __name__ == "__main__":
    main()
