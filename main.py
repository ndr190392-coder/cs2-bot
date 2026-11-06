import asyncio
import json
import os
import random
import time
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === ОСНОВНЫЕ НАСТРОЙКИ ===
BOT_TOKEN = "8825098686:AAHsz7XDYyLOSgD8oMOWOF5uhsKUApmoXB8"
ADMIN_CHAT_ID = 8876279113

CHANNEL_USERNAME = "@CS_Drop_Hub"
CHANNEL_URL = "https://t.me/CS_Drop_Hub"

DATA_FILE = "users_data.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = {}
used_trade_urls = set()
promo_codes = {}
used_promos = {}
custom_quests = {}

# === РАБОТА С БАЗОЙ ДАННЫХ ===

def load_data():
    global users, used_trade_urls, promo_codes, used_promos, custom_quests
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                used_trade_urls = set(data.get("used_trade_urls", []))
                promo_codes = data.get("promo_codes", {})
                used_promos = {int(k): set(v) for k, v in data.get("used_promos", {}).items()}
                custom_quests = data.get("custom_quests", {})
                logging.info("❄️ Зимняя база данных успешно загружена!")
        except Exception as e:
            logging.error(f"⚠️ Ошибка загрузки базы данных: {e}")
            init_empty_db()
    else:
        init_empty_db()

def init_empty_db():
    global users, used_trade_urls, promo_codes, used_promos, custom_quests
    users = {}
    used_trade_urls = set()
    promo_codes = {}
    used_promos = {}
    custom_quests = {}
    save_data()

def save_data():
    try:
        data = {
            "users": {str(k): v for k, v in users.items()},
            "used_trade_urls": list(used_trade_urls),
            "promo_codes": promo_codes,
            "used_promos": {str(k): list(v) for k, v in used_promos.items()},
            "custom_quests": custom_quests
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"⚠️ Ошибка сохранения базы данных: {e}")

# === ЗИМНИЕ НАСТРОЙКИ КЕЙСОВ ===

CASES = {
    "case_winter": {
        "name": "❄️ Зимний Праздничный Кейс",
        "price": 400,
        "max_limit": 1200,
        "rarities": {
            "Ширпотреб (❄️ Ice)": {"chance": 90.0, "min": 100, "max": 500},
            "Uncommon (🎄 New Year)": {"chance": 8.0, "min": 550, "max": 900},
            "Rare (⭐ Frostbite)": {"chance": 2.0, "min": 950, "max": 1200}
        }
    },
    "case_new_year": {
        "name": "🎄 Новогодний Премиум",
        "price": 800,
        "max_limit": 2000,
        "rarities": {
            "Ширпотреб": {"chance": 85.0, "min": 300, "max": 900},
            "Uncommon": {"chance": 10.0, "min": 950, "max": 1500},
            "Rare": {"chance": 5.0, "min": 1550, "max": 2000}
        }
    },
    "case_santa": {
        "name": "🎅 Мешок Санты (Элитный)",
        "price": 2500,
        "max_limit": 3500,
        "rarities": {
            "Uncommon": {"chance": 45.0, "min": 1500, "max": 2200},
            "Rare": {"chance": 35.0, "min": 2250, "max": 3500},
            "Ширпотреб": {"chance": 20.0, "min": 1000, "max": 1400}
        }
    }
}

ROULETTE_POOL = [
    "❄️ AK-47 | Ice Coaled - 800 монет",
    "🎄 AWP | Asiimov (Winter) - 2500 монет",
    "🧊 M4A4 | Neo-Noir - 1400 монет",
    "⭐ ★ Karambit | Freehand - 3500 монет",
    "🎁 USP-S | Printstream - 1900 монет",
    "❄️ Glock-18 | Gamma Doppler - 1100 монет",
    "🎄 Desert Eagle | Code Red - 1600 монет",
    "🧊 P90 | Asiimov - 700 монет",
    "⭐ Ширпотреб (Лед) - 300 монет",
    "🎁 Uncommon (Снеговик) - 600 монет"
]

