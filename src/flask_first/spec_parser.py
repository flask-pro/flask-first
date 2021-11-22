"""The module contains tools for preprocessing and serializing the OpenAPI specification."""
from copy import deepcopy

import marshmallow
import yaml
from openapi_spec_validator import validate_spec
from yaml import CLoader as Loader

from .exc import FlaskFirstSpecificationValidation
from .schemas import OpenAPIObjectSchema


class Specification:
    """This class implemented methods for specification API."""

    def __init__(self, path_to_spec: str):
        self.raw = self._load_from_yaml(path_to_spec)
        self.serialized = self._serialization_spec()

    @staticmethod
    def _load_from_yaml(spec_path: str) -> dict:
        with open(spec_path) as spec_file:
            spec = yaml.load(spec_file, Loader=Loader)
        validate_spec(deepcopy(spec))
        return spec

    def _serialization_spec(self):
        schema = OpenAPIObjectSchema()
        schema.context['raw_spec'] = deepcopy(self.raw)

        try:
            return schema.load(self.raw)
        except marshmallow.exceptions.ValidationError as e:
            raise FlaskFirstSpecificationValidation(e)
