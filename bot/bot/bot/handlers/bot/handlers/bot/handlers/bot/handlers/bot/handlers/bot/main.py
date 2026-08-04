import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PATH, WEBHOOK_URL, WEBHOOK_SECRET, PORT
from bot.db import init_db
from bot.handlers import search, upload, playlist, ai_generate

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(search.router)
dp.include_router(playlist.router)
dp.include_router(ai_generate.router)
dp.include_router(upload.router)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to BMusicStudioAIBot! 🎵\n\n"
        "/search <query> — find royalty-free tracks\n"
        "Send me an audio file — save it to your library\n"
        "/myuploads — see your saved tracks\n"
        "/newplaylist <name> — create a playlist\n"
        "/addtotrack <playlist_id> <track_number> — add a track to a playlist\n"
        "/play <playlist_id> — play a playlist\n"
        "/generate <description> — AI-generate a track"
    )


async def on_startup(bot: Bot):
    await init_db()
    if WEBHOOK_HOST:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        logging.info("Webhook set to %s", WEBHOOK_URL)


def main():
    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
