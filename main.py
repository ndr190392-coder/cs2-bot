import os
import sys
import logging
import random
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from motor.motor_asyncio import AsyncIOMotorClient

# --- НАЛАШТУВАННЯ ЛОГУВАННЯ ТА ОКРУЖЕННЯ ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("CS2_WINTER_BOT")

# Конфігураційні змінні
BOT_TOKEN = os.getenv("BOT_TOKEN", "8825098686:AAH2mVz2pOo_vl6T6yMpRA_f-zWLMPMfVdc")
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://ndr190392_db_user:D5eeW7ZwpeBjbryY@cluster0.evqeech.mongodb.net/?retryWrites=true&w=majority")
PORT = int(os.getenv("PORT", 10000))

# --- ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ MONGODB ATLAS ---
db_client: AsyncIOMotorClient = None
db = None
users_collection = None

async def initialize_database():
    """Ініціалізація підключення до MongoDB Atlas та перевірка зв'язку."""
    global db_client, db, users_collection
    try:
        db_client = AsyncIOMotorClient(MONGO_URL)
        db = db_client.get_database("cs2_winter_drop_db")
        users_collection = db.get_collection("users")
        # Перевіряємо пінг бази даних
        await db_client.admin.command('ping')
        logger.info("❄️ Успішне підключення до MongoDB Atlas (Winter DB активна)!")
    except Exception as exc:
        logger.error(f"❌ Критична помилка підключення до MongoDB: {exc}")
        sys.exit(1)

# --- ІНІЦІАЛІЗАЦІЯ BOT ТА DISPATCHER ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# --- ЗИМОВИЙ КАТАЛОГ КЕЙСІВ ТА СКІНІВ ---
WINTER_CASES = {
    "winter_knife_case": {
        "name": "❄️ Новорічний Кеш із Ножами",
        "price": 600,
        "description": "Морозний кейс із легендарними ножами у крижаному покритті.",
        "items": [
            {"name": "Karambit | Arctic Fade (FN)", "price": 18000, "rarity": "⭐️ Covert (Секретне)", "drop_rate": 1},
            {"name": "M9 Bayonet | Blizzard Steel (MW)", "price": 14000, "rarity": "⭐️ Covert (Секретне)", "drop_rate": 2},
            {"name": "Butterfly Knife | Ice Free (FN)", "price": 12500, "rarity": "⭐️ Covert (Секретне)", "drop_rate": 3},
            {"name": "AWP | Winter Asiimov (FT)", "price": 2200, "rarity": "🔴 Classified (Заборонене)", "drop_rate": 15},
            {"name": "AK-47 | Blue Snow (MW)", "price": 500, "rarity": "🟣 Restricted (Видатне)", "drop_rate": 30},
            {"name": "P250 | Frozen Dune (BS)", "price": 15, "rarity": "⚪️ Consumer (Базове)", "drop_rate": 49}
        ]
    },
    "new_year_weapon_case": {
        "name": "🎄 Святковий Оружейний Кейс",
        "price": 200,
        "description": "Зимові розмальовки зброї на честь Нового Року.",
        "items": [
            {"name": "AK-47 | New Year Serpent (FT)", "price": 9500, "rarity": "⭐️ Covert (Секретне)", "drop_rate": 1},
            {"name": "M4A4 | Snow Howl (MW)", "price": 28000, "rarity": "⭐️ Extraordinary", "drop_rate": 1},
            {"name": "Desert Eagle | Crystal Printstream (MW)", "price": 1500, "rarity": "🔴 Classified (Заборонене)", "drop_rate": 12},
            {"name": "USP-S | Frost Cortex (FT)", "price": 350, "rarity": "🟣 Restricted (Видатне)", "drop_rate": 35},
            {"name": "Glock-18 | Ice Grinder (FN)", "price": 45, "rarity": "🔵 Mil-Spec (Армійське)", "drop_rate": 51}
        ]
    }
}

