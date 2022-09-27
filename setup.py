from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="Flask-First",
    install_requires=[
        'Flask>=2.0.2',
        'jsonschema>=4.10.0',
        'openapi_schema_validator==0.2.3',
        'openapi-spec-validator==0.4.0',
        'marshmallow>=3.14.1',
    ],
)
