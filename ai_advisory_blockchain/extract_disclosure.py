"""
Structured disclosure-extraction component.

This is deterministic keyword/regex logic, NOT an autonomous agent -- it is a
single-purpose extraction function used as a supporting utility by the
debate / advisory workflow.

Implements extract_signals(snippet) -> dict with:
    risk_flags: list[str]
    hedging_detected: bool
    sentiment: "confident" | "cautious" | "neutral"

Mock-mode rule (graded baseline, no LLM call):
    - risk_flags: flag "litigation", "regulatory", or "customer
      concentration"-style phrasing.
    - hedging_detected: True if the snippet contains "assuming",
      "cautiously", or "visibility".
    - sentiment: "confident" if the snippet contains "confident" or
      "approved"; "cautious" if it contains a hedging phrase (i.e.
      hedging_detected is True); otherwise "neutral".

Works entirely without an LLM.

Run:
    python extract_disclosure.py
"""

import re

RISK_KEYWORDS = {
    "litigation": [r"\blitigation\b", r"\blawsuit\b", r"\blegal (dispute|proceeding)\b"],
    "regulatory": [r"\bregulator(y|s)?\b", r"\bregulatory notice\b", r"\bcompliance\b"],
    "customer_concentration": [r"\btop (three|3|two|2|five|5) customers?\b", r"\bconcentration\b",
                                r"percent of total revenue"],
}

HEDGING_WORDS = [r"\bassuming\b", r"\bcautiously\b", r"\bvisibility\b"]
CONFIDENT_WORDS = [r"\bconfident\b", r"\bapproved\b"]


def _any_match(patterns, text):
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def extract_signals(snippet):
    text = snippet.lower()

    risk_flags = [category for category, patterns in RISK_KEYWORDS.items() if _any_match(patterns, text)]
    hedging_detected = _any_match(HEDGING_WORDS, text)

    if _any_match(CONFIDENT_WORDS, text):
        sentiment = "confident"
    elif hedging_detected:
        sentiment = "cautious"
    else:
        sentiment = "neutral"

    return {
        "risk_flags": risk_flags,
        "hedging_detected": hedging_detected,
        "sentiment": sentiment,
    }


def main():
    from disclosure_snippets import DISCLOSURE_SNIPPETS

    for snippet in DISCLOSURE_SNIPPETS:
        signals = extract_signals(snippet)
        print("-" * 70)
        print(snippet)
        print(signals)


if __name__ == "__main__":
    main()
