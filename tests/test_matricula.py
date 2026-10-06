import pytest

from models.matricula import Matricula


def test_criar_matricula_com_valores_padrao(matricula):
	assert matricula.nota_1 == 0.0
	assert matricula.nota_2 == 0.0
	assert matricula.frequencia == 100.0
	assert matricula.status == "Cursando"
	assert "Grazielly Bibiano" in str(matricula)


def test_matriculas_com_mesmo_aluno_e_turma_sao_iguais(matricula):
	outro = Matricula(matricula.aluno, matricula.turma)

	assert matricula == outro
	assert matricula != object()


def test_matricula_calcula_media_e_aprova(matricula):
	matricula.nota_1 = 8
	matricula.nota_2 = 6
	matricula.atualizar_status()

	assert matricula.calcular_media() == 7.0
	assert matricula.status == "Aprovado"


def test_matricula_rejeita_nota_e_frequencia_invalidas(matricula):
	with pytest.raises(ValueError):
		matricula.nota_1 = 10.1

	with pytest.raises(ValueError):
		matricula.frequencia = 100.1


def test_matricula_reprova_quando_frequencia_fica_abaixo_do_minimo(matricula):
	matricula.nota_1 = 10
	matricula.nota_2 = 10
	matricula.frequencia = 74.9
	matricula.atualizar_status()

	assert matricula.status == "Reprovado"
