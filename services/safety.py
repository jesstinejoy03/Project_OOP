"""Simple safety check: show support information when an entry sounds serious.

This is deliberately conservative keyword matching, not a diagnosis tool. It is
meant to catch explicit self-harm language, not to judge how someone feels:
words like "hopelessly behind on revision" deliberately do not match, because a
false alarm on ordinary stress teaches users to ignore the prompt entirely.
"""
import re
from typing import Iterable, Optional

IMMEDIATE_CRISIS_WORDS = r"\b(?:kill|hang|stab|shoot|attack|maim|murder|strangle|poison|overdose|suicide|die|death)\b"

CRISIS_PATTERNS = [
    # explicit intent
    r"\bkill myself\b", r"\bend my life\b", r"\bsuicid", r"\bwant to die\b",
    r"\bdon'?t want to (be here|live)\b", r"\bhurt myself\b", r"\bself[- ]harm\b",
    r"\bno reason to live\b", r"\bbetter off without me\b",
    # explicit harm toward others
    r"\b(?:want to|plan to|going to|might)\s+(?:kill|hurt|attack|stab|shoot|maim|hang|smack|humiliate)\s+(?:someone|others|them|people|my (?:friend|partner|family|sibling|parent|child|sister|brother|wife|husband|daughter|son|boyfriend|girlfriend))\b",
    r"\b(?:kill|hurt|attack|stab|shoot|maim|hang|smack|humiliate)\s+(?:someone|others|them|people)\b",
    # despair / giving up
    r"\bcan'?t go on\b", r"\bnothing (matters|will ever (get better|change))\b",
    r"\bno (point|reason) in (anything|going on|trying)\b",
    r"\b(i'?m|i am|feel) (completely )?(worthless|hopeless)\b",
    r"\bnobody would (notice|care|miss me)\b",
    r"\b(?:i need|need) (?:someone|anyone) to (?:save|help) me\b",
    r"\b(?:i'?m|i am|feel) (?:completely )?(?:helpless|powerless|alone|trapped)\b",
    r"\b(?:i'?m|i am) (?:not )?going to make it\b",
    r"\b(?:i can'?t|i cannot|i can't) (?:cope|handle this|do this|go on|keep going)\b",
    r"\b(?:i don't|i do not) know how to go on\b",
    r"\b(?:i don't|i do not) know how to keep going\b",
]

SUPPORT_MESSAGE = (
    "What you wrote sounds really heavy, and you deserve support from a real person.\n\n"
    "Please consider contacting someone now: a trusted friend or family member, "
    "your university counselling service, or your local emergency number if you "
    "feel you might act on these thoughts.\n\n"
    "This app is a self-reflection tool. It cannot diagnose or treat anything.\n\n"
    "Remember, you are not alone. You deserve help and support, and there are people who want to listen and help you through this."
)


class SafetyCheck:
    """Flags text that should trigger the support message."""

    def __init__(self, patterns: Optional[Iterable[str]] = None):
        self._regexes = [re.compile(p, re.IGNORECASE)
                         for p in (list(patterns) if patterns else CRISIS_PATTERNS)]

    def needs_support(self, text: str) -> bool:
        if not text:
            return False
        if re.search(IMMEDIATE_CRISIS_WORDS, text, flags=re.IGNORECASE):
            return True
        return any(rx.search(text) for rx in self._regexes)
