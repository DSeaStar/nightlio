"""AI insight routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

try:
    from api.services.ai_service import AIService, AIServiceError
    from api.utils.auth_middleware import get_current_user_id, require_auth
except ImportError:  # pragma: no cover
    from services.ai_service import AIService, AIServiceError  # type: ignore
    from utils.auth_middleware import get_current_user_id, require_auth  # type: ignore


def create_ai_routes(ai_service: AIService):
    bp = Blueprint("ai", __name__)

    @bp.route("/ai/insights", methods=["POST"])
    @require_auth
    def generate_insights():
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        if not ai_service.enabled:
            return jsonify({"error": "AI insights is not configured on this server."}), 503

        data = request.get_json(silent=True) or {}
        content = data.get("content")
        if not content or not str(content).strip():
            return jsonify({"error": "content is required"}), 400

        mood = data.get("mood")
        mood_value: Optional[int] = None
        if mood is not None and mood != "":
            try:
                mood_value = int(mood)
            except (TypeError, ValueError):
                return jsonify({"error": "mood must be an integer 1-5"}), 400
            if mood_value < 1 or mood_value > 5:
                return jsonify({"error": "mood must be between 1 and 5"}), 400

        tags = data.get("tags") or []
        if not isinstance(tags, list):
            return jsonify({"error": "tags must be an array"}), 400
        tags = [str(t) for t in tags][:20]

        history = data.get("history") or []
        if not isinstance(history, list):
            return jsonify({"error": "history must be an array"}), 400
        history = _sanitize_history(history)

        locale = str(data.get("locale") or "zh")[:10]
        date = data.get("date")
        date_value = str(date) if date is not None else None

        try:
            result = ai_service.generate_insights(
                content=str(content),
                mood=mood_value,
                date=date_value,
                tags=tags,
                history=history,
                locale=locale,
            )
            return jsonify(result), 200
        except AIServiceError as exc:
            return jsonify({"error": exc.message}), exc.status_code
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": f"Unexpected AI error: {exc}"}), 500

    return bp


def _sanitize_history(history: List[Any]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for item in history[:20]:
        if not isinstance(item, dict):
            continue
        entry: Dict[str, Any] = {
            "date": str(item.get("date") or "")[:32],
            "content": str(item.get("content") or "")[:400],
        }
        mood = item.get("mood")
        if mood is not None:
            try:
                entry["mood"] = int(mood)
            except (TypeError, ValueError):
                pass
        cleaned.append(entry)
    return cleaned
