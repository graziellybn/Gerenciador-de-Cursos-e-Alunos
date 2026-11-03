from models.pessoa import ComPermissoes, Pessoa


class Adm(Pessoa, ComPermissoes):
	"""Administrador com permissões para gerir o sistema acadêmico."""

	DOMINIO_EMAIL = "adm.uniesquina.edu.br"
	PERMISSOES = frozenset({
		"gerir_cursos",
		"gerir_alunos",
		"gerir_turmas",
		"gerir_matriculas",
		"ver_relatorios",
	})

	def __init__(self, nome_completo: str, data_nascimento: str, email: str,
				 telefone: str, usuario: str = "admin"):
		super().__init__(nome_completo, data_nascimento, email, telefone)
		self.usuario = usuario
