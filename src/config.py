import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    max_phone_number: str
    tg_bot_token: str
    chat_ids: dict[str, str]


def get_config() -> Settings:
    max_phone_number = os.getenv("MAX_PHONE_NUMBER")
    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    raw = os.getenv("CHAT_IDS")
    chat_ids = dict(
            pair.split(":")
            for pair in raw.split(",")
            if pair
        )
    return Settings(max_phone_number, tg_bot_token, chat_ids)

config = get_config()
