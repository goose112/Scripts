import telebot
import requests
import datetime

# Замените на ваши токены
TG_BOT_TOKEN = "7970600935:AAEa3EH3MdPfMc3FDEFYcmiCUP8xlXhrUeI" # Ваш токен Telegram бота
OPENWEATHER_TOKEN = "3c40c4a65ae92807fdc86fdceaa3dd07" # Ваш токен OpenWeatherMap

bot = telebot.TeleBot(TG_BOT_TOKEN)

user_data = {}
CODE_TO_SMILE = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "☔️",
    "Drizzle": "☔️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️"
}

def get_weather(city):
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
        )
        response.raise_for_status()
        data = response.json()
        if data["cod"] != 200:
            raise ValueError(f"Ошибка от OpenWeatherMap: {data['message']}")

        city_name = data["name"]
        temperature = data["main"]["temp"]
        weather_description = data["weather"][0]["main"]
        smile = CODE_TO_SMILE.get(weather_description, "❓")
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        day_length = sunset_timestamp - sunrise_timestamp

        return {
            "city": city_name,
            "temperature": temperature,
            "description": smile + " " + weather_description,
            "humidity": humidity,
            "pressure": pressure,
            "wind": wind,
            "sunrise": sunrise_timestamp.strftime("%H:%M"),
            "sunset": sunset_timestamp.strftime("%H:%M"),
            "day_length": day_length,
        }

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Ошибка сети: {e}")
    except KeyError as e:
        raise ValueError(f"Неверный формат данных от OpenWeatherMap: {e}")
    except Exception as e:
        raise ValueError(f"Произошла неизвестная ошибка: {e}")


def create_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Узнать погоду", callback_data="get_weather"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Привет! Как тебя зовут? (Напиши своё имя)")
        bot.register_next_step_handler(message, process_name)
    else:
        bot.send_message(chat_id, f"Привет, {user_data[chat_id]['name']}! Выбери действие:", reply_markup=create_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_weather":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"В каком городе ты хочешь узнать погоду, {user_data[call.message.chat.id]['name']}?",
            reply_markup=create_keyboard()
        )
        bot.register_next_step_handler(call.message, process_city)

def process_name(message):
    chat_id = message.chat.id
    name = message.text
    user_data[chat_id] = {'name': name}
    bot.send_message(chat_id, f"Приятно познакомиться, {name}! Выбери действие:", reply_markup=create_keyboard())


def process_city(message):
    chat_id = message.chat.id
    try:
        weather_info = get_weather(message.text)
        report = (
            f"*{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
            f"Привет, {user_data[chat_id]['name']}!\n"
            f"Погода в городе: {weather_info['city']}\n"
            f"Температура: {weather_info['temperature']}°C {weather_info['description']}\n"
            f"Влажность: {weather_info['humidity']}%\n"
            f"Давление: {weather_info['pressure']} мм.рт.ст\n"
            f"Ветер: {weather_info['wind']} м/с\n"
            f"Восход солнца: {weather_info['sunrise']}\n"
            f"Закат солнца: {weather_info['sunset']}\n"
            f"Продолжительность дня: {weather_info['day_length']}\n"
            f"*Хорошего дня!*"
        )
        bot.send_message(chat_id, report, reply_markup=create_keyboard())
    except ValueError as e:
        bot.send_message(chat_id, f"\U00002620 Ошибка: {e}", reply_markup=create_keyboard())

bot.infinity_polling()