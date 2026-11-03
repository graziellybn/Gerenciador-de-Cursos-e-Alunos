from typing import Iterable

from models import PermissaoNegadaError, ValidacaoError
from models.aluno import Aluno


class Monitor(Aluno):
    """Aluno que também auxilia turmas específicas.

    Herda tudo de Aluno e ganha permissões extras valendo SOMENTE para as
    turmas listadas em turmas_monitoradas.
    """

    PERMISSOES = Aluno.PERMISSOES | frozenset({"ver_desempenho_turma", "criar_atividade"})

    def __init__(self, *args, turmas_monitoradas: Iterable[str] = (), **kwargs):
        """Cria o monitor e inicia a lista de turmas sob sua responsabilidade."""
        super().__init__(*args, **kwargs)
        self._turmas_monitoradas = set(turmas_monitoradas)

    @property
    def turmas_monitoradas(self) -> frozenset:
        """Retorna uma visão somente leitura das turmas que o monitor acompanha."""
        return frozenset(self._turmas_monitoradas)

    def monitora(self, id_oferta: str) -> bool:
        """Indica se o monitor está designado para a turma informada."""
        return id_oferta in self._turmas_monitoradas

    def exigir_monitoria(self, id_oferta: str) -> None:
        """Lança PermissaoNegadaError se o monitor não atua nessa turma."""
        if not self.monitora(id_oferta):
            raise PermissaoNegadaError(f"Você não é monitor da turma {id_oferta}.")

    @classmethod
    def validar_elegibilidade(cls, aluno: Aluno, turma) -> None:
        """Regras: ter sido aprovado na disciplina e não estar matriculado na própria turma."""
        if not aluno.aprovou(turma.disciplina.codigo):
            raise ValidacaoError(
                f"{aluno.nome_completo} não foi aprovado em {turma.disciplina.codigo}; não pode monitorar."
            )
        if any(m.turma.id_oferta == turma.id_oferta for m in aluno.matriculas):
            raise ValidacaoError("O aluno não pode monitorar uma turma em que está matriculado.")

    def adicionar_turma(self, turma) -> None:
        """Passa a monitorar a turma, depois de validar a elegibilidade."""
        self.validar_elegibilidade(self, turma)
        self._turmas_monitoradas.add(turma.id_oferta)