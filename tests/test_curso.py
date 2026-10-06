import pytest


def test_criar_curso_com_valores_padrao(curso):
	assert curso.codigo == "POO101"
	assert curso.nome == "Programação Orientada a Objetos"
	assert curso.carga_horaria == 60
	assert curso.tipo == "Obrigatória"
	assert curso.pre_requisitos == []


def test_curso_adiciona_pre_requisito_sem_repetir(curso):
	curso.adicionar_pre_requisito("ALG101")
	curso.adicionar_pre_requisito("ALG101")

	assert curso.pre_requisitos == ["ALG101"]
	assert str(curso) == "POO101 - Programação Orientada a Objetos (60h) | Obrigatória"


def test_curso_rejeita_carga_horaria_invalida():
	from models.curso import Curso

	with pytest.raises(ValueError):
		Curso("POO101", "POO", 0)
