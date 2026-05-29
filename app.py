import threading
import webbrowser

from flask import Flask, render_template

import config
import database
from routes.dashboard import dashboard_bp
from routes.packages import packages_bp
from routes.students import students_bp
from routes.submissions import submissions_bp
from routes.settings import settings_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    database.init_db()

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(packages_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(settings_bp)

    @app.route("/health")
    def health():
        return ("OK", 200)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html", error=str(e)), 500

    return app


if __name__ == "__main__":
    app = create_app()
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
