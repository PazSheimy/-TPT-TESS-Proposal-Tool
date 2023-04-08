from routes import register_routes
from flask import Flask


app = Flask(__name__)
register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)

