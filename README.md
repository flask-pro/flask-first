# Flask-First

Flask extension for using "specification first" principle.

Features:

* Decorator for mapping routes from OpenAPI specification on Python's view functions via Flask.
* `Application Factory` supported.
* Validating path parameters from url.
* Validating arguments from url.
* Validating JSON from request.
* Validating JSON from response.

----

Limitations

* All specification in one file.
* Not supported `Encoding Object`.
* Not supported `Discriminator Object`.
* Not supported `XML Object`.
* Not supported `Specification Extensions`.
* Not supported `OAuthFlowsObject`.

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
First(path_to_spec, app)


@app.specification
def index(name):
    return {'message': name}


if __name__ == '__main__':
    app.run()
```

Run application:

```shell
$ python main.py
```

Check url in browser `http://127.0.0.1:5000/username`.

## Settings

`FIRST_RESPONSE_VALIDATION` - Default: `False`. Enabling response body validation. Useful when
developing. May be disabled in a production environment.

## Additional documentation

* [OpenAPI Documentation](<https://swagger.io/specification/>).
* [OpenAPI on GitHub](<https://github.com/OAI/OpenAPI-Specification>).
* [JSON Schema Documentation](<https://json-schema.org/specification.html>).
