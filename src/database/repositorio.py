"""Persistência local das entidades acadêmicas em arquivos JSON."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from config import carregar_configuracoes
from models import DuplicidadeError, NaoEncontradoError, ValidacaoError
from models.adm import Adm
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.monitor import Monitor
from models.turma import Turma

CAMINHO_PADRAO = Path(__file__).resolve().parent / "data"
_ARQUIVOS = {
    "cursos": "cursos.json",
    "disciplinas": "disciplinas.json",
    "alunos": "alunos.json",
    "adm": "adm.json",
    "turmas": "turmas.json",
    "monitores": "monitores.json",
    "relatorios": "relatorios_alunos.json",
}
_CAMPOS_OBRIGATORIOS = {
    "cursos": {"codigo", "nome"},
    "disciplinas": {"codigo", "nome", "carga_horaria", "curso_codigo", "tipo"},
    "alunos": {"matricula", "nome_completo", "data_nascimento", "email", "telefone", "curso", "cr", "status"},
    "turmas": {"id_oferta", "disciplina", "professor", "periodo", "vagas"},
    "adm": {"usuario", "senha_hash", "nome_completo", "email", "telefone"},
    "monitores": {"matricula", "turmas_monitoradas"},
    "relatorios": {"matricula", "gerado_em", "dados"},
}
_CHAVES_UNICAS = {
    "cursos": ("codigo",),
    "disciplinas": ("codigo",),
    "alunos": ("matricula", "email"),
    "turmas": ("id_oferta",),
    "adm": ("usuario",),
    "monitores": ("matricula",),
}


class Repositorio:
    """Lê e grava os dados do sistema em arquivos JSON separados por entidade."""

    def __init__(self, caminho=CAMINHO_PADRAO, configuracoes=None):
        self.configuracoes = configuracoes or carregar_configuracoes()
        self._em_memoria = str(caminho) == ":memory:"
        self._diretorio = None if self._em_memoria else Path(caminho)
        self._nivel = 0
        self._alterado = False
        self._dados = {nome: [] for nome in _ARQUIVOS}
        if self._diretorio is not None:
            self._diretorio.mkdir(parents=True, exist_ok=True)
            self._carregar()

    def _carregar(self) -> None:
        """Carrega os arquivos existentes e valida sua estrutura básica."""
        arquivos_existentes = set()
        for entidade, nome_arquivo in _ARQUIVOS.items():
            caminho = self._diretorio / nome_arquivo
            if not caminho.exists():
                continue
            arquivos_existentes.add(entidade)
            try:
                dados = json.loads(caminho.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as erro:
                raise ValidacaoError(f"Não foi possível ler {nome_arquivo}: {erro}.") from erro
            if not isinstance(dados, list) or any(not isinstance(item, dict) for item in dados):
                raise ValidacaoError(f"O arquivo {nome_arquivo} precisa conter uma lista de objetos JSON.")
            campos = _CAMPOS_OBRIGATORIOS[entidade]
            if any(not campos.issubset(item) for item in dados):
                raise ValidacaoError(f"Há registros incompletos no arquivo {nome_arquivo}.")
            self._dados[entidade] = dados
        dados_migrados = self._migrar_dados_legados(arquivos_existentes)
        try:
            self._validar_integridade()
        except (AttributeError, KeyError, TypeError) as erro:
            raise ValidacaoError("Os arquivos JSON têm registros com estrutura inválida.") from erro
        if dados_migrados:
            self._persistir()
            for nome_antigo in (
                "usuarios.json", "administradores.json", "matriculas.json", "monitorias.json"
            ):
                (self._diretorio / nome_antigo).unlink(missing_ok=True)

    def _ler_lista_legada(self, nome_arquivo: str) -> list[dict]:
        caminho = self._diretorio / nome_arquivo
        if not caminho.exists():
            return []
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as erro:
            raise ValidacaoError(f"Não foi possível ler {nome_arquivo}: {erro}.") from erro
        if not isinstance(dados, list) or any(not isinstance(item, dict) for item in dados):
            raise ValidacaoError(f"O arquivo {nome_arquivo} precisa conter uma lista de objetos JSON.")
        return dados

    def _migrar_dados_legados(self, arquivos_existentes: set[str]) -> bool:
        """Move matrículas, monitorias e contas antigas para os arquivos atuais."""
        alterado = False
        for aluno in self._dados["alunos"]:
            if "matriculas" not in aluno:
                aluno["matriculas"] = []
                alterado = True

        caminho_matriculas = self._diretorio / "matriculas.json"
        if caminho_matriculas.exists():
            matriculas_antigas = self._ler_lista_legada("matriculas.json")
            alunos_por_matricula = {
                aluno["matricula"]: aluno for aluno in self._dados["alunos"]
            }
            for registro in matriculas_antigas:
                if not {"aluno", "turma", "frequencia", "status"}.issubset(registro):
                    raise ValidacaoError("Há registros incompletos no arquivo matriculas.json.")
                aluno = alunos_por_matricula.get(registro["aluno"])
                if aluno is None:
                    raise ValidacaoError(
                        f"A matrícula de {registro['aluno']} não possui cadastro de aluno."
                    )
                turma = registro["turma"]
                if any(item.get("turma") == turma for item in aluno["matriculas"]):
                    continue
                aluno["matriculas"].append({
                    chave: valor for chave, valor in registro.items() if chave != "aluno"
                })
                alterado = True

        caminho_antigo = self._diretorio / "monitorias.json"
        if caminho_antigo.exists():
            monitorias = self._ler_lista_legada("monitorias.json")
            por_aluno = {}
            for item in monitorias:
                if not {"aluno", "turma"}.issubset(item):
                    raise ValidacaoError("Há registros incompletos no arquivo monitorias.json.")
                turmas = por_aluno.setdefault(item["aluno"], [])
                if item["turma"] not in turmas:
                    turmas.append(item["turma"])
            monitores = {
                monitor["matricula"]: monitor for monitor in self._dados["monitores"]
            }
            for matricula, turmas in por_aluno.items():
                monitor = monitores.get(matricula)
                if monitor is None:
                    monitor = {"matricula": matricula, "turmas_monitoradas": []}
                    self._dados["monitores"].append(monitor)
                    monitores[matricula] = monitor
                atualizadas = set(monitor["turmas_monitoradas"]) | set(turmas)
                if atualizadas != set(monitor["turmas_monitoradas"]):
                    monitor["turmas_monitoradas"] = sorted(atualizadas)
                    alterado = True
            if por_aluno:
                alterado = True

        caminho_usuarios = self._diretorio / "usuarios.json"
        caminho_admins = self._diretorio / "administradores.json"
        if caminho_usuarios.exists() or caminho_admins.exists():
            contas = self._ler_lista_legada("usuarios.json")
            perfis_admin = self._ler_lista_legada("administradores.json")
            perfis_por_usuario = {
                item["usuario"].casefold(): item
                for item in perfis_admin if isinstance(item.get("usuario"), str)
            }
            admins = {item["usuario"].casefold() for item in self._dados["adm"]}
            matriculas = {item["matricula"]: item for item in self._dados["alunos"]}
            for conta in contas:
                if not {"usuario", "senha_hash", "papel", "matricula"}.issubset(conta):
                    raise ValidacaoError("Há credenciais incompletas em usuarios.json.")
                usuario = conta["usuario"]
                if conta["papel"] == "adm" and usuario.casefold() not in admins:
                    perfil = perfis_por_usuario.get(usuario.casefold(), {})
                    self._dados["adm"].append({
                        "usuario": usuario,
                        "senha_hash": conta["senha_hash"],
                        "nome_completo": perfil.get("nome_completo", usuario),
                        "email": perfil.get("email", "admin@adm.uniesquina.edu.br"),
                        "telefone": perfil.get("telefone", ""),
                    })
                    admins.add(usuario.casefold())
                    alterado = True
                elif conta["papel"] == "pessoa":
                    aluno = matriculas.get(conta["matricula"])
                    if aluno is None:
                        raise ValidacaoError(
                            f"A credencial do aluno {conta['matricula']} não tem cadastro correspondente."
                        )
                    aluno["usuario"] = usuario
                    aluno["senha_hash"] = conta["senha_hash"]
                    alterado = True
                else:
                    raise ValidacaoError("Há uma conta com papel inválido em usuarios.json.")

        if caminho_matriculas.exists() or caminho_antigo.exists():
            alterado = True
        if caminho_usuarios.exists() or caminho_admins.exists():
            alterado = True
        return alterado

    def _registros_matricula(self):
        """Itera os registros de matrícula anexando a matrícula do aluno para consulta."""
        for aluno in self._dados["alunos"]:
            for registro in aluno.get("matriculas", []):
                yield {**registro, "aluno": aluno["matricula"]}

    def _validar_integridade(self) -> None:
        """Confere chaves únicas e referências entre os arquivos carregados."""
        for entidade, campos in _CHAVES_UNICAS.items():
            for campo in campos:
                valores = [
                    str(item[campo]).casefold() if campo in {"email", "usuario"} else item[campo]
                    for item in self._dados[entidade] if item.get(campo) is not None
                ]
                if len(valores) != len(set(valores)):
                    raise ValidacaoError(f"Há valores duplicados para {campo} em {_ARQUIVOS[entidade]}.")

        codigos_cursos = {r["codigo"] for r in self._dados["cursos"]}
        codigos_disciplinas = {r["codigo"] for r in self._dados["disciplinas"]}
        matriculas = {r["matricula"] for r in self._dados["alunos"]}
        turmas = {r["id_oferta"] for r in self._dados["turmas"]}
        for registro in self._dados["disciplinas"]:
            referencias = [registro["curso_codigo"], *registro.get("pre_requisitos", [])]
            if registro.get("equivalente_a"):
                referencias.append(registro["equivalente_a"])
            if registro["curso_codigo"] not in codigos_cursos:
                raise ValidacaoError(f"A disciplina {registro['codigo']} referencia um curso inexistente.")
            if any(codigo not in codigos_disciplinas for codigo in referencias[1:]):
                raise ValidacaoError(f"A disciplina {registro['codigo']} referencia disciplina inexistente.")
        if any(r["disciplina"] not in codigos_disciplinas for r in self._dados["turmas"]):
            raise ValidacaoError("Há turma vinculada a uma disciplina inexistente.")
        registros_matricula = list(self._registros_matricula())
        pares_matricula = [(r["aluno"], r["turma"]) for r in registros_matricula]
        if len(pares_matricula) != len(set(pares_matricula)):
            raise ValidacaoError("Há matrículas duplicadas para o mesmo aluno e turma.")
        if any(
            r["aluno"] not in matriculas or r.get("turma") not in turmas
            or not {"frequencia", "status"}.issubset(r)
            for r in registros_matricula
        ):
            raise ValidacaoError("Há matrícula inválida ou vinculada a aluno ou turma inexistente.")
        if any(r["matricula"] not in matriculas
               or any(turma not in turmas for turma in r["turmas_monitoradas"])
               for r in self._dados["monitores"]):
            raise ValidacaoError("Há monitoria vinculada a aluno ou turma inexistente.")
        if any(r["matricula"] not in matriculas for r in self._dados["relatorios"]):
            raise ValidacaoError("Há relatório vinculado a aluno inexistente.")
        usuarios = {item["usuario"].casefold() for item in self._dados["adm"]}
        for aluno in self._dados["alunos"]:
            tem_usuario = bool(aluno.get("usuario"))
            tem_senha = bool(aluno.get("senha_hash"))
            if tem_usuario != tem_senha:
                raise ValidacaoError(f"A conta do aluno {aluno['matricula']} está incompleta.")
            if tem_usuario:
                usuario = aluno["usuario"].casefold()
                if usuario in usuarios:
                    raise ValidacaoError("Há nomes de usuário duplicados entre alunos e administradores.")
                usuarios.add(usuario)

    def _persistir(self) -> None:
        """Grava os conjuntos alterados usando substituição atômica por arquivo."""
        if self._diretorio is None:
            return
        temporarios = []
        originais = {}
        substituidos = []
        try:
            for entidade, nome_arquivo in _ARQUIVOS.items():
                destino = self._diretorio / nome_arquivo
                temporario = destino.with_name(destino.name + ".tmp")
                originais[destino] = destino.read_bytes() if destino.exists() else None
                temporario.write_text(
                    json.dumps(self._dados[entidade], ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                temporarios.append((temporario, destino))
            for temporario, destino in temporarios:
                os.replace(temporario, destino)
                substituidos.append(destino)
        except OSError as erro:
            for temporario, _ in temporarios:
                temporario.unlink(missing_ok=True)
            for destino in reversed(substituidos):
                conteudo = originais[destino]
                if conteudo is None:
                    destino.unlink(missing_ok=True)
                else:
                    restauracao = destino.with_name(destino.name + ".restore")
                    restauracao.write_bytes(conteudo)
                    os.replace(restauracao, destino)
            raise ValidacaoError(f"Não foi possível salvar os dados JSON: {erro}.") from erro

    @contextmanager
    def transacao(self):
        """Agrupa gravações; em caso de erro restaura os dados mantidos em memória."""
        if self._nivel:
            self._nivel += 1
            try:
                yield
            finally:
                self._nivel -= 1
            return
        anterior = deepcopy(self._dados)
        self._alterado = False
        self._nivel = 1
        try:
            yield
            if self._alterado:
                self._persistir()
        except BaseException:
            self._dados = anterior
            raise
        finally:
            self._nivel = 0
            self._alterado = False

    def _marcar_alteracao(self) -> None:
        self._alterado = True

    @staticmethod
    def _exigir_unico(registros: list[dict], chave: str, valor: str) -> None:
        if any(registro.get(chave) == valor for registro in registros):
            raise DuplicidadeError("Registro duplicado: a chave já está cadastrada.")

    @staticmethod
    def _achar(registros: list[dict], chave: str, valor: str):
        return next((registro for registro in registros if registro.get(chave) == valor), None)

    def fechar(self) -> None:
        """Mantido para compatibilidade com a inicialização anterior."""

    # Cursos
    def salvar_curso(self, curso: Curso) -> None:
        with self.transacao():
            self._exigir_unico(self._dados["cursos"], "codigo", curso.codigo)
            self._dados["cursos"].append({"codigo": curso.codigo, "nome": curso.nome})
            self._marcar_alteracao()

    def buscar_curso(self, codigo: str):
        codigo = codigo.strip().upper()
        registro = self._achar(self._dados["cursos"], "codigo", codigo)
        return Curso(registro["codigo"], registro["nome"]) if registro else None

    def listar_cursos(self) -> list[Curso]:
        return [Curso(r["codigo"], r["nome"]) for r in sorted(
            self._dados["cursos"], key=lambda item: (item["nome"].casefold(), item["codigo"])
        )]

    # Disciplinas
    def salvar_disciplina(self, disciplina: Disciplina) -> None:
        with self.transacao():
            self._exigir_unico(self._dados["disciplinas"], "codigo", disciplina.codigo)
            if self.buscar_curso(disciplina.curso_codigo) is None:
                raise NaoEncontradoError(f"Curso {disciplina.curso_codigo} não encontrado.")
            for codigo in disciplina.pre_requisitos:
                if self.buscar_disciplina(codigo) is None:
                    raise NaoEncontradoError(f"Pré-requisito {codigo} não encontrado.")
            if disciplina.equivalente_a and self.buscar_disciplina(disciplina.equivalente_a) is None:
                raise NaoEncontradoError(f"Disciplina equivalente {disciplina.equivalente_a} não encontrada.")
            self._dados["disciplinas"].append({
                "codigo": disciplina.codigo,
                "nome": disciplina.nome,
                "carga_horaria": disciplina.carga_horaria,
                "curso_codigo": disciplina.curso_codigo,
                "tipo": disciplina.tipo,
                "pre_requisitos": disciplina.pre_requisitos,
                "equivalente_a": disciplina.equivalente_a,
            })
            self._marcar_alteracao()

    def buscar_disciplina(self, codigo: str):
        registro = self._achar(self._dados["disciplinas"], "codigo", codigo.strip().upper())
        if registro is None:
            return None
        return Disciplina(
            registro["codigo"], registro["nome"], registro["carga_horaria"],
            registro["curso_codigo"], registro.get("tipo", "Obrigatória"),
            registro.get("pre_requisitos", []), registro.get("equivalente_a"),
        )

    def listar_disciplinas(self, curso_codigo: str = None) -> list[Disciplina]:
        registros = self._dados["disciplinas"]
        if curso_codigo is not None:
            codigo = curso_codigo.strip().upper()
            registros = [r for r in registros if r["curso_codigo"] == codigo]
        registros = sorted(registros, key=lambda item: (item["nome"].casefold(), item["codigo"]))
        return [self.buscar_disciplina(r["codigo"]) for r in registros]

    def grafo_prerequisitos_disciplinas(self) -> dict[str, set[str]]:
        return {
            r["codigo"]: set(r.get("pre_requisitos", []))
            for r in self._dados["disciplinas"] if r.get("pre_requisitos")
        }

    def salvar_prerequisito_disciplina(self, codigo: str, prerequisito: str) -> None:
        codigo, prerequisito = codigo.strip().upper(), prerequisito.strip().upper()
        with self.transacao():
            disciplina = self._achar(self._dados["disciplinas"], "codigo", codigo)
            if disciplina is None:
                raise NaoEncontradoError(f"Disciplina {codigo} não encontrada.")
            if self.buscar_disciplina(prerequisito) is None:
                raise NaoEncontradoError(f"Pré-requisito {prerequisito} não encontrado.")
            if prerequisito in disciplina.setdefault("pre_requisitos", []):
                raise DuplicidadeError("Esse pré-requisito já está cadastrado.")
            disciplina["pre_requisitos"].append(prerequisito)
            self._marcar_alteracao()

    def codigos_equivalentes(self, codigo: str) -> set[str]:
        equivalentes = {codigo.strip().upper()}
        mudou = True
        while mudou:
            mudou = False
            for registro in self._dados["disciplinas"]:
                codigo_disciplina = registro["codigo"]
                equivalente = registro.get("equivalente_a")
                if equivalente and (codigo_disciplina in equivalentes or equivalente in equivalentes):
                    novos = {codigo_disciplina, equivalente} - equivalentes
                    if novos:
                        equivalentes.update(novos)
                        mudou = True
        return equivalentes

    # Alunos
    def salvar_aluno(self, aluno: Aluno) -> None:
        with self.transacao():
            self._exigir_unico(self._dados["alunos"], "matricula", aluno.matricula)
            if any(r["email"].casefold() == aluno.email.casefold() for r in self._dados["alunos"]):
                raise DuplicidadeError("Já existe um aluno cadastrado com esse e-mail.")
            self._dados["alunos"].append({
                "matricula": aluno.matricula,
                "nome_completo": aluno.nome_completo,
                "data_nascimento": aluno.data_nascimento,
                "email": aluno.email,
                "telefone": aluno.telefone,
                "curso": aluno.curso,
                "cr": aluno.cr,
                "status": aluno.status,
                "matriculas": [],
            })
            self._marcar_alteracao()

    def atualizar_aluno(self, aluno: Aluno) -> None:
        with self.transacao():
            registro = self._achar(self._dados["alunos"], "matricula", aluno.matricula)
            if registro is None:
                raise NaoEncontradoError(f"Aluno {aluno.matricula} não encontrado.")
            if any(
                r["matricula"] != aluno.matricula and r["email"].casefold() == aluno.email.casefold()
                for r in self._dados["alunos"]
            ):
                raise DuplicidadeError("Já existe um aluno cadastrado com esse e-mail.")
            registro.update({
                "nome_completo": aluno.nome_completo,
                "data_nascimento": aluno.data_nascimento,
                "email": aluno.email,
                "telefone": aluno.telefone,
                "curso": aluno.curso,
                "cr": aluno.cr,
                "status": aluno.status,
            })
            self._marcar_alteracao()

    def buscar_aluno(self, matricula: str, com_matriculas: bool = True):
        registro = self._achar(self._dados["alunos"], "matricula", matricula)
        if registro is None:
            return None
        turmas_monitoradas = self.monitorias_do_aluno(matricula)
        dados = {
            "nome_completo": registro["nome_completo"],
            "data_nascimento": registro["data_nascimento"],
            "email": registro["email"],
            "telefone": registro["telefone"],
            "matricula": registro["matricula"],
            "curso": registro["curso"],
            "cr": registro["cr"],
            "status": registro["status"],
        }
        aluno = Monitor(**dados, turmas_monitoradas=turmas_monitoradas) if turmas_monitoradas else Aluno(**dados)
        if com_matriculas:
            for registro_matricula in registro.get("matriculas", []):
                turma = self.buscar_turma(registro_matricula["turma"], com_alunos=False)
                if turma is not None:
                    aluno.registrar_matricula(
                        self._matricula_de_linha(registro_matricula, aluno, turma)
                    )
        return aluno

    def listar_alunos(self) -> list[Aluno]:
        registros = sorted(self._dados["alunos"], key=lambda item: item["nome_completo"].casefold())
        return [self.buscar_aluno(r["matricula"], com_matriculas=False) for r in registros]

    # Turmas
    def salvar_turma(self, turma: Turma) -> None:
        with self.transacao():
            self._exigir_unico(self._dados["turmas"], "id_oferta", turma.id_oferta)
            disciplina = self.buscar_disciplina(turma.disciplina.codigo)
            if disciplina is None:
                raise NaoEncontradoError(f"Disciplina {turma.disciplina.codigo} não encontrada.")
            self._dados["turmas"].append({
                "id_oferta": turma.id_oferta,
                "disciplina": turma.disciplina.codigo,
                "professor": turma.professor,
                "periodo": turma.periodo,
                "vagas": turma.vagas,
                "horario": turma.horario,
                "local": turma.local,
                "aberta": turma.aberta,
            })
            self._marcar_alteracao()

    def atualizar_turma(self, turma: Turma) -> None:
        with self.transacao():
            registro = self._achar(self._dados["turmas"], "id_oferta", turma.id_oferta)
            if registro is None:
                raise NaoEncontradoError(f"Turma {turma.id_oferta} não encontrada.")
            self._validar_capacidade_ativa(turma.id_oferta, turma.vagas, exigir_vaga=False)
            registro.update({
                "professor": turma.professor,
                "periodo": turma.periodo,
                "vagas": turma.vagas,
                "horario": turma.horario,
                "local": turma.local,
                "aberta": turma.aberta,
            })
            self._marcar_alteracao()

    def buscar_turma(self, id_oferta: str, com_alunos: bool = True):
        registro = self._achar(self._dados["turmas"], "id_oferta", id_oferta)
        return self._turma_de_registro(registro, com_alunos) if registro else None

    def listar_turmas(self, periodo: str = None) -> list[Turma]:
        registros = self._dados["turmas"]
        if periodo is not None:
            registros = [r for r in registros if r["periodo"] == periodo]
        return [self._turma_de_registro(r, True) for r in sorted(registros, key=lambda item: item["id_oferta"])]

    def _turma_de_registro(self, registro: dict, com_alunos: bool) -> Turma:
        disciplina = self.buscar_disciplina(registro["disciplina"])
        if disciplina is None:
            raise NaoEncontradoError(f"Disciplina {registro['disciplina']} não encontrada.")
        turma = Turma(
            registro["id_oferta"], disciplina, registro["professor"], registro["periodo"],
            registro["vagas"], registro.get("horario", {}), registro.get("local"),
        )
        if not registro.get("aberta", True):
            turma.fechar()
        if com_alunos:
            matriculas_ativas = [
                {**item, "aluno": aluno["matricula"]}
                for aluno in self._dados["alunos"]
                for item in aluno.get("matriculas", [])
                if item["turma"] == turma.id_oferta and item["status"] != Matricula.TRANCADO
            ]
            for item in matriculas_ativas:
                aluno = self.buscar_aluno(item["aluno"], com_matriculas=False)
                if aluno is not None:
                    turma._lista_alunos.append(aluno)
        return turma

    # Matrículas
    def salvar_matricula(self, matricula: Matricula) -> None:
        with self.transacao():
            self._validar_matricula(matricula)
            aluno = self._achar(self._dados["alunos"], "matricula", matricula.aluno.matricula)
            if aluno is None:
                raise NaoEncontradoError(f"Aluno {matricula.aluno.matricula} não encontrado.")
            turma = self.buscar_turma(matricula.turma.id_oferta, com_alunos=False)
            if turma is None:
                raise NaoEncontradoError(f"Turma {matricula.turma.id_oferta} não encontrada.")
            aluno.setdefault("matriculas", [])
            if any(r["turma"] == turma.id_oferta for r in aluno["matriculas"]):
                raise DuplicidadeError("O aluno já está matriculado nesta turma.")
            if matricula.status != Matricula.TRANCADO:
                self._validar_capacidade_ativa(turma.id_oferta, turma.vagas)
            registro = self._registro_matricula(matricula)
            registro.pop("aluno")
            aluno["matriculas"].append(registro)
            self._marcar_alteracao()

    def atualizar_matricula(self, matricula: Matricula) -> None:
        with self.transacao():
            self._validar_matricula(matricula)
            aluno = self._achar(self._dados["alunos"], "matricula", matricula.aluno.matricula)
            registro = next((r for r in (aluno or {}).get("matriculas", [])
                             if r["turma"] == matricula.turma.id_oferta), None)
            if registro is None:
                raise NaoEncontradoError("Matrícula não encontrada para esse aluno e turma.")
            if matricula.status != Matricula.TRANCADO:
                turma = self.buscar_turma(matricula.turma.id_oferta, com_alunos=False)
                if turma is None:
                    raise NaoEncontradoError(f"Turma {matricula.turma.id_oferta} não encontrada.")
                if registro["status"] == Matricula.TRANCADO:
                    self._validar_capacidade_ativa(turma.id_oferta, turma.vagas)
            dados = self._registro_matricula(matricula)
            dados.pop("aluno")
            registro.update(dados)
            self._marcar_alteracao()

    @staticmethod
    def _registro_matricula(matricula: Matricula) -> dict:
        return {
            "aluno": matricula.aluno.matricula,
            "turma": matricula.turma.id_oferta,
            "nota_1": matricula.nota_1 if matricula.nota_1_lancada else None,
            "nota_2": matricula.nota_2 if matricula.nota_2_lancada else None,
            "frequencia": matricula.frequencia,
            "frequencia_lancada": matricula.frequencia_lancada,
            "status": matricula.status,
            "data_trancamento": matricula.data_trancamento.isoformat() if matricula.data_trancamento else None,
        }

    @staticmethod
    def _validar_matricula(matricula: Matricula) -> None:
        if matricula.status in Matricula.SITUACOES_FINAIS and not matricula.notas_lancadas:
            raise ValidacaoError("Uma situação final exige que as duas notas estejam lançadas.")
        if (matricula.status == Matricula.TRANCADO) != (matricula.data_trancamento is not None):
            raise ValidacaoError("Matrícula trancada precisa de data; demais situações não podem tê-la.")

    def _validar_capacidade_ativa(self, id_oferta: str, capacidade: int, exigir_vaga: bool = True) -> None:
        ocupacao = sum(
            registro["turma"] == id_oferta and registro["status"] != Matricula.TRANCADO
            for aluno in self._dados["alunos"]
            for registro in aluno.get("matriculas", [])
        )
        if ocupacao > capacidade or (exigir_vaga and ocupacao >= capacidade):
            from models import TurmaLotadaError
            raise TurmaLotadaError(f"A turma {id_oferta} não tem vagas ativas disponíveis.")

    def _achar_matricula(self, matricula_aluno: str, id_oferta: str):
        aluno = self._achar(self._dados["alunos"], "matricula", matricula_aluno)
        return next((r for r in (aluno or {}).get("matriculas", [])
                     if r["turma"] == id_oferta), None)

    def trancar_matricula(self, matricula: Matricula, data_trancamento) -> None:
        with self.transacao():
            registro = self._achar_matricula(
                matricula.aluno.matricula, matricula.turma.id_oferta
            )
            if registro is None or registro["status"] != Matricula.CURSANDO:
                raise ValidacaoError("A matrícula não está cursando ou já foi alterada.")
            registro["status"] = Matricula.TRANCADO
            registro["data_trancamento"] = data_trancamento.isoformat()
            self._marcar_alteracao()

    def matriculas_de_aluno(self, matricula_aluno: str) -> list[Matricula]:
        aluno = self.buscar_aluno(matricula_aluno, com_matriculas=False)
        if aluno is None:
            raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
        resultado = []
        registro_aluno = self._achar(self._dados["alunos"], "matricula", matricula_aluno)
        for registro in registro_aluno.get("matriculas", []):
            turma = self.buscar_turma(registro["turma"], com_alunos=False)
            if turma is not None:
                resultado.append(self._matricula_de_linha(registro, aluno, turma))
        return resultado

    def matriculas_da_turma(self, id_oferta: str) -> list[Matricula]:
        turma = self.buscar_turma(id_oferta, com_alunos=False)
        if turma is None:
            raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
        resultado = []
        for registro in self._registros_matricula():
            if registro["turma"] == id_oferta:
                aluno = self.buscar_aluno(registro["aluno"], com_matriculas=False)
                if aluno is not None:
                    resultado.append(self._matricula_de_linha(registro, aluno, turma))
        return resultado

    def todas_matriculas(self) -> list[Matricula]:
        resultado = []
        for linha in self._registros_matricula():
            aluno = self.buscar_aluno(linha["aluno"], com_matriculas=False)
            turma = self.buscar_turma(linha["turma"], com_alunos=False)
            if aluno is not None and turma is not None:
                resultado.append(self._matricula_de_linha(linha, aluno, turma))
        return resultado

    def _matricula_de_linha(self, linha: dict, aluno: Aluno, turma: Turma) -> Matricula:
        matricula = Matricula(aluno, turma, self.configuracoes)
        if linha.get("nota_1") is not None:
            matricula.nota_1 = linha["nota_1"]
        if linha.get("nota_2") is not None:
            matricula.nota_2 = linha["nota_2"]
        if linha.get("frequencia_lancada", False):
            matricula.frequencia = linha.get("frequencia", 100.0)
        if linha.get("data_trancamento"):
            from datetime import date
            matricula.data_trancamento = date.fromisoformat(linha["data_trancamento"])
        matricula.status = linha["status"]
        return matricula

    # Monitores
    def salvar_monitoria(self, matricula_aluno: str, id_oferta: str) -> None:
        with self.transacao():
            if self.buscar_aluno(matricula_aluno, com_matriculas=False) is None:
                raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
            if self.buscar_turma(id_oferta, com_alunos=False) is None:
                raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
            monitor = self._achar(self._dados["monitores"], "matricula", matricula_aluno)
            if monitor is None:
                monitor = {"matricula": matricula_aluno, "turmas_monitoradas": []}
                self._dados["monitores"].append(monitor)
            if id_oferta in monitor["turmas_monitoradas"]:
                raise DuplicidadeError("O aluno já monitora essa turma.")
            monitor["turmas_monitoradas"].append(id_oferta)
            monitor["turmas_monitoradas"].sort()
            self._marcar_alteracao()

    def monitorias_do_aluno(self, matricula_aluno: str) -> set[str]:
        monitor = self._achar(self._dados["monitores"], "matricula", matricula_aluno)
        return set(monitor["turmas_monitoradas"]) if monitor else set()

    # Administradores
    def salvar_administrador(self, administrador: Adm, senha_hash: str) -> None:
        with self.transacao():
            self._exigir_unico(self._dados["adm"], "usuario", administrador.usuario)
            if any(
                str(registro.get("usuario") or "").casefold() == administrador.usuario.casefold()
                for registro in self._dados["alunos"]
            ):
                raise DuplicidadeError("Esse usuário já está cadastrado.")
            self._dados["adm"].append({
                "usuario": administrador.usuario,
                "senha_hash": senha_hash,
                "nome_completo": administrador.nome_completo,
                "email": administrador.email,
                "telefone": administrador.telefone,
            })
            self._marcar_alteracao()

    def buscar_administrador(self, usuario: str):
        registro = next((r for r in self._dados["adm"]
                         if r["usuario"].casefold() == usuario.strip().casefold()), None)
        if registro is None:
            return None
        return Adm(
            registro["nome_completo"], "", registro["email"], registro["telefone"],
            usuario=registro["usuario"],
        )

    # Relatórios individuais
    def salvar_relatorio_aluno(self, matricula_aluno: str, dados: dict) -> dict:
        with self.transacao():
            if self.buscar_aluno(matricula_aluno, com_matriculas=False) is None:
                raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
            if not isinstance(dados, dict):
                raise ValidacaoError("Os dados do relatório precisam ser um objeto JSON.")
            try:
                json.dumps(dados, ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError) as erro:
                raise ValidacaoError("O relatório contém dados que não podem ser salvos em JSON.") from erro
            registro = {
                "matricula": matricula_aluno,
                "gerado_em": datetime.now(timezone.utc).isoformat(),
                "dados": deepcopy(dados),
            }
            self._dados["relatorios"].append(registro)
            self._marcar_alteracao()
            return deepcopy(registro)

    def relatorios_do_aluno(self, matricula_aluno: str) -> list[dict]:
        if self.buscar_aluno(matricula_aluno, com_matriculas=False) is None:
            raise NaoEncontradoError(f"Aluno {matricula_aluno} não encontrado.")
        return deepcopy([
            registro for registro in self._dados["relatorios"]
            if registro["matricula"] == matricula_aluno
        ])

    # Credenciais de alunos
    def salvar_credenciais_aluno(self, matricula: str, usuario: str, senha_hash: str) -> None:
        with self.transacao():
            aluno = self._achar(self._dados["alunos"], "matricula", matricula)
            if aluno is None:
                raise NaoEncontradoError("Aluno vinculado à conta não encontrado.")
            if any(r["usuario"].casefold() == usuario.casefold() for r in self._dados["adm"]):
                raise DuplicidadeError("Esse usuário já está cadastrado.")
            if any(
                r["matricula"] != matricula
                and str(r.get("usuario") or "").casefold() == usuario.casefold()
                for r in self._dados["alunos"]
            ):
                raise DuplicidadeError("Esse usuário já está cadastrado.")
            if aluno.get("usuario"):
                if aluno["usuario"].casefold() != usuario.casefold():
                    raise DuplicidadeError("Esse aluno já possui uma conta de acesso.")
                if aluno.get("senha_hash"):
                    raise DuplicidadeError("Esse aluno já possui uma conta de acesso.")
            aluno["usuario"] = usuario
            aluno["senha_hash"] = senha_hash
            self._marcar_alteracao()

    def buscar_usuario_acesso(self, usuario: str):
        registro = next((r for r in self._dados["adm"]
                         if r["usuario"].casefold() == usuario.strip().casefold()), None)
        if registro:
            return {
                "usuario": registro["usuario"],
                "senha_hash": registro["senha_hash"],
                "papel": "adm",
                "matricula": None,
            }
        aluno = next((r for r in self._dados["alunos"]
                      if str(r.get("usuario") or "").casefold() == usuario.strip().casefold()
                      and r.get("senha_hash")), None)
        if aluno is None:
            return None
        return {
            "usuario": aluno["usuario"],
            "senha_hash": aluno["senha_hash"],
            "papel": "pessoa",
            "matricula": aluno["matricula"],
        }

    def tem_administrador(self) -> bool:
        return bool(self._dados["adm"])
