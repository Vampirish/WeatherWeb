from flask import Flask, render_template
import requests
from datetime import datetime
from cryptography.fernet import Fernet
import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import WeatherHistory

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# function for read the files
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()


# class where we work with weather
class WeatherService:
    def __init__(self, api_key, city):
        self.api_key = api_key
        self.city = city
        logging.info("WeatherService initialized")

    def get_current_weather(self):
        # shows the current weather
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&units=metric"
            logging.info(f"Fetching current weather from URL: {url}")
            response = requests.get(url)
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching current weather: {e}")
            return None

    def get_noon_forecast(self):
        # get noon forecast
        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={self.city}&appid={self.api_key}&units=metric"
            logging.info(f"Fetching noon forecast from URL: {url}")
            response = requests.get(url)
            forecast_data = response.json()

            noon_forecasts = []
            for item in forecast_data['list']:
                forecast_time = datetime.fromtimestamp(item['dt'])
                if forecast_time.hour == 12:
                    noon_forecasts.append(item)
            return noon_forecasts
        except requests.RequestException as e:
            logging.error(f"Error fetching noon forecast: {e}")
            return []


# class where we work with encryption and decryption
class EncryptionManager:
    @staticmethod
    def generate_key():
        # generate key for next using
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
        logging.info("Encryption key generated")

    @staticmethod
    def load_key():
        # loading the key
        logging.info("Loading encryption key")
        return open("secret.key", "rb").read()

    @staticmethod
    def encrypt_message(message):
        # encrypt messages
        key = EncryptionManager.load_key()
        f = Fernet(key)
        encrypted_message = f.encrypt(message.encode())
        with open("encrypted_api_key.txt", "wb") as file:
            file.write(encrypted_message)
        logging.info("Message encrypted")

    @staticmethod
    def decrypt_message():
        # decrypt messages
        try:
            key = EncryptionManager.load_key()
            f = Fernet(key)
            with open("encrypted_api_key.txt", "rb") as file:
                encrypted_message = file.read()
            decrypted_message = f.decrypt(encrypted_message)
            logging.info("Message decrypted")
            return decrypted_message.decode()
        except Exception as e:
            logging.error(f"Error during decryption: {e}")
            return None


# function what shows us the page in website
@app.route('/')
def weather():
    logging.info("Weather route called")
    api_key = EncryptionManager.decrypt_message()
    city = 'Almaty'

    weather_service = WeatherService(api_key, city)

    current_weather = weather_service.get_current_weather()
    if current_weather is None:
        return "Error: Unable to fetch current weather."

    current_weather_record = WeatherHistory(
        city=city,
        temperature=current_weather['main']['temp'],
        description=current_weather['weather'][0]['description']
    )
    db.session.add(current_weather_record)
    db.session.commit()
    current_weather_display = f"Текущая погода в {city}: {current_weather['main']['temp']}°C, {current_weather['weather'][0]['description']}"

    noon_forecasts = weather_service.get_noon_forecast()
    weather_data = [{
        'day': datetime.fromtimestamp(forecast['dt']).strftime('%A'),
        'temp': forecast['main']['temp'],
        'description': forecast['weather'][0]['description']
    } for forecast in noon_forecasts]

    logging.info("Rendering template with weather data")
    weather_history = WeatherHistory.query.order_by(WeatherHistory.query_time.desc()).all()

    return render_template('index.html', current_weather=current_weather_display, weather_data=weather_data,
                           weather_history=weather_history, image_url=read_file("photoUrl.txt"))


# when we start the program, starts this lines of code
if __name__ == '__main__':
    logging.info(f"App is start")
    app.run(debug=True)
