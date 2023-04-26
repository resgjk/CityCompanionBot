import telebot
from telebot import types
from config import TOKEN
from constants import CITY

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start_bot(message):
    bot.send_message(message.chat.id,
                     f"Приветствую, {message.from_user.first_name}! Я - бот-компаньон. Моя цель - сделать вашу"
                     f" жизнь в городе комфортнее и удобнее."
                     f" Ниже вы можете ознакомиться с моим функционалом."
                     f" А сейчас, пожалуйста, введите ваш населенный пункт!",
                     parse_mode="html")


@bot.message_handler(content_types=["text"], func=lambda x: CITY is None)
def append_city(message):
    global CITY
    CITY = message.text
    bot.send_message(message.chat.id, f"Ваш населенный пункт: {CITY}", parse_mode="html")


bot.polling(none_stop=True)
