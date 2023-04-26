from pprint import pprint

import telebot
from telebot import types
from data import db_session
from config import TOKEN
from data.users import User
import requests
from constants import ORGANIZATION_API_KEY, ORGANIZATION_API_SERVER, GEOCODER_API_KEY, GEOCODER_API_SERVER, \
    WEATHER_API_SERVER, WEATHER_API_KEY, STATIC_MAPS_API_SERVER, WEATHER_KEYS, WIND_KEYS

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

    markup = types.InlineKeyboardMarkup(row_width=1)
    item_1 = types.InlineKeyboardButton("Прогноз погоды на день", callback_data="weather_day")
    item_2 = types.InlineKeyboardButton("Прогноз погоды на неделю", callback_data="weather_week")
    markup.add(item_1, item_2)
    bot.send_message(message.chat.id, "Список функций:", reply_markup=markup)


@bot.message_handler(content_types=["text"], func=lambda x: get_user_city(x.from_user.id) is None)
def append_city(message):
    set_user_city(message.from_user.id, message.text)
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    bot.send_message(message.chat.id, f"Ваш населенный пункт: {user.user_city}", parse_mode="html")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        session = db_session.create_session()
        user = session.query(User).filter(User.user_id == call.from_user.id).first()
        if call.data == "weather_day":
            params = {
                "apikey": GEOCODER_API_KEY,
                "geocode": user.user_city,
                "format": "json"
            }
            res = requests.get(GEOCODER_API_SERVER, params=params).json()
            res_pos = res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split()

            weather_params = {
                "lat": res_pos[0],
                "lon": res_pos[-1],
                "limit": "1"
            }
            headers = {
                "X-Yandex-API-Key": WEATHER_API_KEY
            }
            res = requests.get(WEATHER_API_SERVER, params=weather_params, headers=headers).json()
            temp = res["fact"]["temp"]
            feels_like = res["fact"]["feels_like"]
            discription = WEATHER_KEYS[res["fact"]["condition"]]
            wet = f'{res["fact"]["humidity"]}%'
            speed = f'{res["fact"]["wind_speed"]} м/c'
            napr = WIND_KEYS[res["fact"]["wind_dir"]]
            bot.send_message(call.message.chat.id,
                             f"Температура: {temp}\nОщущается как: {feels_like}\nОписание погоды: {discription}\n"
                             f"Влажность воздуха: {wet}\nСкорость ветра: {speed}\nНаправление ветра: {napr}")
        elif call.data == "weather_week":
            params = {
                "apikey": GEOCODER_API_KEY,
                "geocode": user.user_city,
                "format": "json"
            }
            res = requests.get(GEOCODER_API_SERVER, params=params).json()
            res_pos = res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split()

            weather_params = {
                "lat": res_pos[0],
                "lon": res_pos[-1],
                "limit": "7",
                "hours": "false"
            }
            headers = {
                "X-Yandex-API-Key": WEATHER_API_KEY
            }
            res = requests.get(WEATHER_API_SERVER, params=weather_params, headers=headers).json()
            days_weather = []
            for day in res["forecasts"]:
                d = day["date"].split("-")
                date = f"{d[-1]}.{d[-2]}"
                temp = day["parts"]["day"]["temp_avg"]
                feels_like = day["parts"]["day"]["feels_like"]
                discription = WEATHER_KEYS[day["parts"]["day"]["condition"]]
                wet = f'{day["parts"]["day"]["humidity"]}%'
                speed = f'{day["parts"]["day"]["wind_speed"]} м/c'
                napr = WIND_KEYS[day["parts"]["day"]["wind_dir"]]
                days_weather.append([date, temp, feels_like, discription, wet, speed, napr])
            for i in days_weather:
                bot.send_message(call.message.chat.id,
                                 f"Дата: {i[0]}\nТемпература: {i[1]}\nОщущается как: {i[2]}\nОписание погоды: {i[3]}\n"
                                 f"Влажность воздуха: {i[4]}\nСкорость ветра: {i[5]}\nНаправление ветра: {i[6]}")


def main():
    db_session.global_init("db/users.db")
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
