# Flask-First

Flask extension for using "specification first" principle.

Features:

* `Application Factory` supported.
* Validating and serializing path parameters from `request.view_args` to `request.first_view_args`.
* Validating and serializing arguments from `request.args` to `request.first_args`.
* Validating JSON from request.
* Validating JSON from response.
* Provides a Swagger UI.

----

Limitations

* Full specification in one file.

## Installing

Install and update using `pip`:

```shell
$ pip install flask_first
```

Simple example
--------------
OpenAPI 3 specification file `openapi.yaml`:

```yaml
openapi: 3.0.3
info:
  title: Simple API for Flask-First
  version: 1.0.0
paths:
  /{name}:
    parameters:
      - name: name
        in: path
        required: true
        schema:
          type: string
    get:
      operationId: index
      summary: Returns a list of items
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
```

File with application initialization `main.py`:

```python
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

```

Run application:

```shell
$ python main.py
```

Check url in browser `http://127.0.0.1:5000/username`. Check SwaggerUI url in browser `http://127.0.0.1:5000/docs`.

## Settings

`FIRST_RESPONSE_VALIDATION` - Default: `False`. Enabling response body validation. Useful when
developing. May be disabled in a production environment.

## CORS support

Your need enable CORS in Flask and adding `OPTIONS` method in your specification. Example:

```yaml
...
paths:
  /index:
    post: ...
    get: ...
    put: ...
    patch: ...
    delete: ...
    options:
      summary: CORS support
      responses:
        200:
          headers:
            Access-Control-Allow-Origin:
              schema:
                type: string
            Access-Control-Allow-Methods:
              schema:
                type: string
            Access-Control-Allow-Headers:
              schema:
                type: string
          content: { }
```

## Additional documentation

* [OpenAPI Documentation](https://swagger.io/specification/).
* [OpenAPI on GitHub](https://github.com/OAI/OpenAPI-Specification).
* [JSON Schema Documentation](https://json-schema.org/specification.html).
