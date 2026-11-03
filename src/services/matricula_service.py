"""Regras de negócio e autorização para matrículas, notas e trancamentos."""

from datetime import date

from database.repositorio import Repositorio
from models import (
    ChoqueHorarioError,
    DuplicidadeError,
    LimiteTurmasError,
    NaoEncontradoError,
    PreRequisitoNaoCumpridoError,
    TurmaFechadaError,
    ValidacaoError,
)
from models.adm import Adm
from models.aluno import Aluno
from models.matricula import Matricula
from services.auth_service import exigir_administrador, exigir_aluno_proprio


class MatriculaService:
    """Orquestra o ciclo de vida acadêmico das matrículas."""

    def __init__(self, repo: Repositorio, configuracoes=None, max_turmas_por_aluno=None):
        self._repo = repo
        self._config = configuracoes or repo.configuracoes
        self._max_turmas = (
            max_turmas_por_aluno
            if max_turmas_por_aluno is not None
            else self._config.max_turmas_por_aluno
        )

    def matricular(self, matricula_aluno: str, id_oferta: str, sessao=None) -> Matricula:
        if isinstance(getattr(sessao, "pessoa", None), Adm):
            exigir_administrador(sessao)
        else:
            exigir_aluno_proprio(sessao, matricula_aluno)

        with self._repo.transacao():
            aluno = self._repo.buscar_aluno(matricula_aluno)
            if aluno is None:
                raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
            turma = self._repo.buscar_turma(id_oferta)
            if turma is None:
                raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
            if not turma.aberta:
                raise TurmaFechadaError(f"A turma {id_oferta} está fechada para matrículas.")
            if any(m.turma.id_oferta == id_oferta for m in aluno.matriculas):
                raise DuplicidadeError("O aluno já está matriculado nesta turma.")
            self._validar_pre_requisitos(aluno, turma)
            self._validar_limite(aluno, turma)
            self._validar_choque(aluno, turma)

            turma.adicionar_aluno(aluno)
            matricula = Matricula(aluno, turma, self._config)
            self._repo.salvar_matricula(matricula)
            aluno.registrar_matricula(matricula)
            return matricula

    def _validar_pre_requisitos(self, aluno: Aluno, turma) -> None:
        faltando = [
            codigo for codigo in turma.disciplina.pre_requisitos
            if not any(
                aluno.aprovou(equivalente)
                for equivalente in self._repo.codigos_equivalentes(codigo)
            )
        ]
        if faltando:
            raise PreRequisitoNaoCumpridoError(
                f"Pré-requisito(s) não cumprido(s): {', '.join(faltando)}."
            )

    def _validar_limite(self, aluno: Aluno, turma) -> None:
        if self._max_turmas is None:
            return
        ativas = [
            m for m in aluno.matriculas
            if m.turma.periodo == turma.periodo and m.status == Matricula.CURSANDO
        ]
        if len(ativas) >= self._max_turmas:
            raise LimiteTurmasError(
                f"Limite de {self._max_turmas} turmas por período atingido."
            )

    @staticmethod
    def _validar_choque(aluno: Aluno, turma) -> None:
        for matricula in aluno.matriculas:
            if matricula.status == Matricula.TRANCADO:
                continue
            if matricula.turma.conflita_com(turma):
                raise ChoqueHorarioError(
                    f"Choque de horário com a turma {matricula.turma.id_oferta} "
                    f"({matricula.turma.disciplina.nome})."
                )

    def matricular_proprio_aluno(self, sessao, id_oferta: str) -> Matricula:
        aluno = exigir_aluno_proprio(sessao)
        return self.matricular(aluno.matricula, id_oferta, sessao=sessao)

    def trancar(self, matricula_aluno: str, id_oferta: str, sessao, quando: date = None) -> Matricula:
        if isinstance(getattr(sessao, "pessoa", None), Adm):
            exigir_administrador(sessao)
        else:
            exigir_aluno_proprio(sessao, matricula_aluno)
        quando = quando or date.today()
        if not isinstance(quando, date):
            raise ValidacaoError("A data de trancamento deve ser uma data YYYY-MM-DD válida.")
        if quando > self._config.data_limite_trancamento:
            raise ValidacaoError(
                f"O prazo para trancamento terminou em "
                f"{self._config.data_limite_trancamento.isoformat()}."
            )
        with self._repo.transacao():
            registros = self._repo.matriculas_de_aluno(matricula_aluno)
            matricula = next((m for m in registros if m.turma.id_oferta == id_oferta), None)
            if matricula is None:
                raise NaoEncontradoError("Matrícula não encontrada para esse aluno e turma.")
            matricula.trancar(quando)
            self._repo.trancar_matricula(matricula, quando)
            return matricula

    def lancar_notas(
        self, matricula_aluno: str, id_oferta: str, nota_1: float,
        nota_2: float, frequencia: float, sessao,
    ) -> Matricula:
        exigir_administrador(sessao)
        with self._repo.transacao():
            registros = self._repo.matriculas_da_turma(id_oferta)
            matricula = next(
                (m for m in registros if m.aluno.matricula == matricula_aluno), None
            )
            if matricula is None:
                raise NaoEncontradoError("Matrícula não encontrada nessa turma.")
            if matricula.status == Matricula.TRANCADO:
                raise ValidacaoError("Não é possível lançar notas em matrícula trancada.")
            matricula.nota_1 = nota_1
            matricula.nota_2 = nota_2
            matricula.frequencia = frequencia
            matricula.atualizar_status(self._config)
            self._repo.atualizar_matricula(matricula)

            aluno = self._repo.buscar_aluno(matricula_aluno)
            historico = next(m for m in aluno.matriculas if m.turma.id_oferta == id_oferta)
            historico.nota_1 = nota_1
            historico.nota_2 = nota_2
            historico.frequencia = frequencia
            historico.atualizar_status(self._config)
            aluno.recalcular_cr()
            self._repo.atualizar_aluno(aluno)
            return matricula

    def historico_proprio(self, sessao) -> list[Matricula]:
        aluno = exigir_aluno_proprio(sessao)
        return self._repo.matriculas_de_aluno(aluno.matricula)
