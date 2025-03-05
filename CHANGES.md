## Version 0.19.1

* For date and time from `date-dime` format fields, the time zone is enforced set in the UTC.

## Version 0.19.1

* Fix ref resolver.

## Version 0.19.0

* Remake loading from yaml files.

## Version 0.18.2

* Add setting `FIRST_DATETIME_FORMAT`.

## Version 0.18.1

* Improve exception message for response validation error.

## Version 0.17.0

* Authorization via HTTPBasicAuth and Bearer token supported.
* Add append serialized path-parameters, arguments, json, cookie and headers to object of request
  Flask.

## Version 0.16.1

* Fix the display of the specification described in several files in Swagger UI.

## Version 0.16.0

* Add support for splitting OpenAPI specification into multiple files.

## Version 0.15.0

* Add specification experimental validator for OpenAPI 3.1.

## Version 0.14.6

* The `default` response is now processed correctly.

## Version 0.14.5

* Bump version SwaggerUI.

## Version 0.14.4

* Fix url data format.

## Version 0.14.3

* Add Python versions 3.9, 3.10, 3.11, 3.12 support.

## Version 0.14.2

* Fix case-sensitive url validation.

## Version 0.14.1

* Fix README.md.

## Version 0.14.0

* Fix parameters validation.

## Version 0.13.2

* Fix cookie validation.

## Version 0.13.1

* Fix hashable field.

## Version 0.13.0

* Fix exceptions structure.

## Version 0.12.1

* Fix arguments validation.

## Version 0.12.0

* Validating and serializing arguments from `request.view_args` to `request.first_view_args`.
* Validating and serializing arguments from `request.args` to `request.first_args`.
* Validating and serializing arguments from `request.cookies` to `request.first_cookies`.

## Version 0.11.0

* Add using marshmallow schemas for validation and serialization data.
* Remove several depends.
* Validating and serializing arguments from `request.args`, `request.view_args`
  and `request.cookies` union and store to `request.first_args`.

## Version 0.10.9

* Fix download file with any "Content-Type".

## Version 0.10.8

* Fix validation of the OPTIONS method.

* ## Version 0.10.7

* Fix requirements.

## Version 0.10.6

* Fix bug in validate args.
* Bump version Python to 3.10.

## Version 0.10.5

* Bump version SwaggerUI to 4.12.0.

## Version 0.10.4

* Add CORS support.

## Version 0.9.4

* Fix serializing arguments.

## Version 0.9.3

* Fix first_args and first_view_args not creating if args and view_args empty.

## Version 0.9.2

* Fix serializing parameters from request.

## Version 0.9.1

* Fix '$ref' resolve.

## Version 0.9.0

* Fix validate parameters from path, arguments and JSON.

## Version 0.8.1

* Fix generate schema for object type field from response.

## Version 0.7.0

* add 'nullable' parameter.

## Version 0.5.1

* Fix using in application factory.

## Version 0.5

* Initial public release
