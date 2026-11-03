from models import DuplicidadeError, ValidacaoError
from models.pessoa import ComPermissoes, Pessoa


class Aluno(Pessoa, ComPermissoes):
    """Representa um aluno do curso, incluindo o histórico e as permissões pessoais."""

    DOMINIO_EMAIL = "aluno.uniesquina.edu.br"
    PERMISSOES = frozenset({"matricular", "ver_proprio_historico"})

    def __init__(self, nome_completo: str, data_nascimento: str, email: str, telefone: str,
                 matricula: str, curso, cr: float = 0.0, status: str = "Ativo"):
        """Cria o aluno e já registra a matrícula, curso e dados básicos do cadastro."""
        super().__init__(nome_completo, data_nascimento, email, telefone)
        self.matricula = matricula
        self.curso = curso
        self.cr = cr
        self.status = status
        self._matriculas = []

    @property
    def matricula(self) -> str:
        """Retorna a matrícula do aluno como identificador principal."""
        return self._matricula

    @matricula.setter
    def matricula(self, valor: str):
        """Valida que a matrícula exista e seja útil para o cadastro."""
        if valor is None or not str(valor).strip():
            raise ValidacaoError("A matrícula do aluno não pode estar em branco.")
        self._matricula = str(valor).strip()

    @property
    def cr(self) -> float:
        """Retorna o coeficiente de rendimento do aluno."""
        return self._cr

    @cr.setter
    def cr(self, valor: float):
        """Valida que o CR esteja dentro da faixa acadêmica aceita pelo sistema."""
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not (0.0 <= valor <= 10.0):
            raise ValidacaoError("O CR deve ser um número entre 0.0 e 10.0.")
        self._cr = float(valor)

    @property
    def status(self) -> str:
        """Retorna o status geral do aluno no sistema."""
        return self._status

    @status.setter
    def status(self, valor: str) -> None:
        """Valida que o status do aluno não fique vazio."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValidacaoError("O status do aluno não pode ficar em branco.")
        self._status = valor.strip()

    @property
    def matriculas(self) -> tuple:
        """Retorna uma cópia somente leitura do histórico acadêmico do aluno."""
        return tuple(self._matriculas)

    def registrar_matricula(self, matricula) -> None:
        """Registra uma matrícula nova e evita duplicidade na mesma turma."""
        if matricula in self._matriculas:
            raise DuplicidadeError("O aluno já possui matrícula nesta turma.")
        self._matriculas.append(matricula)

    def aprovou(self, codigo_disciplina: str) -> bool:
        """Checa se o aluno já teve aprovação na disciplina informada."""
        return any(
            m.turma.disciplina.codigo == codigo_disciplina and m.status == m.APROVADO
            for m in self._matriculas
        )

    def recalcular_cr(self) -> float:
        """Atualiza o CR usando as matrículas finalizadas e a carga horária de cada disciplina."""
        finalizadas = [m for m in self._matriculas if m.status in m.SITUACOES_FINAIS]
        total_horas = sum(m.turma.disciplina.carga_horaria for m in finalizadas)
        if total_horas == 0:
            self.cr = 0.0
        else:
            soma = sum(m.calcular_media() * m.turma.disciplina.carga_horaria for m in finalizadas)
            self.cr = soma / total_horas
        return self.cr

    def __eq__(self, outro: object) -> bool:
        """Compara alunos pela matrícula, que é a identidade do cadastro."""
        if not isinstance(outro, Aluno):
            return NotImplemented
        return self.matricula == outro.matricula

    def __hash__(self) -> int:
        """Permite que o aluno seja usado em coleções e buscas rápidas."""
        return hash(self.matricula)

    def __lt__(self, outro: "Aluno") -> bool:
        """Ordena alunos por CR e, em caso de empate, pelo nome completo."""
        if not isinstance(outro, Aluno):
            return NotImplemented
        if self.cr == outro.cr:
            return self.nome_completo < outro.nome_completo
        return self.cr < outro.cr

    def __str__(self) -> str:
        """Cria uma mensagem curta com dados principais do aluno para leitura no console."""
        return f"Aluno: {self.nome_completo} | Matrícula: {self.matricula} | CR: {self.cr:.2f}"


