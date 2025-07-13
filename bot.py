from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Хранилище прогресса игроков в памяти (для простоты)
players = {}

# Начальные параметры врага и игрока
BASE_ENEMY_HEALTH = 10
BASE_ENEMY_XP = 5
BASE_ENEMY_GOLD = 2

# Улучшения в магазине
UPGRADES = {
    'sword': {'name': 'Меч +1 урон', 'cost': 10, 'damage_increase': 1},
    'armor': {'name': 'Броня (позже)', 'cost': 15, 'damage_increase': 0},  # Пока не используется
    'crit': {'name': 'Критический удар', 'cost': 30, 'damage_increase': 3},
}

def get_player(user_id):
    if user_id not in players:
        players[user_id] = {
            'level': 1,
            'xp': 0,
            'gold': 0,
            'damage': 1,
            'enemy_hp': BASE_ENEMY_HEALTH,
            'enemy_level': 1,
        }
    return players[user_id]

def enemy_stats(level):
    health = BASE_ENEMY_HEALTH + (level - 1) * 5
    xp = BASE_ENEMY_XP + (level - 1) * 3
    gold = BASE_ENEMY_GOLD + (level - 1) * 2
    return health, xp, gold

def level_up(player):
    # Простой уровень: каждые 20 XP - уровень вверх
    while player['xp'] >= player['level'] * 20:
        player['xp'] -= player['level'] * 20
        player['level'] += 1

async def send_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    player = get_player(user_id)

    text = (f"⚔️ Уровень игрока: {player['level']}\n"
            f"💥 Урон за клик: {player['damage']}\n"
            f"⭐️ Опыт: {player['xp']}\n"
            f"💰 Золото: {player['gold']}\n\n"
            f"👹 Враг (уровень {player['enemy_level']}):\n"
            f"❤️ Здоровье: {player['enemy_hp']}")

    keyboard = [
        [InlineKeyboardButton("Атаковать", callback_data='attack')],
        [InlineKeyboardButton("Магазин", callback_data='shop')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_player(user_id)  # Инициализация игрока
    await update.message.reply_text("Привет! Это RPG кликер. Нажимай 'Атаковать', чтобы бить врага и получать золото и опыт!")
    await send_status(update, context)

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    player = get_player(user_id)

    player['enemy_hp'] -= player['damage']
    if player['enemy_hp'] <= 0:
        # Враг побеждён
        enemy_hp, enemy_xp, enemy_gold = enemy_stats(player['enemy_level'])
        player['xp'] += enemy_xp
        player['gold'] += enemy_gold
        player['enemy_level'] += 1
        player['enemy_hp'] = BASE_ENEMY_HEALTH + (player['enemy_level'] - 1) * 5

        level_up(player)
        await query.answer("Враг побеждён! Ты получил золото и опыт.")
    else:
        await query.answer(f"Ты нанес {player['damage']} урона.")

    await send_status(update, context)

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = []
    for key, item in UPGRADES.items():
        keyboard.append([InlineKeyboardButton(f"{item['name']} - {item['cost']} золота", callback_data=f"buy_{key}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "🛒 Магазин улучшений:\nВыбери улучшение для покупки."
    await query.edit_message_text(text, reply_markup=reply_markup)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    player = get_player(user_id)

    item_key = query.data.replace('buy_', '')
    if item_key not in UPGRADES:
        await query.answer("Ошибка покупки.")
        return

    item = UPGRADES[item_key]
    if player['gold'] < item['cost']:
        await query.answer("Недостаточно золота!")
        return

    player['gold'] -= item['cost']
    player['damage'] += item['damage_increase']
    await query.answer(f"Ты купил {item['name']}!")

    await send_status(update, context)

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update, context)

def main():
    TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(attack, pattern='^attack$'))
    app.add_handler(CallbackQueryHandler(shop, pattern='^shop$'))
    app.add_handler(CallbackQueryHandler(buy, pattern='^buy_'))
    app.add_handler(CallbackQueryHandler(back, pattern='^back$'))

    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
