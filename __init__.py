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