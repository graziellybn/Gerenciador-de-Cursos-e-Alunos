import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from database.repositorio import Repositorio
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma


@pytest.fixture
def aluno():
	return Aluno(
		"Grazielly Bibiano",
		"2000-01-01",
		"grazielly@aluno.uniesquina.edu.br",
		"88999999999",
		"2026001",
		"Engenharia de Software",
	)


@pytest.fixture
def curso():
	return Curso("ES001", "Engenharia de Software")


@pytest.fixture
def disciplina(curso):
	return Disciplina("POO101", "Programação Orientada a Objetos", 60, curso)


@pytest.fixture
def turma(disciplina):
	return Turma("T01", disciplina, "Jayr Alencar", "2026.2", vagas=2)


@pytest.fixture
def matricula(aluno, turma):
	return Matricula(aluno, turma)


@pytest.fixture
def turma_com_horario(disciplina):
	"""Turma de 2 vagas às terças e quintas, 10h-12h (para testar choque)."""
	return Turma(
		"T02", disciplina, "Jayr Alencar", "2026.2", vagas=2,
		horario={"ter": "10:00-12:00", "qui": "10:00-12:00"},
	)


@pytest.fixture
def fabrica_aluno():
	"""Cria alunos distintos: fabrica_aluno('2026002', 'Ana')."""
	def _criar(matricula: str, nome: str = "Aluno Teste") -> Aluno:
		return Aluno(
			nome, "2000-01-01", f"{matricula}@aluno.uniesquina.edu.br", "88999999999",
			matricula, "Engenharia de Software",
		)
	return _criar


@pytest.fixture
def repo():
	"""Repositório JSON em memória, novo a cada teste."""
	r = Repositorio(":memory:")
	yield r
	r.fechar()