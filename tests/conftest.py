import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from models.aluno import Aluno
from models.curso import Curso
from models.matricula import Matricula
from models.turma import Turma


@pytest.fixture
def aluno():
	return Aluno(
		"Grazielly Bibiano",
		"2000-01-01",
		"grazielly@ufca.edu.br",
		"88999999999",
		"2026001",
		"Engenharia de Software",
	)


@pytest.fixture
def curso():
	return Curso("POO101", "Programação Orientada a Objetos", 60)


@pytest.fixture
def turma(curso):
	return Turma("T01", curso, "Jayr Alencar", "2026.2", vagas=2)


@pytest.fixture
def matricula(aluno, turma):
	return Matricula(aluno, turma)