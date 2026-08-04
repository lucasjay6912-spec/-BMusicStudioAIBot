import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.config import JAMENDO_CLIENT_ID
from bot.db import get_session, Track

router = Router()


async def jamendo_search(query: str, limit: int = 5):
    url = "https://api.jamendo.com/v3.0/tracks"
    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": limit,
        "search": query,
        "audioformat": "mp32",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])


@router.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.removeprefix("/search").strip()
    if not query:
        await message.answer("Usage: /search <song or artist name>")
        return

    if not JAMENDO_CLIENT_ID:
        await message.answer("Search isn't configured yet — add JAMENDO_CLIENT_ID in Railway variables.")
        return

    results = await jamendo_search(query)
    if not results:
        await message.answer("No results found. Try a different search.")
        return

    for track in results:
        name = f"{track['name']} — {track['artist_name']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬇️ Send to me", callback_data=f"send:{track['id']}")
        ]])
        await message.answer(name, reply_markup=kb)


@router.callback_query(F.data.startswith("send:"))
async def send_track(callback: CallbackQuery):
    track_id = callback.data.split(":", 1)[1]

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://api.jamendo.com/v3.0/tracks",
            params={"client_id": JAMENDO_CLIENT_ID, "format": "json", "id": track_id},
        )
        data = resp.json().get("results", [])

    if not data:
        await callback.answer("Track not found anymore.", show_alert=True)
        return

    track = data[0]
    audio_url = track["audio"]
    caption = f"{track['name']} — {track['artist_name']}"

    sent = await callback.message.answer_audio(audio=audio_url, caption=caption)

    async with get_session() as session:
        session.add(Track(
            owner_id=callback.from_user.id,
            title=caption,
            source="jamendo",
            file_id=sent.audio.file_id,
        ))
        await session.commit()

    await callback.answer()
