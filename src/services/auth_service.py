"""Autenticação local de contas para perfis administrativos e acadêmicos."""

from dataclasses import dataclass
import hashlib
import hmac
import secrets

from models import AutenticacaoError, DuplicidadeError, NaoEncontradoError
from models.adm import Adm
from models.monitor import Monitor

_ITERACOES = 310_000
_PREFIXO_HASH = "pbkdf2_sha256"


@dataclass(frozen=True)
class Sessao:
    """Identidade autenticada e papel efetivo do usuário."""

    usuario: str
    papel: str
    pessoa: object


def exigir_administrador(sessao: Sessao) -> None:
    """Permite a operação somente para uma sessão de administrador válida."""
    if not isinstance(sessao, Sessao) or sessao.papel != "adm" or not isinstance(sessao.pessoa, Adm):
        raise AutenticacaoError("Somente um administrador pode realizar esta operação.")


def exigir_aluno_proprio(sessao: Sessao, matricula: str = None):
    """Retorna o aluno da sessão e, se informada, confere sua matrícula."""
    from models.aluno import Aluno

    if not isinstance(sessao, Sessao) or sessao.papel not in {"pessoa", "monitor"} \
            or not isinstance(sessao.pessoa, Aluno):
        raise AutenticacaoError("Esta operação exige uma sessão autenticada de aluno.")
    if matricula is not None and sessao.pessoa.matricula != matricula:
        raise AutenticacaoError("Você só pode consultar ou alterar seus próprios dados.")
    return sessao.pessoa


class AuthService:
    """Cria e valida contas; senhas nunca são armazenadas em texto puro."""

    def __init__(self, repo):
        self._repo = repo

    @staticmethod
    def _validar_senha(senha: str) -> None:
        if not isinstance(senha, str) or len(senha) < 8:
            raise ValueError("A senha precisa ter pelo menos 8 caracteres.")

    @staticmethod
    def _gerar_hash(senha: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, _ITERACOES)
        return f"{_PREFIXO_HASH}${_ITERACOES}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verificar_senha(senha: str, senha_hash: str) -> bool:
        try:
            algoritmo, iteracoes, salt_hex, digest_esperado = senha_hash.split("$", 3)
            if algoritmo != _PREFIXO_HASH:
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes)
            ).hex()
            return hmac.compare_digest(digest, digest_esperado)
        except (ValueError, TypeError):
            return False

    def cadastrar_administrador(self, usuario: str, senha: str) -> None:
        """Cria o primeiro administrador durante a configuração inicial."""
        usuario = self._normalizar_usuario(usuario)
        self._validar_senha(senha)
        try:
            with self._repo.transacao():
                if self._repo.tem_administrador():
                    raise AutenticacaoError("Já existe um administrador cadastrado.")
                self._repo.salvar_administrador(
                    Adm(usuario, "", "admin@adm.uniesquina.edu.br", "", usuario=usuario),
                    self._gerar_hash(senha),
                )
        except DuplicidadeError as erro:
            raise AutenticacaoError("Esse usuário já está cadastrado.") from erro

    def registrar_aluno(self, matricula: str, email: str, senha: str) -> None:
        """Permite que o aluno crie a própria credencial após confirmar seus dados."""
        self._validar_senha(senha)
        aluno = self._repo.buscar_aluno(matricula, com_matriculas=False)
        if aluno is None:
            raise NaoEncontradoError(f"Aluno {matricula} não encontrado.")
        if self._repo.buscar_usuario_acesso(aluno.matricula) is not None:
            raise AutenticacaoError("Esse aluno já possui uma conta de acesso.")
        if not isinstance(email, str) or not hmac.compare_digest(
            aluno.email.casefold(), email.strip().casefold()
        ):
            raise AutenticacaoError("A matrícula e o e-mail não correspondem ao cadastro do aluno.")
        try:
            self._repo.salvar_credenciais_aluno(
                aluno.matricula, aluno.matricula, self._gerar_hash(senha)
            )
        except DuplicidadeError as erro:
            raise AutenticacaoError("Esse aluno já possui uma conta de acesso.") from erro

    def autenticar(self, usuario: str, senha: str) -> Sessao:
        usuario = self._normalizar_usuario(usuario)
        registro = self._repo.buscar_usuario_acesso(usuario)
        if registro is None or not self._verificar_senha(senha, registro["senha_hash"]):
            raise AutenticacaoError("Usuário ou senha inválidos.")

        papel = registro["papel"]
        if papel == "adm":
            pessoa = self._repo.buscar_administrador(registro["usuario"])
            if pessoa is None:
                raise AutenticacaoError("A conta não possui um perfil administrativo válido.")
        else:
            pessoa = self._repo.buscar_aluno(registro["matricula"])
            if pessoa is None:
                raise AutenticacaoError("A conta não está vinculada a um aluno válido.")
            if isinstance(pessoa, Monitor):
                papel = "monitor"
        return Sessao(registro["usuario"], papel, pessoa)

    @staticmethod
    def _normalizar_usuario(usuario: str) -> str:
        if not isinstance(usuario, str) or not usuario.strip():
            raise ValueError("Informe um usuário válido.")
        return usuario.strip()
