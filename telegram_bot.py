import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext,
)

from models import User, Task, Event, File
from database import SessionLocal, engine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


TOKEN = os.environ.get("5884394290:AAG5KRca93pUSO6A81wqbi9_dEpkB1iF0VA")


def create_tables():
    Base.metadata.create_all(engine)
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        task TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        description TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY,
                        file TEXT NOT NULL)''')

    connection.commit()
    connection.close()


def connect_to_db():
    connection = sqlite3.connect('my_database.db')
    return connection


def get_or_create_user(db_session, tg_user: User):
    user = db_session.query(User).filter_by(user_id=tg_user.id).first()
    if not user:
        user = User(user_id=tg_user.id, username=tg_user.username)
        db_session.add(user)
        db_session.commit()
    return user


def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    button_data = query.data

    if button_data == "list_tasks":
        list_tasks(update, context)
    elif button_data == "add_task":
        add_task_prompt(update, context)
    elif button_data == "list_events":
        list_events(update, context)
    elif button_data == "add_event":
        add_event_prompt(update, context)
    elif button_data == "list_files":
        list_files(update, context)
    elif button_data == "upload_file":
        upload_file_prompt(update, context)
    elif button_data == "send_message_to_all_prompt":
        send_message_to_all_prompt(update, context)

    query.answer()


def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user = User.query.filter_by(telegram_id=user_id).first()

    if user:
        update.message.reply_text(f"Добро пожаловать, {user.name}! Ваш аккаунт был зарегистрирован.")
    else:
        new_user = get_or_create_user(update.message.from_user)
        update.message.reply_text(f"Добро пожаловать, {new_user.name}! Ваш аккаунт был зарегистрирован.")
    show_buttons(update, context)


def message_needs_modification(new_text, reply_markup, message):
    return new_text != message.text or reply_markup != message.reply_markup


def show_buttons(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Список задач", callback_data="list_tasks"),
            InlineKeyboardButton("Добавить задачу", callback_data="add_task")
        ],
        [
            InlineKeyboardButton("Список мероприятий", callback_data="list_events"),
            InlineKeyboardButton("Добавить мероприятие", callback_data="add_event")
        ],
        [
            InlineKeyboardButton("Список файлов", callback_data="list_files"),
            InlineKeyboardButton("Загрузить файл", callback_data="upload_file")
        ],
        [
            InlineKeyboardButton("Отправить сообщение всем", callback_data="send_message_to_all_prompt")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    new_text = "Выберите действие:"

    if update.callback_query:
        query = update.callback_query
        message = query.message

        if message_needs_modification(new_text, reply_markup, message):
            query.edit_message_text(new_text, reply_markup=reply_markup)
        else:
            query.answer()
    else:
        update.message.reply_text(new_text, reply_markup=reply_markup)


def handle_callback(update, context, state, bot_functions=None, SENDING_MESSAGE=None):
    query = update.callback_query
    query.answer()

    if state == SENDING_MESSAGE:
        if query.data == "list_tasks":
            list_tasks(update, context)

    if query.data == "list_tasks":
        bot_functions.list_tasks(update, context)
    elif query.data == "add_task":
        bot_functions.add_task(update, context)
    elif query.data == "list_events":
        bot_functions.list_events(update, context)
    elif query.data == "add_event":
        bot_functions.add_event(update, context)
    elif query.data == "delete_event":
        bot_functions.delete_event(update, context)
    elif query.data == "list_files":
        bot_functions.list_files(update, context)
    elif query.data == "upload_file":
        bot_functions.upload_file(update, context)
    elif query.data == "delete_file":
        bot_functions.delete_file(update, context)
    elif query.data == "send_message_to_all_prompt":
        query.message.reply_text("Введите сообщение, которое вы хотите отправить всем пользователям:")
        return 1
    else:
        query.message.reply_text("Неизвестный запрос.")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Список доступных команд:\n"
        "/start - начать работу с ботом\n"
        "/help - список доступных команд\n"
        "/send_message_to_all - отправить сообщение всем пользователям\n"
        "/list_tasks - показать список задач\n"
        "/add_task - добавить задачу\n"
        "/delete_task - удалить задачу\n"
        "/list_events - показать список событий\n"
        "/add_event - добавить событие\n"
        "/delete_event - удалить событие\n"
        "/list_files - показать список файлов\n"
        "/upload_file - загрузить файл\n"
        "/delete_file - удалить файл\n"
    )


def get_all_tasks():
    cursor = connection.cursor()
    cursor.execute("SELECT task FROM tasks")
    connection.close()
    tasks = db_session.query(Task).all()
    return sorted(tasks, key=lambda x: x.due_date)


def list_tasks(update: Update, context: CallbackContext):
    tasks = get_all_tasks()
    if tasks:
        tasks_text = "\n".join([f"{task.title} - {task.due_date.strftime('%Y-%m-%d')} - {task.description}" for task in tasks])
        update.callback_query.message.reply_text(f"Список задач:\n{tasks_text}")
    else:
        update.callback_query.message.reply_text("Список задач пуст.")


def add_task(update: Update, context: CallbackContext):
    try:
        user_id = update.message.chat_id
        user = User.query.filter_by(telegram_id=user_id).first()
        title, description, due_date = context.args
        due_date = datetime.strptime(due_date, "%Y-%m-%d")
        task = Task(user_id=user.id, title=title, description=description, due_date=due_date)
        db_session.add(task)
        db_session.commit()
        update.message.reply_text(f"Задача '{title}' добавлена.")
    except Exception as e:
        update.message.reply_text("Ошибка при добавлении задачи. Пожалуйста, проверьте формат команды.")


def add_task_prompt(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, введите информацию о задаче в формате:\n\nНазвание задачи; Описание задачи; Дата выполнения задачи (ГГГГ-ММ-ДД)")


def delete_task(update: Update, context: CallbackContext):
    try:
        task_id = int(context.args[0])
        task = Task.query.get(task_id)
        if task:
            db_session.delete(task)
            db_session.commit()
            update.message.reply_text(f"Задача '{task.title}' удалена.")
        else:
            update.message.reply_text("Задача не найдена.")
    except Exception as e:
        update.message.reply_text("Ошибка при удалении задачи. Пожалуйста, проверьте формат команды.")


def get_all_events():
    cursor = connection.cursor()
    cursor.execute("SELECT title, date, time, description FROM events")
    connection.close()
    events = db_session.query(Event).all()
    return sorted(events, key=lambda x: (x.date, x.time))


def list_events(update: Update, context: CallbackContext):
    events = get_all_events()
    if events:
        events_text = "\n".join([f"{event.title} - {event.date} - {event.time} - {event.description}" for event in events])
        update.callback_query.message.reply_text(f"Список мероприятий:\n{events_text}")
    else:
        update.callback_query.message.reply_text("Список мероприятий пуст.")


def add_event(update: Update, context: CallbackContext):
    try:
        title, date, time, description = context.args
        date = datetime.strptime(date, "%Y-%m-%d")
        time = datetime.strptime(time, "%H:%M").time()
        event = Event(title=title, date=date, time=time, description=description)
        db_session.add(event)
        db_session.commit()
        update.message.reply_text(f"Мероприятие '{title}' добавлено.")
    except Exception as e:
        update.message.reply_text("Ошибка при добавлении мероприятия. Пожалуйста, проверьте формат команды.")


def add_event_prompt(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, введите информацию о мероприятии в/"
                                                                    "формате:\n\nНазвание мероприятия;/"
                                                                    " Дата мероприятия (ГГГГ-ММ-ДД);/"
                                                                    " Время мероприятия (ЧЧ:ММ); Описание мероприятия")


def delete_event(update: Update, context: CallbackContext):
    try:
        event_id = int(context.args[0])
        event = Event.query.get(event_id)
        if event:
            db_session.delete(event)
            db_session.commit()
            update.message.reply_text(f"Мероприятие '{event.title}' удалено.")
        else:
            update.message.reply_text("Мероприятие не найдено.")
    except Exception as e:
        update.message.reply_text("Ошибка при удалении мероприятия. Пожалуйста, проверьте формат команды.")


def handle_message(update: Update, context: CallbackContext):
    update.message.reply_text("Неизвестная команда. Введите /help для получения списка команд.")


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


def send_message_to_all(update: Update, context: CallbackContext):
    message = update.message.text
    if not message:
        update.message.reply_text("Пожалуйста, предоставьте сообщение для отправки.")
        return

    all_users = User.query.all()
    for user in all_users:
        try:
            context.bot.send_message(chat_id=user.telegram_id, text=message)
        except Exception as e:
            print(f"Error sending message to {user.telegram_id}: {e}")

    update.message.reply_text("Сообщение отправлено всем пользователям.")
    return ConversationHandler.END


def send_message_to_all_prompt(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите сообщение, которое вы хотите отправить всем пользователям.")


def get_all_files():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT file FROM files")
    connection.close()
    files = db_session.query(File).all()
    return files


def list_files(update: Update, context: CallbackContext):
    user = get_or_create_user(db_session, update.effective_user)
    files = db_session.query(File).filter(File.user_id == user.id).all()
    if not files:  # Check if there are no files
        update.message.reply_text("У вас нет сохраненных файлов.")
        return
    files_list = '\n'.join([f"{file.id}. {file.file_name}" for file in files])
    update.message.reply_text(f"Ваши файлы:\n{files_list}")


def upload_file(update: Update, context: CallbackContext):
    file_id = update.message.document.file_id
    file = context.bot.get_file(file_id)
    file.download(update.message.document.file_name)

    new_file = File(filename=update.message.document.file_name, file_id=file_id)
    db_session.add(new_file)
    db_session.commit()

    update.message.reply_text(f"Файл '{update.message.document.file_name}' загружен.")


def upload_file_prompt(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, отправьте файл для загрузки.")


def handle_uploaded_file(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file.download(f"downloads/{file.file_path.split('/')[-1]}")
    context.user_data['files'].append(file.file_id)
    update.message.reply_text(f"Файл {file.file_name} успешно загружен.")


def handle_file(update: Update, context: CallbackContext):
    file = update.message.document or update.message.photo[-1] if update.message.photo else None
    if file:
        file_id = file.file_id
        file_name = file.file_name or f"{file_id}.jpg"

        user = get_or_create_user(db_session, update.effective_user)
        new_file = File(file_id=file_id, file_name=file_name, user_id=user.id)
        db_session.add(new_file)
        db_session.commit()

        update.message.reply_text(f"Файл {file_name} был успешно сохранен.")
        return new_file.id  # return the file ID
    else:
        update.message.reply_text("Не удалось сохранить файл. Пожалуйста, попробуйте еще раз.")
        return None


def delete_file(update: Update, context: CallbackContext):
    try:
        file_id = int(context.args[0])
        file = File.query.get(file_id)
        if file:
            db_session.delete(file)
            db_session.commit()
            update.message.reply_text(f"Файл '{file.filename}' удален.")
        else:
            update.message.reply_text("Файл не найден.")
    except Exception as e:
        update.message.reply_text("Ошибка при удалении файла. Пожалуйста, проверьте формат команды.")


# MAIN
SEND_MESSAGE = 0

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("send_message_to_all", send_message_to_all_prompt)],
    states={
        SEND_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, send_message_to_all)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


def menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Список задач", callback_data='list_tasks'),
            InlineKeyboardButton("Добавить задачу", callback_data='add_task')
        ],
        [
            InlineKeyboardButton("Список событий", callback_data='list_events'),
            InlineKeyboardButton("Добавить событие", callback_data='add_event')
        ],
        [
            InlineKeyboardButton("Список файлов", callback_data='list_files'),
            InlineKeyboardButton("Загрузить файл", callback_data='upload_file_prompt')
        ],
        [
            InlineKeyboardButton("Отправить сообщение всем", callback_data="send_message_to_all_prompt")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


def main() -> None:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list_tasks", list_tasks))
    dp.add_handler(CommandHandler("add_task", add_task))
    dp.add_handler(CommandHandler("delete_task", delete_task))
    dp.add_handler(CommandHandler("list_events", list_events))
    dp.add_handler(CommandHandler("add_event", add_event))
    dp.add_handler(CommandHandler("delete_event", delete_event))
    dp.add_handler(CommandHandler("list_files", list_files))
    dp.add_handler(CommandHandler("upload_file", upload_file))
    dp.add_handler(CallbackQueryHandler(upload_file_prompt, pattern='^upload_file_prompt$'))
    dp.add_handler(CommandHandler("delete_file", delete_file))
    dp.add_handler(CallbackQueryHandler(handle_button_click))
    dp.add_handler(conversation_handler)

    send_message_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(lambda update, context: handle_callback(update, context, SENDING_MESSAGE),
                                           pattern='^send_message_to_all_prompt$')],
        states={
            SENDING_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, send_message_to_all)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(send_message_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()