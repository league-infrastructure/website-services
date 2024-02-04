import pandas as pd
from flask import Flask
from flask import current_app, g
import os
import re
from flask.cli import with_appcontext
from leaguesync import *

def get_p13():
    if 'p13' not in g:
        g.p13 = Pike13(current_app.config)

    return g.p13

def strip_html(text):
    return re.sub('<.*?>', '', text) if text else ''

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    config = get_config(os.getenv('LEAGUESYNC_CONFIG'))

    app.config.from_mapping(
        SECRET_KEY='dev',
        DEBUG=True,
        **config
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register the custom filter
    app.jinja_env.filters['strip_html'] = strip_html


    return app

def hours_dow(df):
    """From a Pike13 DataFrame, return a DataFrame that lists the
    day of week and hours for each event_id"""
    t = df.copy()
    t['hour'] = t.start_at.dt.hour
    t = t[['event_id', 'dow', 'hour']].drop_duplicates()

    rows = []
    for idx, g in t.groupby('event_id'):
        dh = []
        for _, r in g.iterrows():
            dh.append({'hour': r.hour, 'dow': r.dow})
        rows.append({'event_id': idx, 'dow_hours': dh})

    t = df[['event_id', 'event_name', 'location_name', 'description_short', 'description']].drop_duplicates()

    t = t.merge(pd.DataFrame(rows), on='event_id')

    t['sort_order'] = t.apply(lambda r: r.dow_hours[0]['dow'] * 100 + r.dow_hours[0]['hour'], axis=1)

    return t.sort_values('sort_order')

def make_when_df(df):
    dow_names = {
        0: 'Mondays',
        1: 'Tuesdays',
        2: 'Wednesdays',
        3: 'Thursdays',
        4: 'Fridays',
        5: 'Saturdays',
        6: 'Sundays'
    }

    def format_hour(hour):
        if hour == 0 or hour == 24:
            return '12:00AM'
        elif hour < 12:
            return f'{hour}:00AM'
        elif hour == 12:
            return '12:00PM'
        else:
            return f'{hour - 12}:00PM'

    events = hours_dow(df)

    t = events.explode('dow_hours')
    t['dh_hour'] = t.dow_hours.apply(lambda r: r['hour'])
    t['dh_hour_str'] = t.dh_hour.apply(format_hour)
    t['dh_dow'] = t.dow_hours.apply(lambda r: r['dow'])
    t['dh_dow_str'] = t.dh_dow.map(dow_names)

    t['when'] = t.apply(lambda r: f"{r.dh_dow_str} at {r.dh_hour_str}", axis=1)

    t = t.merge(df[['event_id', 'service_id']].drop_duplicates())
    return t


def includes_str(t: pd.DataFrame, s):
    """Return all rows in t where the string s in one of these columns:
    service_name, event_name, description, description_short or instructions"""

    if s is None:
        return t

    s = s.lower()

    def includes_str(r, x):
        strs = [r.service_name, r.event_name, r.description,
                r.description_short, r.instructions]

        strs = [e.lower() for e in strs if e is not None]

        return any([s in e for e in strs])

    return t[t.apply(includes_str, args=(s,), axis=1)]
