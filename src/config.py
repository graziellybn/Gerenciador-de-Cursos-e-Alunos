"""Carregamento validado da configuração acadêmica central."""

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

from models import ValidacaoError

CAMINHO_CONFIGURACAO = Path(__file__).resolve().parents[1] / "settings.json"


@dataclass(frozen=True)
class Configuracoes:
    nota_minima_aprovacao: float = 7.0
    frequencia_minima: float = 75.0
    data_limite_trancamento: date = date(2099, 12, 31)
    max_turmas_por_aluno: int | None = None
    top_n_alunos: int = 5


def carregar_configuracoes(caminho: str | Path = CAMINHO_CONFIGURACAO) -> Configuracoes:
    """Lê settings.json; configuração malformada nunca é ignorada silenciosamente."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ValidacaoError(f"Arquivo de configuração não encontrado: {caminho}.")
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ValidacaoError(f"Não foi possível ler settings.json: {erro}.") from erro
    if not isinstance(dados, dict):
        raise ValidacaoError("settings.json deve conter um objeto JSON.")

    permitidas = {
        "nota_minima_aprovacao", "frequencia_minima", "data_limite_trancamento",
        "max_turmas_por_aluno", "top_n_alunos",
    }
    extras = set(dados) - permitidas
    if extras:
        raise ValidacaoError(f"Configurações desconhecidas: {', '.join(sorted(extras))}.")

    nota = dados.get("nota_minima_aprovacao", 7.0)
    frequencia = dados.get("frequencia_minima", 75.0)
    max_turmas = dados.get("max_turmas_por_aluno")
    top_n = dados.get("top_n_alunos", 5)
    data_texto = dados.get("data_limite_trancamento", "2099-12-31")

    if isinstance(nota, bool) or not isinstance(nota, (int, float)) or not 0 <= nota <= 10:
        raise ValidacaoError("nota_minima_aprovacao deve ser um número entre 0 e 10.")
    if (isinstance(frequencia, bool) or not isinstance(frequencia, (int, float))
            or not 0 <= frequencia <= 100):
        raise ValidacaoError("frequencia_minima deve ser um número entre 0 e 100.")
    if max_turmas is not None and (
        isinstance(max_turmas, bool) or not isinstance(max_turmas, int) or max_turmas < 1
    ):
        raise ValidacaoError("max_turmas_por_aluno deve ser null ou um inteiro positivo.")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ValidacaoError("top_n_alunos deve ser um inteiro positivo.")
    if not isinstance(data_texto, str):
        raise ValidacaoError("data_limite_trancamento deve usar o formato YYYY-MM-DD.")
    try:
        limite = date.fromisoformat(data_texto)
    except ValueError as erro:
        raise ValidacaoError("data_limite_trancamento deve ser uma data válida em YYYY-MM-DD.") from erro
    if limite.isoformat() != data_texto:
        raise ValidacaoError("data_limite_trancamento deve usar exatamente o formato YYYY-MM-DD.")

    return Configuracoes(float(nota), float(frequencia), limite, max_turmas, top_n)
