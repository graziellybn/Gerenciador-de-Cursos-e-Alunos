"""Operações administrativas sobre ofertas de turma."""

from database.repositorio import Repositorio
from models import ChoqueHorarioError, NaoEncontradoError
from models.matricula import Matricula
from models.turma import Turma
from services.auth_service import exigir_administrador


class TurmaService:
    def __init__(self, repo: Repositorio):
        self._repo = repo

    def cadastrar_turma(self, turma: Turma, sessao=None) -> Turma:
        exigir_administrador(sessao)
        disciplina = self._repo.buscar_disciplina(turma.disciplina.codigo)
        if disciplina is None:
            raise NaoEncontradoError(f"Disciplina {turma.disciplina.codigo} não encontrada.")
        self._repo.salvar_turma(turma)
        return turma

    def atualizar_turma(self, turma: Turma, sessao=None) -> Turma:
        exigir_administrador(sessao)
        if self._repo.buscar_turma(turma.id_oferta, com_alunos=False) is None:
            raise NaoEncontradoError(f"Turma {turma.id_oferta} não encontrada.")
        for matricula in self._repo.matriculas_da_turma(turma.id_oferta):
            if matricula.status == Matricula.TRANCADO:
                continue
            for outra in self._repo.matriculas_de_aluno(matricula.aluno.matricula):
                if outra.turma.id_oferta == turma.id_oferta or outra.status == Matricula.TRANCADO:
                    continue
                if turma.conflita_com(outra.turma):
                    raise ChoqueHorarioError(
                        f"A alteração conflita com a turma {outra.turma.id_oferta} "
                        f"do aluno {matricula.aluno.matricula}."
                    )
        self._repo.atualizar_turma(turma)
        return turma
