from setuptools import setup

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="Flask-First",
    install_requires=[
        'Flask>=2.0.2',
        'pyyaml>=6.0',
        'openapi-spec-validator>=0.3.1',
        'marshmallow>=3.14.1',
    ],
)
