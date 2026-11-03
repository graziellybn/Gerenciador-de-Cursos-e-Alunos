from database.repositorio import Repositorio
from models import CicloPreRequisitoError, NaoEncontradoError, ValidacaoError
from models.curso import Curso
from models.disciplina import Disciplina
from services.auth_service import exigir_administrador


class CursoService:
    """Cadastro e consulta de cursos de graduação."""

    def __init__(self, repo: Repositorio):
        self._repo = repo

    def cadastrar_curso(self, curso: Curso, sessao=None) -> Curso:
        exigir_administrador(sessao)
        self._repo.salvar_curso(curso)
        return curso


class DisciplinaService:
    """Cadastro de disciplinas e suas relações curriculares."""

    def __init__(self, repo: Repositorio):
        self._repo = repo

    def cadastrar_disciplina(self, disciplina: Disciplina, sessao=None) -> Disciplina:
        exigir_administrador(sessao)
        if self._repo.buscar_curso(disciplina.curso_codigo) is None:
            raise NaoEncontradoError(f"Curso {disciplina.curso_codigo} não encontrado.")
        for codigo in disciplina.pre_requisitos:
            if self._repo.buscar_disciplina(codigo) is None:
                raise NaoEncontradoError(f"Pré-requisito {codigo} não encontrado.")
        if disciplina.equivalente_a and self._repo.buscar_disciplina(disciplina.equivalente_a) is None:
            raise NaoEncontradoError(f"Disciplina equivalente {disciplina.equivalente_a} não encontrada.")
        if Disciplina.tem_ciclo(
            disciplina.codigo, disciplina.pre_requisitos,
            self._repo.grafo_prerequisitos_disciplinas(),
        ):
            raise CicloPreRequisitoError("Os pré-requisitos da disciplina formariam um ciclo.")
        self._repo.salvar_disciplina(disciplina)
        return disciplina

    def adicionar_pre_requisito(self, codigo: str, prerequisito: str, sessao=None) -> Disciplina:
        exigir_administrador(sessao)
        codigo, prerequisito = codigo.strip().upper(), prerequisito.strip().upper()
        disciplina = self._repo.buscar_disciplina(codigo)
        if disciplina is None:
            raise NaoEncontradoError(f"Disciplina {codigo} não encontrada.")
        if self._repo.buscar_disciplina(prerequisito) is None:
            raise NaoEncontradoError(f"Pré-requisito {prerequisito} não encontrado.")
        if codigo == prerequisito:
            raise ValidacaoError("Uma disciplina não pode ser pré-requisito de si mesma.")
        if Disciplina.tem_ciclo(
            codigo, [prerequisito], self._repo.grafo_prerequisitos_disciplinas(),
        ):
            raise CicloPreRequisitoError("Os pré-requisitos da disciplina formariam um ciclo.")
        if prerequisito not in disciplina.pre_requisitos:
            self._repo.salvar_prerequisito_disciplina(codigo, prerequisito)
        return self._repo.buscar_disciplina(codigo)
