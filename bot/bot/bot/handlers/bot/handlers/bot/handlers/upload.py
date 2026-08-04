from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.db import get_session, Track

router = Router()


@router.message(F.audio | F.voice | (F.document & F.document.mime_type.startswith("audio/")))
async def handle_audio_upload(message: Message):
    if message.audio:
        file_id = message.audio.file_id
        title = message.audio.title or message.audio.file_name or "Untitled"
    elif message.document:
        file_id = message.document.file_id
        title = message.document.file_name or "Untitled"
    else:
        file_id = message.voice.file_id
        title = "Voice note"

    async with get_session() as session:
        session.add(Track(owner_id=message.from_user.id, title=title, source="upload", file_id=file_id))
        await session.commit()

    await message.reply(f"Saved \"{title}\" to your library. Use /myuploads to see everything, or /playlist to organize it.")


@router.message(Command("myuploads"))
async def list_uploads(message: Message):
    async with get_session() as session:
        result = await session.execute(
            select(Track).where(Track.owner_id == message.from_user.id).order_by(Track.added_at.desc()).limit(20)
        )
        tracks = result.scalars().all()

    if not tracks:
        await message.answer("You haven't saved anything yet — send me an audio file, or use /search.")
        return

    lines = [f"{i+1}. {t.title} ({t.source})" for i, t in enumerate(tracks)]
    await message.answer("Your library:\n" + "\n".join(lines))
