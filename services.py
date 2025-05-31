import logging
import requests
import json
from datetime import datetime
import pytz
from config import (
    WEATHER_API_KEY, 
    DEFAULT_CITY, 
    WEATHER_API_URL, 
    QUOTES_API_URL, 
    FACTS_API_URL,
    ENABLE_WEATHER
)

logger = logging.getLogger(__name__)

class ExternalServices:
    """Handles external API calls for weather, quotes, facts, etc."""
    
    def __init__(self):
        """Initialize the services handler."""
        self.session = requests.Session()
        self.session.timeout = 10
    
    async def get_weather(self, city: str = None) -> dict:
        """
        Get current weather information using WeatherStack API.
        
        Args:
            city (str): City name (defaults to DEFAULT_CITY)
            
        Returns:
            dict: Weather information or error message
        """
        if not ENABLE_WEATHER:
            return {
                "success": False,
                "message": "Weather service not configured"
            }
        
        city = city or DEFAULT_CITY
        
        try:
            params = {
                'access_key': WEATHER_API_KEY,
                'query': city,
                'units': 'm'  # metric units
            }
            
            response = self.session.get(WEATHER_API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for WeatherStack API errors
            if 'error' in data:
                return {
                    "success": False,
                    "message": f"Weather error: {data['error'].get('info', 'Unknown error')}"
                }
            
            current = data['current']
            location = data['location']
            
            weather_info = {
                "success": True,
                "city": location['name'],
                "country": location['country'],
                "temperature": round(current['temperature']),
                "feels_like": round(current['feelslike']),
                "humidity": current['humidity'],
                "description": current['weather_descriptions'][0],
                "icon": current.get('weather_icons', [''])[0],
                "wind_speed": current['wind_speed']
            }
            
            logger.info(f"Weather data retrieved for {city}")
            return weather_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather: {e}")
            return {
                "success": False,
                "message": f"Could not fetch weather for {city}"
            }
        except KeyError as e:
            logger.error(f"Unexpected weather API response format: {e}")
            return {
                "success": False,
                "message": "Weather service temporarily unavailable"
            }
    
    async def get_inspirational_quote(self) -> dict:
        """
        Get a random inspirational quote.
        
        Returns:
            dict: Quote information or error message
        """
        try:
            response = self.session.get(QUOTES_API_URL)
            response.raise_for_status()
            
            data = response.json()
            
            quote_info = {
                "success": True,
                "text": data['content'],
                "author": data['author'],
                "tags": data.get('tags', [])
            }
            
            logger.info("Inspirational quote retrieved")
            return quote_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quote: {e}")
            return {
                "success": False,
                "message": "Could not fetch inspirational quote"
            }
        except KeyError as e:
            logger.error(f"Unexpected quote API response format: {e}")
            return {
                "success": False,
                "message": "Quote service temporarily unavailable"
            }
    
    async def get_random_fact(self) -> dict:
        """
        Get a random interesting fact.
        
        Returns:
            dict: Fact information or error message
        """
        try:
            response = self.session.get(FACTS_API_URL)
            response.raise_for_status()
            
            data = response.json()
            
            fact_info = {
                "success": True,
                "text": data['text'],
                "source": data.get('source', 'Unknown')
            }
            
            logger.info("Random fact retrieved")
            return fact_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching fact: {e}")
            return {
                "success": False,
                "message": "Could not fetch random fact"
            }
        except KeyError as e:
            logger.error(f"Unexpected fact API response format: {e}")
            return {
                "success": False,
                "message": "Fact service temporarily unavailable"
            }
    
    def get_greeting_based_on_time(self) -> str:
        """
        Get an appropriate greeting based on current time.
        
        Returns:
            str: Time-based greeting
        """
        try:
            # You can adjust timezone as needed
            tz = pytz.timezone('UTC')
            current_time = datetime.now(tz)
            hour = current_time.hour
            
            if 5 <= hour < 12:
                return "🌅 Good morning"
            elif 12 <= hour < 17:
                return "☀️ Good afternoon"
            elif 17 <= hour < 21:
                return "🌆 Good evening"
            else:
                return "🌙 Good night"
                
        except Exception as e:
            logger.error(f"Error getting time-based greeting: {e}")
            return "👋 Hello"
    
    def format_weather_message(self, weather_data: dict) -> str:
        """
        Format weather data into a nice message.
        
        Args:
            weather_data (dict): Weather information
            
        Returns:
            str: Formatted weather message
        """
        if not weather_data["success"]:
            return f"❌ {weather_data['message']}"
        
        # Simple weather emoji mapping based on description
        description_lower = weather_data["description"].lower()
        if "sunny" in description_lower or "clear" in description_lower:
            weather_emoji = "☀️"
        elif "cloudy" in description_lower or "overcast" in description_lower:
            weather_emoji = "☁️"
        elif "partly cloudy" in description_lower:
            weather_emoji = "⛅"
        elif "rain" in description_lower or "drizzle" in description_lower:
            weather_emoji = "🌧️"
        elif "snow" in description_lower:
            weather_emoji = "🌨️"
        elif "thunderstorm" in description_lower or "storm" in description_lower:
            weather_emoji = "⛈️"
        elif "fog" in description_lower or "mist" in description_lower:
            weather_emoji = "🌫️"
        else:
            weather_emoji = "🌤️"
        
        message = (
            f"{weather_emoji} **Weather in {weather_data['city']}, {weather_data['country']}**\n\n"
            f"🌡️ **Temperature:** {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)\n"
            f"💧 **Humidity:** {weather_data['humidity']}%\n"
            f"🍃 **Wind:** {weather_data['wind_speed']} km/h\n"
            f"📝 **Description:** {weather_data['description']}"
        )
        
        return message 