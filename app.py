from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

API_KEY = "e677069c430201033f099e0b7687d7e3"
db = SQLAlchemy(app)

# WeatherRecord model for storing weather data
class WeatherRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    humidity = db.Column(db.Integer, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    temp_max = db.Column(db.Float, nullable=True)
    temp_min = db.Column(db.Float, nullable=True)

# Resolve a location from user input
def resolve_location(query):
    if ',' in query:
        parts = query.split(',')
        try:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return {'lat': lat, 'lon': lon}
        except:
            pass
    if query.isdigit():
        return {'zip': f'{query},us'}
    return {'q': query}

@app.route('/', methods=['GET', 'POST'])
def home():
    weather = None
    forecast_data = []
    city_input = request.form.get('city')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    def fetch_weather_and_forecast(url, forecast_url):
        nonlocal weather, forecast_data
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            city_name = data['name']
            weather = {
                'city': city_name,
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'temp_max': data['main']['temp_max'],
                'temp_min': data['main']['temp_min']
            }
            record = WeatherRecord(**weather)
            db.session.add(record)
            db.session.commit()

            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_json = forecast_response.json()
                for item in forecast_json['list']:
                    if "12:00:00" in item['dt_txt']:
                        forecast_data.append({
                            'date': item['dt_txt'].split()[0],
                            'temp': item['main']['temp'],
                            'description': item['weather'][0]['description'],
                            'icon': item['weather'][0]['icon']
                        })
        else:
            weather = {'error': 'Location not found'}

    if request.method == 'POST' and city_input:
        loc = resolve_location(city_input)
        if 'lat' in loc and 'lon' in loc:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={loc['lat']}&lon={loc['lon']}&appid={API_KEY}&units=metric"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={loc['lat']}&lon={loc['lon']}&appid={API_KEY}&units=metric"
        elif 'zip' in loc:
            url = f"http://api.openweathermap.org/data/2.5/weather?zip={loc['zip']}&appid={API_KEY}&units=metric"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?zip={loc['zip']}&appid={API_KEY}&units=metric"
        else:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={loc['q']}&appid={API_KEY}&units=metric"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={loc['q']}&appid={API_KEY}&units=metric"
        fetch_weather_and_forecast(url, forecast_url)

    elif lat and lon:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        fetch_weather_and_forecast(url, forecast_url)

    return render_template('index.html', weather=weather, forecast=forecast_data)

@app.route('/records')
def records():
    all_records = WeatherRecord.query.all()
    return render_template('records.html', records=all_records)

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    record = WeatherRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('records'))

@app.route('/update/<int:record_id>', methods=['GET', 'POST'])
def update_record(record_id):
    record = WeatherRecord.query.get_or_404(record_id)
    if request.method == 'POST':
        city = request.form.get('city')
        temperature = request.form.get('temperature')
        description = request.form.get('description')
        humidity = request.form.get('humidity')
        wind_speed = request.form.get('wind_speed')
        temp_max = request.form.get('temp_max')
        temp_min = request.form.get('temp_min')

        if not city or not temperature or not description:
            return "Please fill all required fields", 400
        try:
            temperature = float(temperature)
            humidity = int(humidity)
            wind_speed = float(wind_speed)
            temp_max = float(temp_max)
            temp_min = float(temp_min)
        except ValueError:
            return "Invalid number format", 400

        record.city = city
        record.temperature = temperature
        record.description = description
        record.humidity = humidity
        record.wind_speed = wind_speed
        record.temp_max = temp_max
        record.temp_min = temp_min
        db.session.commit()
        return redirect(url_for('records'))

    return render_template('update.html', record=record)

@app.route('/export/<string:format>')
def export_data(format):
    records = WeatherRecord.query.all()

    data = [{
        'id': r.id,
        'city': r.city,
        'temperature': r.temperature,
        'description': r.description,
        'humidity': r.humidity,
        'wind_speed': r.wind_speed,
        'temp_max': r.temp_max,
        'temp_min': r.temp_min
    } for r in records]

    if format == 'json':
        return jsonify(data)

    elif format == 'csv':
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(data[0].keys() if data else [])
        for row in data:
            cw.writerow(row.values())
        output = si.getvalue()
        return Response(output, mimetype='text/csv',
                        headers={"Content-Disposition": "attachment;filename=weather_records.csv"})

    elif format == 'md':
        if not data:
            return "No data to export", 404
        headers = data[0].keys()
        md = '| ' + ' | '.join(headers) + ' |\n'
        md += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
        for row in data:
            md += '| ' + ' | '.join(str(row[h]) for h in headers) + ' |\n'
        return Response(md, mimetype='text/markdown',
                        headers={"Content-Disposition": "attachment;filename=weather_records.md"})

    else:
        return "Unsupported export format", 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
