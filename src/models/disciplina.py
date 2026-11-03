from typing import Iterable

from models import ValidacaoError


class Disciplina:
    """Representa uma disciplina do currículo e suas dependências acadêmicas."""

    TIPOS = frozenset({"Obrigatória", "Optativa"})

    def __init__(
        self,
        codigo: str,
        nome: str,
        carga_horaria: int,
        curso,
        tipo: str = "Obrigatória",
        pre_requisitos: Iterable[str] = (),
        equivalente_a: str = None,
    ):
        """Cria a disciplina com validações de código, carga, tipo e pré-requisitos."""
        self.codigo = codigo
        self.nome = nome
        self.carga_horaria = carga_horaria
        self.curso = curso
        self.tipo = tipo
        self._pre_requisitos = []
        for codigo_pre in pre_requisitos or ():
            self.adicionar_pre_requisito(codigo_pre)
        self.equivalente_a = equivalente_a

    @property
    def codigo(self) -> str:
        """Retorna o código único da disciplina, em maiúsculas."""
        return self._codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        """Garante que a disciplina tenha um código válido e padronizado."""
        self._codigo = self._texto_obrigatorio(valor, "O código da disciplina")
        self._codigo = self._codigo.upper()

    @property
    def nome(self) -> str:
        """Retorna o nome da disciplina."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """Valida que o nome da disciplina não esteja vazio."""
        self._nome = self._texto_obrigatorio(valor, "O nome da disciplina")

    @property
    def carga_horaria(self) -> int:
        """Retorna a carga horária em horas da disciplina."""
        return self._carga_horaria

    @carga_horaria.setter
    def carga_horaria(self, valor: int) -> None:
        """Valida que a carga horária seja um número positivo e inteiro."""
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValidacaoError("A carga horária da disciplina deve ser um inteiro positivo.")
        self._carga_horaria = valor

    @property
    def tipo(self) -> str:
        """Retorna se a disciplina é obrigatória ou optativa."""
        return self._tipo

    @tipo.setter
    def tipo(self, valor: str) -> None:
        """Restrige o tipo da disciplina às opções previstas pelo projeto."""
        if valor not in self.TIPOS:
            raise ValidacaoError("O tipo da disciplina deve ser 'Obrigatória' ou 'Optativa'.")
        self._tipo = valor

    @property
    def curso_codigo(self) -> str:
        """Retorna o código do curso ao qual a disciplina pertence."""
        return self.curso.codigo if hasattr(self.curso, "codigo") else str(self.curso).strip().upper()

    @property
    def pre_requisitos(self) -> list[str]:
        """Retorna uma cópia da lista de pré-requisitos da disciplina."""
        return list(self._pre_requisitos)

    def adicionar_pre_requisito(self, codigo: str) -> None:
        """Adiciona um pré-requisito caso ele ainda não exista e a regra permita."""
        codigo = self._texto_obrigatorio(codigo, "O código do pré-requisito").upper()
        if codigo == self.codigo:
            raise ValidacaoError("Uma disciplina não pode ser pré-requisito de si mesma.")
        if codigo not in self._pre_requisitos:
            self._pre_requisitos.append(codigo)

    @property
    def equivalente_a(self) -> str | None:
        """Retorna a disciplina equivalente, se houver."""
        return self._equivalente_a

    @equivalente_a.setter
    def equivalente_a(self, valor: str | None) -> None:
        """Valida a disciplina equivalente e evita referência circular."""
        if valor in (None, ""):
            self._equivalente_a = None
            return
        codigo = self._texto_obrigatorio(valor, "O código da disciplina equivalente").upper()
        if codigo == self.codigo:
            raise ValidacaoError("Uma disciplina não pode ser equivalente a si mesma.")
        self._equivalente_a = codigo

    @staticmethod
    def _texto_obrigatorio(valor: str, rotulo: str) -> str:
        """Centraliza a validação de campos textuais obrigatórios."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError(f"{rotulo} não pode ficar em branco.")
        return valor.strip()

    def __eq__(self, outra: object) -> bool:
        """Compara disciplinas pela chave principal, que é o código."""
        if not isinstance(outra, Disciplina):
            return NotImplemented
        return self.codigo == outra.codigo

    def __hash__(self) -> int:
        """Permite usar a disciplina em coleções e buscas por código."""
        return hash(self.codigo)

    @staticmethod
    def tem_ciclo(codigo: str, novos: Iterable[str], grafo: dict) -> bool:
        """Verifica se a adição de pré-requisitos criaria um ciclo no grafo curricular."""
        pilha = [item.strip().upper() for item in novos]
        visitados = set()
        codigo = codigo.strip().upper()
        while pilha:
            atual = pilha.pop()
            if atual == codigo:
                return True
            if atual in visitados:
                continue
            visitados.add(atual)
            pilha.extend(grafo.get(atual, ()))
        return False

    def __str__(self) -> str:
        """Cria uma representação curta e útil da disciplina para prints e relatórios."""
        return f"{self.codigo} - {self.nome} ({self.carga_horaria}h, {self.tipo})"
