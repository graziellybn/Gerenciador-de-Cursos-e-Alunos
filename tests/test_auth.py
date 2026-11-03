import json

import pytest

from cli.menu import MenuCLI
from database.repositorio import Repositorio
from models import AutenticacaoError
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.monitor import Monitor
from models.turma import Turma
from services.auth_service import AuthService
from services.aluno_service import AlunoService
from services.matricula_service import MatriculaService


def _registrar_aprovacao(repo, aluno, disciplina):
    turma_anterior = Turma("T0", disciplina, "Prof", "2025.2", 2)
    repo.salvar_turma(turma_anterior)
    matricula = Matricula(
        repo.buscar_aluno(aluno.matricula, com_matriculas=False),
        repo.buscar_turma("T0", com_alunos=False),
        repo.configuracoes,
    )
    matricula.nota_1 = matricula.nota_2 = 9
    matricula.frequencia = 90
    repo.salvar_matricula(matricula)


def test_autentica_administrador_e_pessoa(repo, fabrica_aluno):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "segredo123")
    sessao_adm = auth.autenticar("ROOT", "segredo123")

    repo.salvar_aluno(fabrica_aluno("2026001", "Ana"))
    auth.registrar_aluno("2026001", "2026001@aluno.uniesquina.edu.br", "senha-aluno")
    sessao_pessoa = auth.autenticar("2026001", "senha-aluno")

    assert sessao_adm.papel == "adm"
    assert sessao_adm.pessoa.tem_permissao("gerir_cursos")
    assert sessao_adm.pessoa.email.endswith("@adm.uniesquina.edu.br")
    assert repo.buscar_administrador("root").email == sessao_adm.pessoa.email
    assert sessao_pessoa.papel == "pessoa"
    assert sessao_pessoa.pessoa.matricula == "2026001"
    assert sessao_pessoa.pessoa.email.endswith("@aluno.uniesquina.edu.br")


def test_somente_administrador_designa_monitor(repo, fabrica_aluno):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "segredo123")
    sessao_adm = auth.autenticar("root", "segredo123")
    repo.salvar_aluno(fabrica_aluno("2026005", "Eva"))
    repo.salvar_curso(Curso("C1", "Curso de graduação"))
    repo.salvar_disciplina(Disciplina("D1", "Disciplina", 60, "C1"))
    repo.salvar_turma(Turma("T1", repo.buscar_disciplina("D1"), "Prof", "2026.2", 2))
    repo.salvar_turma(Turma("T2", repo.buscar_disciplina("D1"), "Prof", "2026.2", 2))
    aluno = repo.buscar_aluno("2026005", com_matriculas=False)
    _registrar_aprovacao(repo, aluno, repo.buscar_disciplina("D1"))
    auth.registrar_aluno("2026005", "2026005@aluno.uniesquina.edu.br", "senha-aluno")
    sessao_aluno = auth.autenticar("2026005", "senha-aluno")

    with pytest.raises(AutenticacaoError, match="Somente um administrador"):
        AlunoService(repo).designar_monitor("2026005", "T1", sessao=sessao_aluno)

    monitor = AlunoService(repo).designar_monitor("2026005", "T1", sessao=sessao_adm)
    assert monitor.monitora("T1")
    MatriculaService(repo).matricular("2026005", "T2", sessao=sessao_adm)

    saida = []
    MenuCLI(repo, output_fn=saida.append).listar_alunos()
    linha_monitor = next(linha for linha in saida if "Eva" in linha)
    assert "Perfil: Monitor" in linha_monitor
    assert "Situação: Ativo" in linha_monitor
    assert "Matrículas cursando: T2" in linha_monitor
    assert "Turmas de monitoria: T1" in linha_monitor

def test_designacao_de_monitor_fica_salva_em_json_e_carrega_ao_reabrir(tmp_path, fabrica_aluno):
    caminho = tmp_path / "dados"
    repo = Repositorio(caminho)
    repo.salvar_aluno(fabrica_aluno("2026007", "Lia"))
    repo.salvar_curso(Curso("C1", "Curso de graduação"))
    disciplina = Disciplina("D1", "Disciplina", 60, "C1")
    repo.salvar_disciplina(disciplina)
    repo.salvar_turma(Turma("T1", disciplina, "Prof", "2026.2", 2))
    aluno = repo.buscar_aluno("2026007", com_matriculas=False)
    _registrar_aprovacao(repo, aluno, disciplina)

    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "segredo123")
    sessao_adm = auth.autenticar("root", "segredo123")
    AlunoService(repo).designar_monitor("2026007", "T1", sessao=sessao_adm)

    dados = json.loads((caminho / "monitores.json").read_text(encoding="utf-8"))
    assert dados == [{"matricula": "2026007", "turmas_monitoradas": ["T1"]}]
    repo.fechar()

    repo = Repositorio(caminho)
    monitor = repo.buscar_aluno("2026007")
    assert isinstance(monitor, Monitor)
    assert monitor.turmas_monitoradas == frozenset({"T1"})
    repo.fechar()
