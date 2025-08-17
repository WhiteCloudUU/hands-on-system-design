import requests

REGISTRY_URL = "http://localhost:5000"


def discover_service(name):
    """Discover a service by name."""
    response = requests.get(f"{REGISTRY_URL}/discover/{name}")
    return response.json()


# Example Usage
if __name__ == "__main__":
    service_name = "example-service"

    print(f"Discovering '{service_name}'...")
    service_url = discover_service(service_name)["address"]
    print(f"Service '{service_name}' is at {service_url}.")

    print(f"Calling  {service_url}...")
    response = requests.get(service_url)
    print(f"Get: {response.text}")
