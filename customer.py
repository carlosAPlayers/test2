def criar_cliente(nome, email):
    """Cria um novo cliente com nome e e-mail.

    Args:
        nome: Nome do cliente.
        email: E-mail do cliente.

    Returns:
        dict: Dicionário com os dados do cliente criado.

    Raises:
        ValueError: Se nome ou email estiverem vazios.
    """
    if not nome or not nome.strip():
        raise ValueError("O nome do cliente é obrigatório.")
    if not email or not email.strip():
        raise ValueError("O e-mail do cliente é obrigatório.")

    cliente = {
        "nome": nome.strip(),
        "email": email.strip(),
    }
    return cliente
