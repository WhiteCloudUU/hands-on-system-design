from flask import Flask, request, jsonify

app = Flask(__name__)
services = {}  # In-memory store for registered services


@app.route("/register", methods=["POST"])
def register_service():
    """Register a service with service name and address."""
    data = request.json
    name = data.get("name")
    address = data.get("address")

    if not name or not address:
        return jsonify({"error": "Missing service name or address"}), 400

    services[name] = address
    return jsonify({"message": f"Service {name} registered successfully"}), 200


@app.route("/discover/<service_name>", methods=["GET"])
def discover_service(service_name):
    """Retrieve the address of a registered service."""
    address = services.get(service_name)

    if not address:
        return jsonify({"error": "Service not found"}), 404

    return jsonify({"address": address}), 200


if __name__ == "__main__":
    app.run(port=5000)
