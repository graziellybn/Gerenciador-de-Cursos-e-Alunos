from models import ValidacaoError


class Curso:
    """Representa um curso de graduação e seu identificador principal."""

    def __init__(self, codigo: str, nome: str):
        """Cria um curso validando código e nome antes de guardar os dados."""
        self.codigo = codigo
        self.nome = nome

    @property
    def codigo(self) -> str:
        """Retorna o código do curso em maiúsculas, como referência do catálogo."""
        return self._codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        """Valida que o código não fique vazio e padroniza para letras maiúsculas."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O código do curso não pode estar em branco.")
        self._codigo = valor.strip().upper()

    @property
    def nome(self) -> str:
        """Retorna o nome oficial do curso."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """Valida que o nome do curso tenha texto útil e não fique vazio."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O nome do curso não pode estar em branco.")
        self._nome = valor.strip()

    def __eq__(self, outro: object) -> bool:
        """Compara cursos pela matrícula/código do curso, que é a chave principal."""
        if not isinstance(outro, Curso):
            return NotImplemented
        return self.codigo == outro.codigo

    def __hash__(self) -> int:
        """Permite usar o curso em estruturas como sets e chaves de dicionários."""
        return hash(self.codigo)

    def __str__(self) -> str:
        """Mostra uma leitura simples do curso para uso em relatórios e console."""
        return f"{self.codigo} - {self.nome}"

    def __repr__(self) -> str:
        """Ajuda a depurar e identificar o objeto em mensagens de erro e testes."""
        return f"Curso(codigo={self.codigo!r}, nome={self.nome!r})"
