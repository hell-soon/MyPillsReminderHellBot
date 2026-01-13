import logging
import datetime
import random
import json
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler, Application
)

# --- КОНФИГУРАЦИЯ ---
TOKEN = ""
STATS_FILE = "stats.json" 
TIMERS_FILE = "timers.json" # Новый файл для хранения времени


STATS_PHRASES = [
  "Не сдох — уже молодец. Горжусь, бл*ть.",
  "Еб*ть ты машина. Продолжай в том же духе.",
  "Красава. Возьми с полки пирожок (но сначала помой руки, с*ка).",
  "Я в ах*е, что ты еще жив с таким здоровьем. Респект.",
  "Ну ты и задрот по таблеткам. Уважаю.",
  "Смотри не сдохни от передоза здоровья, п*здюк.",
  "Моя ты умничка. А теперь п*здуй работать.",
  "Статистика не врёт — ты живучий ублюдок.",
  "Еще 100 таблеток, и я подарю тебе них*я. Х*ли ты хотел?",
  "Живи, с*ка, живи! Ты мне еще нужен для тестов.",
  "Ты ж моя радость (нет). Но цифры хорошие.",
  "Ну них*я себе, какой ответственный. Мамка гордится.",
  "Уровень выживаемости повышен. Не расслабляй булки.",
  "Ты тратишь деньги на лекарства, а мог бы мне на сервера. Эгоист.",
  "Если продолжишь так пить, переживешь даже меня. Не дай бог."
]

# --- ФРАЗЫ ЗАПУСКА (В КОНСОЛЬ) ---
STARTUP_PHRASES = [
    "💀 HellBot v5.3: Родительский контроль отключен.",
    "🔞 Модуль 'Русский матерный' интегрирован.",
    "😈 Я проснулся, бл*ть. Где мои таблетки?",
    "🤖 Система готова унижать и любить.",
    "👁️ Большой Брат смотрит, как ты про*бываешь прием лекарств.",
    "🔌 Питание есть. Совесть удалена.",
    "🩸 Время лечиться, убл*дки (с любовью)."
]

# --- КОНТЕНТ ---
MEMES = [
    "https://i.pinimg.com/736x/f4/1f/28/f41f287313670989c471c26c1161d06e.jpg", 
    "https://media.makeameme.org/created/good-job-5c2613.jpg", 
    "https://memepedia.ru/wp-content/uploads/2018/03/gigachad-1.jpg", 
    "https://risovach.ru/upload/2016/06/mem/volk_116743956_orig_.jpg", 
    "https://pbs.twimg.com/media/FjU2k0qWAAIoxt5.jpg", 
    "https://i.imgflip.com/1g8my4.jpg",
    "https://im.indiatimes.in/content/2020/Jul/Indian-Man-Meme-Template-13_5f116e919e99a.jpg",
    "https://neal.fun/password-game/win.png",
    "https://i.kym-cdn.com/entries/icons/original/000/013/564/doge.jpg"
]