# --- ДОПОМІЖНІ ФУНКЦІЇ РОБОТИ З КОРИСТУВАЧЕМ ---
async def get_or_create_user(user_id: int, username: str = "Стрілець"):
    """Отримує користувача з бази або створює нового із зимовим бонусом."""
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "username": username,
            "balance": 1500,  # Зимовий стартовий капітал 1500 монет
            "inventory": [],
            "cases_opened": 0,
            "last_bonus_date": None,
            "registered_at": datetime.utcnow()
        }
        await users_collection.insert_one(user)
        logger.info(f"❄️ Зареєстровано нового користувача ID: {user_id} ({username})")
    return user

# --- КЛАВІАТУРИ ГОЛОВНОГО МЕНЮ (З ЗИМОВИМ ВАЙБОМ) ---
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Відкрити зимові кейси", callback_data="cases_menu")],
        [InlineKeyboardButton(text="👤 Мій профіль та скіни", callback_data="profile")],
        [InlineKeyboardButton(text="❄️ Отримати морозний бонус", callback_data="get_bonus")],
        [InlineKeyboardButton(text="📊 Топ гравців та ринок", callback_data="top_players")]
    ])

def get_cases_keyboard():
    keyboard = []
    for case_id, case_data in WINTER_CASES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"{case_data['name']} — {case_data['price']} 🪙",
                callback_data=f"open_case_{case_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад у морозне меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- ОБРОБНИКИ КОМАНД ТА КНОПОК ---

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Головний привітальний блок з атмосферним зимовим текстом."""
    await get_or_create_user(message.from_user.id, message.from_user.first_name)
    
    welcome_text = (
        "❄️ **Вітаю у CS2 Drop Hub: Winter Edition!** 🎄\n\n"
        "На вулиці падає сніг, а у нас на відкритті кейсів спекотно! "
        "Вибивай унікальні зимові скіни, колекціонуй рідкісні ножі, отримуй щоденні бонуси "
        "та стань легендою морозного маркету CS2.\n\n"
        "👇 Обери потрібний розділ нижче:"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    """Повернення до головного зимового меню."""
    await callback.message.edit_text(
        "🏠 **Головне меню CS2 Winter Hub:**\nТут панує святкова атмосфера та гарячі дропи:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    """Перегляд профілю користувача, балансу та останніх предметів."""
    user = await get_or_create_user(callback.from_user.id)
    balance = user.get("balance", 0)
    inventory = user.get("inventory", [])
    opened = user.get("cases_opened", 0)
    
    # Форматуємо останні 10 предметів в інвентарі
    if inventory:
        recent_items = inventory[-10:]
        inv_text = "\n".join([f"• 🧊 {item['name']} ({item['rarity']}) — **{item['price']} 🪙**" for item in recent_items])
    else:
        inv_text = "Твій інвентарь поки порожній. Час відкрити перший зимовий кейс! 🎁"
    
    text = (
        f"👤 **Профіль гравця (Winter Edition):**\n\n"
        f"❄️ Ім'я: {callback.from_user.first_name}\n"
        f"🆔 ID: `{callback.from_user.id}`\n"
        f"💰 Зимовий баланс: **{balance} 🪙**\n"
        f"📦 Відкрито кейсів: **{opened}**\n"
        f"🎒 Предметів у сховищі: **{len(inventory)}**\n\n"
        f"🧊 **Останні вибиті скіни:**\n{inv_text}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад у меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "get_bonus")
async def cb_get_bonus(callback: CallbackQuery):
    """Щоденний морозний бонус для гравців."""
    user_id = callback.from_user.id
    user = await get_or_create_user(user_id)
    
    # Нараховуємо 350 монет зимового бонусу
    bonus_amount = 350
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": bonus_amount}}
    )
    
    await callback.answer(f"🎉 Ти успішно зібрав морозний бонус у розмірі {bonus_amount} 🪙!", show_alert=True)
    
    # Оновлюємо відображення профілю або повертаємо в меню
    updated_user = await get_or_create_user(user_id)
    text = (
        f"❄️ **Морозний бонус успішно отримано!**\n\n"
        f"💰 Твій новий баланс: **{updated_user['balance']} 🪙**\n"
        f"Заходь щодня, щоб збирати ще більше монет для новорічних кейсів!"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 До кейсів", callback_data="cases_menu")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "top_players")
async def cb_top_players(callback: CallbackQuery):
    """Топ гравців за балансом у базі даних."""
    cursor = users_collection.find().sort("balance", -1).limit(5)
    top_list = await cursor.to_list(length=5)
    
    top_text = "📊 **Топ-5 найбагатших стрільців (Winter Season):**\n\n"
    for idx, usr in enumerate(top_list, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"🔹 {idx}."
        name = usr.get("username", "Гравець")
        bal = usr.get("balance", 0)
        top_text += f"{medal} **{name}** — {bal} 🪙\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад у меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(top_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "cases_menu")
async def cb_cases_menu(callback: CallbackQuery):
    """Меню вибору кейсів."""
    await callback.message.edit_text(
        "🎁 **Зимові кейси доступні для відкриття:**\nОбери свій морозний кейс та вибивай найкращі скіни:",
        reply_markup=get_cases_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("open_case_"))
async def cb_open_case(callback: CallbackQuery):
    """Логіка відкриття кейсу з рандомом і збереженням в MongoDB."""
    case_id = callback.data.replace("open_case_", "")
    if case_id not in WINTER_CASES:
        await callback.answer("❌ Зимовий кейс не знайдено!", show_alert=True)
        return
        
    case = WINTER_CASES[case_id]
    user_id = callback.from_user.id
    user = await get_or_create_user(user_id, callback.from_user.first_name)
    
    if user["balance"] < case["price"]:
        await callback.answer("❌ Недостатньо морозних монет! Отримай бонус у меню.", show_alert=True)
        return
        
    # Списуємо кошти та збільшуємо лічильник відкритих кейсів
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": -case["price"],
                "cases_opened": 1
            }
        }
    )
    
    # Випадковий вибір предмета на основі ваги (drop_rate)
    items_pool = case["items"]
    weights = [item["drop_rate"] for item in items_pool]
    won_item = random.choices(items_pool, weights=weights, k=1)[0]
    
    # Додаємо предмет в масив інвентарю користувача в MongoDB
    await users_collection.update_one(
        {"user_id": user_id},
        {"$push": {"inventory": won_item}}
    )
    
    updated_user = await get_or_create_user(user_id)
    
    result_text = (
        f"❄️ **Ти успішно відкрив {case['name']}!** 🎁\n\n"
        f"🧊 **Твій виграш:**\n"
        f"🔹 **{won_item['name']}**\n"
        f"⭐ Рідкісність: `{won_item['rarity']}`\n"
        f"💵 Вартість: **{won_item['price']} 🪙**\n\n"
        f"💰 Твій баланс: **{updated_user['balance']} 🪙**"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Відкрити ще раз", callback_data=f"open_case_{case_id}")],
        [InlineKeyboardButton(text="📦 До всіх кейсів", callback_data="cases_menu")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer("🎉 Вітаємо з крутим зимовим дропом!")

# --- ВЕБ-СЕРВЕР AIOHTTP ДЛЯ ПІДТРИМКИ 24/7 НА RENDER ---

async def handle_root(request):
    """Обробник кореневого маршруту веб-сервера."""
    return web.Response(
        text="❄️ CS2 Drop Hub Bot (Winter Edition) is running live 24/7 on Render! 🚀",
        content_type="text/plain"
    )

async def start_web_server():
    """Запуск асинхронного веб-сервера на порту Render."""
    app = web.Application()
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Зимовий веб-сервер успішно запущено на порті {PORT}!")

# --- ГОЛОВНА ТОЧКА ВХОДУ ---

async def main():
    """Головна асинхронна функція запуску додатку."""
    # 1. Підключаємо базу даних
    await initialize_database()
    
    # 2. Реєструємо роутери
    dp.include_router(router)
    
    # 3. Запускаємо веб-сервер для 24/7 аптайму
    await start_web_server()
    
    # 4. Очищаємо вебхуки та запускаємо довготривалий полінг (long polling)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Бот перейшов у режим очікування подій (Start polling)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("❄️ Зимовий бот був штатно зупинений користувачем.")
