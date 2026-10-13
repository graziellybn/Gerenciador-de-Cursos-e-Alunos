class Matricula:
    def __init__(self, aluno, turma):
        self.aluno = aluno
        self.turma = turma
        self._nota_1 = 0.0
        self._nota_2 = 0.0
        self._frequencia = 100.0
        self.status = "Cursando"

    def __eq__(self, outra: object) -> bool:
        if not isinstance(outra, Matricula):
            return False
        return (
            self.aluno.matricula == outra.aluno.matricula
            and self.turma.id_oferta == outra.turma.id_oferta
        )

    @property
    def nota_1(self) -> float:
        return self._nota_1

    @nota_1.setter
    def nota_1(self, valor: float):
        if not isinstance(valor, (int, float)) or not (0.0 <= valor <= 10.0):
            raise ValueError("A nota deve ser um número entre 0.0 e 10.0.")
        self._nota_1 = float(valor)

    @property
    def nota_2(self) -> float:
        return self._nota_2

    @nota_2.setter
    def nota_2(self, valor: float):
        if not isinstance(valor, (int, float)) or not (0.0 <= valor <= 10.0):
            raise ValueError("A nota deve ser um número entre 0.0 e 10.0.")
        self._nota_2 = float(valor)

    @property
    def frequencia(self) -> float:
        return self._frequencia

    @frequencia.setter
    def frequencia(self, valor: float):
        if not isinstance(valor, (int, float)) or not (0.0 <= valor <= 100.0):
            raise ValueError("A frequência deve ser um percentual entre 0.0 e 100.0.")
        self._frequencia = float(valor)

    def calcular_media(self) -> float:
        return (self.nota_1 + self.nota_2) / 2

    def atualizar_status(self):
        media = self.calcular_media()
        if media >= 7.0 and self.frequencia >= 75.0:
            self.status = "Aprovado"
        else:
            self.status = "Reprovado"

    def __str__(self) -> str:
        return (
            f"Matrícula: {self.aluno.nome_completo} em {self.turma.disciplina.nome} | "
            f"Média: {self.calcular_media():.1f} | Frequência: {self.frequencia:.0f}% | Status: {self.status}"
        )