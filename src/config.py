import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    max_phone_number: str
    tg_bot_token: str
    tg_target_user_id: int


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def get_config() -> Settings:
    max_phone_number = _require_env("MAX_PHONE_NUMBER")
    tg_bot_token = _require_env("TG_BOT_TOKEN")
    tg_target_user_id = int(_require_env("TG_TARGET_USER_ID"))

    return Settings(
        max_phone_number=max_phone_number,
        tg_bot_token=tg_bot_token,
        tg_target_user_id=tg_target_user_id,
    )


config = get_config()
