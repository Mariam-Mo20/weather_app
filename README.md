# Weather App

A simple Flask web application that allows users to search and view real-time weather conditions and 5-day forecasts using the OpenWeatherMap API.

##  Features
- Search by city name, zip code, coordinates, or landmarks
- Use browser location to get current weather
- View current weather and 5-day forecast
- Save weather search records in a database
- Export data to JSON, CSV, or Markdown
- Embedded map and YouTube search for selected city
-  Edit or delete previous records

## Tech Stack
- Python 3
- Flask + Jinja2
- OpenWeatherMap API
- Bootstrap 5

## How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/Mariam-Mo20/weather-app.git
cd weather-app

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
python app.py
