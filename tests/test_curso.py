import json

import pytest

from database.repositorio import Repositorio
from models import CicloPreRequisitoError
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma
from services.auth_service import AuthService
from services.curso_service import DisciplinaService


def _sessao_administrador(repo):
    auth = AuthService(repo)
    auth.cadastrar_administrador("root", "senha-segura")
    return auth.autenticar("root", "senha-segura")


def test_pre_requisitos_de_disciplinas_nao_podem_formar_ciclo(repo, curso):
    repo.salvar_curso(curso)
    servico = DisciplinaService(repo)
    sessao = _sessao_administrador(repo)
    servico.cadastrar_disciplina(
        Disciplina("ALG101", "Algoritmos", 60, curso), sessao=sessao
    )
    servico.cadastrar_disciplina(
        Disciplina("POO101", "POO", 60, curso, pre_requisitos=["ALG101"]),
        sessao=sessao,
    )

    with pytest.raises(CicloPreRequisitoError):
        servico.adicionar_pre_requisito("ALG101", "POO101", sessao=sessao)


def test_repositorio_json_preserva_relacoes_ao_reabrir(tmp_path, curso):
    caminho = tmp_path / "dados"
    repo = Repositorio(caminho)
    repo.salvar_curso(curso)
    disciplina = Disciplina("ALG101", "Algoritmos", 60, curso)
    repo.salvar_disciplina(disciplina)
    aluno = Aluno(
        "Ana", "2000-01-01", "ana@aluno.uniesquina.edu.br", "999", "A1", curso.nome
    )
    repo.salvar_aluno(aluno)
    turma = Turma("T1", disciplina, "Prof", "2026.2", 2)
    repo.salvar_turma(turma)
    matricula = Matricula(aluno, turma, repo.configuracoes)
    matricula.nota_1 = matricula.nota_2 = 9
    matricula.frequencia = 90
    repo.salvar_matricula(matricula)
    repo.fechar()

    repo = Repositorio(caminho)
    recuperada = repo.buscar_aluno("A1").matriculas[0]
    assert recuperada.turma.disciplina.codigo == "ALG101"
    assert recuperada.status == Matricula.APROVADO
    assert recuperada.frequencia_lancada
    assert repo.buscar_turma("T1").lista_alunos[0].matricula == "A1"
    dados_alunos = json.loads((caminho / "alunos.json").read_text(encoding="utf-8"))
    assert dados_alunos[0]["matriculas"][0]["turma"] == "T1"
    assert not (caminho / "matriculas.json").exists()
    assert not (caminho / "monitorias.json").exists()
    repo.fechar()
