import datetime
import json
import logging
import os
import random

import pytz
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    Application,
)

from config import conf
from texts import STATS_PHRASES, PHRASES, STARTUP_PHRASES, MEMES

# --- КОНФИГУРАЦИЯ ---
STATS_FILE = "stats.json"
TIMERS_FILE = "timers.json"
TZ_MSK = pytz.timezone("Europe/Moscow")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# --- РАБОТА С ФАЙЛАМИ (JSON) ---


def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


def update_user_stats(user_id):
    stats = load_json(STATS_FILE)
    str_id = str(user_id)
    if str_id not in stats:
        stats[str_id] = 0
    stats[str_id] += 1
    save_json(STATS_FILE, stats)
    return stats[str_id]


def get_user_stats(user_id):
    stats = load_json(STATS_FILE)
    return stats.get(str(user_id), 0)


def add_timer_to_db(chat_id, hour, minute):
    timers = load_json(TIMERS_FILE)
    str_id = str(chat_id)
    if str_id not in timers:
        timers[str_id] = []
    new_timer = {"h": hour, "m": minute}
    if new_timer not in timers[str_id]:
        timers[str_id].append(new_timer)
        save_json(TIMERS_FILE, timers)


def remove_timer_from_db(chat_id, hour, minute):
    timers = load_json(TIMERS_FILE)
    str_id = str(chat_id)
    if str_id in timers:
        timers[str_id] = [
            t for t in timers[str_id] if not (t["h"] == hour and t["m"] == minute)
        ]
        save_json(TIMERS_FILE, timers)


def remove_all_timers_from_db(chat_id):
    timers = load_json(TIMERS_FILE)
    str_id = str(chat_id)
    if str_id in timers:
        del timers[str_id]
        save_json(TIMERS_FILE, timers)


# --- ВОССТАНОВЛЕНИЕ ТАЙМЕРОВ ---
async def restore_timers(app: Application):
    timers = load_json(TIMERS_FILE)
    count = 0
    print("♻️  Восстановление матрицы таймеров (МСК)...")
    for chat_id, user_timers in timers.items():
        for t in user_timers:
            # Указываем TZ_MSK при восстановлении
            time_obj = datetime.time(hour=t["h"], minute=t["m"], tzinfo=TZ_MSK)
            app.job_queue.run_daily(
                send_remind, time=time_obj, chat_id=int(chat_id), name=str(chat_id)
            )
            count += 1
    print(f"✅ Успех. {count} таймеров снова в строю.")


# --- ГЕНЕРАТОР СТАТИСТИКИ ---
def generate_funny_stats(count):
    if count < 5:
        title = "Подопытная крыса 🐀"
    elif count < 15:
        title = "Чмоня 🗿"
    elif count < 30:
        title = "Пожиратель колес 🍬"
    elif count < 60:
        title = "Любимец фармацевтов 💊"
    elif count < 100:
        title = "Химозный голем 🧟"
    elif count < 200:
        title = "Киборг-убийца 🤖"
    elif count < 400:
        title = "Бессмертный ублюдок 🦄"
    else:
        title = "Гигачад медицины 💪"

    weight = count * 0.5
    cyber_level = min(100, count * 0.42)
    saved_money = count * 20

    random_end = random.choice(STATS_PHRASES)

    text = (
        f"📊 <b>ДОСЬЕ ПАЦИЕНТА</b>\n\n"
        f"💊 Закинулся раз: <b>{count}</b>\n"
        f"🏆 Погоняло: <b>{title}</b>\n"
        f"⚖️ Вес химии внутри: <b>{weight} г.</b>\n"
        f"🤖 Оцифровка души: <b>{cyber_level:.1f}%</b>\n"
        f"💰 Сэкономил на гробе: <b>${saved_money}</b>\n\n"
        f"<i>{random_end}</i>"
    )
    return text


# --- УТИЛИТЫ ---
async def delete_message_later(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=job_data["chat_id"], message_id=job_data["message_id"]
        )
    except:
        pass


