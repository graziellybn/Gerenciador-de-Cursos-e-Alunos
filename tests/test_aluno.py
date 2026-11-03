import pytest
from models import ValidacaoError
from models.adm import Adm
from models.aluno import Aluno
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma


def test_email_invalido():
    with pytest.raises(ValidacaoError):
        Aluno("Ana", "2000-01-01", "ana-sem-arroba", "1", "1", "ES")
    with pytest.raises(ValidacaoError, match="aluno.uniesquina.edu.br"):
        Aluno("Ana", "2000-01-01", "ana@example.com", "1", "1", "ES")
    with pytest.raises(ValidacaoError, match="adm.uniesquina.edu.br"):
        Adm("Admin", "", "admin@example.com", "1")


def test_cr_ponderado_pela_carga_horaria(aluno):
    forte = Turma("A", Disciplina("C1", "Disciplina 1", 60, "ES001"), "P", "2026.1", 5)
    fraca = Turma("B", Disciplina("C2", "Disciplina 2", 30, "ES001"), "P", "2026.1", 5)
    for turma, nota in ((forte, 10), (fraca, 4)):
        m = Matricula(aluno, turma)
        m.nota_1 = m.nota_2 = nota
        m.atualizar_status()
        aluno.registrar_matricula(m)
    assert aluno.recalcular_cr() == pytest.approx(8.0)   # (10*60 + 4*30) / 90