import pytest

from cli.menu import MenuCLI
from database.repositorio import Repositorio
from services.auth_service import AuthService


def _sessao_administrador(repo):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "senha-segura")
    return auth.autenticar("root", "senha-segura")


@pytest.fixture
def repo():
    repositorio = Repositorio(":memory:")
    yield repositorio
    repositorio.fechar()


def test_cli_cadastra_entidades_matricula_e_emite_relatorio(repo, monkeypatch):
    from services.aluno_service import AlunoService

    gerada = AlunoService(repo).gerar_matricula()
    assert len(gerada) == 10 and gerada.startswith("202600") and gerada[6:].isdigit()
    monkeypatch.setattr(AlunoService, "gerar_matricula", lambda _self: "2026001234")
    respostas = iter([
        "2", "ES001", "Engenharia de Software",
        "4", "Ana Silva", "2000-01-01", "ana@aluno.uniesquina.edu.br", "999999999", "Engenharia",
        "12", "ES001", "ALG101", "Algoritmos", "60", "", "", "",
        "6", "ALG101", "", "T1", "Prof. Lima", "2026.2", "2", "Sala 1",
        "7", "2026001234", "T1",
        "9", "T1",
        "0",
    ])
    saida = []
    MenuCLI(
        repo,
        input_fn=lambda _prompt: next(respostas),
        output_fn=saida.append,
        sessao=_sessao_administrador(repo),
    ).executar()

    assert repo.buscar_curso("ES001").nome == "Engenharia de Software"
    assert repo.buscar_disciplina("ALG101").nome == "Algoritmos"
    assert repo.buscar_aluno("2026001234").email == "ana@aluno.uniesquina.edu.br"
    assert repo.buscar_aluno("2026001234").matricula == "2026001234"
    assert len(repo.buscar_turma("T1")) == 1
    assert any("Ana Silva" in linha for linha in saida)
    assert any("1/2" in linha for linha in saida)


def test_cli_salva_notas_frequencia_status_e_cr(repo):
    from models.curso import Curso
    from models.disciplina import Disciplina
    from models.turma import Turma
    from services.matricula_service import MatriculaService

    repo.salvar_curso(Curso("ES001", "Engenharia de Software"))
    repo.salvar_disciplina(Disciplina("ALG101", "Algoritmos", 60, "ES001"))
    repo.salvar_turma(Turma("T1", repo.buscar_disciplina("ALG101"), "Prof. Lima", "2026.2", 2))
    # Usa a fixture de aluno para manter os mesmos dados válidos da suíte.
    from models.aluno import Aluno
    repo.salvar_aluno(Aluno(
        "Ana Silva", "2000-01-01", "ana@aluno.uniesquina.edu.br", "999999999", "2026001", "Engenharia"
    ))
    sessao = _sessao_administrador(repo)
    MatriculaService(repo).matricular("2026001", "T1", sessao=sessao)

    respostas = iter(["8", "2026001", "T1", "8", "9", "90", "0"])
    saida = []
    MenuCLI(
        repo,
        input_fn=lambda _prompt: next(respostas),
        output_fn=saida.append,
        sessao=sessao,
    ).executar()

    aluno = repo.buscar_aluno("2026001")
    assert aluno.matriculas[0].status == "Aprovado"
    assert aluno.matriculas[0].calcular_media() == 8.5
    assert aluno.cr == 8.5
    assert any("Aprovado" in linha for linha in saida)


def test_cli_sem_sessao_nao_recebe_menu_administrativo(repo):
    respostas = iter(["2", "0"])
    saida = []

    MenuCLI(repo, input_fn=lambda _prompt: next(respostas), output_fn=saida.append).executar()

    assert repo.listar_cursos() == []
    assert any("Essa opção não existe" in linha for linha in saida)
    assert not any("Cadastrar curso" in linha for linha in saida)


def test_zero_cancela_operacao_e_retorna_ao_menu(repo):
    respostas = iter(["2", "0", "0"])
    saida = []

    MenuCLI(
        repo,
        input_fn=lambda _prompt: next(respostas),
        output_fn=saida.append,
        sessao=_sessao_administrador(repo),
    ).executar()

    assert repo.listar_cursos() == []
    assert any("Operação cancelada" in linha for linha in saida)
    assert sum("Bem-vindo" in linha for linha in saida) == 2


def test_cancelar_cadastro_de_disciplina_retorna_ao_menu_sem_salvar(repo):
    from models.curso import Curso

    repo.salvar_curso(Curso("ES001", "Engenharia de Software"))
    respostas = iter([
        "12", "ES001", "ALG101", "Algoritmos", "0", "0",
    ])
    saida = []

    MenuCLI(
        repo,
        input_fn=lambda _prompt: next(respostas),
        output_fn=saida.append,
        sessao=_sessao_administrador(repo),
    ).executar()

    assert repo.buscar_disciplina("ALG101") is None
    assert any("Operação cancelada" in linha for linha in saida)
    assert sum("Bem-vindo" in linha for linha in saida) == 2


def test_cadastro_de_turma_exige_disciplina_existente(repo):
    from models.curso import Curso

    repo.salvar_curso(Curso("ES001", "Engenharia de Software"))
    respostas = iter(["6", "DISC999", "0", "0"])
    saida = []

    MenuCLI(
        repo,
        input_fn=lambda _prompt: next(respostas),
        output_fn=saida.append,
        sessao=_sessao_administrador(repo),
    ).executar()

    assert repo.buscar_disciplina("DISC999") is None
    assert repo.listar_turmas() == []
    assert any("Cadastre a disciplina antes de criar a turma" in linha for linha in saida)


def test_000_volta_ao_login_sem_sair_da_aplicacao(repo):
    saida = []
    menu = MenuCLI(
        repo,
        input_fn=lambda _prompt: "000",
        output_fn=saida.append,
        sessao=_sessao_administrador(repo),
    )

    deve_encerrar = menu.executar()

    assert deve_encerrar is False
    assert any("Voltar ao menu de login" in linha for linha in saida)
    assert any("Voltando ao menu de login" in linha for linha in saida)


def test_main_volta_a_autenticar_depois_de_000(monkeypatch):
    import main as aplicacao

    class RepositorioFalso:
        fechado = False

        def fechar(self):
            self.fechado = True

    repo = RepositorioFalso()
    sessoes = [object(), object()]
    autenticacoes = []
    resultados_menu = iter([False, True])

    class MenuFalso:
        def __init__(self, _repo, sessao):
            self.sessao = sessao

        def executar(self):
            return next(resultados_menu)

    monkeypatch.setattr(aplicacao, "Repositorio", lambda: repo)
    monkeypatch.setattr(aplicacao, "autenticar_usuario", lambda _repo: autenticacoes.append(True) or sessoes.pop(0))
    monkeypatch.setattr(aplicacao, "MenuCLI", MenuFalso)

    aplicacao.main([])

    assert len(autenticacoes) == 2
    assert repo.fechado