import os

from flask import Flask
from flask_first import First

basedir = os.path.abspath(os.path.dirname(__file__))
path_to_spec = os.path.join(basedir, 'openapi.yaml')

app = Flask(__name__)
app.config['FIRST_RESPONSE_VALIDATION'] = True
first = First(path_to_spec, app=app, swagger_ui_path='/docs')


def index(name):
    return {'message': name}


first.add_view_func(index)

if __name__ == '__main__':
    app.run()
