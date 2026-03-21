from app.config import BotSettings, get_bot_settings


def load_bot_settings() -> BotSettings:
    return get_bot_settings()
