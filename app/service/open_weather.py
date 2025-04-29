import httpx
import os
from dotenv import load_dotenv

load_dotenv()

api_url = f"http://{os.environ['IP_SERVER']}:8000/openweather/create"

async def get_weather(api_key, lat, lon):
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            temperature = data['main']['temp']
            temperature = round((temperature - 273.15), 1)

            feels_like = data['main']['feels_like']
            feels_like = round((feels_like - 273.15), 1)

            humidity = data['main']['humidity']

            weather_data = {
                'temperature': temperature,
                'feels_like': feels_like,
                'humidity': humidity
            }

            await store_data(weather_data)

        except httpx.HTTPStatusError as e:
            print(f"Failed to retrieve data: {e}")

async def store_data(data):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=data)
            response.raise_for_status()
            print("OpenWeather data stored successfully")
        except httpx.HTTPStatusError as e:
            print(f"OpenWeather failed to store data: {e}")