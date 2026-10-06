class Curso:

    def __init__(self, codigo: str, nome: str, carga_horaria: int, tipo: str = "Obrigatória", 
        pre_requisitos: list = None):
        self.codigo = codigo
        self.nome = nome
        self.carga_horaria = carga_horaria  
        self.tipo = tipo
        self.pre_requisitos = pre_requisitos if pre_requisitos is not None else []

    @property
    def carga_horaria(self) -> int:
        return self._carga_horaria

    @carga_horaria.setter
    def carga_horaria(self, valor: int):
        if not isinstance(valor, int) or valor <= 0:
            raise ValueError("A carga horária deve ser um número inteiro positivo.")
        self._carga_horaria = valor

    def adicionar_pre_requisito(self, codigo_disciplina: str):
        if codigo_disciplina not in self.pre_requisitos:
            self.pre_requisitos.append(codigo_disciplina)

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome} ({self.carga_horaria}h) | {self.tipo}"    