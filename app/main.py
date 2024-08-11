import os
from decimal import Decimal

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import JWTManager

from app.blueprints.rate_limit.base import limiter


# Custom JSON encoder to handle Decimal objects returned by SQLAlchemy raw queries
class CustomJSONEncoder(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)


def create_app(config_filename="config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    app.config.from_prefixed_env()

    from app.blueprints.auth.views import auth
    from app.blueprints.core.views import core_api
    from app.blueprints.core.views_tree import tree_api

    app.register_blueprint(core_api)
    app.register_blueprint(tree_api)
    app.register_blueprint(auth, url_prefix="/auth")

    # Set the custom JSON encoder in the Flask app
    app.json = CustomJSONEncoder(app)

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
    JWTManager(app)

    # Initializing the limiter with the app
    limiter.init_app(app)

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run()