def get_user(user_id, username, referrer_id=None):
    now = time.time()
    if user_id not in users:
        users[user_id] = {
            "username": username or "Снеговик",
            "balance": 500,
            "inventory": [],
            "trade_url": None,
            "last_daily": 0,
            "quest_channel": False,
            "completed_quests": [],
            "referrals": 0,
            "first_case_opened": False,
            "joined_at": now,
            "last_active": now
        }
        if referrer_id and referrer_id in users and referrer_id != user_id:
            users[referrer_id]["balance"] += 500
            users[referrer_id]["referrals"] += 1
            users[user_id]["balance"] += 200
        save_data()
    else:
        users[user_id]["last_active"] = now
        if username:
            users[user_id]["username"] = username
        if "completed_quests" not in users[user_id]:
            users[user_id]["completed_quests"] = []
        if "first_case_opened" not in users[user_id]:
            users[user_id]["first_case_opened"] = False
    return users[user_id]

# === ЗИМНИЕ КЛАВИАТУРЫ ===

def main_keyboard(user_id):
    kb = [
        [KeyboardButton(text="🎁 Зимние Кейсы"), KeyboardButton(text="❄️ Мой Профиль")],
        [KeyboardButton(text="🎯 Зимние Квесты"), KeyboardButton(text="🧊 Бонусы и Промокоды")],
        [KeyboardButton(text="📜 Правила")]
    ]
    if user_id == ADMIN_CHAT_ID:
        kb.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def cases_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❄️ Зимний Праздничный Кейс - 400 монет")],
            [KeyboardButton(text="🎄 Новогодний Премиум - 800 монет")],
            [KeyboardButton(text="🎅 Мешок Санты - 2500 монет")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )

def bonus_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Забрать зимний бонус")],
            [KeyboardButton(text="🎟 Ввести промокод")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎯 Создать квест", callback_data="admin_add_quest")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🎟 Промокоды", callback_data="admin_promos")]
    ])

# === ОСНОВНЫЕ ОБРАБОТЧИКИ ===

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    get_user(message.from_user.id, message.from_user.username, referrer_id)
    
    await message.answer(
        f"❄️ **Здравствуй, {message.from_user.first_name} в зимней сказке!** 🎄\n\n"
        f"Добро пожаловать в новогодний **CS2 Drop Hub**!\n"
        f"Открывай праздничные кейсы, собирай монеты и выводи лучшие зимние скины в Steam. 🎁\n\n"
        f"Выбери нужный раздел в меню ниже:",
        parse_mode="Markdown",
        reply_markup=main_keyboard(message.from_user.id)
    )

@dp.message(F.text == "⬅️ Назад в меню")
async def back_to_menu(message: types.Message):
    await message.answer(
        "🎄 **Главное новогоднее меню**\nВыбери пункт назначения:",
        reply_markup=main_keyboard(message.from_user.id)
    )

@dp.message(F.text == "📜 Правила")
async def show_rules(message: types.Message):
    rules_text = (
        "📜 **ПРАВИЛА ЗИМНЕГО СЕЗОНА CS2 DROP HUB** ❄️\n\n"
        "1️⃣ **Мультиаккаунты:**\n"
        "• Создание нескольких аккаунтов для фарма новогодних монет строго запрещено. Система блокирует нарушителей навсегда.\n\n"
        "2️⃣ **Вывод скинов:**\n"
        "• Убедись, что твой Trade URL открыт.\n"
        "• **Минимальная стоимость скина для вывода: 500 монет!**\n"
        "• Заявки обрабатываются в течение 24-48 часов."
    )
    await message.answer(rules_text, parse_mode="Markdown")

# === КВЕСТЫ ===

