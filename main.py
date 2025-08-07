# import os
# import logging
# import hashlib
# import asyncio
# import dotenv
# import re

# from aiogram import Bot, Dispatcher, F
# from aiogram.types import (
#     Message, InlineQuery, InlineQueryResultArticle,
#     InputTextMessageContent, InlineQueryResultAudio
# )
# from aiogram.enums import ContentType
# from aiogram.filters import Command
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup

# from database import init_db, add_audio, search_audios, get_all_audios

# # Load environment variables
# dotenv.load_dotenv()
# API_TOKEN = os.getenv("BOT_TOKEN")
# if not API_TOKEN:
#     raise ValueError("BOT_TOKEN environment variable not set!")

# # Logger
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Bot and Dispatcher
# bot = Bot(token=API_TOKEN)
# dp = Dispatcher(storage=MemoryStorage())

# # Telegram post linkini tekshirish uchun regex
# TELEGRAM_POST_REGEX = re.compile(
#     r'^https?://t\.me/([a-zA-Z0-9_]{5,32})/(\d+)$'
# )

# # FSM for /add

# class AddAudio(StatesGroup):
#     waiting_for_link = State()


# # Start command
# @dp.message(Command("start"))
# async def start_handler(msg: Message):
#     await msg.answer("Salom! /add buyrug'ini yozing va kanal postining linkini yuboring (audio va caption bo'lishi kerak).")

# @dp.message(Command("add"))
# async def add_handler(msg: Message, state: FSMContext):
#     user_id = msg.from_user.id
#     if user_id == 7149602547:
#         await msg.answer("Kanal postining linkini yuboring (audio va caption bo'lishi kerak):")
#         await state.set_state(AddAudio.waiting_for_link)
#     else:
#         await msg.answer("Siz admin emassiz, buyrug'ni ishlata olmaysiz!")    



# @dp.message(AddAudio.waiting_for_link)
# async def process_link(msg: Message, state: FSMContext):
#     link = msg.text.strip()
#     match = TELEGRAM_POST_REGEX.match(link)
#     if not match:
#         await msg.answer("❗ To'g'ri Telegram kanal post linkini yuboring!")
#         return

#     channel, post_id = match.groups()
#     try:
#         fwd_msg = await bot.forward_message(
#             chat_id=msg.chat.id,
#             from_chat_id=f"@{channel}",
#             message_id=int(post_id)
#         )

#         if not fwd_msg.audio or not fwd_msg.caption:
#             await msg.answer("❗ Postda audio va caption bo'lishi kerak!")
#             return

#         name = fwd_msg.caption.strip()
#         audio_link = link
#         file_id = fwd_msg.audio.file_id  # <-- kerakli joy

#         add_audio(name, audio_link, file_id)
#         await msg.answer(f"✅ '{name}' nomli audio saqlandi!")
#         await state.clear()
#     except Exception as e:
#         logger.error(f"Xatolik: {e}")
#         await msg.answer("❌ Postdan audio va caption olishda xatolik!")



# @dp.inline_query()
# async def inline_audio_search(inline_query: InlineQuery):
#     query = inline_query.query.strip()
    
#     # If empty query, return all audios (you might want to limit this)
#     if not query:
#         results = get_all_audios()  # You'll need to implement this function
#     else:
#         results = search_audios(query)
#         if not results:
#             await bot.answer_inline_query(
#                 inline_query.id,
#                 results=[],
#                 switch_pm_text="Hech nima topilmadi 😕",
#                 switch_pm_parameter="empty_results",
#                 cache_time=1
#             )
#             return

#     answers = []
#     for idx, (name, audio_link) in enumerate(results[:50]):  # Limit to 50 results
#         answers.append(
#             InlineQueryResultAudio(
#                 id=f"{inline_query.id}_{idx}",
#                 audio_url=audio_link,
#                 title=name,
#                 caption=f"{name}",
#                 performer="Ketmon's Audio Bot",
#                 parse_mode="HTML"
#             )
#         )

#     try:
#         await bot.answer_inline_query(
#             inline_query.id,
#             results=answers,
#             cache_time=300,
#             is_personal=True
#         )
#     except Exception as e:
#         logging.error(f"Error answering inline query: {e}")



# async def main():
#     init_db()
#     await dp.start_polling(bot)

# if __name__ == "__main__":
#     asyncio.run(main())


import os
import logging
import hashlib
import asyncio
import dotenv
import re

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from database import init_db, add_audio, search_audios, get_all_audios

# Load environment variables
dotenv.load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram post linkini tekshirish uchun regex
TELEGRAM_POST_REGEX = re.compile(
    r'^https?://t\.me/([a-zA-Z0-9_]{5,32})/(\d+)$'
)

# FSM for /add
class AddAudio(StatesGroup):
    waiting_for_link = State()

# Bot and Dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Start command
@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    await msg.answer("Salom! /add buyrug'ini yozing va kanal postining linkini yuboring (audio va caption bo'lishi kerak).")

# /add command
@dp.message_handler(commands=["add"])
async def add_handler(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    if user_id == 7149602547:
        await msg.answer("Kanal postining linkini yuboring (audio va caption bo'lishi kerak):")
        await AddAudio.waiting_for_link.set()
    else:
        await msg.answer("Siz admin emassiz, buyrug'ni ishlata olmaysiz!")    

# Linkni qabul qilish
@dp.message_handler(state=AddAudio.waiting_for_link)
async def process_link(msg: types.Message, state: FSMContext):
    link = msg.text.strip()
    match = TELEGRAM_POST_REGEX.match(link)
    if not match:
        await msg.answer("❗ To'g'ri Telegram kanal post linkini yuboring!")
        return

    channel, post_id = match.groups()
    try:
        fwd_msg = await bot.forward_message(
            chat_id=msg.chat.id,
            from_chat_id=f"@{channel}",
            message_id=int(post_id)
        )

        if not fwd_msg.audio or not fwd_msg.caption:
            await msg.answer("❗ Postda audio va caption bo'lishi kerak!")
            return

        name = fwd_msg.caption.strip()
        audio_link = link
        file_id = fwd_msg.audio.file_id

        add_audio(name, audio_link, file_id)
        await msg.answer(f"✅ '{name}' nomli audio saqlandi!")
        await state.finish()
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await msg.answer("❌ Postdan audio va caption olishda xatolik!")

# Inline query qabul qilish
@dp.inline_handler()
async def inline_audio_search(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    if not query:
        results = get_all_audios()
    else:
        results = search_audios(query)
        if not results:
            await bot.answer_inline_query(
                inline_query.id,
                results=[],
                switch_pm_text="Hech nima topilmadi 😕",
                switch_pm_parameter="empty_results",
                cache_time=1
            )
            return

    answers = []
    for idx, (name, audio_link) in enumerate(results[:50]):
        answers.append(
            types.InlineQueryResultAudio(
                id=f"{inline_query.id}_{idx}",
                audio_url=audio_link,
                title=name,
                caption=name,
                performer="Ketmon's Audio Bot",
                parse_mode="HTML"
            )
        )

    try:
        await bot.answer_inline_query(
            inline_query.id,
            results=answers,
            cache_time=300,
            is_personal=True
        )
    except Exception as e:
        logging.error(f"Inline query xatoligi: {e}")


# Botni ishga tushirish
async def on_startup(_):
    init_db()
    print("Bot ishga tushdi.")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
