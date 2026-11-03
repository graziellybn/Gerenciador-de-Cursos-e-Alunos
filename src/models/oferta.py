from models import ValidacaoError


class Oferta:
    """Base para uma turma ou oferta de disciplina com capacidade e estado de matrícula."""

    def __init__(self, id_oferta, disciplina, professor, periodo, vagas):
        """Cria a oferta validando identificador, disciplina, período e capacidade."""
        if id_oferta is None or not str(id_oferta).strip():
            raise ValidacaoError("O id da oferta não pode estar em branco.")
        if disciplina is None:
            raise ValidacaoError("A oferta precisa de uma disciplina.")
        if not isinstance(periodo, str) or not periodo.strip():
            raise ValidacaoError("O período não pode estar em branco.")
        self.id_oferta = str(id_oferta).strip()
        self.disciplina = disciplina
        self.professor = professor
        self.periodo = periodo.strip()
        self._aberta = True
        self.vagas = vagas

    @property
    def vagas(self) -> int:
        """Retorna a capacidade total da oferta."""
        return self._vagas

    @vagas.setter
    def vagas(self, valor: int):
        """Valida que a quantidade de vagas seja inteira e compatível com a ocupação."""
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValidacaoError("O número de vagas deve ser um inteiro maior ou igual a zero.")
        if valor < self.ocupacao:
            raise ValidacaoError("As vagas não podem ficar abaixo do número de alunos matriculados.")
        self._vagas = valor

    @property
    def ocupacao(self) -> int:
        """Quantidade de vagas ocupadas. A subclasse define esse cálculo."""
        return 0

    @property
    def vagas_disponiveis(self) -> int:
        """Calcula o número de vagas remanescentes da oferta."""
        return self.vagas - self.ocupacao

    @property
    def aberta(self) -> bool:
        """Indica se a oferta aceita novas matrículas."""
        return self._aberta

    def abrir(self) -> None:
        """Reabre a oferta para matrícula."""
        self._aberta = True

    def fechar(self) -> None:
        """Fecha a oferta e impede novas inscrições."""
        self._aberta = False

    def tem_vagas_disponiveis(self) -> bool:
        """Retorna True quando ainda há vagas disponíveis."""
        return self.vagas_disponiveis > 0

    def __str__(self) -> str:
        """Gera uma representação resumida da oferta para uso em console e relatórios."""
        return f"Oferta {self.id_oferta} - {self.disciplina} ({self.periodo}) | Vagas: {self.vagas}"