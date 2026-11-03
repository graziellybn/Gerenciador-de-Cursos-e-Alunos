import re
from datetime import date

from models import PermissaoNegadaError, ValidacaoError


class ComPermissoes:
    """Mixin para representar as ações permitidas por um perfil do sistema."""

    PERMISSOES: frozenset = frozenset()

    def tem_permissao(self, acao: str) -> bool:
        """Retorna True quando a ação solicitada está na lista de permissões."""
        return acao in self.PERMISSOES

    def exigir_permissao(self, acao: str) -> None:
        """Levanta erro quando a pessoa tenta executar uma ação não autorizada."""
        if not self.tem_permissao(acao):
            raise PermissaoNegadaError(
                f"{self.__class__.__name__} não tem permissão para: {acao}."
            )


class Pessoa:
    """Base para dados pessoais de alunos, administradores e outras entidades humanas."""

    _PADRAO_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    def __init__(self, nome_completo: str, data_nascimento: str, email: str, telefone: str):
        """Cria a pessoa validando dados pessoais básicos e o contato eletrônico."""
        self.nome_completo = nome_completo
        self.data_nascimento = data_nascimento
        self.email = email
        self.telefone = telefone

    @property
    def nome_completo(self) -> str:
        """Retorna o nome da pessoa já normalizado."""
        return self._nome_completo

    @nome_completo.setter
    def nome_completo(self, valor: str):
        """Valida que o nome da pessoa não fique em branco."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O nome completo não pode estar em branco.")
        self._nome_completo = valor.strip()

    @property
    def email(self) -> str:
        """Retorna o e-mail em minúsculas e validado."""
        return self._email

    @email.setter
    def email(self, valor: str):
        """Valida o formato do e-mail e padroniza a caixa da string."""
        if not isinstance(valor, str) or not self._PADRAO_EMAIL.match(valor.strip()):
            raise ValidacaoError(
                "E-mail inválido. O formato correto deve ser 'usuario@dominio.com'."
            )
        email = valor.strip().lower()
        dominio = getattr(type(self), "DOMINIO_EMAIL", None)
        if dominio and not email.endswith(f"@{dominio}"):
            raise ValidacaoError(f"O e-mail deve terminar com @{dominio}.")
        self._email = email

    @property
    def data_nascimento(self) -> str:
        """Retorna a data de nascimento em formato ISO."""
        return self._data_nascimento

    @data_nascimento.setter
    def data_nascimento(self, valor: str) -> None:
        """Valida a data e evita vazios ou valores futuros."""
        if valor in (None, ""):
            self._data_nascimento = ""
            return
        if not isinstance(valor, str):
            raise ValidacaoError("A data de nascimento deve usar o formato YYYY-MM-DD.")
        try:
            data = date.fromisoformat(valor.strip())
        except ValueError as erro:
            raise ValidacaoError("A data de nascimento deve ser válida e usar YYYY-MM-DD.") from erro
        if data.isoformat() != valor.strip() or data > date.today():
            raise ValidacaoError("A data de nascimento deve ser YYYY-MM-DD e não pode estar no futuro.")
        self._data_nascimento = data.isoformat()

    def __str__(self) -> str:
        """Fornece uma representação curta para logs e exibição textual."""
        return f"{self.nome_completo} ({self.email})"

    def __repr__(self) -> str:
        """Ajuda na depuração e nos testes com uma visão resumida da pessoa."""
        return f"{self.__class__.__name__}(nome_completo={self.nome_completo!r}, email={self.email!r})"