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
        history: Optional[List[Dict[str, Any]]] = None,
        locale: str = "zh",
        limit: int = 14,
    ) -> Dict[str, Any]:
        """Analyze recent journal entries (not a single in-progress draft)."""
        if not self.enabled:
            raise AIServiceError("AI insights is not configured (missing API key).", 503)

        entries = list(history or [])
        if not entries:
            raise AIServiceError("Need recent journal entries to analyze.", 400)

        # Prefer newest-first from client; take up to limit entries
        limit = max(3, min(int(limit or 14), 30))
        entries = entries[:limit]

        language = "Simplified Chinese" if str(locale).lower().startswith("zh") else "English"
        history_lines = self._format_history(entries)
        moods = [e.get("mood") for e in entries if e.get("mood") is not None]
        avg_mood = None
        if moods:
            try:
                avg_mood = round(sum(int(m) for m in moods) / len(moods), 2)
            except (TypeError, ValueError):
                avg_mood = None

        system = (
            "You are a compassionate journaling coach for the Nightlio mood tracker. "
            "The user wants a holistic review of their RECENT journals (multiple entries), "
            "not analysis of a single draft they are currently writing. "
            f"Output ONLY one JSON object. No markdown, no code fences, no extra text. "
            f"Every user-facing string MUST be written in {language}. "
            "Be concise, kind, practical, non-clinical; do not diagnose. "
            "Required keys exactly: summary (string), sentiment (object with label, score, emotions), "
            "tags (string array), trend_prediction (string), suggestions (string array). "
            "summary: overall insight across recent entries. "
            "sentiment: overall emotional tone of the period. "
            "tags: recurring themes/topics across entries (3-8). "
            "trend_prediction: near-term mood trend based on the sequence. "
            "suggestions: 2-4 personalized actionable tips. "
            "sentiment.label must be one of: positive, neutral, negative, mixed. "
            "sentiment.score is 0..1 how positive the period feels overall."
        )

        user = (
            f"Please analyze the following recent journal entries and return the JSON object now.\n"
            f"Entry count: {len(entries)}\n"
            f"Average mood score (1=terrible … 5=amazing): {avg_mood if avg_mood is not None else 'unknown'}\n"
            f"Entries (newest first):\n{history_lines}\n\n"
            "Focus on patterns across days, recurring themes, mood movement, and practical next steps.\n"
            "Remember: respond with JSON only."
        )

        raw = self._chat_completion(system=system, user=user)
        data = self._parse_json_object(raw)
        result = self._normalize(data)
        result["entry_count"] = len(entries)
        return result

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "(no recent history)"
        lines = []
        for item in history:
            d = item.get("date") or "?"
            m = item.get("mood")
            excerpt = str(item.get("content") or "").replace("\n", " ").strip()
            # Allow longer excerpts for multi-entry analysis
            if len(excerpt) > 280:
                excerpt = excerpt[:280] + "…"
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