def schedule_deletion(context, chat_id, message_id, delay=10):
    context.job_queue.run_once(
        delete_message_later, delay, data={"chat_id": chat_id, "message_id": message_id}
    )


# --- КЛАВИАТУРЫ ---
main_keyboard = [
    ["⏰ Новый таймер", "🕒 Мои таймеры"],
    ["📊 Моя статистика", "❌ Удалить таймер"],
]
markup_main = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)


def get_hours_keyboard():
    keyboard = []
    row = []
    for i in range(24):
        row.append(InlineKeyboardButton(f"{i:02d}:00", callback_data=f"hour_{i}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(keyboard)


def get_minutes_keyboard(hour):
    keyboard = []
    row = []
    for i in range(0, 60, 10):
        label = f"{hour:02d}:{i:02d}"
        row.append(InlineKeyboardButton(label, callback_data=f"set_{hour}_{i}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hours")])
    return InlineKeyboardMarkup(keyboard)


def get_delete_keyboard(chat_id, context):
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    keyboard = []
    if current_jobs:
        # Сортировка по времени
        sorted_jobs = sorted(
            current_jobs,
            key=lambda x: (
                x.next_t.astimezone(TZ_MSK).time() if x.next_t else datetime.time(0, 0)
            ),
        )
        for job in sorted_jobs:
            if job.next_t:
                # Переводим в МСК для отображения в кнопке
                msk_time = job.next_t.astimezone(TZ_MSK)
                time_str = msk_time.strftime("%H:%M")
                hour, minute = msk_time.hour, msk_time.minute
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"🗑 Удалить {time_str}",
                            callback_data=f"del_{hour}_{minute}",
                        )
                    ]
                )

    keyboard.append(
        [InlineKeyboardButton("🧨 Удалить ВСЕ к херам", callback_data="del_all")]
    )
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(keyboard)


# --- ОБРАБОТЧИКИ ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😈 HellBot (18+).\nЯ буду ругаться, но это для твоего же блага, суч*ныш. Время по МСК.",
        reply_markup=markup_main,
    )


async def start_timer_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass
    await update.message.reply_text(
        "Выбери ЧАС (по МСК):", reply_markup=get_hours_keyboard()
    )


async def show_active_timers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not current_jobs:
        msg = await update.message.reply_text("📭 Них*я нет. Ты здоров или забил?")
    else:
        # Переводим каждое время в МСК для корректного вывода списка
        job_times = []
        for job in current_jobs:
            if job.next_t:
                msk_t = job.next_t.astimezone(TZ_MSK)
                job_times.append(msk_t.time())

        job_times.sort()
        times_str = [f"⏰ <b>{t.strftime('%H:%M')}</b>" for t in job_times]
        text = "💀 <b>Твои дедлайны (МСК):</b>\n" + "\n".join(times_str)
        msg = await update.message.reply_text(text, parse_mode="HTML")
    schedule_deletion(context, chat_id, msg.message_id, delay=10)


