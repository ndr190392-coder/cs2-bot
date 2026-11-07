"""
================================================================================
❄️ CS2 DROP HUB BOT - FULL WINTER EDITION & ADVANCED CORE (v3.5.0 PROD) ❄️
================================================================================
"""

import os
import sys
import logging
import random
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from motor.motor_asyncio import AsyncIOMotorClient

# Логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("CS2_WINTER_HUB_BOT")

BOT_TOKEN = os.getenv("BOT_TOKEN", "8825098686:AAH2mVz2pOo_vl6T6yMpRA_f-zWLMPMfVdc")
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://ndr190392_db_user:D5eeW7ZwpeBjbryY@cluster0.evqeech.mongodb.net/?retryWrites=true&w=majority")
PORT = int(os.getenv("PORT", 10000))

# Підключення до БД
db_client: AsyncIOMotorClient = None
db = None
users_collection = None

async def initialize_database_cluster() -> None:
    global db_client, db, users_collection
    try:
        db_client = AsyncIOMotorClient(MONGO_URL)
        db = db_client.get_database("cs2_winter_ultimate_db")
        users_collection = db.get_collection("users")
        await db_client.admin.command('ping')
        logger.info("❄️ [DB] Успішне підключення до MongoDB Atlas!")
    except Exception as err:
        logger.error(f"❌ [DB] Помилка підключення: {err}")
        sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

WINTER_CASES_CATALOG = {
    "winter_knife_case": {
        "name": "❄️ Новорічний Кеш із Ножами",
        "price": 600,
        "items": [
            {"name": "Karambit | Arctic Fade (FN)", "price": 18000, "rarity": "⭐️ Covert", "drop_rate": 1},
            {"name": "M9 Bayonet | Blizzard Steel (MW)", "price": 14000, "rarity": "⭐️ Covert", "drop_rate": 2},
            {"name": "AWP | Winter Asiimov (FT)", "price": 2200, "rarity": "🔴 Classified", "drop_rate": 15},
            {"name": "AK-47 | Blue Snow (MW)", "price": 500, "rarity": "🟣 Restricted", "drop_rate": 30},
            {"name": "P250 | Frozen Dune (BS)", "price": 15, "rarity": "⚪️ Consumer", "drop_rate": 52}
        ]
    }
}

async def fetch_user_profile(user_id: int, username: str = "Стрілець") -> dict:
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "username": username,
            "balance": 2000,
            "inventory": [],
            "cases_opened": 0
        }
        await users_collection.insert_one(user)
    return user

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await fetch_user_profile(message.from_user.id, message.from_user.first_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Відкрити кейси", callback_data="cases_menu")],
        [InlineKeyboardButton(text="👤 Профіль", callback_data="profile")]
    ])
    await message.answer("❄️ **Вітаю у CS2 Winter Hub!**", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "profile")
async def callback_user_profile(callback: CallbackQuery) -> None:
    user = await fetch_user_profile(callback.from_user.id)
    await callback.message.edit_text(
        f"👤 **Профіль:**\n💰 Баланс: **{user['balance']} 🪙**\n📦 Відкрито кейсів: **{user['cases_opened']}**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")]]),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Відкрити кейси", callback_data="cases_menu")],
        [InlineKeyboardButton(text="👤 Профіль", callback_data="profile")]
    ])
    await callback.message.edit_text("🏠 **Головне меню:**", reply_markup=kb, parse_mode="Markdown")

async def handle_web_ping(request: web.Request) -> web.Response:
    return web.Response(text="Bot is running 24/7!", content_type="text/plain")

async def start_background_web_server() -> None:
    app = web.Application()
    app.router.add_get("/", handle_web_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main() -> None:
    await initialize_database_cluster()
    dp.include_router(router)
    await start_background_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
