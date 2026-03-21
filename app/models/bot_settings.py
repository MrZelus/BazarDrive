import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BotSettings:
    bot_token: str
    admin_chat_id: int
    group_chat_id: int
    admin_ids: set[int]



def load_bot_settings() -> BotSettings:
    return BotSettings(
        bot_token=os.getenv("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE"),
        admin_chat_id=int(os.getenv("ADMIN_CHAT_ID", "-1001234567890")),
        group_chat_id=int(os.getenv("GROUP_CHAT_ID", "-1009876543210")),
        admin_ids={int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",") if uid.strip()},
    )
