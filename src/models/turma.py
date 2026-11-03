import re

from models import DuplicidadeError, TurmaFechadaError, TurmaLotadaError, ValidacaoError
from models.oferta import Oferta

_PADRAO_INTERVALO = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")
DIAS_VALIDOS = ("seg", "ter", "qua", "qui", "sex", "sab")


class Turma(Oferta):
    """Oferta concreta de uma disciplina, com horários e alunos matriculados.

    Relações: Turma -> Curso (disciplina) e Turma <-> Aluno (lista_alunos / Matricula).
    Cuidado: `__len__` conta alunos; uma turma vazia é "falsa" em `if turma:`.
    Use sempre `if turma is not None`.
    """

    def __init__(self, id_oferta: str, disciplina, professor: str, periodo: str,
                 vagas: int, horario=None, local: str = None):
        self._lista_alunos = []         # antes do super(): vagas valida a ocupação
        super().__init__(id_oferta, disciplina, professor, periodo, vagas)
        self.horario = horario
        self.local = local

    # ---------- horários ----------
    @property
    def horario(self) -> dict:
        """Dict {'ter': '10:00-12:00', ...} (cópia)."""
        return dict(self._horario)

    @horario.setter
    def horario(self, valor):
        if valor in (None, ""):
            self._horario = {}
            return
        if not isinstance(valor, dict):
            raise ValidacaoError("O horário deve ser um dict como {'ter': '10:00-12:00'}.")
        normalizado = {}
        for dia, intervalo in valor.items():
            dia = str(dia).strip().lower()
            if dia not in DIAS_VALIDOS:
                raise ValidacaoError(f"Dia inválido: {dia!r}. Use {', '.join(DIAS_VALIDOS)}.")
            self._converter_intervalo(intervalo)      # só valida
            if dia in normalizado:
                raise ValidacaoError(f"Dia duplicado no horário: {dia}.")
            normalizado[dia] = intervalo.strip()
        self._horario = normalizado

    @staticmethod
    def _converter_intervalo(texto: str) -> tuple:
        """'10:00-12:00' -> (600, 720) minutos desde 00:00."""
        correspondencia = _PADRAO_INTERVALO.match(texto.strip()) if isinstance(texto, str) else None
        if not correspondencia:
            raise ValidacaoError(f"Horário inválido: {texto!r}. Use 'HH:MM-HH:MM'.")
        h1, m1, h2, m2 = (int(g) for g in correspondencia.groups())
        if h1 > 23 or h2 > 23 or m1 > 59 or m2 > 59:
            raise ValidacaoError(f"Horário inválido: {texto!r}.")
        inicio, fim = h1 * 60 + m1, h2 * 60 + m2
        if fim <= inicio:
            raise ValidacaoError("O horário final deve ser maior que o inicial.")
        return inicio, fim

    @property
    def intervalos(self) -> tuple:
        """Tuplas comparáveis (dia, inicio_min, fim_min)."""
        return tuple((d, *self._converter_intervalo(i)) for d, i in self._horario.items())

    def conflita_com(self, outra: "Turma") -> bool:
        """True se há sobreposição no mesmo período e dia.

        Intervalos que apenas se encostam (10-12 e 12-14) NÃO conflitam.
        """
        if self.periodo != outra.periodo:
            return False
        for dia_a, ini_a, fim_a in self.intervalos:
            for dia_b, ini_b, fim_b in outra.intervalos:
                if dia_a == dia_b and ini_a < fim_b and ini_b < fim_a:
                    return True
        return False

    # ---------- alunos ----------
    @property
    def ocupacao(self) -> int:
        return len(self._lista_alunos)

    @property
    def lista_alunos(self) -> tuple:
        """Alunos ativos na turma; a coleção retornada não permite alteração externa."""
        return tuple(self._lista_alunos)

    def adicionar_aluno(self, aluno) -> bool:
        """Adiciona o aluno. Lança TurmaFechadaError, DuplicidadeError ou TurmaLotadaError."""
        if not self.aberta:
            raise TurmaFechadaError(f"A turma {self.id_oferta} está fechada para matrículas.")
        if aluno in self._lista_alunos:
            raise DuplicidadeError(f"O aluno {aluno.nome_completo} já está matriculado na turma.")
        if not self.tem_vagas_disponiveis():
            raise TurmaLotadaError(
                f"Não é possível adicionar {aluno.nome_completo}: turma {self.id_oferta} lotada."
            )
        self._lista_alunos.append(aluno)
        return True

    def remover_aluno(self, aluno) -> bool:
        """Remove o aluno. Lança ValidacaoError se ele não estiver na turma."""
        if aluno not in self._lista_alunos:
            raise ValidacaoError("O aluno não está matriculado na turma.")
        self._lista_alunos.remove(aluno)
        return True

    def __len__(self) -> int:
        return len(self._lista_alunos)

    def __repr__(self) -> str:
        return (
            f"Turma(id_oferta={self.id_oferta!r}, disciplina={self.disciplina.codigo!r}, "
            f"periodo={self.periodo!r}, ocupacao={self.ocupacao}, vagas={self.vagas})"
        )

    def __str__(self) -> str:
        return f"Turma {self.id_oferta} - {self.disciplina} | Matriculados: {len(self)}/{self.vagas}"