@dp.message(F.text == "🎯 Зимние Квесты")
async def show_quests(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    main_status = "✅ Выполнено" if user["quest_channel"] else "❌ Не выполнено"

    kb_list = [
        [InlineKeyboardButton(text="📢 Подписаться на @CS_Drop_Hub", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="❄️ Проверить подписку (+250 монет)", callback_data="check_quest_channel")]
    ]

    custom_text = ""
    if custom_quests:
        custom_text = "\n\n🔥 **ДОП. ЗАДАНИЯ:**\n"
        for q_id, q_data in custom_quests.items():
            is_done = q_id in user.get("completed_quests", [])
            q_status = "✅" if is_done else "❌"
            custom_text += f"• {q_data['title']} — **{q_data['reward']} монет** [{q_status}]\n"
            if not is_done:
                kb_list.append([InlineKeyboardButton(text=f"Перейти: {q_data['title']}", url=q_data['url'])])
                kb_list.append([InlineKeyboardButton(text=f"Проверить: {q_data['title']}", callback_data=f"check_custom_q_{q_id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_list)

    await message.answer(
        f"🎯 **Зимние квесты и награды:**\n\n"
        f"1️⃣ **Подписка на канал {CHANNEL_USERNAME}**\n"
        f"🎁 Награда: **250 монет** [{main_status}]\n\n"
        f"2️⃣ **Пригласи друзей (Новогодняя рефералка)**\n"
        f"💰 Награда: **+500 монет** за друга! (Другу +200 на старт)\n"
        f"👥 Приглашено: **{user['referrals']}** друзей\n\n"
        f"🔗 Твоя личная ссылка:\n`{ref_link}`"
        f"{custom_text}",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == "check_quest_channel")
async def check_quest(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    if user["quest_channel"]:
        await callback.answer("❄️ Ты уже забрал награду за этот квест!", show_alert=True)
        return

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=callback.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            user["balance"] += 250
            user["quest_channel"] = True
            save_data()
            await callback.message.answer("🎉 Ура! Подписка подтверждена. Начислено **+250 монет** 🎁!")
            await callback.answer()
        else:
            await callback.answer("❌ Ты еще не подписался на канал @CS_Drop_Hub!", show_alert=True)
    except Exception:
        await callback.answer("❌ Ошибка проверки. Убедись, что бот админ в канале!", show_alert=True)

@dp.callback_query(F.data.startswith("check_custom_q_"))
async def check_custom_quest_cb(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    q_id = callback.data.replace("check_custom_q_", "")

    if q_id not in custom_quests or q_id in user.get("completed_quests", []):
        await callback.answer("Квест не найден или уже выполнен!", show_alert=True)
        return

    reward = custom_quests[q_id]["reward"]
    user["balance"] += reward
    user["completed_quests"].append(q_id)
    save_data()

    await callback.message.answer(f"🎉 Квест выполнен! Зачислено **+{reward} монет** ❄️.")
    await callback.answer()

# === ЗИМНИЕ КЕЙСЫ И АНИМАЦИЯ РУЛЕТКИ ===

@dp.message(F.text == "🎁 Зимние Кейсы")
async def show_cases_menu(message: types.Message):
    await message.answer("🛒 **Выбери новогодний кейс для открытия:**", parse_mode="Markdown", reply_markup=cases_keyboard())

@dp.message(F.text.in_({
    "❄️ Зимний Праздничный Кейс - 400 монет",
    "🎄 Новогодний Премиум - 800 монет",
    "🎅 Мешок Санты - 2500 монет"
}))
async def open_selected_case(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    
    if "Мешок" in message.text:
        case_key = "case_santa"
    elif "Премиум" in message.text:
        case_key = "case_new_year"
    else:
        case_key = "case_winter"

    case_info = CASES[case_key]
    price = case_info["price"]

    if user["balance"] < price:
        await message.answer(f"❌ Недостаточно монет! Цена кейса: **{price} монет**. Твой баланс: **{user['balance']}** 🧊", parse_mode="Markdown")
        return

    user["balance"] -= price

    # Зимняя анимированная рулетка прямо в чате
    spin_msg = await message.answer(
        "🎰 **Запускаем новогоднюю рулетку...**\n"
        "╭────────────────────────╮\n"
        "│  ❄️ [ 🧊 ]  [ 🎄 ]  [ 🎁 ]  ❄️  │\n"
        "╰────────────────────────╯", 
        parse_mode="Markdown"
    )

    for step in range(4):
        await asyncio.sleep(0.4)
        items_mix = random.sample(ROULETTE_POOL, 3)
        if step == 0:
            frame = f"│  🎁 [ {items_mix[0]} ]  │"
        elif step == 1:
            frame = f"│  ❄️ [ {items_mix[0]} ] ➔ [ {items_mix[1]} ]  │"
        elif step == 2:
            frame = f"│  🎄 ... [ {items_mix[0]} | **{items_mix[1]}** | {items_mix[2]} ] ... │"
        else:
            frame = f"│  ⭐ ФИНАЛ: [ **{items_mix[1]}** ]  ⭐│"

        await spin_msg.edit_text(
            f"🎰 **Крутим праздничный барабан... (Шаг {step+1}/4)**\n"
            f"╭────────────────────────╮\n"
            f"{frame}\n"
            f"╰────────────────────────╯",
            parse_mode="Markdown"
        )

    await asyncio.sleep(0.5)

    if not user.get("first_case_opened", False):
        win_rarity = "Rare (⭐ Frostbite)" if "case_winter" in case_key else "Rare"
        rarity_data = case_info["rarities"][list(case_info["rarities"].keys())[-1]]
        item_value = rarity_data["max"]
        user["first_case_opened"] = True
    else:
        rand = random.uniform(0, 100)
        cumulative = 0
        win_rarity = list(case_info["rarities"].keys())[0]

        for rarity, info in case_info["rarities"].items():
            cumulative += info["chance"]
            if rand <= cumulative:
                win_rarity = rarity
                break

        rarity_data = case_info["rarities"][win_rarity]
        item_value = random.randint(rarity_data["min"], rarity_data["max"])
        if item_value > case_info["max_limit"]:
            item_value = case_info["max_limit"]

    item_title = f"{win_rarity} — {item_value} монет"

    user["inventory"].append({"name": item_title, "value": item_value})
    save_data()

    await spin_msg.edit_text(
        f"🎉 **Поздравляем! Из кейса {case_info['name']} выпало:**\n\n"
        f"🎁 **{item_title}** 🌟\n\n"
        f"💰 Твой баланс монет: **{user['balance']}** ❄️",
        parse_mode="Markdown"
    )

# === БОНУСЫ И ПРОМОКОДЫ ===

@dp.message(F.text == "🧊 Бонусы и Промокоды")
async def show_bonus_menu(message: types.Message):
    await message.answer("🎁 **Зимний центр бонусов:**", parse_mode="Markdown", reply_markup=bonus_keyboard())

@dp.message(F.text == "🎁 Забрать зимний бонус")
async def daily_bonus(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    now = time.time()
    cooldown = 24 * 3600

    if now - user["last_daily"] < cooldown:
        remaining = cooldown - (now - user["last_daily"])
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await message.answer(f"⏳ Зимний бонус уже собран! Жди еще **{hours} ч {minutes} мин** ❄️.", parse_mode="Markdown")
        return

    reward = random.randint(150, 250)
    user["balance"] += reward
    user["last_daily"] = now
    save_data()
    await message.answer(f"🎁 Ты забрал ежедневный подарок Санты: **+{reward} монет**!\n💰 Баланс: **{user['balance']}** 🎄", parse_mode="Markdown")

@dp.message(F.text == "🎟 Ввести промокод")
async def ask_promo(message: types.Message):
    await message.answer("🔑 Напиши свой новогодний промокод в ответ на это сообщение:", parse_mode="Markdown")

# === ПРОФИЛЬ И ИНВЕНТАРЬ ===

@dp.message(F.text == "❄️ Мой Профиль")
async def show_profile_msg(message: types.Message):
    await send_profile(message.from_user.id, message.from_user.username, message)

async def send_profile(user_id, username, message: types.Message):
    user = get_user(user_id, username)
    trade_status = user["trade_url"] if user["trade_url"] else "❌ Не указана"
    
    if user["inventory"]:
        inv_text = "\n".join([f"• {item['name']}" for item in user["inventory"]])
    else:
        inv_text = "Пусто 🧊"

    text = (
        f"❄️ **Твой зимний профиль:**\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Монет на балансе: **{user['balance']}**\n"
        f"👥 Приглашено друзей: **{user['referrals']}**\n"
        f"🔗 Trade URL: {trade_status}\n\n"
        f"🎒 **Твой инвентарь:**\n{inv_text}"
    )

    kb_buttons = []
    if not user["trade_url"]:
        kb_buttons.append([InlineKeyboardButton(text="🔗 Установить Trade URL", callback_data="set_trade")])
    
    if user["inventory"]:
        total_value = sum(item["value"] for item in user["inventory"])
        kb_buttons.append([InlineKeyboardButton(text=f"💰 Продать всё (+{total_value} монет)", callback_data="sell_all")])

        for idx, item in enumerate(user["inventory"]):
            kb_buttons.append([
                InlineKeyboardButton(text=f"📤 Вывести ({item['value']}м)", callback_data=f"withdraw_{idx}"),
                InlineKeyboardButton(text=f"💰 Продать (+{item['value']})", callback_data=f"sell_{idx}")
            ])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons) if kb_buttons else None
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "sell_all")
async def sell_all_items(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    if not user["inventory"]:
        await callback.answer("⚠️ Инвентарь пуст!", show_alert=True)
        return

    total_value = sum(item["value"] for item in user["inventory"])
    user["balance"] += total_value
    user["inventory"].clear()
    save_data()

    await callback.answer(f"✅ Продано всё на +{total_value} монет! 🎄", show_alert=True)
    await send_profile(callback.from_user.id, callback.from_user.username, callback.message)

@dp.callback_query(F.data.startswith("sell_"))
async def sell_item(callback: types.CallbackQuery):
    if callback.data == "sell_all":
        return
    user = get_user(callback.from_user.id, callback.from_user.username)
    item_idx = int(callback.data.split("_")[1])

    if item_idx < len(user["inventory"]):
        item = user["inventory"].pop(item_idx)
        user["balance"] += item["value"]
        save_data()
        await callback.answer(f"✅ Предмет продан за +{item['value']} монет!", show_alert=True)
        await send_profile(callback.from_user.id, callback.from_user.username, callback.message)

@dp.callback_query(F.data == "set_trade")
async def ask_trade_url(callback: types.CallbackQuery):
    await callback.message.answer("✏️ Отправь свой Steam Trade URL следующим сообщением:")
    await callback.answer()

@dp.message(F.text.startswith("https://steamcommunity.com/tradeoffer/"))
async def save_trade_url(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    url = message.text.strip()

    if url in used_trade_urls and user["trade_url"] != url:
        await message.answer("❌ Эта ссылка уже привязана к другому аккаунту!", parse_mode="Markdown")
        return

    if user["trade_url"]:
        used_trade_urls.remove(user["trade_url"])

    user["trade_url"] = url
    used_trade_urls.add(url)
    save_data()
    await message.answer("✅ **Trade URL успешно сохранен!** ❄️", parse_mode="Markdown")

# === ВЫВОД СКИНОВ (ОТ 500 МОНЕТ) ===

@dp.callback_query(F.data.startswith("withdraw_"))
async def withdraw_item(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    item_idx = int(callback.data.split("_")[1])

    if not user["trade_url"]:
        await callback.answer("⚠️ Сначала укажи свой Trade URL в профиле!", show_alert=True)
        return

    if item_idx < len(user["inventory"]):
        item = user["inventory"][item_idx]

        if item.get("value", 0) < 500:
            await callback.answer("❌ Вывод доступен только для предметов стоимостью от 500 монет!", show_alert=True)
            return

        admin_msg = (
            f"📥 **НОВАЯ НОВОГОДНЯЯ ЗАЯВКА НА ВЫВОД!**\n\n"
            f"👤 Игрок: @{user['username']} (ID: `{callback.from_user.id}`)\n"
            f"🎁 Предмет: **{item['name']}**\n"
            f"🔗 Trade URL: {user['trade_url']}"
        )
        try:
            await bot.send_message(ADMIN_CHAT_ID, admin_msg, parse_mode="Markdown")
            user["inventory"].pop(item_idx)
            save_data()
            await callback.answer("✅ Заявка отправлена администратору!", show_alert=True)
            await send_profile(callback.from_user.id, callback.from_user.username, callback.message)
        except Exception:
            await callback.answer("❌ Ошибка отправки заявки.", show_alert=True)

# === АДМИН-ПАНЕЛЬ ===

@dp.message(F.text == "⚙️ Админ-панель")
async def open_admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer(
        "⚙️ **Зимняя панель администратора**\n\n"
        "• `/makecode <код> <монеты> <лимит> <часов>`\n"
        "• `/addquest <id> <название> <награда> <url>`\n"
        "• `/give <user_id> <монеты>`",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_CHAT_ID:
        return
    total_users = len(users)
    total_balance = sum(u.get("balance", 0) for u in users.values() if isinstance(u, dict))
    
    stats_text = (
        f"📊 **Зимняя статистика:**\n\n"
        f"👥 Всего пользователей: **{total_users}**\n"
        f"💰 Баланс всех игроков: **{total_balance:,} монет**\n"
        f"🎟 Активных промокодов: **{len(promo_codes)}**"
    )
    await callback.message.edit_text(stats_text, parse_mode="Markdown", reply_markup=admin_keyboard())
    await callback.answer()

@dp.message(Command("give"))
async def admin_give_coins(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    args = message.text.split()
    if len(args) == 3 and args[1].isdigit() and args[2].isdigit():
        target_id, amount = int(args[1]), int(args[2])
        if target_id in users:
            users[target_id]["balance"] += amount
            save_data()
            await message.answer(f"✅ Начислено +{amount} монет игроку `{target_id}` ❄️", parse_mode="Markdown")
            try:
                await bot.send_message(target_id, f"🎁 Администратор начислил вам новогодний бонус: **+{amount} монет**!")
            except:
                pass

@dp.message(Command("makecode"))
async def admin_make_code(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    args = message.text.split()
    if len(args) == 5:
        code = args[1].upper()
        amount, max_uses, hours = int(args[2]), int(args[3]), int(args[4])
        promo_codes[code] = {
            "amount": amount,
            "max_uses": max_uses,
            "uses_count": 0,
            "expires_at": time.time() + (hours * 3600)
        }
        save_data()
        await message.answer(f"✅ Промокод `{code}` на **{amount} монет** создан! 🎄", parse_mode="Markdown")

# === АКТИВАЦИЯ ПРОМОКОДОВ ===

@dp.message()
async def process_promo(message: types.Message):
    text_code = message.text.strip().upper()
    user_id = message.from_user.id

    if text_code in promo_codes:
        promo = promo_codes[text_code]
        if time.time() > promo["expires_at"] or promo["uses_count"] >= promo["max_uses"]:
            await message.answer("❌ Этот промокод уже устарел или исчерпал лимит активаций!")
            return

        if user_id not in used_promos:
            used_promos[user_id] = set()

        if text_code in used_promos[user_id]:
            await message.answer("❌ Ты уже активировал этот промокод!")
            return

        reward = promo["amount"]
        user = get_user(user_id, message.from_user.username)
        user["balance"] += reward
        used_promos[user_id].add(text_code)
        promo["uses_count"] += 1
        save_data()

        await message.answer(f"🎉 Промокод успешно активирован! Получено **+{reward} монет** 🎁.\n💰 Твой баланс: **{user['balance']}**", parse_mode="Markdown")

# === ЗАПУСК ===

async def main():
    load_data()
    print("❄️ Зимний CS2 Drop Hub Bot успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())