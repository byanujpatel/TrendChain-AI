from crypto_pulse.llm import ClaudeAnalyzer
from crypto_pulse.sample_data import load_sample_items


class ToolBlock:
    type = "tool_use"
    name = "submit"
    input = {"value": 1}


class ToolMessage:
    content = [ToolBlock()]


def test_extract_json_accepts_markdown_fence():
    result = ClaudeAnalyzer._extract_json('```json\n{"value": 1}\n```')
    assert result == {"value": 1}


def test_validate_exact_idea_counts():
    ideas = {
        "instagram_reels": [{} for _ in range(5)],
        "youtube_videos": [{} for _ in range(3)],
        "twitter_threads": [{} for _ in range(3)],
    }
    ClaudeAnalyzer._validate_idea_counts(ideas)


def test_evidence_payload_balances_platforms():
    payload = ClaudeAnalyzer._evidence_payload(load_sample_items(), limit=6)
    assert len({item["platform"] for item in payload}) >= 3


def test_tool_input_extracts_structured_payload():
    assert ClaudeAnalyzer._tool_input(ToolMessage(), "submit") == {"value": 1}
