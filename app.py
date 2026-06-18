from customer import criar_cliente


def main():
    """Formulário de cadastro de cliente via terminal."""
    print("=== Cadastro de Cliente ===")

    nome = input("Nome: ")
    email = input("E-mail: ")

    try:
        criar_cliente(nome, email)
        print("Cliente cadastrado com sucesso")
    except ValueError as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
