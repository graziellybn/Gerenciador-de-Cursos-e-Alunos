"""Relatórios acadêmicos e fórmulas adotadas.

Taxa de aprovação = aprovações / matrículas finalizadas (somente estados finais).
Trancamentos e matrículas cursando não entram no denominador. Distribuição de
notas usa média, mediana e desvio-padrão populacional (pstdev) das médias finais.
Top N ordena CR decrescente; empates são resolvidos por nome e matrícula crescentes.
Risco acadêmico considera matrícula cursando com média parcial abaixo do corte
(ao menos uma nota lançada) ou frequência abaixo do mínimo.
"""

from statistics import mean, median, pstdev

from database.repositorio import Repositorio
from models import AutenticacaoError, NaoEncontradoError
from models.matricula import Matricula
from services.auth_service import (
    Sessao,
    exigir_administrador,
    exigir_aluno_proprio,
)


class RelatorioService:
    def __init__(self, repo: Repositorio, configuracoes=None):
        self._repo = repo
        self._config = configuracoes or repo.configuracoes

    @staticmethod
    def _exigir_acesso_turma(sessao, id_oferta: str) -> None:
        if isinstance(sessao, Sessao) and sessao.papel == "adm":
            exigir_administrador(sessao)
            return
        aluno = exigir_aluno_proprio(sessao)
        if sessao.papel != "monitor":
            raise AutenticacaoError("Este relatório é exclusivo para administradores e monitores.")
        aluno.exigir_monitoria(id_oferta)

    def alunos_por_turma(self, id_oferta: str, sessao=None) -> dict:
        self._exigir_acesso_turma(sessao, id_oferta)
        turma = self._repo.buscar_turma(id_oferta)
        if turma is None:
            raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
        return {
            "turma": turma,
            "ocupadas": len(turma),
            "vagas": turma.vagas,
            "alunos": sorted(turma.lista_alunos, key=lambda a: a.nome_completo.casefold()),
        }

    def formatar_alunos_por_turma(self, id_oferta: str, sessao=None) -> str:
        dados = self.alunos_por_turma(id_oferta, sessao=sessao)
        turma = dados["turma"]
        linhas = [
            f"Turma {turma.id_oferta} - {turma.disciplina.nome} ({turma.periodo})",
            f"Vagas ocupadas: {dados['ocupadas']}/{dados['vagas']}",
        ]
        if dados["alunos"]:
            linhas.extend(
                f"  {i}. {aluno.nome_completo} ({aluno.matricula})"
                for i, aluno in enumerate(dados["alunos"], start=1)
            )
        else:
            linhas.append("  (nenhum aluno matriculado)")
        return "\n".join(linhas)

    def taxa_aprovacao_turma(self, id_oferta: str, sessao=None) -> dict:
        exigir_administrador(sessao)
        turma = self._repo.buscar_turma(id_oferta, com_alunos=False)
        if turma is None:
            raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
        finais = [m for m in self._repo.matriculas_da_turma(id_oferta)
                  if m.status in Matricula.SITUACOES_FINAIS]
        aprovados = sum(m.status == Matricula.APROVADO for m in finais)
        return {"turma": turma, "finalizadas": len(finais), "aprovados": aprovados,
                "taxa": aprovados / len(finais) if finais else None}

    def taxa_aprovacao_curso(self, codigo_curso: str, sessao=None) -> dict:
        exigir_administrador(sessao)
        curso = self._repo.buscar_curso(codigo_curso)
        if curso is None:
            raise NaoEncontradoError(f"Curso {codigo_curso} não encontrado.")
        disciplinas = {d.codigo for d in self._repo.listar_disciplinas(curso.codigo)}
        finais = []
        for m in self._repo.todas_matriculas():
            if m.turma.disciplina.codigo not in disciplinas or m.status not in Matricula.SITUACOES_FINAIS:
                continue
            finais.append(m)
        aprovados = sum(m.status == Matricula.APROVADO for m in finais)
        return {"curso": curso, "finalizadas": len(finais), "aprovados": aprovados,
                "taxa": aprovados / len(finais) if finais else None}

    def distribuicao_notas_turma(self, id_oferta: str, sessao=None) -> dict:
        exigir_administrador(sessao)
        turma = self._repo.buscar_turma(id_oferta, com_alunos=False)
        if turma is None:
            raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
        notas = [m.calcular_media() for m in self._repo.matriculas_da_turma(id_oferta)
                 if m.status in Matricula.SITUACOES_FINAIS and m.notas_lancadas]
        return {
            "turma": turma,
            "quantidade": len(notas),
            "media": mean(notas) if notas else None,
            "mediana": median(notas) if notas else None,
            "desvio_padrao": pstdev(notas) if notas else None,
            "notas": notas,
        }

    def top_n_alunos_por_cr(self, n: int = None, sessao=None) -> list:
        exigir_administrador(sessao)
        n = self._config.top_n_alunos if n is None else n
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise ValueError("N deve ser um inteiro positivo.")
        alunos = []
        for aluno in self._repo.listar_alunos():
            completo = self._repo.buscar_aluno(aluno.matricula)
            completo.recalcular_cr()
            alunos.append(completo)
        return sorted(alunos, key=lambda a: (-a.cr, a.nome_completo.casefold(), a.matricula))[:n]

    def alunos_em_risco(self, sessao=None) -> list[dict]:
        exigir_administrador(sessao)
        riscos = []
        for matricula in self._repo.todas_matriculas():
            if matricula.status != Matricula.CURSANDO:
                continue
            notas = [nota for nota, lançada in (
                (matricula.nota_1, matricula.nota_1_lancada),
                (matricula.nota_2, matricula.nota_2_lancada),
            ) if lançada]
            parcial = mean(notas) if notas else None
            motivos = []
            if parcial is not None and parcial < self._config.nota_minima_aprovacao:
                motivos.append("nota abaixo do mínimo")
            if matricula.frequencia < self._config.frequencia_minima:
                motivos.append("frequência abaixo do mínimo")
            if motivos:
                riscos.append({"aluno": matricula.aluno, "matricula": matricula,
                               "media_parcial": parcial, "motivos": tuple(motivos)})
        return sorted(riscos, key=lambda r: (
            r["aluno"].nome_completo.casefold(), r["matricula"].turma.id_oferta
        ))

    def relatorio_proprio_por_turma(self, sessao, id_oferta: str) -> str:
        aluno = exigir_aluno_proprio(sessao)
        turma = self._repo.buscar_turma(id_oferta, com_alunos=False)
        if turma is None:
            raise NaoEncontradoError(f"Turma {id_oferta} não encontrada.")
        matricula = next((m for m in self._repo.matriculas_de_aluno(aluno.matricula)
                          if m.turma.id_oferta == id_oferta), None)
        if matricula is None:
            raise NaoEncontradoError("Você não possui matrícula nessa turma.")
        if not matricula.notas_lancadas or not matricula.frequencia_lancada:
            texto = (
                f"{turma.id_oferta} — {turma.disciplina.nome}: "
                "notas e frequência ainda não registradas."
            )
        else:
            texto = (
                f"{turma.id_oferta} — {turma.disciplina.nome}: {matricula.status}; "
                f"média {matricula.calcular_media():.1f}; frequência {matricula.frequencia:.0f}%"
            )
        self._repo.salvar_relatorio_aluno(aluno.matricula, {
            "tipo": "relatorio_individual_por_turma",
            "turma": turma.id_oferta,
            "disciplina": turma.disciplina.nome,
            "situacao": matricula.status,
            "notas_registradas": matricula.notas_lancadas,
            "nota_1": matricula.nota_1 if matricula.nota_1_lancada else None,
            "nota_2": matricula.nota_2 if matricula.nota_2_lancada else None,
            "frequencia_registrada": matricula.frequencia_lancada,
            "frequencia": matricula.frequencia if matricula.frequencia_lancada else None,
            "media": matricula.calcular_media() if matricula.notas_lancadas else None,
            "texto": texto,
        })
        return texto

    def relatorio_monitoria(self, sessao, id_oferta: str) -> str:
        exigir_aluno_proprio(sessao)
        if sessao.papel != "monitor":
            raise AutenticacaoError("Este relatório é exclusivo para monitores.")
        return self.formatar_alunos_por_turma(id_oferta, sessao=sessao)

    def relatorio_admin(self, sessao, operacao: str, *args):
        exigir_administrador(sessao)
        operacoes = {
            "taxa_turma": self.taxa_aprovacao_turma,
            "taxa_curso": self.taxa_aprovacao_curso,
            "notas_turma": self.distribuicao_notas_turma,
            "top_n": self.top_n_alunos_por_cr,
            "risco": self.alunos_em_risco,
        }
        if operacao not in operacoes:
            raise ValueError("Tipo de relatório inválido.")
        return operacoes[operacao](*args, sessao=sessao)
