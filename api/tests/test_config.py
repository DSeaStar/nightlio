import json

from api.config import get_config, config_to_public_dict


def test_public_config_shape():
    cfg = get_config()
    public = config_to_public_dict(cfg)
    assert set(public.keys()) == {
        "enable_google_oauth",
        "enable_mood_music",
        "enable_ai_insights",
        "google_client_id",
    }
    assert isinstance(public["enable_google_oauth"], bool)
    assert isinstance(public["enable_mood_music"], bool)
    assert isinstance(public["enable_ai_insights"], bool)


def test_public_config_default_values():
    cfg = get_config()
    public = config_to_public_dict(cfg)
    assert public["enable_google_oauth"] in (True, False)
    assert public["enable_mood_music"] in (True, False)
    assert public["enable_ai_insights"] in (True, False)