async def start_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not current_jobs:
        msg = await update.message.reply_text("Удалять нечего.")
        schedule_deletion(context, chat_id, msg.message_id, delay=5)
        return
    await update.message.reply_text(
        "Что сносим?", reply_markup=get_delete_keyboard(chat_id, context)
    )


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data.startswith("hour_"):
        hour = int(data.split("_")[1])
        await query.edit_message_text(
            f"Час: {hour:02d}. Минуты:", reply_markup=get_minutes_keyboard(hour)
        )

    elif data == "back_to_hours":
        await query.edit_message_text("Выбери ЧАС:", reply_markup=get_hours_keyboard())

    elif data.startswith("set_"):
        parts = data.split("_")
        hour = int(parts[1])
        minute = int(parts[2])
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        is_duplicate = False

        # Создаем время с учетом МСК
        target_time = datetime.time(hour=hour, minute=minute)

        for job in current_jobs:
            if job.next_t:
                # Сравниваем время, приведя оба к МСК
                job_msk_time = (
                    job.next_t.astimezone(TZ_MSK)
                    .time()
                    .replace(second=0, microsecond=0)
                )
                if job_msk_time == target_time.replace(tzinfo=None):
                    is_duplicate = True
                    break

        if is_duplicate:
            await query.edit_message_text(
                f"⚠️ Бл*ть, таймер на {hour:02d}:{minute:02d} уже стоит!"
            )
        else:
            context.job_queue.run_daily(
                send_remind, time=target_time, chat_id=chat_id, name=str(chat_id)
            )
            add_timer_to_db(chat_id, hour, minute)
            await query.edit_message_text(
                f"✅ Готово. Я напомню в {hour:02d}:{minute:02d} по МСК. Не про*би."
            )
            schedule_deletion(context, chat_id, query.message.message_id, delay=10)

    elif data.startswith("del_") and data != "del_all":
        parts = data.split("_")
        hour, minute = int(parts[1]), int(parts[2])
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))

        # Искомое время в формате МСК
        target_t = datetime.time(hour=hour, minute=minute)

        deleted = False
        for job in current_jobs:
            if job.next_t:
                job_msk_t = (
                    job.next_t.astimezone(TZ_MSK)
                    .time()
                    .replace(second=0, microsecond=0)
                )
                if job_msk_t == target_t:
                    job.schedule_removal()
                    deleted = True

        if deleted:
            remove_timer_from_db(chat_id, hour, minute)
            remaining = context.job_queue.get_jobs_by_name(str(chat_id))
            if not remaining:
                await query.edit_message_text("🗑 Чисто.")
            else:
                await query.edit_message_text(
                    "🗑 Снес. Еще?", reply_markup=get_delete_keyboard(chat_id, context)
                )
        else:
            await query.edit_message_text("Ошибка удаления.")

    elif data == "del_all":
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()
        remove_all_timers_from_db(chat_id)
        await query.edit_message_text("💥 Всё взорвано к х*рам.")

    elif data == "cancel_delete":
        await query.message.delete()

    elif data == "pill_taken":
        total = update_user_stats(query.from_user.id)
        meme_url = random.choice(MEMES)
        await query.message.delete()
        try:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=meme_url,
                caption=f"Принято! Доз: {total}. Красава.",
            )
            schedule_deletion(context, chat_id, msg.message_id, delay=30)
        except:
            await context.bot.send_message(chat_id, "Записан, чукча.")


async def send_remind(context: ContextTypes.DEFAULT_TYPE):
    print(f"--- ТРИГГЕР СРАБОТАЛ В {datetime.datetime.now()} ---")  # Отладка
    job = context.job
    phrase = random.choice(PHRASES)
    keyboard = [
        [InlineKeyboardButton("✅ Я выпил, отвали!", callback_data="pill_taken")]
    ]
    await context.bot.send_message(
        job.chat_id, text=phrase, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass
    count = get_user_stats(update.effective_user.id)
    text = generate_funny_stats(count)
    msg = await update.message.reply_text(text, parse_mode="HTML")
    schedule_deletion(context, update.effective_chat.id, msg.message_id, delay=15)


if __name__ == "__main__":
    from telegram.ext import Defaults

    defaults = Defaults(tzinfo=TZ_MSK)
    # Создаем приложение и передаем функцию восстановления таймеров
    app = (
        ApplicationBuilder()
        .token(conf.token)
        .defaults(defaults)
        .post_init(restore_timers)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.Regex("^⏰ Новый таймер$"), start_timer_selection)
    )
    app.add_handler(
        MessageHandler(filters.Regex("^🕒 Мои таймеры$"), show_active_timers)
    )
    app.add_handler(MessageHandler(filters.Regex("^📊 Моя статистика$"), show_stats))
    app.add_handler(
        MessageHandler(filters.Regex("^❌ Удалить таймер$"), start_delete_selection)
    )
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print(f"\n{random.choice(STARTUP_PHRASES)}\n")
    app.run_polling()
