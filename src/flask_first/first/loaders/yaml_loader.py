from collections.abc import Hashable
from functools import reduce
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import FirstResolverError
from ..exceptions import FirstYAMLReaderError


class YAMLReader:
    """
    Open OpenAPI specification from yaml file. The specification from multiple files is supported.
    """

    def __init__(self, path: Path):
        self.path = path
        self.root_file_name = self.path.name
        self.store = {}

    @staticmethod
    def _yaml_to_dict(path: Path) -> dict:
        with open(path) as f:
            s = yaml.safe_load(f)
        return s

    def add_file_to_store(self, ref: str) -> None:
        try:
            file_path, node_path = ref.split('#/')
        except (AttributeError, ValueError):
            raise FirstYAMLReaderError(f'"$ref" with value <{ref}> is not valid.')

        if file_path and file_path not in self.store:
            path_to_spec_file = Path(self.path.parent, file_path)

            try:
                self.store[file_path] = self._yaml_to_dict(path_to_spec_file)
            except FileNotFoundError:
                raise FirstYAMLReaderError(f'No such file or directory: <{file_path}>')

    def search_file(self, obj: dict or list) -> None:
        if isinstance(obj, dict):
            ref = obj.get('$ref')
            if ref:
                self.add_file_to_store(ref)
            else:
                for _, v in obj.items():
                    self.search_file(v)

        elif isinstance(obj, list):
            for item in obj:
                self.search_file(item)

        else:
            return

    def load(self) -> 'YAMLReader':
        root_file = self._yaml_to_dict(self.path)
        self.store[self.root_file_name] = root_file
        self.search_file(root_file)
        return self


class Resolver:
    def __init__(self, yaml_reader: YAMLReader):
        self.yaml_reader = yaml_reader
        self.resolved_spec = None

    def _get_schema_via_local_ref(self, file_path: str, node_path: str) -> dict:
        keys = node_path.split('/')

        def get_value_of_key_from_dict(source_dict: dict, key: Hashable) -> Any:
            return source_dict[key]

        try:
            return reduce(get_value_of_key_from_dict, keys, self.yaml_reader.store[file_path])
        except KeyError:
            raise FirstResolverError(f'No such path: "{node_path}"')

    def _get_schema(self, root_file_path: str, ref: str) -> Any:
        try:
            file_path, node_path = ref.split('#/')
        except (AttributeError, ValueError):
            raise FirstResolverError(
                f'"$ref" with value <{ref}> is not valid in file <{root_file_path}>'
            )

        if file_path and node_path:
            obj = self._get_schema_via_local_ref(file_path, node_path)

        elif node_path and not file_path:
            obj = self._get_schema_via_local_ref(root_file_path, node_path)

        else:
            raise NotImplementedError

        return obj

    def _resolving_all_refs(self, file_path: str, obj: Any) -> Any:
        if isinstance(obj, dict):
            ref = obj.get('$ref', ...)
            if ref is not ...:
                obj = self._resolving_all_refs(file_path, self._get_schema(file_path, ref))
            else:
                for key, value in obj.items():
                    obj[key] = self._resolving_all_refs(file_path, value)

        if isinstance(obj, list):
            objs = []
            for item_obj in obj:
                objs.append(self._resolving_all_refs(file_path, item_obj))
            obj = objs

        return obj

    def resolving(self) -> 'Resolver':
        root_file_path = self.yaml_reader.root_file_name
        root_spec = self.yaml_reader.store[root_file_path]
        self.resolved_spec = self._resolving_all_refs(root_file_path, root_spec)
        return self


def load_from_yaml(path: Path) -> Resolver:
    yaml_reader = YAMLReader(path).load()
    resolved_obj = Resolver(yaml_reader).resolving()
    return resolved_obj.resolved_spec
