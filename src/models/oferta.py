class Oferta:
    def __init__(self, id_oferta, disciplina, professor, periodo, vagas):
        self.id_oferta = id_oferta
        self.disciplina = disciplina
        self.professor = professor
        self.periodo = periodo
        self.vagas = vagas

    @property
    def vagas(self) -> int:
        return self._vagas

    @vagas.setter
    def vagas(self, valor: int):
        if not isinstance(valor, int) or valor < 0:
            raise ValueError("O número de vagas deve ser um inteiro maior ou igual a zero.")
        self._vagas = valor

    def tem_vagas_disponiveis(self) -> bool:
        return self.vagas > 0

    def __str__(self) -> str:
        return f"Oferta {self.id_oferta} - {self.disciplina} ({self.periodo}) | Vagas: {self.vagas}"