from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.db import get_session, Playlist, PlaylistTrack, Track

router = Router()


@router.message(Command("newplaylist"))
async def new_playlist(message: Message):
    name = message.text.removeprefix("/newplaylist").strip()
    if not name:
        await message.answer("Usage: /newplaylist <name>")
        return

    async with get_session() as session:
        session.add(Playlist(owner_id=message.from_user.id, name=name))
        await session.commit()

    await message.answer(f'Created playlist "{name}". Add tracks with /addtotrack once you have some saved.')


@router.message(Command("playlists"))
async def list_playlists(message: Message):
    async with get_session() as session:
        result = await session.execute(select(Playlist).where(Playlist.owner_id == message.from_user.id))
        playlists = result.scalars().all()

    if not playlists:
        await message.answer("No playlists yet. Create one with /newplaylist <name>.")
        return

    lines = [f"• {p.name} (id {p.id})" for p in playlists]
    await message.answer("Your playlists:\n" + "\n".join(lines))


@router.message(Command("addtotrack"))
async def add_to_playlist(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Usage: /addtotrack <playlist_id> <track_number_from_myuploads>")
        return

    _, playlist_id, track_num = parts

    async with get_session() as session:
        result = await session.execute(
            select(Track).where(Track.owner_id == message.from_user.id).order_by(Track.added_at.desc()).limit(20)
        )
        tracks = result.scalars().all()
        idx = int(track_num) - 1
        if idx < 0 or idx >= len(tracks):
            await message.answer("Track number not found — check /myuploads.")
            return

        session.add(PlaylistTrack(playlist_id=int(playlist_id), track_id=tracks[idx].id))
        await session.commit()

    await message.answer("Added to playlist.")


@router.message(Command("play"))
async def play_playlist(message: Message):
    playlist_id = message.text.removeprefix("/play").strip()
    if not playlist_id.isdigit():
        await message.answer("Usage: /play <playlist_id> (see /playlists)")
        return

    async with get_session() as session:
        result = await session.execute(
            select(Track).join(PlaylistTrack).where(PlaylistTrack.playlist_id == int(playlist_id))
        )
        tracks = result.scalars().all()

    if not tracks:
        await message.answer("That playlist is empty.")
        return

    for t in tracks:
        await message.answer_audio(audio=t.file_id, caption=t.title)
