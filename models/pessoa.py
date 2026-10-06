import re


class Pessoa:
    def __init__(self, nome_completo: str, data_nascimento: str, email: str, telefone: str):
        self.nome_completo = nome_completo
        self.data_nascimento = data_nascimento
        self.email = email
        self.telefone = telefone

    @property
    def nome_completo(self) -> str:
        return self._nome_completo

    @nome_completo.setter
    def nome_completo(self, valor: str):
        if not valor or not valor.strip():
            raise ValueError("O nome completo não pode estar em branco.")
        self._nome_completo = valor.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str):
        padrao_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not valor or not re.match(padrao_email, valor.strip()):
            raise ValueError(
                "E-mail inválido. O formato correto deve ser 'usuario@dominio.com'."
            )

        self._email = valor.strip().lower()

    def __str__(self) -> str:
        return f"{self.nome_completo} ({self.email})"