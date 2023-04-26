import telebot
from telebot import types
from data import db_session
from config import TOKEN
from data.users import User

bot = telebot.TeleBot(TOKEN)


def check_user_in_db(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == id).first()
    if user is None:
        return False
    return True


def get_user_city(id):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == id).first()
    city = user.user_city
    if city == "Не указан":
        return None
    return city


def set_user_city(id, city):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == id).first()
    user.user_city = city
    session.commit()


def add_user_in_db(id):
    session = db_session.create_session()
    user = User(
        user_id=id
    )
    session.add(user)
    session.commit()


@bot.message_handler(commands=["start"])
def start_bot(message):
    if check_user_in_db(message.from_user.id):
        bot.send_message(message.chat.id,
                         f"Приветствую, {message.from_user.first_name}! Я - бот-компаньон. Моя цель - сделать вашу"
                         f" жизнь в городе комфортнее и удобнее."
                         f" Ниже вы можете ознакомиться с моим функционалом.",
                         parse_mode="html")
    else:
        bot.send_message(message.chat.id,
                         f"Приветствую, {message.from_user.first_name}! Я - бот-компаньон. Моя цель - сделать вашу"
                         f" жизнь в городе комфортнее и удобнее."
                         f" Ниже вы можете ознакомиться с моим функционалом."
                         f" А сейчас, пожалуйста, введите ваш населенный пункт!",
                         parse_mode="html")
        add_user_in_db(message.from_user.id)


@bot.message_handler(content_types=["text"], func=lambda x: get_user_city(x.from_user.id) is None)
def append_city(message):
    set_user_city(message.from_user.id, message.text)
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    bot.send_message(message.chat.id, f"Ваш населенный пункт: {user.user_city}", parse_mode="html")


def main():
    db_session.global_init("db/users.db")
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
