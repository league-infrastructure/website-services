import json

import pandas as pd
from flask import current_app, jsonify
from flask import (
    render_template
)
from leaguesync import Pike13DataFrames, Pike13, one_month_ago, Calendar

from . import create_app, get_p13
from .util import *
from leaguesync.util import convert_naive
app = create_app()


def in_date_range(df):
    """Filter the DataFrame to only include events in the current week and the next 30 days"""

    from datetime import datetime, timedelta

    start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
    end_date = datetime.now().date() + timedelta(days=30)

    mask = (df['start_at'] >= str(start_date)) & (df['start_at'] <= str(end_date) )
    return df.loc[mask]




def pike13_events_df(p13: Pike13, location=None, select_f=None, incl_str=None):
    """Get the events from Pike13 as a DataFrame, form on month ago to now."""

    pdf = Pike13DataFrames(p13)

    eo = pdf.event_occurrences
    loc = pdf.locations
    srv = pdf.services

    t = eo.merge(loc).merge(srv)
    t = t[t.start_at >= str(one_month_ago().date())]

    if location:
        t = Calendar.filter_location(t, location)

    if select_f:
        t = t[t.apply(select_f, axis=1)]

    if includes_str:
        t = includes_str(t, incl_str)

    t = in_date_range(t)

    # Ensure the datetime is timezone-aware, set to UTC
    for c in ['start_at', 'end_at']:
        t[c] = t[c].apply(lambda x: convert_naive(x).tz_convert('America/Los_Angeles'))

    return t

@app.route('/')
def hello_world():  # put application's code here

    p13 = get_p13()

    def select(event):
        return (
                'java' in event.event_name.lower() and
                not 'make-up' in event.event_name.lower() and
                not '@' in event.event_name.lower() and
                event.location_code == 'CV'
                )

    events = pike13_events_df(p13, select_f=select)

    # Add the day of week and hours strings, such as
    # Sundays at 4:00PM, Saturdays at 4:00PM
    events = make_when_df(events)

    return render_template('calendar.html',
                           events = events.to_dict(orient='records'))


@app.route('/config')
def show_config():  # put application's code here

    d = {}
    for k, v in current_app.config.items():
        try:
            jsonify(v)
            d[k] = v
        except:
            print(f"Could not jsonify {k}")

    return jsonify(d)


if __name__ == '__main__':
    app.run()
