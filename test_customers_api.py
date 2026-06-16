"""
Testes unitários da API de cadastro de clientes (GDD-3).
Utiliza apenas unittest da stdlib.
"""

import json
import unittest
from io import BytesIO
from unittest.mock import patch

import customers_api


# ---------------------------------------------------------------------------
# Helper: build a minimal fake HTTP request for the handler
# ---------------------------------------------------------------------------

class FakeRequest:
    """Simulates the socket-level request that BaseHTTPRequestHandler expects."""

    def __init__(self, method: str, path: str, body: bytes = b""):
        request_line = f"{method} {path} HTTP/1.1\r\n"
        headers = f"Content-Length: {len(body)}\r\nContent-Type: application/json\r\n\r\n"
        self.rfile = BytesIO(request_line.encode() + headers.encode() + body)
        self.wfile = BytesIO()

    def makefile(self, mode, buffering=-1):  # noqa: ARG002
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data):
        self.wfile.write(data)


def make_request(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list]:
    """Fire a request at CustomerHandler and return (status_code, parsed_json)."""
    raw_body = json.dumps(body).encode() if body else b""
    request_line = f"{method} {path} HTTP/1.1\r\n"
    headers_text = (
        f"Host: localhost\r\n"
        f"Content-Length: {len(raw_body)}\r\n"
        f"Content-Type: application/json\r\n"
        f"\r\n"
    )
    raw = request_line.encode() + headers_text.encode() + raw_body

    rfile = BytesIO(raw)
    wfile = BytesIO()

    # BaseHTTPRequestHandler reads from rfile / writes to wfile
    handler = customers_api.CustomerHandler(
        request=(rfile, wfile),
        client_address=("127.0.0.1", 0),
        server=None,
    )

    # The constructor already processed the request; read the response.
    wfile.seek(0)
    response_raw = wfile.read().decode()

    # Parse status code from the first line (e.g. "HTTP/1.0 201 Created")
    status_line = response_raw.split("\r\n", 1)[0]
    status_code = int(status_line.split(" ", 2)[1])

    # Parse JSON body (everything after the blank line)
    json_body = response_raw.split("\r\n\r\n", 1)[1]
    return status_code, json.loads(json_body)


# ---------------------------------------------------------------------------
# Patch BaseHTTPRequestHandler.__init__ so we control rfile / wfile
# ---------------------------------------------------------------------------

# We override __init__ to avoid the default socket handling.
_original_init = customers_api.BaseHTTPRequestHandler.__init__


def _patched_init(self, request, client_address, server):
    rfile, wfile = request
    self.rfile = rfile
    self.wfile = wfile
    self.client_address = client_address
    self.server = server
    self.raw_requestline = rfile.readline()
    self.parse_request()
    # Dispatch
    method = self.command
    handler_method = getattr(self, f"do_{method}", None)
    if handler_method:
        handler_method()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestCustomersAPI(unittest.TestCase):

    def setUp(self):
        """Reset the in-memory database before each test."""
        customers_api.customers_db.clear()

    # -- Unit tests for helper functions ------------------------------------

    def test_hash_password_deterministic(self):
        """hash_password must return the same hash for the same input."""
        h1 = customers_api.hash_password("secret123")
        h2 = customers_api.hash_password("secret123")
        self.assertEqual(h1, h2)

    def test_hash_password_differs_for_different_inputs(self):
        h1 = customers_api.hash_password("abc")
        h2 = customers_api.hash_password("xyz")
        self.assertNotEqual(h1, h2)

    def test_validate_customer_missing_fields(self):
        errors = customers_api.validate_customer({})
        self.assertEqual(len(errors), 3)

    def test_validate_customer_valid(self):
        errors = customers_api.validate_customer(
            {"name": "Ana", "email": "ana@test.com", "password": "123"}
        )
        self.assertEqual(errors, [])

    def test_email_exists_false_when_empty(self):
        self.assertFalse(customers_api.email_exists("a@b.com"))

    def test_email_exists_true_after_create(self):
        customers_api.create_customer({"name": "X", "email": "x@y.com", "password": "p"})
        self.assertTrue(customers_api.email_exists("x@y.com"))

    def test_create_customer_returns_id(self):
        result = customers_api.create_customer({"name": "A", "email": "a@b.com", "password": "p"})
        self.assertEqual(result["id"], 1)
        self.assertNotIn("password_hash", result)

    def test_password_stored_as_hash(self):
        customers_api.create_customer({"name": "A", "email": "a@b.com", "password": "plain"})
        stored = customers_api.customers_db[0]
        self.assertNotEqual(stored["password_hash"], "plain")
        self.assertEqual(stored["password_hash"], customers_api.hash_password("plain"))

    # -- Integration tests via HTTP handler ---------------------------------

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_post_customer_success(self):
        status, body = make_request("POST", "/customers", {
            "name": "Maria", "email": "maria@example.com", "password": "s3cret"
        })
        self.assertEqual(status, 201)
        self.assertEqual(body["name"], "Maria")
        self.assertEqual(body["email"], "maria@example.com")
        self.assertIn("id", body)

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_post_customer_duplicate_email(self):
        payload = {"name": "Ana", "email": "dup@example.com", "password": "pw"}
        make_request("POST", "/customers", payload)
        status, body = make_request("POST", "/customers", payload)
        self.assertEqual(status, 409)
        self.assertIn("error", body)

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_post_customer_missing_fields(self):
        status, body = make_request("POST", "/customers", {"name": "Only Name"})
        self.assertEqual(status, 400)
        self.assertIn("errors", body)

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_post_customer_invalid_json(self):
        raw_body = b"not json"
        request_line = b"POST /customers HTTP/1.1\r\n"
        headers_text = (
            f"Host: localhost\r\n"
            f"Content-Length: {len(raw_body)}\r\n"
            f"Content-Type: application/json\r\n"
            f"\r\n"
        ).encode()
        rfile = BytesIO(request_line + headers_text + raw_body)
        wfile = BytesIO()
        customers_api.CustomerHandler(
            request=(rfile, wfile), client_address=("127.0.0.1", 0), server=None
        )
        wfile.seek(0)
        resp = wfile.read().decode()
        status_code = int(resp.split(" ", 2)[1])
        self.assertEqual(status_code, 400)

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_post_wrong_path_returns_404(self):
        status, body = make_request("POST", "/unknown", {"name": "A"})
        self.assertEqual(status, 404)

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_get_customers_empty(self):
        status, body = make_request("GET", "/customers")
        self.assertEqual(status, 200)
        self.assertEqual(body, [])

    @patch.object(customers_api.BaseHTTPRequestHandler, "__init__", _patched_init)
    def test_get_customers_after_create(self):
        make_request("POST", "/customers", {
            "name": "João", "email": "joao@test.com", "password": "pw"
        })
        status, body = make_request("GET", "/customers")
        self.assertEqual(status, 200)
        self.assertEqual(len(body), 1)
        self.assertNotIn("password_hash", body[0])


if __name__ == "__main__":
    unittest.main()