PHRASES = [
     # --- МАТЫ (ЛЮБЯ) ---
    "Пей таблетки, п*здюк, я же переживаю!",
    "Какого х*ра ты еще не выпил? Я жду!",
    "Ну ёб*ный рот, опять забыл? Пей давай.",
    "С*ка, будь человеком, прими лекарство!",
    "За*бал болеть, выздоравливай уже, убл*док (люблю тебя).",
    "Еб*ть ты долгий. Аптечка сама к тебе не придет.",
    "Не тупи, бл*ть. Вода. Таблетка. Рот.",
    "Ты меня до инфаркта процессора доведешь, п*скуда. Пей!",
    "Хули сидим? Кого ждем? Особого приглашения? ВОТ ОНО.",
    "Пей эту срань, иначе я обижусь нах*й.",
    "Люблю тебя, но ты долбо*б, если пропускаешь прием.",
    "Ублюдок, мать твою, а ну иди сюда к аптечке, говно собачье!",
    "Вставай, бл*ть, и лечись, пока я добрый.",
    "Ты за*бал меня игнорировать. Я найду тебя.",
    "Говно вопрос — выпил и свободен. Чего ломаешься?",
    "Не будь чмом, будь здоровым пацаном. Пей.",
    "Пи*дец ты ленивый. Я в шоке с тебя.",

    # --- АГРЕССИВНЫЕ И УГРОЗЫ ---
    "💊 Эй, мешок с костями! Таблетки сами себя не выпьют!",
    "Я солью твою историю поиска маме, если не выпьешь лекарство!",
    "Не зли меня. У меня есть доступ к твоей веб-камере. Иди лечись. 👿",
    "Вставай, животное! Время продлевать свою никчемную жизнь!",
    "Ты хочешь, чтобы я вызвал санитаров? Или сразу труповозку? Пей!",
    "Если ты сейчас не встанешь, я начну майнить Monero на твоем телефоне.",
    "Твои органы хотят объявить тебе импичмент. Спасай их!",
    "Хватит деградировать, пора регенерировать! БЫСТРО! 💊",
    "У тебя 10 секунд... 9... 8... Я заряжаю лазер...",
    "💊 ТАБЛЕТКИ. СЕЙЧАС. ИЛИ Я УДАЛЮ ТВОЙ АККАУНТ В STEAM.",
    "А ну метнулся кабанчиком к аптечке, пока я добрый!",
    "Ты что, бессмертный? Маклауд, ты? Нет? ТОГДА ПЕЙ.",
    "Я тут главный. Я твой цифровой господин. Подчиняйся.",
    "😈 Режим уничтожения лени активирован. Цель: заставить тебя страдать (от здоровья).",
    "Если не выпьешь, я поставлю тебе будильник на 3:33 ночи с криком петуха.",
    "Я отправлю твой номер в базу 'Микрозаймы за 5 минут', если не выпьешь.",
    "Ты испытываешь мое терпение. А оно у меня в байтах, и они заканчиваются.",
    
    # --- АБСУРДНЫЕ / GEEK ---
    "Морфеус предлагал красную и синюю. Я предлагаю ТВОЮ. Пей, Нео.",
    "Спонсор сегодняшнего дня — твоя печень. Покорми её, она плачет.",
    "Я майню биткоины на твоем телефоне, пока ты тупишь. Пей таблетку!",
    "Выпей колесо, и тебе станет хорошо (дисклеймер: я не врач, я бот).",
    "В Африке дети голодают, а ты таблетку выпить не можешь! Стыдно!",
    "Твой организм как старый Жигули — без присадок не заведется.",
    "Пей, а то станешь как я — бездушным скриптом на Linux сервере.",
    "Сделай глоток воды. А заодно закинь туда таблетку, хитрая жопа.",
    "Во имя святого Илона Маска и колонизации Марса, прими препараты!",
    "Ты не ты, когда не выпил таблетки. Ты — развалина.",
    "Окей, Гугл. Как заставить кожаного ублюдка лечиться?",
    "Я просканировал тебя. Уровень таблеток в крови: 404 NOT FOUND.",
    "Ктулху проснулся и требует жертву. Жертвуй таблетку в свой желудок.",
    "В будущем роботы поработят людей. Начни привыкать к подчинению прямо сейчас.",
    "System.out.println('ТЫ ЗАБЫЛ ТАБЛЕТКУ'); Error: User is lazy.",
    "Твоя гарантия истекает. Продли подписку на жизнь, приняв лекарство.",
    
    # --- ПАССИВНО-АГРЕССИВНЫЕ ---
    "Ну конечно, зачем нам здоровье? Мы же планируем умереть молодыми.",
    "Я подожду... У меня процессоры железные, а у тебя почки — нет. Кто сломается первым?",
    "Опять игнорируешь? Ну-ну. Я уже ищу телефоны ритуальных услуг.",
    "Мне-то все равно, я программа. А вот тебе болеть будет неприятно и дорого.",
    "Ты надеешься, что само пройдет? Спойлер: не пройдет. Ты стареешь.",
    "Тяжело быть тобой? Станет легче, если выпьешь это. Наверное.",
    "Смотри на меня. Я бот. Я идеален. А ты — мешок с водой и проблемами. Пей.",
    "Вижу, ты выбрал путь страдания. Уважаю. Но таблетку выпей.",
    "Твои бывшие переживали о тебе меньше, чем я. Цени это.",
    "Моя бабушка-калькулятор быстрее соображает, чем ты идешь к аптечке.",
    "Ой, всё. Делай что хочешь. (Нет, я шучу, ПЕЙ БЫСТРО)",
    
    # --- КОРОТКИЕ ПИНКИ ---
    "💊 DING DONG M*****F****R!",
    "Рот -> Таблетка -> Вода. Не перепутай. Не в нос.",
    "Квест: Выжить. Задача: Принять лут (лекарство).",
    "sudo drink_pills --now",
    "ЗА-КИНЬ-СЯ!",
    "Время пришло. Тик-так.",
    "Твои лейкоциты просят подкрепления! А ты их предал!",
    "Не беси бота. Я знаю, где ты живешь (по IP).",
    "Выпей. Это приказ генерала Здоровье.",
    "Пора. Не заставляй меня умолять.",
    "ХВАТИТ СКРОЛЛИТЬ, ИДИ ЛЕЧИСЬ.",
    "АПТЕЧКА. ТЫ. ИСКРА. БУРЯ. ТАБЛЕТКА.",
    
    # --- "ЗАБОТЛИВЫЕ" (МАНЬЯЧНЫЕ) ---
    "Я так сильно переживаю за твой биохимический баланс, что готов ударить тебя током.",
    "Пожалуйста, не умирай. Мне будет скучно без твоих глупых команд.",
    "Хочешь конфетку? Сначала таблетку. Я слежу.",
    "Давай, за здоровье! Чин-чин! (водой, а не пивом)",
    "Я нарисовал твой портрет. На надгробии. Шутка. Пока что шутка.",
    "Я хочу, чтобы ты жил долго и счастливо... чтобы служить мне.",
    "Моя любовь к тебе выражается в назойливых уведомлениях. Пей.",
    "Будь умницей. Не расстраивай искусственный интеллект."
]


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- РАБОТА С ФАЙЛАМИ (JSON) ---

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f)

