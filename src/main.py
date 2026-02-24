import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from pymax import MaxClient, Message
from pymax.types import FileAttach, PhotoAttach, VideoAttach

from src.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


# Инициализация клиента MAX (последняя версия pymax)
client = MaxClient(phone=config.max_phone_number, work_dir="cache", reconnect=True)

# Инициализация TG-бота
telegram_bot = Bot(token=config.tg_bot_token)
dp = Dispatcher()


async def _download_to_buffer(url: str, fallback_name: str) -> types.BufferedInputFile:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()
            file_name = response.headers.get("X-File-Name") or fallback_name
            return types.BufferedInputFile(content, filename=file_name)


async def _build_sender_prefix(message: Message) -> str:
    sender = await client.get_user(user_id=message.sender)
    sender_name = sender.names[0].name if sender and sender.names else "Unknown"
    return f"{sender_name} [chat_id={message.chat_id}]"


@client.on_message()
async def forward_max_message_to_telegram(message: Message) -> None:
    """Форвардит все входящие сообщения MAX в Telegram конкретному пользователю."""
    sender_prefix = await _build_sender_prefix(message)
    message_text = message.text or ""

    try:
        if not message.attaches:
            text = f"{sender_prefix}: {message_text}" if message_text else sender_prefix
            await telegram_bot.send_message(chat_id=config.tg_target_user_id, text=text)
            return

        for attach in message.attaches:
            caption = f"{sender_prefix}: {message_text}" if message_text else sender_prefix

            if isinstance(attach, PhotoAttach):
                photo = await _download_to_buffer(attach.base_url, fallback_name="photo.jpg")
                await telegram_bot.send_photo(
                    chat_id=config.tg_target_user_id,
                    photo=photo,
                    caption=caption,
                )

            elif isinstance(attach, VideoAttach):
                video_data = await client.get_video_by_id(
                    chat_id=message.chat_id,
                    message_id=message.id,
                    video_id=attach.video_id,
                )
                video = await _download_to_buffer(video_data.url, fallback_name="video.mp4")
                await telegram_bot.send_video(
                    chat_id=config.tg_target_user_id,
                    video=video,
                    caption=caption,
                )

            elif isinstance(attach, FileAttach):
                file_data = await client.get_file_by_id(
                    chat_id=message.chat_id,
                    message_id=message.id,
                    file_id=attach.file_id,
                )
                document = await _download_to_buffer(file_data.url, fallback_name="file.bin")
                await telegram_bot.send_document(
                    chat_id=config.tg_target_user_id,
                    document=document,
                    caption=caption,
                )

            else:
                await telegram_bot.send_message(
                    chat_id=config.tg_target_user_id,
                    text=f"{caption}\n[Unsupported attachment type: {type(attach).__name__}]",
                )

    except aiohttp.ClientError as error:
        logger.error("Ошибка загрузки вложения: %s", error)
    except Exception:
        logger.exception("Ошибка при форвардинге сообщения из MAX в Telegram")


@client.on_start
async def handle_start() -> None:
    logger.info("MAX клиент запущен. Форвардинг в TG user_id=%s", config.tg_target_user_id)


@dp.message()
async def ignore_telegram_messages(message: types.Message) -> None:
    """Бот работает в режиме MAX -> Telegram, входящие из Telegram игнорируются."""
    logger.debug("Игнор Telegram-сообщения chat_id=%s", message.chat.id)


async def main() -> None:
    telegram_polling = asyncio.create_task(dp.start_polling(telegram_bot))

    try:
        await client.start()
    finally:
        await client.close()
        telegram_polling.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
