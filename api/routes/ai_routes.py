"""AI insight routes."""

from __future__ import annotations

from typing import Any, Dict, List

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
        """Analyze recent journal entries (homepage history insights)."""
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Unauthorized"}), 401

        if not ai_service.enabled:
            return jsonify({"error": "AI insights is not configured on this server."}), 503

        data = request.get_json(silent=True) or {}

        history = data.get("history") or []
        if not isinstance(history, list):
            return jsonify({"error": "history must be an array of recent entries"}), 400
        history = _sanitize_history(history)
        if not history:
            return jsonify({"error": "history must include at least one journal entry"}), 400

        locale = str(data.get("locale") or "zh")[:10]
        limit = data.get("limit", 14)
        try:
            limit_value = int(limit)
        except (TypeError, ValueError):
            limit_value = 14

        try:
            result = ai_service.generate_insights(
                history=history,
                locale=locale,
                limit=limit_value,
            )
            return jsonify(result), 200
        except AIServiceError as exc:
            return jsonify({"error": exc.message}), exc.status_code
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": f"Unexpected AI error: {exc}"}), 500

    return bp


def _sanitize_history(history: List[Any]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for item in history[:30]:
        if not isinstance(item, dict):
            continue
        entry: Dict[str, Any] = {
            "date": str(item.get("date") or "")[:32],
            "content": str(item.get("content") or "")[:800],
        }
        mood = item.get("mood")
        if mood is not None:
            try:
                entry["mood"] = int(mood)
            except (TypeError, ValueError):
                pass
        # Skip completely empty shells
        if not entry["content"].strip() and entry.get("mood") is None:
            continue
        cleaned.append(entry)
    return cleaned
