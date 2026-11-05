import os

from flask import Flask


def create_app():
    version = os.environ.get("APP_VERSION", "1.0.0").strip()

    if not version:
        raise ValueError("APP_VERSION must not be empty")

    try:
        port = int(os.environ.get("APP_PORT", "8000"))
    except ValueError as error:
        raise ValueError("APP_PORT must be an integer") from error

    if not 1 <= port <= 65535:
        raise ValueError("APP_PORT must be between 1 and 65535")

    app = Flask(__name__)
    app.config.update(
        APP_VERSION=version,
        APP_PORT=port,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.get("/version")
    def get_version():
        return {"version": app.config["APP_VERSION"]}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=app.config["APP_PORT"],
        debug=False,
    )