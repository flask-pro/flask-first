from pathlib import Path

from flask import Blueprint
from flask import Flask
from flask import render_template
from flask import url_for

from .first.specification import Specification


def add_swagger_ui_blueprint(app: Flask, spec: Specification, swagger_ui_path: str or Path) -> None:
    swagger_ui = Blueprint(
        'swagger_ui',
        __name__,
        static_folder='static',
        template_folder='templates',
        url_prefix=swagger_ui_path,
    )

    @swagger_ui.add_app_template_global
    def swagger_ui_static(filename):
        return url_for('swagger_ui.static', filename=filename)

    @swagger_ui.route('/')
    def swagger_ui_page():
        return render_template('swagger_ui/index.html')

    @swagger_ui.route('/openapi.json')
    def get_file_spec():
        return spec.raw_spec

    app.register_blueprint(swagger_ui)
