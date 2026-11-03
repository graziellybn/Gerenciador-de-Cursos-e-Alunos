import pytest

from models import ChoqueHorarioError
from models.matricula import Matricula
from models.turma import Turma
from services.auth_service import AuthService
from services.turma_service import TurmaService


def test_atualizar_horario_nao_cria_conflito_para_aluno(repo, curso, fabrica_aluno):
    from models.curso import Curso
    from models.disciplina import Disciplina

    repo.salvar_curso(Curso(curso.codigo, curso.nome))
    disciplina = Disciplina("D1", "Disciplina", 60, curso.codigo)
    repo.salvar_disciplina(disciplina)
    repo.salvar_aluno(fabrica_aluno("A1"))
    repo.salvar_turma(Turma("T1", disciplina, "Prof", "2026.2", 2, {"seg": "08:00-10:00"}))
    repo.salvar_turma(Turma("T2", disciplina, "Prof", "2026.2", 2, {"ter": "08:00-10:00"}))
    aluno = repo.buscar_aluno("A1", com_matriculas=False)
    repo.salvar_matricula(Matricula(aluno, repo.buscar_turma("T1", False)))
    repo.salvar_matricula(Matricula(aluno, repo.buscar_turma("T2", False)))
    turma_atualizada = repo.buscar_turma("T1", com_alunos=False)
    turma_atualizada.horario = {"ter": "08:30-10:30"}
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "senha-segura")
    sessao = auth.autenticar("root", "senha-segura")

    with pytest.raises(ChoqueHorarioError):
        TurmaService(repo).atualizar_turma(turma_atualizada, sessao=sessao)
