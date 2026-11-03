import pytest

from models import PermissaoNegadaError
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma
from services.auth_service import AuthService
from services.relatorio_service import RelatorioService


def _criar_base(repo):
    curso = Curso("C1", "Curso")
    repo.salvar_curso(curso)
    disciplina = Disciplina("D1", "Disciplina", 60, curso)
    repo.salvar_disciplina(disciplina)
    aluno = Aluno(
        "Ana", "2000-01-01", "ana@aluno.uniesquina.edu.br", "123", "A1", curso.nome
    )
    repo.salvar_aluno(aluno)
    return disciplina, aluno


def _registrar_resultado(repo, aluno, turma, nota, frequencia=90):
    matricula = Matricula(aluno, turma, repo.configuracoes)
    matricula.nota_1 = matricula.nota_2 = nota
    matricula.frequencia = frequencia
    repo.salvar_matricula(matricula)
    return matricula


def _sessao_administrador(repo):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "senha-segura")
    return auth.autenticar("root", "senha-segura")


def test_taxa_do_curso_conta_tentativas_finalizadas(repo):
    disciplina, aluno = _criar_base(repo)
    primeira = Turma("T1", disciplina, "Prof", "2025.1", 2)
    segunda = Turma("T2", disciplina, "Prof", "2025.2", 2)
    repo.salvar_turma(primeira)
    repo.salvar_turma(segunda)
    _registrar_resultado(repo, aluno, primeira, 9)
    _registrar_resultado(repo, aluno, segunda, 5)

    dados = RelatorioService(repo).taxa_aprovacao_curso(
        "C1", sessao=_sessao_administrador(repo)
    )

    assert dados["finalizadas"] == 2
    assert dados["aprovados"] == 1
    assert dados["taxa"] == 0.5


def test_monitor_so_consulta_turma_designada(repo):
    disciplina, aluno = _criar_base(repo)
    turma_monitoria = Turma("T1", disciplina, "Prof", "2026.2", 2)
    turma_propria = Turma("T2", disciplina, "Prof", "2026.2", 2)
    repo.salvar_turma(turma_monitoria)
    repo.salvar_turma(turma_propria)
    repo.salvar_matricula(Matricula(aluno, turma_propria, repo.configuracoes))
    repo.salvar_monitoria("A1", "T1")
    auth = AuthService(repo)
    auth.registrar_aluno("A1", "ana@aluno.uniesquina.edu.br", "senha-aluno")
    sessao = auth.autenticar("A1", "senha-aluno")
    relatorios = RelatorioService(repo)

    assert "Turma T1" in relatorios.relatorio_monitoria(sessao, "T1")
    relatorio_proprio = relatorios.relatorio_proprio_por_turma(sessao, "T2")
    assert "ainda não registradas" in relatorio_proprio
    relatorios_salvos = repo.relatorios_do_aluno("A1")
    assert len(relatorios_salvos) == 1
    assert relatorios_salvos[0]["dados"]["turma"] == "T2"
    assert relatorios_salvos[0]["dados"]["media"] is None
    with pytest.raises(PermissaoNegadaError):
        relatorios.relatorio_monitoria(sessao, "T2")
