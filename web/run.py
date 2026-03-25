import os

from app import create_app

# file to run the application, no configuration should be present
app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV") == "testing"
    app.run(debug=False, host="0.0.0.0")
