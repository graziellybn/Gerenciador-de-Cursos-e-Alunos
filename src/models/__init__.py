"""Exceções de domínio usadas pelos modelos e serviços."""


class ErroAcademico(Exception):
    """Base dos erros de regra de negócio acadêmica."""


class ValidacaoError(ErroAcademico, ValueError):
    """Informação ou operação inválida."""


class CicloPreRequisitoError(ValidacaoError):
    """Pré-requisitos formariam um ciclo."""


class DuplicidadeError(ErroAcademico):
    """Registro duplicado."""


class NaoEncontradoError(ErroAcademico):
    """Entidade solicitada não existe."""


class PermissaoNegadaError(ErroAcademico):
    """A ação não está permitida para este papel."""


class AutenticacaoError(ErroAcademico):
    """Credenciais inválidas ou conta não autorizada."""


class MatriculaNegadaError(ErroAcademico):
    """Base das recusas de matrícula."""


class TurmaFechadaError(MatriculaNegadaError):
    """A turma está fechada para matrículas."""


class TurmaLotadaError(MatriculaNegadaError):
    """A turma não possui vagas disponíveis."""


class ChoqueHorarioError(MatriculaNegadaError):
    """A matrícula conflita com outra turma do aluno."""


class PreRequisitoNaoCumpridoError(MatriculaNegadaError):
    """O aluno não concluiu os pré-requisitos."""


class LimiteTurmasError(MatriculaNegadaError):
    """O limite de turmas por período foi excedido."""
"""Exceções de domínio. ValidacaoError também é ValueError, então
código e testes antigos com `pytest.raises(ValueError)` continuam funcionando."""


class ErroAcademico(Exception):
    """Base de todos os erros de regra de negócio."""


class ValidacaoError(ErroAcademico, ValueError):
    """Dado inválido (nota fora da faixa, e-mail malformado...)."""


class CicloPreRequisitoError(ValidacaoError):
    """Pré-requisitos formariam um ciclo (A exige B e B exige A)."""


class DuplicidadeError(ErroAcademico):
    """Registro já existe (código, matrícula, matrícula na turma)."""


class NaoEncontradoError(ErroAcademico):
    """Entidade referenciada não existe."""


class PermissaoNegadaError(ErroAcademico):
    """O papel do usuário não permite a ação."""


class MatriculaNegadaError(ErroAcademico):
    """Base das recusas de matrícula."""


class TurmaFechadaError(MatriculaNegadaError): ...
class TurmaLotadaError(MatriculaNegadaError): ...
class ChoqueHorarioError(MatriculaNegadaError): ...
class PreRequisitoNaoCumpridoError(MatriculaNegadaError): ...
class LimiteTurmasError(MatriculaNegadaError): ...


class AutenticacaoError(ErroAcademico):
    """Credenciais inválidas ou conta não autorizada."""