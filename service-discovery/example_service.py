import requests
from flask import Flask

app = Flask(__name__)

SERVICE_NAME = "example-service"
SERVICE_ADDRESS = "http://localhost:8080"

REGISTRY_URL = "http://localhost:5000"


def register():
    """Register this service with the registry."""
    try:
        requests.post(
            f"{REGISTRY_URL}/register",
            json={"name": SERVICE_NAME, "address": SERVICE_ADDRESS},
        )
        print(f"Registered {SERVICE_NAME} at {SERVICE_ADDRESS}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to register service: {e}")


@app.route("/")
def home():
    return "Hello from example-service"


if __name__ == "__main__":
    register()
    app.run(port=8080)
