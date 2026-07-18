import json
from api.services.ai_service import AIService


def test_normalize_and_parse_json():
    svc = AIService(api_key="test", base_url="https://example.com/v1", model="test-model")
    raw = json.dumps(
        {
            "summary": "今天整体平稳。",
            "sentiment": {"label": "positive", "score": 0.8, "emotions": ["平静", "期待"]},
            "tags": ["工作", "休息"],
            "trend_prediction": "若保持作息，情绪有望继续向好。",
            "suggestions": ["今晚早点睡", "散步 15 分钟"],
        }
    )
    data = svc._parse_json_object(raw)
    out = svc._normalize(data)
    assert out["summary"]
    assert out["sentiment"]["label"] == "positive"
    assert out["tags"] == ["工作", "休息"]
    assert len(out["suggestions"]) == 2
    assert out["model"] == "test-model"


def test_parse_fenced_json():
    svc = AIService(api_key="test")
    raw = """```json
{"summary":"ok","sentiment":{"label":"neutral","score":0.5,"emotions":[]},"tags":["a"],"trend_prediction":"t","suggestions":["s"]}
```"""
    data = svc._parse_json_object(raw)
    assert data["summary"] == "ok"
