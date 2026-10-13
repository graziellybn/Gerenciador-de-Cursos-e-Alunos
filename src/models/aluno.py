from models.pessoa import Pessoa


class Aluno(Pessoa):
    def __init__(self, nome_completo: str, data_nascimento: str, email: str, telefone: str,
    matricula: str, curso, cr: float = 0.0, status: str = "Ativo"):
        super().__init__(nome_completo, data_nascimento, email, telefone)

        self.matricula = matricula
        self.curso = curso
        self.cr = cr
        self.status = status

    @property
    def cr(self) -> float:
        return self._cr

    @cr.setter
    def cr(self, valor: float):
        if not isinstance(valor, (int, float)) or not (0.0 <= valor <= 10.0):
            raise ValueError("O CR deve ser um número entre 0.0 e 10.0.")
        self._cr = float(valor)

    def __lt__(self, outro: "Aluno") -> bool:
        if not isinstance(outro, Aluno):
            return NotImplemented
        if self.cr == outro.cr:
            return self.nome_completo < outro.nome_completo
        return self.cr < outro.cr

    def __str__(self) -> str:
        return f"Aluno: {self.nome_completo} | Matrícula: {self.matricula} | CR: {self.cr:.2f}"
from models.pessoa import Pessoa


