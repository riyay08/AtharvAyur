"""Deterministic outbound guard. Runs on every LLM reply before it reaches the user.

Mirrors `safety_policy.py`'s style (regex + constants, no DB/HTTP/SDK) but is the
*outbound* bouncer: rather than blocking, it rewrites diagnostic-sounding claims
("you have X", "you are diagnosed with Y") into supportive, non-diagnostic
language and appends a disclaimer when a rewrite happens. Replies are always
delivered — this guard softens language, it never blocks (that's the inbound
`safety_policy`'s job).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_DIAGNOSTIC_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\byou (?:definitely |certainly )?have\b", re.IGNORECASE), "you may be experiencing"),
    (re.compile(r"\byou(?:'re| are) suffering from\b", re.IGNORECASE), "you may be experiencing"),
    (re.compile(r"\byou(?:'re| are) diagnosed with\b", re.IGNORECASE), "some people with similar patterns are diagnosed with"),
    (re.compile(r"\bi diagnose(?:d)? you with\b", re.IGNORECASE), "one possibility worth discussing with a clinician is"),
    (re.compile(r"\bthis is (?:a |an )?diagnosis\b", re.IGNORECASE), "this may be worth discussing with a clinician"),
    (re.compile(r"\byou need to take\b", re.IGNORECASE), "you may want to ask a clinician about"),
    (re.compile(r"\byou must take\b", re.IGNORECASE), "you may want to ask a clinician about"),
)

DISCLAIMER = (
    "This is general wellness information, not a medical diagnosis. "
    "Please consult a qualified clinician for personal medical advice."
)


@dataclass(frozen=True, slots=True)
class OutboundGuardResult:
    text: str
    rewritten: bool
    matched_patterns: tuple[str, ...]


def guard_reply(reply_text: str) -> OutboundGuardResult:
    """Rewrite diagnostic-sounding phrasing in `reply_text`, non-destructively.

    Returns the original text unchanged (with `rewritten=False`) when nothing
    matched. When a rewrite happens, a disclaimer is appended (unless already
    present) so the softened language doesn't stand alone without context.
    """
    if not reply_text or not reply_text.strip():
        return OutboundGuardResult(text=reply_text, rewritten=False, matched_patterns=())

    text = reply_text
    matched: list[str] = []
    for pattern, replacement in _DIAGNOSTIC_REWRITES:
        if pattern.search(text):
            matched.append(pattern.pattern)
            text = pattern.sub(replacement, text)

    if not matched:
        return OutboundGuardResult(text=reply_text, rewritten=False, matched_patterns=())

    if DISCLAIMER not in text:
        text = f"{text}\n\n{DISCLAIMER}"

    return OutboundGuardResult(text=text, rewritten=True, matched_patterns=tuple(matched))