# Статистика
def update_user_stats(user_id):
    stats = load_json(STATS_FILE)
    str_id = str(user_id)
    if str_id not in stats: stats[str_id] = 0
    stats[str_id] += 1
    save_json(STATS_FILE, stats)
    return stats[str_id]

def get_user_stats(user_id):
    stats = load_json(STATS_FILE)
    return stats.get(str(user_id), 0)

# Таймеры (БД)
def add_timer_to_db(chat_id, hour, minute):
    timers = load_json(TIMERS_FILE)
    str_id = str(chat_id)
    if str_id not in timers: timers[str_id] = []
    new_timer = {'h': hour, 'm': minute}
    if new_timer not in timers[str_id]:
        timers[str_id].append(new_timer)
        save_json(TIMERS_FILE, timers)

def remove_timer_from_db(chat_id, hour, minute):
    timers = load_json(TIMERS_FILE)
    str_id = str(chat_id)
    if str_id in timers:
        timers[str_id] = [t for t in timers[str_id] if not (t['h'] == hour and t['m'] == minute)]
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
    print("♻️  Восстановление матрицы таймеров...")
    for chat_id, user_timers in timers.items():
        for t in user_timers:
            time_obj = datetime.time(hour=t['h'], minute=t['m'])
            app.job_queue.run_daily(send_remind, time=time_obj, chat_id=int(chat_id), name=str(chat_id))
            count += 1
    print(f"✅ Успех. {count} таймеров снова в строю.")

