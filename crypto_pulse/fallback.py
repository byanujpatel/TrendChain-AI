from __future__ import annotations

import re
from collections import Counter
from typing import Any

from crypto_pulse.models import ContentItem


STOP_WORDS = {
    "about", "after", "again", "against", "because", "being", "crypto", "from",
    "have", "into", "just", "more", "that", "their", "this", "what", "when",
    "where", "which", "with", "would", "your",
}


def analyze_without_llm(items: list[ContentItem]) -> dict[str, Any]:
    words: Counter[str] = Counter()
    for item in items:
        words.update(
            word
            for word in re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", item.title.lower())
            if word not in STOP_WORDS
        )
    topics = [word.title() for word, _ in words.most_common(6)]
    top_titles = [item.title for item in items[:5]]
    return {
        "trending_topics": topics or ["Bitcoin", "Stablecoins", "Regulation"],
        "viral_hooks": [
            "The hidden cost nobody is talking about",
            "What this means for ordinary investors",
            "Everyone celebrated this news, but there is a catch",
            "The chart looks bullish. The story underneath does not",
            "Before you copy this trade, understand the risk",
        ],
        "emotions": ["curiosity", "fear", "surprise", "regret", "hope"],
        "storytelling_patterns": [
            "surprising claim -> simple explanation -> consequence",
            "popular belief -> contrarian evidence -> audience question",
            "personal mistake -> lesson -> practical checklist",
            "breaking event -> winners and losers -> what happens next",
        ],
        "audience_questions": [
            f"Why is {topic} trending now?" for topic in (topics[:3] or ["Bitcoin"])
        ],
        "evidence_headlines": top_titles,
        "summary": (
            "The strongest content combines a current event with conflict, a simple analogy, "
            "and a clear consequence for the viewer."
        ),
    }


def generate_without_llm(
    patterns: dict[str, Any], items: list[ContentItem]
) -> dict[str, list[dict[str, Any]]]:
    topics = patterns.get("trending_topics") or ["Bitcoin", "Stablecoins", "Regulation"]
    source_urls = [item.url for item in items[:8] if item.url]

    def topic(index: int) -> str:
        return topics[index % len(topics)]

    reels = [
        _idea(
            f"Nobody explains the dangerous side of {topic(i)} this simply",
            topic(i),
            angle,
            "instagram_reel",
            source_urls[i : i + 2],
            ["Open with a one-line contradiction", "Explain it using a visual analogy",
             "Show who wins and loses", "End with a question viewers will debate"],
        )
        for i, angle in enumerate(
            [
                "Turn a technical story into a left-pocket versus right-pocket analogy.",
                "Start with the popular belief, then reveal the overlooked downside.",
                "Tell the story through one investor's avoidable mistake.",
                "Compare the headline with what the engagement data actually shows.",
                "Explain the issue as a 30-second winners-versus-losers breakdown.",
            ]
        )
    ]
    youtube = [
        _idea(
            hook,
            topic(i),
            angle,
            "youtube",
            source_urls[i : i + 3],
            ["Cold open with the highest-stakes consequence", "Give the timeline",
             "Explain both sides with evidence", "Close with scenarios, not price promises"],
        )
        for i, (hook, angle) in enumerate(
            [
                ("The crypto story everyone is misreading right now",
                 "A research-led investigation separating the headline from the real narrative."),
                ("I analyzed the most viral crypto discussions this month",
                 "Reverse-engineer the hooks, emotions, and stories that drove engagement."),
                ("The next phase of crypto will not look like the last one",
                 "Connect regulation, institutions, stablecoins, and user behavior."),
            ]
        )
    ]
    threads = [
        _idea(
            hook,
            topic(i),
            angle,
            "twitter_thread",
            source_urls[i : i + 3],
            ["Tweet 1: sharp claim", "Tweets 2-4: evidence and context",
             "Tweets 5-7: implications", "Final tweet: question and source links"],
        )
        for i, (hook, angle) in enumerate(
            [
                ("7 signals hiding inside today's crypto headlines",
                 "Convert separate stories into one clear market narrative."),
                ("The strongest argument for crypto is also its biggest risk",
                 "Build a balanced thesis using opposing community reactions."),
                ("Most people will learn this crypto lesson too late",
                 "Use mistakes and regret as the story, followed by a practical checklist."),
            ]
        )
    ]
    return {"instagram_reels": reels, "youtube_videos": youtube, "twitter_threads": threads}


def _idea(
    hook: str,
    topic: str,
    angle: str,
    platform: str,
    evidence_urls: list[str],
    outline: list[str],
) -> dict[str, Any]:
    return {
        "platform": platform,
        "hook": hook,
        "topic": topic,
        "angle": angle,
        "outline": outline,
        "evidence_urls": evidence_urls,
    }

