from marshmallow import EXCLUDE
from marshmallow import fields
from marshmallow import ValidationError
from marshmallow.base import SchemaABC


class AllOf(fields.Field):
    def __init__(self, *nested: SchemaABC):
        self.nested = nested
        super().__init__()

    def _deserialize(self, value, attr, data, **kwargs):
        errors = []
        valid_schemas = []
        for schema in self.nested:
            error = schema(unknown=EXCLUDE).validate(value)
            if error:
                errors.append(error)
            else:
                valid_schemas.append(schema)

        if not errors:
            serialized_data = {}
            for schema in valid_schemas:
                serialized_data = {**serialized_data, **schema(unknown=EXCLUDE).load(value)}
            return serialized_data
        else:
            raise ValidationError(f'The value <{value}> does not match all schemas.')


class AnyOf(fields.Field):
    def __init__(self, *nested: SchemaABC):
        self.nested = nested
        super().__init__()

    def _deserialize(self, value, attr, data, **kwargs):
        errors = []
        valid_schemas = []
        for schema in self.nested:
            error = schema().validate(value)
            if error:
                errors.append(error)
            else:
                valid_schemas.append(schema)

        if valid_schemas:
            return valid_schemas[0]().load(value)
        else:
            raise ValidationError(f'The value <{value}> does not match any schema.')


class OneOf(fields.Field):
    def __init__(self, *nested: SchemaABC):
        self.nested = nested
        super().__init__()

    def _deserialize(self, value, attr, data, **kwargs):
        errors = []
        valid_schemas = []
        for schema in self.nested:
            error = schema().validate(value)
            if error:
                errors.append(error)
            else:
                valid_schemas.append(schema)

        if len(valid_schemas) == 1:
            return valid_schemas[0]().load(value)
        else:
            raise ValidationError(f'The value <{value}> does not match one schema.')
