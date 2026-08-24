"""
Shared LLM access point for advisory_agent.py, debate.py, and (optionally)
extract_disclosure.py.

Default mode is MOCK_LLM=1: no API key required, deterministic Python
templates are used everywhere. The LLM is only ever used for reasoning /
explanation / narrative text -- never for numeric financial calculations,
which are always performed directly in Python.

Optional real-LLM mode (MOCK_LLM=0) calls Groq's OpenAI-compatible API:
    LLM_PROVIDER=groq
    GROQ_API_KEY=...
    LLM_MODEL=openai/gpt-oss-120b
    MOCK_LLM=0

If the real call fails for any reason (missing key, network, missing
`openai` package), this silently falls back to the provided mock response
so the project never hard-fails on the LLM being unavailable.
"""

import os


def is_mock():
    return os.environ.get("MOCK_LLM", "1") == "1"


def call_llm(system_prompt, user_prompt, mock_response):
    if is_mock():
        return mock_response

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return mock_response

    model = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as exc:  # network / auth / package errors all fall back
        return f"{mock_response}\n[note: live LLM call failed ({exc}); showing deterministic fallback]"
