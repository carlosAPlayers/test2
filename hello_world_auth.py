"""
Hello World - Authentication Service
GDD-6: Implementar serviço de autenticação

Simple hello world script for the authentication service.
This module provides a basic entry point for the auth service.
"""


def hello_world():
    """Display a hello world message from the authentication service."""
    message = "Hello World! Welcome to the Authentication Service."
    print(message)
    return message


if __name__ == "__main__":
    hello_world()