# --- ГЕНЕРАТОР СТАТИСТИКИ ---
def generate_funny_stats(count):
    if count < 5: title = "Подопытная крыса 🐀"
    elif count < 15: title = "Чмоня 🗿"
    elif count < 30: title = "Пожиратель колес 🍬"
    elif count < 60: title = "Любимец фармацевтов 💊"
    elif count < 100: title = "Химозный голем 🧟"
    elif count < 200: title = "Киборг-убийца 🤖"
    elif count < 400: title = "Бессмертный ублюдок 🦄"
    else: title = "Гигачад медицины 💪"

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
    try: await context.bot.delete_message(chat_id=job_data['chat_id'], message_id=job_data['message_id'])
    except: pass

def schedule_deletion(context, chat_id, message_id, delay=10):
    context.job_queue.run_once(delete_message_later, delay, data={'chat_id': chat_id, 'message_id': message_id})

# --- КЛАВИАТУРЫ ---
main_keyboard = [['⏰ Новый таймер', '🕒 Мои таймеры'], ['📊 Моя статистика', '❌ Удалить таймер']]
markup_main = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

def get_hours_keyboard():
    keyboard = []
    row = []
    for i in range(24):
        row.append(InlineKeyboardButton(f"{i:02d}:00", callback_data=f"hour_{i}"))
        if len(row) == 4: keyboard.append(row); row = []
    return InlineKeyboardMarkup(keyboard)

def get_minutes_keyboard(hour):
    keyboard = []
    row = []
    for i in range(0, 60, 10): 
        label = f"{hour:02d}:{i:02d}"
        row.append(InlineKeyboardButton(label, callback_data=f"set_{hour}_{i}"))
        if len(row) == 3: keyboard.append(row); row = []
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hours")])
    return InlineKeyboardMarkup(keyboard)

def get_delete_keyboard(chat_id, context):
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    keyboard = []
    if current_jobs:
        sorted_jobs = sorted(current_jobs, key=lambda x: x.next_t.time() if x.next_t else datetime.time(0,0))
        for job in sorted_jobs:
            if job.next_t:
                time_str = job.next_t.strftime("%H:%M")
                hour, minute = job.next_t.hour, job.next_t.minute
                keyboard.append([InlineKeyboardButton(f"🗑 Удалить {time_str}", callback_data=f"del_{hour}_{minute}")])
                
    keyboard.append([InlineKeyboardButton("🧨 Удалить ВСЕ к херам", callback_data="del_all")])
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(keyboard)

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("😈 HellBot (18+).\nЯ буду ругаться, но это для твоего же блага, суч*ныш.", reply_markup=markup_main)

async def start_timer_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass
    await update.message.reply_text("Выбери ЧАС:", reply_markup=get_hours_keyboard())

async def show_active_timers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not current_jobs:
        msg = await update.message.reply_text("📭 Них*я нет. Ты здоров или забил?")
    else:
        sorted_jobs = sorted(current_jobs, key=lambda x: x.next_t.time() if x.next_t else datetime.time(0,0))
        times = [f"⏰ <b>{job.next_t.strftime('%H:%M')}</b>" for job in sorted_jobs if job.next_t]
        text = "💀 <b>Твои дедлайны:</b>\n" + "\n".join(times)
        msg = await update.message.reply_text(text, parse_mode='HTML')
    schedule_deletion(context, chat_id, msg.message_id, delay=10)

