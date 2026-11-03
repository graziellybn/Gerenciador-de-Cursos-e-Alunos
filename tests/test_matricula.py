import pytest

from database.seed import _aluno
from models import ChoqueHorarioError, PreRequisitoNaoCumpridoError
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma
from services.auth_service import AuthService
from services.matricula_service import MatriculaService


def _sessao_administrador(repo):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "senha-segura")
    return auth.autenticar("root", "senha-segura")


# ---------- regras de matrícula (serviço + repositório) ----------
def _cenario(repo):
    curso = Curso("ES001", "Engenharia de Software")
    repo.salvar_curso(curso)
    alg = Disciplina("ALG101", "Algoritmos", 60, curso)
    poo = Disciplina("POO101", "POO", 60, curso, pre_requisitos=["ALG101"])
    bd = Disciplina("BD101", "Banco de Dados", 60, curso)
    repo.salvar_disciplina(alg)
    repo.salvar_disciplina(poo)
    repo.salvar_disciplina(bd)
    repo.salvar_turma(Turma("ALG-0", alg, "P", "2026.1", 5, {"seg": "08:00-10:00"}))
    repo.salvar_turma(Turma("POO-1", poo, "P", "2026.2", 1, {"ter": "10:00-12:00"}))
    repo.salvar_turma(Turma("BD-1", bd, "P", "2026.2", 5, {"ter": "11:00-13:00"}))


def _aprovar_em_alg(repo, matricula: str):
    aluno = _aluno(matricula, f"Aluno {matricula}")
    repo.salvar_aluno(aluno)
    m = Matricula(aluno, repo.buscar_turma("ALG-0", com_alunos=False))
    m.nota_1 = m.nota_2 = 9.0
    m.atualizar_status()
    repo.salvar_matricula(m)


def test_pre_requisito_nao_atendido_nega_matricula(repo):
    _cenario(repo)
    repo.salvar_aluno(_aluno("1", "Sem Histórico"))
    sessao = _sessao_administrador(repo)
    with pytest.raises(PreRequisitoNaoCumpridoError):
        MatriculaService(repo).matricular("1", "POO-1", sessao=sessao)


def test_pre_requisito_atendido_matricula_e_persiste(repo):
    _cenario(repo)
    _aprovar_em_alg(repo, "1")
    MatriculaService(repo).matricular("1", "POO-1", sessao=_sessao_administrador(repo))
    aluno = repo.buscar_aluno("1")
    assert [m.turma.id_oferta for m in aluno.matriculas] == ["ALG-0", "POO-1"]
    assert len(repo.buscar_turma("POO-1")) == 1


def test_choque_de_horario_nega_matricula(repo):
    _cenario(repo)
    _aprovar_em_alg(repo, "1")
    sessao = _sessao_administrador(repo)
    servico = MatriculaService(repo)
    servico.matricular("1", "POO-1", sessao=sessao)
    with pytest.raises(ChoqueHorarioError):
        servico.matricular("1", "BD-1", sessao=sessao)

