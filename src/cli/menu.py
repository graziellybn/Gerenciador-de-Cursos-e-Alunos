from models import ErroAcademico
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.monitor import Monitor
from models.turma import Turma
from services.aluno_service import AlunoService
from services.curso_service import CursoService, DisciplinaService
from services.matricula_service import MatriculaService
from services.relatorio_service import RelatorioService
from services.turma_service import TurmaService


class _OperacaoCancelada(Exception):
	"""Sinaliza que o usuário escolheu voltar ao menu principal."""


class MenuCLI:
	"""Menu de linha de comando para as operações acadêmicas principais."""

	def __init__(self, repo, input_fn=None, output_fn=None, password_fn=None, sessao=None):
		self.repo = repo
		self.input = input_fn or input
		self.output = output_fn or print
		self.password = password_fn or self._ler_senha
		self.sessao = sessao
		self.papel = sessao.papel if sessao else "visitante"
		self.cursos = CursoService(repo)
		self.disciplinas = DisciplinaService(repo)
		self.alunos = AlunoService(repo)
		self.turmas = TurmaService(repo)
		self.matriculas = MatriculaService(repo)
		self.relatorios = RelatorioService(repo)

	def executar(self) -> bool:
		"""Executa o menu e informa se a aplicação deve encerrar."""
		opcoes_adm = {
			"1": ("Listar cursos", self.listar_cursos),
			"2": ("Cadastrar curso", self.cadastrar_curso),
			"3": ("Listar alunos", self.listar_alunos),
			"4": ("Cadastrar aluno", self.cadastrar_aluno),
			"5": ("Listar turmas", self.listar_turmas),
			"6": ("Cadastrar turma", self.cadastrar_turma),
			"7": ("Matricular aluno", self.matricular_aluno),
			"8": ("Lançar notas e frequência", self.lancar_notas),
			"9": ("Relatório de turma", self.relatorio_turma),
			"10": ("Designar monitor para turma", self.designar_monitor),
			"11": ("Listar disciplinas", self.listar_disciplinas),
			"12": ("Cadastrar disciplina", self.cadastrar_disciplina),
			"000": ("Voltar ao menu de login", None),
			"0": ("Sair", None),
		}
		opcoes_pessoa = {
			"1": ("Listar cursos", self.listar_cursos),
			"2": ("Ver meu histórico", self.ver_meu_historico),
			"000": ("Voltar ao menu de login", None),
			"0": ("Sair", None),
		}
		opcoes_monitor = {
			**opcoes_pessoa,
			"3": ("Relatório de turma monitorada", self.relatorio_monitoria),
		}
		opcoes = {
			"adm": opcoes_adm,
			"pessoa": opcoes_pessoa,
			"monitor": opcoes_monitor,
		}.get(self.papel, {"0": ("Sair", None)})
		while True:
			identidade = self.sessao.usuario if self.sessao else "visitante"
			self.output("\n" + "=" * 52)
			self.output("       Bem-vindo ao Gerenciador Acadêmico!")
			self.output("=" * 52)
			self.output(f"Olá! Perfil: {self.papel.capitalize()} | Conta: {identidade}")
			self.output("O que você gostaria de fazer hoje?")
			self.output("")
			for chave, (rotulo, _) in opcoes.items():
				self.output(f"  [{chave:>2}] {rotulo}")
			self.output("-" * 52)
			try:
				escolha = self.input("Escolha uma opção: ").strip()
				if escolha == "0":
					self.output("\nObrigada por usar o sistema. Até logo!")
					return True
				if escolha == "000":
					self.output("\nSessão encerrada. Voltando ao menu de login.")
					return False
				item = opcoes.get(escolha)
				if item is None:
					self.output("Essa opção não existe. Tente novamente.")
					continue
				item[1]()
			except _OperacaoCancelada:
				self.output("\nOperação cancelada. Voltando ao menu principal.")
			except (ErroAcademico, ValueError) as erro:
				self.output(f"\nNão foi possível concluir: {erro}")
				self.output("Confira os dados e tente novamente.")
			except (EOFError, KeyboardInterrupt):
				self.output("\nEncerrando. Até logo!")
				return True

	def designar_monitor(self) -> None:
		if self.papel != "adm" or self.sessao is None:
			self.output("Somente um administrador autenticado pode designar monitores.")
			return
		matricula = self._perguntar("Matrícula do aluno já cadastrado: ").strip()
		self.listar_turmas()
		id_oferta = self._perguntar("Código da turma que o aluno acompanhará: ").strip()
		self.alunos.designar_monitor(matricula, id_oferta, sessao=self.sessao)
		self.output(f"Sucesso! O aluno {matricula} acompanhará a turma {id_oferta}.")

	def ver_meu_historico(self) -> None:
		if self.sessao is None or not hasattr(self.sessao.pessoa, "matriculas"):
			self.output("Histórico indisponível para esta conta.")
			return
		matriculas = self.sessao.pessoa.matriculas
		if not matriculas:
			self.output("Seu histórico ainda não tem matrículas. Quando houver, elas aparecerão aqui.")
			return
		for registro in matriculas:
			texto = f"{registro.turma.id_oferta} — {registro.turma.disciplina.nome}: {registro.status}"
			if registro.notas_lancadas and registro.frequencia_lancada:
				texto += (
					f", média {registro.calcular_media():.1f}, "
					f"frequência {registro.frequencia:.0f}%"
				)
			else:
				texto += "; notas e frequência ainda não registradas"
			self.output(texto)

	def relatorio_monitoria(self) -> None:
		if self.papel != "monitor" or self.sessao is None:
			self.output("Esta opção é exclusiva para monitores.")
			return
		id_oferta = self._perguntar("Código da turma monitorada: ").strip()
		self.output(self.relatorios.relatorio_monitoria(self.sessao, id_oferta))

	@staticmethod
	def _ler_senha(prompt: str) -> str:
		return input(prompt)

	def listar_cursos(self) -> None:
		cursos = self.repo.listar_cursos()
		self.output("\n" + "-" * 56)
		self.output("                    CURSOS CADASTRADOS")
		self.output("-" * 56)
		if not cursos:
			self.output("Nenhum curso cadastrado ainda.")
			self.output("Use a opção [2] para cadastrar um curso de graduação.")
			self.output("-" * 56)
			return
		for numero, curso in enumerate(cursos, start=1):
			self.output(f"[{numero}] {curso.codigo} — {curso.nome}")
		self.output("-" * 56)

	def cadastrar_curso(self) -> None:
		curso = Curso(
			self._perguntar("Código do curso de graduação: "),
			self._perguntar("Nome do curso: "),
		)
		self.cursos.cadastrar_curso(curso, sessao=self.sessao)
		self.output(f"Sucesso! O curso {curso.codigo} foi cadastrado.")

	def listar_disciplinas(self) -> None:
		disciplinas = self.repo.listar_disciplinas()
		self.output("\n" + "-" * 56)
		self.output("                 DISCIPLINAS CADASTRADAS")
		self.output("-" * 56)
		if not disciplinas:
			self.output("Nenhuma disciplina cadastrada ainda.")
			self.output("Use a opção [12] para cadastrar uma disciplina.")
			self.output("-" * 56)
			return
		for numero, disciplina in enumerate(disciplinas, start=1):
			prerequisitos = ", ".join(disciplina.pre_requisitos) or "nenhum"
			equivalencia = disciplina.equivalente_a or "nenhuma"
			self.output(f"[{numero}] {disciplina.codigo} — {disciplina.nome}")
			self.output(
				f"    Curso: {disciplina.curso_codigo} | {disciplina.carga_horaria}h | "
				f"{disciplina.tipo} | Pré-requisitos: {prerequisitos} | Equivalente a: {equivalencia}"
			)
		self.output("-" * 56)

	def cadastrar_disciplina(self) -> None:
		"""Cadastra uma disciplina antes que ela seja usada para abrir turmas."""
		self.listar_cursos()
		codigo_curso = self._perguntar("Código do curso da disciplina: ").strip().upper()
		curso = self.repo.buscar_curso(codigo_curso)
		if curso is None:
			raise ValueError(f"Curso {codigo_curso} não encontrado.")

		disciplina = Disciplina(
			self._perguntar("Código da disciplina: ").strip().upper(),
			self._perguntar("Nome da disciplina: "),
			self._inteiro("Carga horária da disciplina (horas): "),
			curso,
			self._tipo_disciplina(),
			self._codigos_opcionais(
				"Códigos de pré-requisitos separados por vírgula (vazio se nenhum): "
			),
			self._perguntar(
				"Código da disciplina equivalente (vazio se nenhuma): "
			).strip().upper() or None,
		)
		self.disciplinas.cadastrar_disciplina(disciplina, sessao=self.sessao)
		self.output(f"Sucesso! A disciplina {disciplina.codigo} foi cadastrada.")

	def _tipo_disciplina(self) -> str:
		tipo = self._perguntar("Tipo [Obrigatória/Optativa] (padrão Obrigatória): ").strip()
		return tipo.title() if tipo else "Obrigatória"

	def _codigos_opcionais(self, prompt: str) -> list[str]:
		return [
			codigo.strip().upper()
			for codigo in self._perguntar(prompt).split(",")
			if codigo.strip()
		]

	def listar_alunos(self) -> None:
		alunos = self.repo.listar_alunos()
		self.output("\n" + "-" * 52)
		self.output("ALUNOS CADASTRADOS")
		self.output("-" * 52)
		if not alunos:
			self.output("Nenhum aluno cadastrado.")
			self.output("-" * 52)
			return
		for aluno in alunos:
			perfil = "Monitor" if isinstance(aluno, Monitor) else "Aluno"
			turmas_cursando = sorted(
				matricula.turma.id_oferta
				for matricula in aluno.matriculas
				if matricula.status == Matricula.CURSANDO
			)
			matriculas_ativas = ", ".join(turmas_cursando) or "nenhuma"
			linha = (
				f"{aluno.matricula} — {aluno.nome_completo} | {aluno.curso} "
				f"| CR {aluno.cr:.2f} | Perfil: {perfil} | Situação: {aluno.status} "
				f"| Matrículas cursando: {matriculas_ativas}"
			)
			if isinstance(aluno, Monitor):
				turmas = ", ".join(sorted(aluno.turmas_monitoradas)) or "nenhuma"
				linha += f" | Turmas de monitoria: {turmas}"
			self.output(linha)
		self.output("-" * 52)

	def cadastrar_aluno(self) -> None:
		aluno = Aluno(
			self._perguntar("Nome completo: "),
			self._perguntar("Data de nascimento (AAAA-MM-DD): "),
			self._perguntar("E-mail: "),
			self._perguntar("Telefone: "),
			self.alunos.gerar_matricula(),
			self._perguntar("Curso do aluno: "),
		)
		self.alunos.cadastrar_aluno(aluno, sessao=self.sessao)
		self.output(
			f"Sucesso! O aluno {aluno.nome_completo} foi cadastrado. "
			f"Matrícula gerada: {aluno.matricula}."
		)

	def listar_turmas(self) -> None:
		turmas = self.repo.listar_turmas()
		self.output("\n" + "-" * 52)
		self.output("TURMAS DISPONÍVEIS")
		self.output("-" * 52)
		if not turmas:
			self.output("Nenhuma turma cadastrada.")
			self.output("-" * 52)
			return
		for turma in turmas:
			self.output(
				f"{turma.id_oferta} — {turma.disciplina.codigo} ({turma.disciplina.nome}) | "
				f"Curso {turma.disciplina.curso_codigo} | {turma.disciplina.carga_horaria}h | "
				f"{turma.periodo} | "
				f"{turma.ocupacao}/{turma.vagas} vagas | {'aberta' if turma.aberta else 'fechada'}"
			)
		self.output("-" * 52)

	def cadastrar_turma(self) -> None:
		self.listar_disciplinas()
		codigo_disciplina = self._perguntar("Código da disciplina: ").strip().upper()
		disciplina = self.repo.buscar_disciplina(codigo_disciplina)
		if disciplina is None:
			raise ValueError(
				f"Disciplina {codigo_disciplina} não encontrada. "
				"Cadastre a disciplina antes de criar a turma."
			)
		self.output(
			f"Disciplina selecionada: {disciplina.codigo} — {disciplina.nome} "
			f"({disciplina.carga_horaria}h)."
		)
		horario_texto = self._perguntar(
			"Horários (ex.: seg=08:00-10:00;qua=14:00-16:00; vazio se nenhum): "
		)
		horario = {}
		for trecho in filter(None, (parte.strip() for parte in horario_texto.split(";"))):
			dia, separador, intervalo = trecho.partition("=")
			if not separador:
				raise ValueError("Informe cada horário como dia=HH:MM-HH:MM.")
			horario[dia.strip()] = intervalo.strip()
		turma = Turma(
			self._perguntar("Código da turma/oferta: "), disciplina,
			self._perguntar("Professor: "), self._perguntar("Período: "),
			self._inteiro("Número de vagas: "), horario or None,
			self._perguntar("Local (opcional): ").strip() or None,
		)
		self.turmas.cadastrar_turma(turma, sessao=self.sessao)
		self.output(f"Sucesso! A turma {turma.id_oferta} foi cadastrada.")

	def matricular_aluno(self) -> None:
		matricula = self._perguntar("Matrícula do aluno: ").strip()
		id_oferta = self._perguntar("Código da turma: ").strip()
		registro = self.matriculas.matricular(matricula, id_oferta, sessao=self.sessao)
		self.output(f"Sucesso! {registro.aluno.nome_completo} está matriculado em {id_oferta}.")

	def lancar_notas(self) -> None:
		matricula_aluno = self._perguntar("Matrícula do aluno: ").strip()
		id_oferta = self._perguntar("Código da turma: ").strip()
		registro = self.matriculas.lancar_notas(
			matricula_aluno,
			id_oferta,
			self._decimal("Nota 1 (0 a 10): "),
			self._decimal("Nota 2 (0 a 10): "),
			self._decimal("Frequência percentual (0 a 100): "),
			sessao=self.sessao,
		)
		self.output(f"Sucesso! Notas salvas. Situação acadêmica: {registro.status}.")

	def relatorio_turma(self) -> None:
		id_oferta = self._perguntar("Código da turma: ").strip()
		self.output(self.relatorios.formatar_alunos_por_turma(id_oferta, sessao=self.sessao))

	def _perguntar(self, prompt: str) -> str:
		"""Lê uma resposta; a opção 0 cancela a operação atual."""
		resposta = self.input(f"{prompt} (0 para cancelar)").strip()
		if resposta == "0":
			raise _OperacaoCancelada
		return resposta

	def _inteiro(self, prompt: str) -> int:
		return int(self._perguntar(prompt))

	def _decimal(self, prompt: str) -> float:
		return float(self._perguntar(prompt).replace(",", "."))
