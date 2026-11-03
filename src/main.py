import argparse

from cli.menu import MenuCLI
from database.repositorio import Repositorio
from database.seed import popular
from models import AutenticacaoError
from services.auth_service import AuthService


def autenticar_usuario(repo, input_fn=input, password_fn=None, output_fn=print):
    """Configura o primeiro administrador e solicita credenciais de acesso."""
    password_fn = password_fn or input
    auth = AuthService(repo)
    if not repo.tem_administrador():
        output_fn("\nConfiguração inicial: crie a conta de administrador.")
        while True:
            try:
                usuario = input_fn("Usuário administrador: ").strip()
                senha = password_fn("Senha (mínimo 8 caracteres): ")
                confirmacao = password_fn("Confirme a senha: ")
                if senha != confirmacao:
                    output_fn("As senhas não conferem. Tente novamente.")
                    continue
                auth.cadastrar_administrador(usuario, senha)
                output_fn("Administrador criado.")
                break
            except (ValueError, AutenticacaoError) as erro:
                output_fn(f"Erro: {erro}")

    while True:
        try:
            output_fn("\n1. Entrar")
            output_fn("2. Primeiro acesso do aluno")
            output_fn("0. Sair")
            opcao = input_fn("Escolha: ").strip()
            if opcao == "0":
                return None
            if opcao == "2":
                matricula = input_fn("Matrícula: ").strip()
                email = input_fn("E-mail informado no cadastro acadêmico: ").strip()
                senha = password_fn("Crie sua senha (mínimo 8 caracteres): ")
                confirmacao = password_fn("Confirme sua senha: ")
                if senha != confirmacao:
                    output_fn("As senhas não conferem.")
                    continue
                auth.registrar_aluno(matricula, email, senha)
                output_fn("Conta criada. Agora entre com sua matrícula e senha.")
                continue
            if opcao != "1":
                output_fn("Opção inválida.")
                continue
            usuario = input_fn("Usuário ou matrícula: ").strip()
            if not usuario:
                continue
            senha = password_fn("Senha: ")
            return auth.autenticar(usuario, senha)
        except (AutenticacaoError, ValueError) as erro:
            output_fn(str(erro))
        except (EOFError, KeyboardInterrupt):
            output_fn("\nEncerrando.")
            return None


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Gerenciador acadêmico com arquivos JSON")
    parser.add_argument("--demo", action="store_true", help="popular arquivos vazios com dados de exemplo")
    args = parser.parse_args(argv)

    repo = Repositorio()
    try:
        if args.demo and not repo.listar_cursos():
            popular(repo)
        while True:
            sessao = autenticar_usuario(repo)
            if sessao is None:
                break
            if MenuCLI(repo, sessao=sessao).executar():
                break
    finally:
        repo.fechar()


if __name__ == "__main__":
    main()