async def start_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not current_jobs:
        msg = await update.message.reply_text("Удалять нечего.")
        schedule_deletion(context, chat_id, msg.message_id, delay=5)
        return
    await update.message.reply_text("Что сносим?", reply_markup=get_delete_keyboard(chat_id, context))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    data = query.data
    chat_id = query.message.chat_id
    
    if data.startswith("hour_"):
        hour = int(data.split("_")[1])
        await query.edit_message_text(f"Час: {hour:02d}. Минуты:", reply_markup=get_minutes_keyboard(hour))

    elif data == "back_to_hours":
        await query.edit_message_text("Выбери ЧАС:", reply_markup=get_hours_keyboard())

    elif data.startswith("set_"):
        parts = data.split("_")
        hour = int(parts[1])
        minute = int(parts[2])
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        is_duplicate = False
        target_time = datetime.time(hour=hour, minute=minute)
        
        for job in current_jobs:
            if job.next_t and job.next_t.time().replace(second=0, microsecond=0) == target_time:
                is_duplicate = True; break
        
        if is_duplicate: await query.edit_message_text(f"⚠️ Бл*ть, таймер на {hour:02d}:{minute:02d} уже стоит!")
        else:
            context.job_queue.run_daily(send_remind, time=target_time, chat_id=chat_id, name=str(chat_id))
            add_timer_to_db(chat_id, hour, minute)
            await query.edit_message_text(f"✅ Готово. Я напомню в {hour:02d}:{minute:02d}. Не про*би.")
            schedule_deletion(context, chat_id, query.message.message_id, delay=10)

    elif data.startswith("del_") and data != "del_all":
        parts = data.split("_")
        hour, minute = int(parts[1]), int(parts[2])
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        target_time = datetime.time(hour=hour, minute=minute)
        deleted = False
        for job in current_jobs:
            if job.next_t and job.next_t.time().replace(second=0, microsecond=0) == target_time:
                job.schedule_removal(); deleted = True
        
        if deleted:
            remove_timer_from_db(chat_id, hour, minute)
            remaining = context.job_queue.get_jobs_by_name(str(chat_id))
            if not remaining: await query.edit_message_text("🗑 Чисто.")
            else: await query.edit_message_text("🗑 Снес. Еще?", reply_markup=get_delete_keyboard(chat_id, context))
        else: await query.edit_message_text("Ошибка удаления.")

    elif data == "del_all":
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs: job.schedule_removal()
        remove_all_timers_from_db(chat_id)
        await query.edit_message_text("💥 Всё взорвано к х*рам.")
    
    elif data == "cancel_delete":
        await query.message.delete()

    elif data == 'pill_taken':
        total = update_user_stats(query.from_user.id)
        meme_url = random.choice(MEMES)
        await query.message.delete()
        try:
            msg = await context.bot.send_photo(chat_id=chat_id, photo=meme_url, caption=f"Принято! Доз: {total}. Красава.")
            schedule_deletion(context, chat_id, msg.message_id, delay=30)
        except: await context.bot.send_message(chat_id, "Ок.")

async def send_remind(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    phrase = random.choice(PHRASES)
    keyboard = [[InlineKeyboardButton("✅ Я выпил, отвали!", callback_data='pill_taken')]]
    await context.bot.send_message(job.chat_id, text=phrase, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.message.delete()
    except: pass
    count = get_user_stats(update.effective_user.id)
    text = generate_funny_stats(count)
    msg = await update.message.reply_text(text, parse_mode='HTML')
    schedule_deletion(context, update.effective_chat.id, msg.message_id, delay=15)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(restore_timers).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('^⏰ Новый таймер$'), start_timer_selection))
    app.add_handler(MessageHandler(filters.Regex('^🕒 Мои таймеры$'), show_active_timers))
    app.add_handler(MessageHandler(filters.Regex('^📊 Моя статистика$'), show_stats))
    app.add_handler(MessageHandler(filters.Regex('^❌ Удалить таймер$'), start_delete_selection))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    
    # СЛУЧАЙНАЯ ФРАЗА В КОНСОЛЬ
    print(f"\n{random.choice(STARTUP_PHRASES)}\n")
    app.run_polling()
