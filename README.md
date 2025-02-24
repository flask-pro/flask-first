# Flask-First

Flask extension for using "specification first" and "API-first" principles.

<!--TOC-->

- [Flask-First](#flask-first)
  - [Features](#features)
  - [Installation](#installation)
  - [Settings](#settings)
  - [Tools](#tools)
  - [Data types](#data-types)
  - [Examples](#examples)
    - [Simple example](#simple-example)
    - [Specification from multiple file](#specification-from-multiple-file)
    - [CORS support](#cors-support)
  - [Additional documentation](#additional-documentation)

<!--TOC-->

## Features

* `Application Factory` supported.
* Validating and serializing headers of request.
* Validating and serializing path parameters of request.
* Validating and serializing arguments of request.
* Validating and serializing cookies of request.
* Validating and serializing JSON of request.
* Validating JSON from response for debugging.
* Provides a Swagger UI.
* Support OpenAPI version 3.1.0.
* Support specification from multiple file.

## Installation

Recommended using the latest version of Python. Flask-First supports Python 3.9 and newer.

Install and update using `pip`:

```shell
$ pip install -U flask_first
```

## Settings

* `FIRST_RESPONSE_VALIDATION` - Default: `False`. Enabling response body validation. Useful when
developing. Must be disabled in a production environment.
* `FIRST_DATETIME_FORMAT` - Default: `None`. Set format for `format: date-time`.
Example: `%Y-%m-%dT%H:%M:%S.%fZ`.

## Tools

Possible to get data from path-parameters, arguments, JSON, cookies and headers in serialized form.
Use flask-first object attached to the query.

```python
from flask import request


def route_func():
    path_parameters = request.extensions['first']['views']
    args = request.extensions['first']['args']
    json = request.extensions['first']['json']
    cookies = request.extensions['first']['cookies']
    headers = request.extensions['first']['headers']
```

## Data types

Supported formats for string type field:

* uuid
* date-time
* date
* time
* email
* ipv4
* ipv6
* uri
* binary

## Examples

### Simple example

OpenAPI 3 specification file `openapi.yaml`:

```yaml
openapi: 3.1.0
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
        200:
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

Check url in browser `http://127.0.0.1:5000/username`. Check SwaggerUI url in
browser `http://127.0.0.1:5000/docs`.

### Specification from multiple file

Flask-First supported specification OpenAPI from multiple files. You need create root file for
specification with name `openapi.yaml`.

Root file `openapi.yaml`:

```yaml
openapi: 3.1.0
info:
  title: Simple API for Flask-First
  version: 1.0.0
paths:
  /{name}:
    $ref: 'name.openapi.yaml#/name'
components:
  schemas:
    MessageField:
      type: string
      description: Field for message.
```

Child file `name.openapi.yaml`:

```yaml
name:
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
        $ref: '#/components/responses/ResponseOK'
components:
  responses:
    ResponseOK:
      description: OK
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                $ref: 'openapi.yaml#/components/schemas/MessageField'
```

### CORS support

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
