import discord
import requests
import asyncio
from discord import app_commands
from rapidfuzz import fuzz
from typing import Literal

# -----------------------------------------
# Read in token(s)
# -----------------------------------------
with open('TOKEN.txt', 'r') as token_file:
  TOKEN = token_file.read().strip()

with open('APIKEY.txt', 'r') as apikey_file:
  APIKEY = apikey_file.read().strip()


# -----------------------------------------
# Discord API Handling
# -----------------------------------------

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -----------------------------------------
# Variables
# -----------------------------------------

API_KEY = '499df9d708bdc92628fae50f6b7f3b00'
FORC_LIST = ['Current', 'Hourly', 'Daily', 'Alerts']
UNITS_LIST = ['imperial', 'metric', 'standard']  # Add other units if needed
STATE_LIST = [
  "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
  "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
  "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
  "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
  "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
  "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
  "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
  "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
  "Washington", "West Virginia", "Wisconsin", "Wyoming"
]


# -----------------------------------------
# Custom Functions
# -----------------------------------------
async def get_matching_states(
  interaction: discord.Interaction,
  current: str,
) -> list[app_commands.Choice[str]]:
  matching_states = []
  current_lower = current.lower()
  for state_name in STATE_LIST:
    if fuzz.partial_ratio(current_lower, state_name.lower()) >= 90:
      matching_states.append(
        discord.app_commands.Choice(name=state_name, value=state_name))
  return matching_states


async def fetch_geolocation(city):
  GEO_URL = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={API_KEY}'
  geo_response = requests.get(GEO_URL)
  data = geo_response.json()
  return data


async def fetch_weather_data(lat, lon, units='imperial'):
  API_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={API_KEY}&units={units}'
  forc_response = requests.get(API_URL)
  weather_data = forc_response.json()
  return weather_data


# -----------------------------------------
# Commands
# -----------------------------------------


@tree.command(name="forecast",
              description="gives you da weather",
              guild=discord.Object(id=1121197365496397944))
@app_commands.describe(type='Type of forecast',
                       city='Name of the city',
                       state='Name of the state',
                       units='Units of measurement')
@app_commands.autocomplete(state=get_matching_states)
async def forecast(interaction, type: Literal['Current', 'Hourly', 'Daily',
                                              'Alerts'], city: str, state: str,
                   units: Literal['imperial', 'metric', 'standard']):
  if state.capitalize() not in STATE_LIST:
    await asyncio.sleep(1)
    await interaction.response.send_message(
      f"{state} is invalid, Please provide a valid state", ephemeral=True)
    return

  if type not in FORC_LIST:
    await asyncio.sleep(1)
    await interaction.response.send_message(
      "Invalid forecast. Please provide a valid forecast", ephemeral=True)
    return

  if units not in UNITS_LIST:
    await asyncio.sleep(1)
    await interaction.response.send_message(
      "Invalid units. Please provide valid units", ephemeral=True)
    return

  matching_location = None
  geolocation_data = await fetch_geolocation(city)

  for location in geolocation_data:
    if location.get("state", "") == state:
      matching_location = location
      break

  if matching_location:
    LAT_VAL = matching_location['lat']
    LON_VAL = matching_location['lon']
    weather_data = await fetch_weather_data(LAT_VAL, LON_VAL, units)

    if type == 'Current':
      current_weather = weather_data['current']
      # Extract data from the 'current' section and create the message_content

      unit_label = '°F' if units == 'imperial' else '°C'
      wind_unit_label = 'mph' if units == 'imperial' else 'm/s'

      message_content = f"The {type} weather in {city.capitalize()}, {state} is .... \n" \
                        f"Current Temperature: {current_weather['temp']} {unit_label}\n" \
                        f"Feels Like: {current_weather['feels_like']} {unit_label}\n" \
                        f"Pressure: {current_weather['pressure']} inHg\n" \
                        f"Humidity: {current_weather['humidity']}%\n" \
                        f"Clouds: {current_weather['clouds']}%\n" \
                        f"Wind Speed: {current_weather['wind_speed']} {wind_unit_label}\n" \
                        f"Description: {current_weather['weather'][0]['description']}\n"

      await interaction.response.send_message(message_content, ephemeral=True)
    else:
      # Handle other forecast types (Hourly, Daily, Alerts) similarly
      message_content = f"{type} weather data still in development"
      await interaction.response.send_message(message_content, ephemeral=True)
  else:
    await interaction.response.send_message(f"City not found in {state}",
                                            ephemeral=True)


@client.event
async def on_ready():
  await tree.sync(guild=discord.Object(id=1121197365496397944))
  print('We have logged in as {0.user}'.format(client))


client.run(TOKEN)
