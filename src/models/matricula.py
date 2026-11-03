from models import ValidacaoError
from datetime import date
from config import Configuracoes


def _validar_faixa(valor, minimo: float, maximo: float, mensagem: str) -> float:
    # bool é subclasse de int: True/False não podem virar nota
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not (minimo <= valor <= maximo):
        raise ValidacaoError(mensagem)
    return float(valor)


class Matricula:
    """Relaciona um Aluno a uma Turma, com notas, frequência e status."""

    CURSANDO = "Cursando"
    APROVADO = "Aprovado"
    REPROVADO_POR_NOTA = "Reprovado por nota"
    REPROVADO = REPROVADO_POR_NOTA  # Compatibilidade com código anterior.
    REPROVADO_POR_FREQUENCIA = "Reprovado por frequência"
    REPROVADO_POR_NOTA_E_FREQUENCIA = "Reprovado por nota e frequência"
    TRANCADO = "Trancado"
    SITUACOES_FINAIS = frozenset({
        APROVADO, REPROVADO, REPROVADO_POR_NOTA, REPROVADO_POR_FREQUENCIA,
        REPROVADO_POR_NOTA_E_FREQUENCIA,
    })

    def __init__(self, aluno, turma, configuracoes: Configuracoes = None):
        self.aluno = aluno
        self.turma = turma
        self.configuracoes = configuracoes or Configuracoes()
        self._nota_1 = 0.0
        self._nota_2 = 0.0
        self._frequencia = 100.0
        self._frequencia_lancada = False
        self._lancadas = set()
        self._status = self.CURSANDO
        self.data_trancamento: date | None = None

    def __eq__(self, outra: object) -> bool:
        if not isinstance(outra, Matricula):
            return False
        return (
            self.aluno.matricula == outra.aluno.matricula
            and self.turma.id_oferta == outra.turma.id_oferta
        )

    def __hash__(self) -> int:
        return hash((self.aluno.matricula, self.turma.id_oferta))

    @property
    def nota_1(self) -> float:
        return self._nota_1

    @nota_1.setter
    def nota_1(self, valor: float):
        self._nota_1 = _validar_faixa(valor, 0.0, 10.0, "A nota deve ser um número entre 0.0 e 10.0.")
        self._lancadas.add("nota_1")
        self.atualizar_status()

    @property
    def nota_2(self) -> float:
        return self._nota_2

    @nota_2.setter
    def nota_2(self, valor: float):
        self._nota_2 = _validar_faixa(valor, 0.0, 10.0, "A nota deve ser um número entre 0.0 e 10.0.")
        self._lancadas.add("nota_2")
        self.atualizar_status()

    @property
    def frequencia(self) -> float:
        return self._frequencia

    @frequencia.setter
    def frequencia(self, valor: float):
        self._frequencia = _validar_faixa(
            valor, 0.0, 100.0, "A frequência deve ser um percentual entre 0.0 e 100.0."
        )
        self._frequencia_lancada = True
        self.atualizar_status()

    @property
    def frequencia_lancada(self) -> bool:
        """Indica se a frequência foi informada, em vez de usar o valor padrão."""
        return self._frequencia_lancada

    @staticmethod
    def _normalizar_status(valor: str) -> str:
        if not isinstance(valor, str):
            raise ValidacaoError(f"Situação acadêmica inválida: {valor!r}.")
        mapa = {
            "CURSANDO": "Cursando",
            "Cursando": "Cursando",
            "APROVADO": "Aprovado",
            "Aprovado": "Aprovado",
            "REPROVADO": Matricula.REPROVADO_POR_NOTA,
            "Reprovado": Matricula.REPROVADO_POR_NOTA,
            "REPROVADO_POR_NOTA": Matricula.REPROVADO_POR_NOTA,
            "Reprovado por nota": Matricula.REPROVADO_POR_NOTA,
            "REPROVADO_POR_FREQUENCIA": "Reprovado por frequência",
            "Reprovado por frequência": "Reprovado por frequência",
            "REPROVADO_POR_NOTA_E_FREQUENCIA": "Reprovado por nota e frequência",
            "Reprovado por nota e frequência": "Reprovado por nota e frequência",
            "TRANCADO": "Trancado",
            "Trancado": "Trancado",
        }
        normalizado = mapa.get(valor.strip(), valor.strip())
        if normalizado not in (Matricula.CURSANDO, Matricula.APROVADO, Matricula.REPROVADO,
                               Matricula.REPROVADO_POR_FREQUENCIA,
                               Matricula.REPROVADO_POR_NOTA_E_FREQUENCIA, Matricula.TRANCADO):
            raise ValidacaoError(f"Situação acadêmica inválida: {valor!r}.")
        return normalizado

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, valor: str) -> None:
        valor = self._normalizar_status(valor)
        estados = self.SITUACOES_FINAIS | {self.CURSANDO, self.TRANCADO}
        if valor not in estados:
            raise ValidacaoError(f"Situação acadêmica inválida: {valor!r}.")
        if valor in self.SITUACOES_FINAIS and not self.notas_lancadas:
            raise ValidacaoError("Uma situação final exige o lançamento das duas notas.")
        if valor == self.TRANCADO and self.data_trancamento is None:
            raise ValidacaoError("Uma matrícula trancada precisa registrar a data do trancamento.")
        if valor != self.TRANCADO and self.data_trancamento is not None:
            raise ValidacaoError("Somente matrículas trancadas podem ter data de trancamento.")
        self._status = valor

    @property
    def nota_1_lancada(self) -> bool:
        return "nota_1" in self._lancadas

    @property
    def nota_2_lancada(self) -> bool:
        return "nota_2" in self._lancadas

    @property
    def notas_lancadas(self) -> bool:
        return self.nota_1_lancada and self.nota_2_lancada

    def calcular_media(self) -> float:
        return (self.nota_1 + self.nota_2) / 2

    def atualizar_status(
        self,
        configuracoes: Configuracoes = None,
        *,
        nota_minima: float = None,
        frequencia_minima: float = None,
    ) -> str:
        """Atualiza situação; reprovação simultânea ganha estado explícito próprio."""
        if self.status == self.TRANCADO:
            return self.status
        if not self.notas_lancadas:
            self.status = self.CURSANDO
            return self.status
        config = configuracoes or self.configuracoes
        if nota_minima is None:
            nota_minima = config.nota_minima_aprovacao
        if frequencia_minima is None:
            frequencia_minima = config.frequencia_minima
        nota_insuficiente = self.calcular_media() < nota_minima
        frequencia_insuficiente = self.frequencia < frequencia_minima
        if not nota_insuficiente and not frequencia_insuficiente:
            self.status = self.APROVADO
        elif nota_insuficiente and frequencia_insuficiente:
            self.status = self.REPROVADO_POR_NOTA_E_FREQUENCIA
        elif nota_insuficiente:
            self.status = self.REPROVADO_POR_NOTA
        else:
            self.status = self.REPROVADO_POR_FREQUENCIA
        return self.status

    def trancar(self, quando: date) -> None:
        if self.status != self.CURSANDO:
            raise ValidacaoError("Somente uma matrícula cursando pode ser trancada.")
        if not isinstance(quando, date):
            raise ValidacaoError("A data de trancamento deve ser uma data válida.")
        self.data_trancamento = quando
        self.status = self.TRANCADO

    def __str__(self) -> str:
        return (
            f"Matrícula: {self.aluno.nome_completo} em {self.turma.disciplina.nome} | "
            f"Média: {self.calcular_media():.1f} | Frequência: {self.frequencia:.0f}% | Status: {self.status}"
        )

    def __repr__(self) -> str:
        return f"Matricula(aluno={self.aluno.matricula!r}, turma={self.turma.id_oferta!r}, status={self.status!r})"