"""
API de cadastro de clientes – POST /customers
Implementação simples usando apenas a stdlib do Python.
"""

import hashlib
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# In-memory "database"
# ---------------------------------------------------------------------------
customers_db: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a SHA-256 hex-digest of the password (with a fixed salt for demo purposes)."""
    salt = "demo_salt_value"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def email_exists(email: str) -> bool:
    """Check whether *email* is already registered."""
    return any(c["email"] == email for c in customers_db)


def validate_customer(data: dict) -> list[str]:
    """Return a list of validation error messages (empty list == valid)."""
    errors: list[str] = []
    if not data.get("name"):
        errors.append("Field 'name' is required.")
    if not data.get("email"):
        errors.append("Field 'email' is required.")
    if not data.get("password"):
        errors.append("Field 'password' is required.")
    return errors


def create_customer(data: dict) -> dict:
    """Persist a new customer and return the public representation."""
    customer = {
        "id": len(customers_db) + 1,
        "name": data["name"],
        "email": data["email"],
        "password_hash": hash_password(data["password"]),
    }
    customers_db.append(customer)
    # Return a safe copy (without the hash) plus the id
    return {"id": customer["id"], "name": customer["name"], "email": customer["email"]}


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class CustomerHandler(BaseHTTPRequestHandler):
    """Minimal HTTP request handler for the /customers endpoint."""

    def _send_json(self, status: int, body: dict | list) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/customers":
            self._send_json(404, {"error": "Not found"})
            return

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # Validate required fields
        errors = validate_customer(data)
        if errors:
            self._send_json(400, {"errors": errors})
            return

        # Duplicate e-mail check
        if email_exists(data["email"]):
            self._send_json(409, {"error": "Email already registered"})
            return

        # Create customer
        customer = create_customer(data)
        self._send_json(201, customer)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/customers":
            self._send_json(404, {"error": "Not found"})
            return
        safe = [{"id": c["id"], "name": c["name"], "email": c["email"]} for c in customers_db]
        self._send_json(200, safe)

    # Suppress default stderr logging during tests
    def log_message(self, format, *args):  # noqa: A002
        pass


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = HTTPServer((host, port), CustomerHandler)
    print(f"Server running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(port=int(os.environ.get("PORT", "8000")))
