import os
import sys
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the project root (parent directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Support running as a package (api.*) and from within the api/ directory
MusicService = None  # type: ignore
create_music_routes = None  # type: ignore
AIService = None  # type: ignore
create_ai_routes = None  # type: ignore

try:
    from api.database import MoodDatabase
    from api.services.mood_service import MoodService
    from api.services.goal_service import GoalService
    from api.services.group_service import GroupService
    from api.services.user_service import UserService
    from api.services.achievement_service import AchievementService
    from api.routes.mood_routes import create_mood_routes
    from api.routes.goal_routes import create_goal_routes
    from api.routes.group_routes import create_group_routes
    from api.routes.auth_routes import create_auth_routes
    from api.routes.misc_routes import create_misc_routes
    from api.routes.config_routes import create_config_routes
    from api.routes.achievement_routes import create_achievement_routes
    from api.utils.error_handlers import setup_error_handlers
    from api.utils.security_headers import add_security_headers
except Exception:  # fallback for running from inside api/
    from database import MoodDatabase
    from services.mood_service import MoodService
    from services.goal_service import GoalService
    from services.group_service import GroupService
    from services.user_service import UserService
    from services.achievement_service import AchievementService
    from routes.mood_routes import create_mood_routes
    from routes.goal_routes import create_goal_routes
    from routes.group_routes import create_group_routes
    from routes.auth_routes import create_auth_routes
    from routes.misc_routes import create_misc_routes
    from routes.config_routes import create_config_routes
    from routes.achievement_routes import create_achievement_routes
    from utils.error_handlers import setup_error_handlers
    from utils.security_headers import add_security_headers

# Optional modules (older published images may not include music)
try:
    try:
        from api.services.mus_service import MusicService  # type: ignore
        from api.routes.mus_routes import create_music_routes  # type: ignore
    except Exception:
        from services.mus_service import MusicService  # type: ignore
        from routes.mus_routes import create_music_routes  # type: ignore
except Exception:
    MusicService = None  # type: ignore
    create_music_routes = None  # type: ignore

try:
    try:
        from api.services.ai_service import AIService  # type: ignore
        from api.routes.ai_routes import create_ai_routes  # type: ignore
    except Exception:
        from services.ai_service import AIService  # type: ignore
        from routes.ai_routes import create_ai_routes  # type: ignore
except Exception:
    AIService = None  # type: ignore
    create_ai_routes = None  # type: ignore

def create_app(config_name="default"):
    """Application factory pattern"""
    try:
        from api.config import config as config_map
        from api.config import get_config
    except Exception:
        # Fallback when running from within api/ directory
        from config import config as config_map  # type: ignore[import-not-found]
        from config import get_config  # type: ignore[import-not-found]

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Load typed runtime config and align secrets
    cfg = None
    try:
        cfg = get_config()
        if getattr(cfg, "JWT_SECRET", None):
            app.config["JWT_SECRET_KEY"] = getattr(cfg, "JWT_SECRET")
        if getattr(cfg, "GOOGLE_CLIENT_ID", None):
            app.config["GOOGLE_CLIENT_ID"] = getattr(cfg, "GOOGLE_CLIENT_ID")
    except Exception:
        cfg = None  # fallback if typed config fails

    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Rely on flask-cors to handle CORS and automatic OPTIONS responses per route

    # Setup error handlers
    setup_error_handlers(app)

    # Add security headers
    add_security_headers(app)

    # Initialize database
    db = MoodDatabase(app.config.get("DATABASE_PATH"))

    # Initialize services
    mood_service = MoodService(db)
    group_service = GroupService(db)
    goal_service = GoalService(db)
    user_service = UserService(db)
    achievement_service = AchievementService(db)

    # Optional music service
    music_service = MusicService(db) if MusicService is not None else None

    # AI insights (OpenAI-compatible; keys stay server-side)
    ai_cfg = cfg
    if ai_cfg is None:
        try:
            ai_cfg = get_config()
        except Exception:
            ai_cfg = None
    ai_service = None
    if AIService is not None:
        ai_service = AIService(
            api_key=getattr(ai_cfg, "AI_API_KEY", None) or "",
            base_url=getattr(ai_cfg, "AI_BASE_URL", None) or "https://api.x.ai/v1",
            model=getattr(ai_cfg, "AI_MODEL", None) or "grok-4.5",
        )

    # Register blueprints
    app.register_blueprint(create_auth_routes(user_service), url_prefix="/api")
    app.register_blueprint(create_mood_routes(mood_service), url_prefix="/api")
    app.register_blueprint(create_group_routes(group_service), url_prefix="/api")
    app.register_blueprint(create_goal_routes(goal_service), url_prefix="/api")
    app.register_blueprint(
        create_achievement_routes(achievement_service), url_prefix="/api"
    )
    app.register_blueprint(create_misc_routes(), url_prefix="/api")
    app.register_blueprint(create_config_routes(), url_prefix="/api")
    if ai_service is not None and create_ai_routes is not None:
        app.register_blueprint(create_ai_routes(ai_service), url_prefix="/api")

    # Expose services for optional blueprints (e.g., OAuth) to reuse
    try:
        if not hasattr(app, "extensions") or app.extensions is None:  # type: ignore[attr-defined]
            app.extensions = {}  # type: ignore[attr-defined]
        app.extensions["user_service"] = user_service  # type: ignore[attr-defined]
    except Exception:
        pass

    # Conditional feature registration (lazy imports)
    if cfg is None:
        try:
            cfg = get_config()
        except Exception:
            cfg = None

    # Register music blueprint only when enabled and available.
    if (
        cfg
        and getattr(cfg, "ENABLE_MOOD_MUSIC", False)
        and music_service is not None
        and create_music_routes is not None
    ):
        app.register_blueprint(create_music_routes(music_service), url_prefix="/api")

    if cfg and getattr(cfg, "ENABLE_GOOGLE_OAUTH", False):
        try:
            # Registered only when enabled; module can lazy-import heavy deps.
            from api.auth.oauth import oauth_bp  # type: ignore

            app.register_blueprint(oauth_bp, url_prefix="/api")
        except Exception as e:
            try:
                from auth.oauth import oauth_bp  # type: ignore

                app.register_blueprint(oauth_bp, url_prefix="/api")
            except Exception as e2:
                if app.debug:
                    print(
                        f"[warn] ENABLE_GOOGLE_OAUTH is true but oauth blueprint not available: {e} / {e2}"
                    )

    # Web3 functionality removed from the application

    # Debug: Print all registered routes
    if app.debug:
        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            methods = sorted(list(getattr(rule, "methods", []) or []))
            print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(methods)}]")

    return app


if __name__ == "__main__":
    # Ensure project root is on sys.path when running this file directly
    root = str(Path(__file__).parent)
    if root not in sys.path:
        sys.path.insert(0, root)

    # Get environment from Railway or default to development
    env = os.getenv("RAILWAY_ENVIRONMENT", "development")
    app = create_app(env)

    print("Starting Flask app...")
    print(f"Environment: {env}")
    print(
        f"Google Client ID: {'Set' if app.config.get('GOOGLE_CLIENT_ID') else 'Missing'}"
    )

    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    if env == "production":
        print("WARNING: Running in production mode with Flask development server!")
        print("For production deployments, use: gunicorn wsgi:application")
        print("Or run: python3 wsgi.py")
        app.run(host="::", port=port, debug=False)
    else:
        print("Using Flask development server (debug mode on)")
        app.run(debug=True, host="127.0.0.1", port=port)
