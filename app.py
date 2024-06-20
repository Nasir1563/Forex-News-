from flask import Flask, render_template, request, redirect, url_for, session
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def today():
    settings = get_settings()
    news_events = get_news_events(filter_past_events=True, settings=settings)
    currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
    return render_template('today.html', news_events=news_events, currencies=currencies, settings=settings)

@app.route('/week')
def week():
    settings = get_settings()
    news_events = get_news_events(filter_past_events=False, settings=settings)
    currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
    return render_template('week.html', news_events=news_events, currencies=currencies, settings=settings)

@app.route('/month')
def month():
    settings = get_settings()
    news_events = get_news_events(filter_past_events=False, settings=settings)
    currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
    return render_template('month.html', news_events=news_events, currencies=currencies, settings=settings)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session['timezone'] = request.form.get('timezone')
        session['preferred_currencies'] = request.form.getlist('preferred_currencies')
        session['impact_filter'] = request.form.get('impact_filter')
        return redirect(url_for('settings'))

    timezones = pytz.all_timezones
    currencies = ['AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
    impacts = ['all', 'low', 'medium', 'high', 'holiday']
    settings = get_settings()
    return render_template('settings.html', timezones=timezones, currencies=currencies, impacts=impacts, settings=settings)

def get_settings():
    return {
        'timezone': session.get('timezone', 'Asia/Dhaka'),
        'preferred_currencies': session.get('preferred_currencies', ['USD']),
        'impact_filter': session.get('impact_filter', 'all')
    }

def get_news_events(filter_past_events, settings):
    url = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json'
    response = requests.get(url)
    if response.status_code == 200:
        events = response.json()
        formatted_events = []
        now = datetime.now(pytz.utc)
        for event in events:
            event_time = datetime.strptime(event.get('date'), '%Y-%m-%dT%H:%M:%S%z')
            if not filter_past_events or event_time > now:
                currency = event.get('country', 'USD')  # Use 'country' field for currency
                formatted_event = {
                    'title': event.get('title'),
                    'time': convert_to_timezone(event.get('date'), settings['timezone']),
                    'actual': event.get('actual', 'N/A'),
                    'forecast': event.get('forecast', 'N/A'),
                    'previous': event.get('previous', 'N/A'),
                    'impact': event.get('impact', 'low').lower(),
                    'currency': currency,
                    'remaining_time': calculate_remaining_time(event.get('date')),
                    'graph_url': event.get('url', '#'),  # Use 'url' field for graph URL
                    'event_time': event_time
                }
                if currency in settings['preferred_currencies'] and (settings['impact_filter'] == 'all' or formatted_event['impact'] == settings['impact_filter']):
                    formatted_events.append(formatted_event)
        # Sort events by time and add a class to the next upcoming event
        formatted_events.sort(key=lambda x: x['event_time'])
        if filter_past_events and formatted_events:
            formatted_events[0]['next_upcoming'] = True
        return formatted_events
    else:
        return []

def convert_to_timezone(event_time, timezone):
    event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S%z')
    local_time = event_time.astimezone(pytz.timezone(timezone))
    return local_time.strftime('%Y-%m-%d %I:%M %p')

def calculate_remaining_time(event_time):
    event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S%z')
    now = datetime.now(pytz.utc)
    remaining_time = event_time - now
    days = remaining_time.days
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{days}d {hours}h {minutes}m {seconds}s'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

