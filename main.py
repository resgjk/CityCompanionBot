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


def send_list_of_fuction(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item_1 = types.InlineKeyboardButton("Прогноз погоды на день", callback_data="weather_day")
    item_2 = types.InlineKeyboardButton("Прогноз погоды на неделю", callback_data="weather_week")
    item_3 = types.InlineKeyboardButton("Информация об организации", callback_data="info_one_place")
    item_4 = types.InlineKeyboardButton("Поиск мест", callback_data="list_of_places")
    item_5 = types.InlineKeyboardButton("Поиск ближайшего места", callback_data="info_nearest_place")
    item_6 = types.InlineKeyboardButton("Отметить точку назначения на карте", callback_data="return_point_on_map")
    markup.add(item_1, item_2, item_3, item_4, item_5, item_6)
    bot.send_message(message.chat.id, "Список функций:", reply_markup=markup)


@bot.message_handler(commands=["start", "help"])
def start_bot(message):
    if check_user_in_db(message.from_user.id):
        bot.send_message(message.chat.id,
                         f"Приветствую, {message.from_user.first_name}! Я - бот-компаньон. Моя цель - сделать вашу"
                         f" жизнь в городе комфортнее и удобнее."
                         f" Ниже вы можете ознакомиться с моим функционалом.",
                         parse_mode="html")
        markup = types.InlineKeyboardMarkup(row_width=1)
        item_1 = types.InlineKeyboardButton("Прогноз погоды на день", callback_data="weather_day")
        item_2 = types.InlineKeyboardButton("Прогноз погоды на неделю", callback_data="weather_week")
        item_3 = types.InlineKeyboardButton("Информация об организации", callback_data="info_one_place")
        item_4 = types.InlineKeyboardButton("Поиск мест", callback_data="list_of_places")
        item_5 = types.InlineKeyboardButton("Поиск ближайшего места", callback_data="info_nearest_place")
        item_6 = types.InlineKeyboardButton("Отметить точку назначения на карте", callback_data="return_point_on_map")
        markup.add(item_1, item_2, item_3, item_4, item_5, item_6)
        bot.send_message(message.chat.id, "Список функций:", reply_markup=markup)
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
    markup = types.InlineKeyboardMarkup(row_width=1)
    item_1 = types.InlineKeyboardButton("Прогноз погоды на день", callback_data="weather_day")
    item_2 = types.InlineKeyboardButton("Прогноз погоды на неделю", callback_data="weather_week")
    item_3 = types.InlineKeyboardButton("Информация об организации", callback_data="info_one_place")
    item_4 = types.InlineKeyboardButton("Поиск мест", callback_data="list_of_places")
    item_5 = types.InlineKeyboardButton("Поиск ближайшего места", callback_data="info_nearest_place")
    item_6 = types.InlineKeyboardButton("Отметить точку назначения на карте", callback_data="return_point_on_map")
    markup.add(item_1, item_2, item_3, item_4, item_5, item_6)
    bot.send_message(message.chat.id, "Список функций:", reply_markup=markup)


def info_nearest_place(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": ORGANIZATION_API_KEY,
        "text": f"{user.user_city} {message.text}",
        "lang": "ru_RU",
        "type": "biz",
        "ll": user.user_address,
        "results": "1"
    }
    work_time = "Не указано"
    phone = "Не указан"
    address = "Не указан"
    name = "Не указано"
    site = "Не указан"

    resp = requests.get(ORGANIZATION_API_SERVER, params=params)
    if not resp.json()["properties"]["ResponseMetaData"]["SearchResponse"]["found"]:
        bot.send_message(message.chat.id, "Увы, но рядом с вами нет подходящего места(")
        return
    res = resp.json()
    try:
        work_time = res["features"][0]["properties"]["CompanyMetaData"]["Hours"]["text"]
    except Exception:
        pass
    try:
        phone = res["features"][0]["properties"]["CompanyMetaData"]["Phones"][0]["formatted"]
    except Exception:
        pass
    try:
        address = res["features"][0]["properties"]["CompanyMetaData"]["address"]
    except Exception:
        pass
    try:
        name = res["features"][0]["properties"]["CompanyMetaData"]["name"]
    except Exception:
        pass
    try:
        site = res["features"][0]["properties"]["CompanyMetaData"]["url"]
    except Exception:
        pass
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add("Список функций")
    sent = bot.send_message(message.chat.id, f"Название: {name}\nАдрес: {address}\nВремя работы: {work_time}\n"
                                             f"Номер телефона: {phone}\nСайт: {site}", reply_markup=keyboard)
    bot.register_next_step_handler(sent, send_list_of_fuction)


def set_user_address_for_nearest(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": f"{user.user_city} {message.text}",
        "format": "json"
    }
    res = requests.get(GEOCODER_API_SERVER, params=params).json()
    res_pos = ",".join(res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split())
    user.user_address = res_pos
    session.commit()
    sent = bot.send_message(message.chat.id, "Какое место вы хотите найти?")
    bot.register_next_step_handler(sent, info_nearest_place)


def return_list_of_places(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": ORGANIZATION_API_KEY,
        "text": f"{user.user_city} {message.text}",
        "lang": "ru_RU",
        "type": "biz"
    }
    resp = requests.get(ORGANIZATION_API_SERVER, params=params)
    if not resp.json()["properties"]["ResponseMetaData"]["SearchResponse"]["found"]:
        bot.send_message(message.chat.id, "Увы, но я не смог найти подходящих вам мест(")
        return
    res = resp.json()["features"]
    bot.send_message(message.chat.id, f"Вот список мест по запросу: {message.text}")
    for i in res:
        work_time = "Не указано"
        phone = "Не указан"
        address = "Не указан"
        name = "Не указано"
        site = "Не указан"
        try:
            work_time = i["properties"]["CompanyMetaData"]["Hours"]["text"]
        except Exception:
            pass
        try:
            phone = i["properties"]["CompanyMetaData"]["Phones"][0]["formatted"]
        except Exception:
            pass
        try:
            address = i["properties"]["CompanyMetaData"]["address"]
        except Exception:
            pass
        try:
            name = i["properties"]["CompanyMetaData"]["name"]
        except Exception:
            pass
        try:
            site = i["properties"]["CompanyMetaData"]["url"]
        except Exception:
            pass
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        keyboard.add("Список функций")
        sent = bot.send_message(message.chat.id, f"Название: {name}\nАдрес: {address}\nВремя работы: {work_time}\n"
                                                 f"Номер телефона: {phone}\nСайт: {site}", reply_markup=keyboard)
        bot.register_next_step_handler(sent, send_list_of_fuction)


def return_info_one_place(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": ORGANIZATION_API_KEY,
        "text": f"{user.user_city} {message.text}",
        "lang": "ru_RU",
        "type": "biz",
        "results": "1"
    }
    work_time = "Не указано"
    phone = "Не указан"
    address = "Не указан"
    name = "Не указано"
    site = "Не указан"

    resp = requests.get(ORGANIZATION_API_SERVER, params=params)
    if not resp.json()["properties"]["ResponseMetaData"]["SearchResponse"]["found"]:
        bot.send_message(message.chat.id, "Увы, но я не смог найти информацию о данном месте(")
        return
    res = resp.json()
    try:
        work_time = res["features"][0]["properties"]["CompanyMetaData"]["Hours"]["text"]
    except Exception:
        pass
    try:
        phone = res["features"][0]["properties"]["CompanyMetaData"]["Phones"][0]["formatted"]
    except Exception:
        pass
    try:
        address = res["features"][0]["properties"]["CompanyMetaData"]["address"]
    except Exception:
        pass
    try:
        name = res["features"][0]["properties"]["CompanyMetaData"]["name"]
    except Exception:
        pass
    try:
        site = res["features"][0]["properties"]["CompanyMetaData"]["url"]
    except Exception:
        pass
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add("Список функций")
    sent = bot.send_message(message.chat.id, f"Название: {name}\nАдрес: {address}\nВремя работы: {work_time}\n"
                                             f"Номер телефона: {phone}\nСайт: {site}", reply_markup=keyboard)
    bot.register_next_step_handler(sent, send_list_of_fuction)


def point_on_map(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": f"{user.user_city} {message.text}",
        "format": "json"
    }
    res = requests.get(GEOCODER_API_SERVER, params=params).json()
    res_pos = ",".join(res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split())
    print(res_pos)
    map_params = {
        "l": "map",
        "ll": user.user_address,
        "pt": f"{user.user_address},pma~{res_pos},pmb"
    }
    resp = requests.get(STATIC_MAPS_API_SERVER, params=map_params)
    print(resp)
    if not resp:
        bot.send_message(message.chat.id, "Увы, но я не смог отметить нужные вам места(")
        return
    map_pic = resp.content
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add("Список функций")
    sent = bot.send_photo(message.chat.id, map_pic, reply_markup=keyboard)
    bot.register_next_step_handler(sent, send_list_of_fuction)


def set_user_address_for_point_on_map(message):
    session = db_session.create_session()
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": f"{user.user_city} {message.text}",
        "format": "json"
    }
    res = requests.get(GEOCODER_API_SERVER, params=params).json()
    res_pos = ",".join(res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split())
    user.user_address = res_pos
    session.commit()
    sent = bot.send_message(message.chat.id, "Введите адрес места назначения")
    bot.register_next_step_handler(sent, point_on_map)


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
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            keyboard.add("Список функций")
            sent = bot.send_message(call.message.chat.id,
                                    f"Температура: {temp}\nОщущается как: {feels_like}\nОписание погоды: {discription}\n"
                                    f"Влажность воздуха: {wet}\nСкорость ветра: {speed}\nНаправление ветра: {napr}",
                                    reply_markup=keyboard)
            bot.register_next_step_handler(sent, send_list_of_fuction)
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
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            keyboard.add("Список функций")

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
                sent = bot.send_message(call.message.chat.id,
                                        f"Дата: {i[0]}\nТемпература: {i[1]}\nОщущается как: {i[2]}\nОписание погоды: {i[3]}\n"
                                        f"Влажность воздуха: {i[4]}\nСкорость ветра: {i[5]}\nНаправление ветра: {i[6]}",
                                        reply_markup=keyboard)
                bot.register_next_step_handler(sent, send_list_of_fuction)
        elif call.data == "info_one_place":
            sent = bot.send_message(call.message.chat.id, "Введите адрес или название организации")
            bot.register_next_step_handler(sent, return_info_one_place)
        elif call.data == "list_of_places":
            sent = bot.send_message(call.message.chat.id, "Какое место вы хотите найти?")
            bot.register_next_step_handler(sent, return_list_of_places)
        elif call.data == "info_nearest_place":
            sent = bot.send_message(call.message.chat.id, "Введите адрес, на котором вы находитесь")
            bot.register_next_step_handler(sent, set_user_address_for_nearest)
        elif call.data == "return_point_on_map":
            sent = bot.send_message(call.message.chat.id, "Введите адрес, на котором вы находитесь")
            bot.register_next_step_handler(sent, set_user_address_for_point_on_map)


def main():
    db_session.global_init("db/users.db")
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
