import pytest

from models.aluno import Aluno


def test_criar_manipular_e_ordenar_aluno(aluno):
	assert aluno.nome_completo == "Grazielly Bibiano"
	assert aluno.matricula == "2026001"
	assert aluno.curso == "Engenharia de Software"
	assert aluno.cr == 0.0
	assert aluno.status == "Ativo"
	aluno.cr = 8.5
	assert aluno.cr == 8.5

	outro = Aluno("Zoe Ferreira", "2000-01-01", "zoe@ufca.edu.br", "1", "2", "Curso", cr=9.0)
	assert aluno < outro
	outro.cr = 8.5
	assert aluno < outro  # Mesmo CR: desempata pelo nome.
	assert "Grazielly Bibiano" in str(aluno)


def test_aluno_rejeita_cr_invalido_e_herda_validacoes_de_pessoa(aluno):
	with pytest.raises(ValueError):
		aluno.cr = -1

	with pytest.raises(ValueError):
		Aluno("Grazielly Bibiano", "2000-01-01", "email-invalido", "1", "3", "Curso")

