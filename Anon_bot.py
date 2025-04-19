from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio, random

API_ID = 23240409
API_HASH = "a5f5bc36ff9e1d6cd13e44b5cdd6f9fd"
BOT_TOKEN = "7592224666:AAF5cQHbVXMy4M_i95E52nuEzELQHF6-tpM"
OWNER_ID = 7773371892

app = Client("anon_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

active_chats = {}
auto_replies = {
    "happy": ["Wah!", "Mast!", "Haha", "Kya baat hai!"],
    "sad": ["Kya hua?", "Arey yaar", "Sab theek ho jaayega", "Hmm..."],
    "angry": ["Shaant hoja bro", "Kya problem hai?", "Relax!"],
    "default": ["Hmm", "Ok", "Thik hai", "Ohh"]
}

def detect_mood(text):
    mood = "default"
    if any(w in text.lower() for w in ["sad", "cry", "miss", "broken"]): mood = "sad"
    elif any(w in text.lower() for w in ["happy", "love", "great", "joy"]): mood = "happy"
    elif any(w in text.lower() for w in ["angry", "hate", "mad"]): mood = "angry"
    return mood

@app.on_message(filters.command("start"))
async def start(_, msg):
    await msg.reply("Bot activated.")

@app.on_message(filters.command("send") & filters.user(OWNER_ID))
async def send_to_user(client, message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Use: /send <user_id> <message>")
    user_id = int(parts[1])
    text = parts[2]
    try:
        await client.send_message(user_id, text)
        active_chats[user_id] = True
        await message.reply(f"Chat started with `{user_id}`.")
    except Exception as e:
        await message.reply(f"Failed: {e}")

@app.on_message(filters.command("stopchat") & filters.user(OWNER_ID))
async def stop_chat(_, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Use: /stopchat <user_id>")
    user_id = int(parts[1])
    active_chats.pop(user_id, None)
    await message.reply(f"Session with `{user_id}` closed.")

async def send_typing_then_reply(client, user_id, func, *args, **kwargs):
    await client.send_chat_action(user_id, "typing")
    await asyncio.sleep(random.uniform(1.2, 2.4))
    await func(user_id, *args, **kwargs)

@app.on_message(filters.private & ~filters.user(OWNER_ID))
async def forward_to_owner(client, message: Message):
    uid = message.from_user.id
    if uid not in active_chats:
        return
    text = message.text or message.caption or ""
    await client.send_chat_action(OWNER_ID, "typing")

    # Forward original message to owner
    if message.text:
        await client.send_message(OWNER_ID, f"[{uid}]: {text}")
    elif message.photo:
        await client.send_photo(OWNER_ID, photo=message.photo.file_id, caption=f"[{uid}]\n{text}")
    elif message.video:
        await client.send_video(OWNER_ID, video=message.video.file_id, caption=f"[{uid}]\n{text}")
    elif message.voice:
        await client.send_voice(OWNER_ID, voice=message.voice.file_id, caption=f"[{uid}]")
    elif message.sticker:
        await client.send_sticker(OWNER_ID, message.sticker.file_id)

    # Optional: auto-reply with emoji mood
    if random.random() < 0.3:
        mood = detect_mood(text)
        response = random.choice(auto_replies.get(mood, auto_replies["default"]))
        await send_typing_then_reply(client, uid, client.send_message, text=response)

@app.on_message(filters.private & filters.user(OWNER_ID) & ~filters.command(["send", "stopchat"]))
async def reply_back(client, message: Message):
    if not message.reply_to_message or "[" not in message.reply_to_message.text:
        return await message.reply("Reply to forwarded message (containing [user_id]).")
    try:
        uid = int(message.reply_to_message.text.split("]")[0].replace("[", ""))
        if uid not in active_chats:
            return await message.reply("User not in active chat.")
        if message.text:
            await send_typing_then_reply(client, uid, client.send_message, text=message.text)
        elif message.photo:
            await send_typing_then_reply(client, uid, client.send_photo, photo=message.photo.file_id, caption=message.caption)
        elif message.video:
            await send_typing_then_reply(client, uid, client.send_video, video=message.video.file_id, caption=message.caption)
        elif message.voice:
            await send_typing_then_reply(client, uid, client.send_voice, voice=message.voice.file_id, caption=message.caption)
        elif message.sticker:
            await client.send_sticker(uid, message.sticker.file_id)
        await message.reply("Sent anonymously.")
    except Exception as e:
        await message.reply(f"Failed: {e}")

app.run()
