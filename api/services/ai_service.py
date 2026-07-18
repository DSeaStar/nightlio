"""LLM-backed mood/journal insights (OpenAI-compatible chat completions)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class AIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIService:
    """Call an OpenAI-compatible API (default: SpaceXAI / xAI)."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.x.ai/v1",
        model: str = "grok-4.5",
        timeout: int = 60,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "https://api.x.ai/v1").rstrip("/")
        self.model = model or "grok-4.5"
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate_insights(
        self,
        *,
        content: str,
        mood: Optional[int] = None,
        date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        locale: str = "zh",
    ) -> Dict[str, Any]:
        if not self.enabled:
            raise AIServiceError("AI insights is not configured (missing API key).", 503)

        text = (content or "").strip()
        if not text:
            raise AIServiceError("Journal content is required.", 400)
        if len(text) > 12000:
            text = text[:12000] + "\n…(truncated)"

        language = "Simplified Chinese" if str(locale).lower().startswith("zh") else "English"
        history_lines = self._format_history(history or [])
        tag_line = ", ".join(tags or []) if tags else "(none)"
        mood_line = str(mood) if mood is not None else "(unknown)"

        system = (
            "You are a compassionate journaling coach for the Nightlio mood tracker. "
            f"Output ONLY one JSON object. No markdown, no code fences, no extra text. "
            f"Every user-facing string MUST be written in {language}. "
            "Be concise, kind, practical, non-clinical; do not diagnose. "
            "Required keys exactly: summary (string), sentiment (object with label, score, emotions), "
            "tags (string array), trend_prediction (string), suggestions (string array). "
            "sentiment.label must be one of: positive, neutral, negative, mixed. "
            "sentiment.score is a number from 0 to 1. Provide 3-8 tags and 2-4 suggestions."
        )

        user = (
            f"Please analyze this journal entry and return the JSON object now.\n\n"
            f"Entry date: {date or 'unknown'}\n"
            f"Mood score (1=terrible … 5=amazing): {mood_line}\n"
            f"Selected tags: {tag_line}\n"
            f"Recent history (newest last):\n{history_lines}\n\n"
            f"Journal entry:\n{text}\n\n"
            "Remember: respond with JSON only."
        )

        raw = self._chat_completion(system=system, user=user)
        data = self._parse_json_object(raw)
        return self._normalize(data)

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "(no recent history)"
        lines = []
        for item in history[-14:]:
            d = item.get("date") or "?"
            m = item.get("mood")
            excerpt = str(item.get("content") or "").replace("\n", " ").strip()
            if len(excerpt) > 120:
                excerpt = excerpt[:120] + "…"
            lines.append(f"- {d} | mood={m} | {excerpt}")
        return "\n".join(lines)

    def _chat_completion(self, *, system: str, user: str) -> str:
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            msg = f"LLM API error {exc.code}"
            try:
                err_json = json.loads(err_body)
                if isinstance(err_json, dict):
                    detail = (
                        err_json.get("error", {}).get("message")
                        if isinstance(err_json.get("error"), dict)
                        else err_json.get("error") or err_json.get("message")
                    )
                    if detail:
                        msg = f"{msg}: {detail}"
            except Exception:
                if err_body:
                    msg = f"{msg}: {err_body[:300]}"
            raise AIServiceError(msg, 502) from exc
        except urllib.error.URLError as exc:
            raise AIServiceError(f"LLM API unreachable: {exc.reason}", 502) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIServiceError("LLM returned non-JSON response.", 502) from exc

        choices = data.get("choices") or []
        if not choices:
            raise AIServiceError("LLM returned no choices.", 502)
        message = choices[0].get("message") or {}
        content = message.get("content")
        # Some reasoning models put final text in alternative fields
        if not content:
            content = (
                message.get("reasoning_content")
                or choices[0].get("text")
                or data.get("output_text")
            )
        if not content:
            raise AIServiceError("LLM returned empty content.", 502)
        return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        # last resort: first {...} block
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start : end + 1])
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        raise AIServiceError("Could not parse AI insight JSON.", 502)

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sentiment = data.get("sentiment") if isinstance(data.get("sentiment"), dict) else {}
        label = str(sentiment.get("label") or "mixed").lower()
        if label not in {"positive", "neutral", "negative", "mixed"}:
            label = "mixed"
        try:
            score = float(sentiment.get("score", 0.5))
        except (TypeError, ValueError):
            score = 0.5
        score = max(0.0, min(1.0, score))

        emotions = sentiment.get("emotions") or []
        if not isinstance(emotions, list):
            emotions = []
        emotions = [str(e).strip() for e in emotions if str(e).strip()][:8]

        tags = data.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip() for t in tags if str(t).strip()][:10]

        suggestions = data.get("suggestions") or []
        if not isinstance(suggestions, list):
            suggestions = []
        suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:6]

        summary = str(data.get("summary") or data.get("insight") or "").strip()
        trend = str(
            data.get("trend_prediction")
            or data.get("trend")
            or data.get("prediction")
            or ""
        ).strip()

        # If model returned mostly empty structured fields, keep a useful fallback
        if not summary and not tags and not suggestions and not trend:
            raise AIServiceError("AI returned empty insight fields.", 502)

        return {
            "summary": summary,
            "sentiment": {
                "label": label,
                "score": score,
                "emotions": emotions,
            },
            "tags": tags,
            "trend_prediction": trend,
            "suggestions": suggestions,
            "model": self.model,
        }
