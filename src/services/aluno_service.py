import secrets

from database.repositorio import Repositorio
from models import NaoEncontradoError
from models.aluno import Aluno
from models.monitor import Monitor
from services.auth_service import exigir_administrador


class AlunoService:
    """Operações de cadastro e designação de monitores."""

    def __init__(self, repo: Repositorio):
        self._repo = repo

    def gerar_matricula(self) -> str:
        """Gera uma matrícula no padrão institucional que ainda não foi usada."""
        while True:
            matricula = f"202600{secrets.randbelow(10_000):04d}"
            if self._repo.buscar_aluno(matricula) is None:
                return matricula

    def cadastrar_aluno(self, aluno: Aluno, sessao=None) -> Aluno:
        exigir_administrador(sessao)
        if (
            len(aluno.matricula) != 10
            or not aluno.matricula.startswith("202600")
            or not aluno.matricula[6:].isascii()
            or not aluno.matricula[6:].isdigit()
            or self._repo.buscar_aluno(aluno.matricula, com_matriculas=False) is not None
        ):
            aluno.matricula = self.gerar_matricula()
        texto = (aluno.curso or "").strip()
        curso = self._repo.buscar_curso(texto)
        if curso is None:
            curso = next(
                (
                    c for c in self._repo.listar_cursos()
                    if c.codigo.casefold() == texto.casefold()
                    or texto.casefold() in c.nome.casefold()
                    or c.nome.casefold() in texto.casefold()
                ),
                None,
            )
        if curso is None:
            raise NaoEncontradoError(f"Curso de graduação {aluno.curso} não encontrado.")
        aluno.curso = curso.nome
        self._repo.salvar_aluno(aluno)
        return aluno

    def designar_monitor(self, matricula_aluno: str, id_oferta: str, sessao=None) -> Monitor:
        """Autoriza um aluno existente a acompanhar a turma escolhida pelo administrador."""
        exigir_administrador(sessao)
        with self._repo.transacao():
            aluno = self._repo.buscar_aluno(matricula_aluno)
            turma = self._repo.buscar_turma(id_oferta, com_alunos=False)
            if aluno is None:
                raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
            if turma is None:
                raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
            Monitor.validar_elegibilidade(aluno, turma)
            if id_oferta not in self._repo.monitorias_do_aluno(matricula_aluno):
                self._repo.salvar_monitoria(matricula_aluno, id_oferta)
        return self._repo.buscar_aluno(matricula_aluno)