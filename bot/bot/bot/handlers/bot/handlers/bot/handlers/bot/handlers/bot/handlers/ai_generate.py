import asyncio
import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import REPLICATE_API_TOKEN
from bot.db import get_session, Track

router = Router()

MUSICGEN_MODEL_VERSION = "671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcf"


@router.message(Command("generate"))
async def cmd_generate(message: Message):
    prompt = message.text.removeprefix("/generate").strip()
    if not prompt:
        await message.answer("Usage: /generate <description, e.g. \"lofi hiphop beat with rain sounds\">")
        return

    if not REPLICATE_API_TOKEN:
        await message.answer("AI generation isn't configured yet — add REPLICATE_API_TOKEN in Railway variables.")
        return

    status_msg = await message.answer("Generating your track — this usually takes 30-60s...")

    headers = {"Authorization": f"Bearer {REPLICATE_API_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        create_resp = await client.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json={"version": MUSICGEN_MODEL_VERSION, "input": {"prompt": prompt, "duration": 15}},
        )
        create_resp.raise_for_status()
        prediction = create_resp.json()
        prediction_url = prediction["urls"]["get"]

        for _ in range(30):
            await asyncio.sleep(3)
            poll_resp = await client.get(prediction_url, headers=headers)
            prediction = poll_resp.json()
            if prediction["status"] in ("succeeded", "failed", "canceled"):
                break

    if prediction["status"] != "succeeded":
        await status_msg.edit_text("Generation failed — try a different prompt.")
        return

    audio_url = prediction["output"]
    sent = await message.answer_audio(audio=audio_url, caption=f'AI generated: "{prompt}"')
    await status_msg.delete()

    async with get_session() as session:
        session.add(Track(owner_id=message.from_user.id, title=prompt[:100], source="ai", file_id=sent.audio.file_id))
        await session.commit()
