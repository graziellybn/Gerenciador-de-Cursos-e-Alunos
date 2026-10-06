import pytest


def test_turma_adiciona_remove_e_impede_duplicata(turma, aluno):
	assert len(turma) == 0

	assert turma.adicionar_aluno(aluno)
	assert len(turma) == 1
	assert turma.vagas == 1
	assert not turma.adicionar_aluno(aluno)

	assert turma.remover_aluno(aluno)
	assert len(turma) == 0
	assert turma.vagas == 2


def test_turma_valida_vagas_e_bloqueia_turma_sem_vagas(turma, aluno):
	turma.vagas = 0

	assert not turma.adicionar_aluno(aluno)
	assert len(turma) == 0
	with pytest.raises(ValueError):
		turma.vagas = -1


def test_turma_rejeita_remover_aluno_nao_matriculado(turma, aluno):
	with pytest.raises(ValueError):
		turma.remover_aluno(aluno)
