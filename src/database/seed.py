from database.repositorio import Repositorio
from models.aluno import Aluno
from models.curso import Curso
from models.disciplina import Disciplina
from models.matricula import Matricula
from models.turma import Turma
from services.aluno_service import AlunoService


def _aluno(matricula: str, nome: str) -> Aluno:
    return Aluno(nome, "2003-05-10", f"{matricula}@aluno.uniesquina.edu.br", "88999990000",
                 matricula, "ES001")


def popular(repo: Repositorio) -> None:
    """Cria dados acadêmicos demonstrativos em um banco vazio."""
    curso = Curso("ES001", "Engenharia de Software")
    repo.salvar_curso(curso)

    alg = Disciplina("ALG101", "Algoritmos", 60, curso)
    poo = Disciplina("POO101", "Programação Orientada a Objetos", 60, curso,
                     pre_requisitos=["ALG101"])
    bd = Disciplina("BD101", "Banco de Dados", 60, curso, tipo="Optativa",
                    equivalente_a="ALG101")
    for disciplina in (alg, poo, bd):
        repo.salvar_disciplina(disciplina)

    turmas = (
        Turma("ALG-2026.1", alg, "Prof. Lima", "2026.1", 30,
              {"seg": "08:00-10:00"}),
        Turma("ALG-2026.2", alg, "Prof. Lima", "2026.2", 30,
              {"seg": "08:00-10:00"}),
        Turma("POO-2026.2", poo, "Profa. Souza", "2026.2", 2,
              {"ter": "10:00-12:00", "qui": "10:00-12:00"}),
        Turma("BD-2026.2", bd, "Prof. Alves", "2026.2", 30,
              {"ter": "11:00-13:00"}),
    )
    for turma in turmas:
        repo.salvar_turma(turma)

    gerador_matricula = AlunoService(repo)
    alunos = []
    for nome in ("Ana Beatriz", "Bruno Costa", "Carla Dias", "Diego Reis"):
        aluno = _aluno(gerador_matricula.gerar_matricula(), nome)
        repo.salvar_aluno(aluno)
        alunos.append(aluno)

    turma_passada = repo.buscar_turma("ALG-2026.1", com_alunos=False)
    for aluno, nota1, nota2 in ((alunos[0], 9.0, 8.5), (alunos[1], 7.0, 8.0)):
        matricula = Matricula(aluno, turma_passada)
        matricula.nota_1, matricula.nota_2 = nota1, nota2
        matricula.atualizar_status()
        repo.salvar_matricula(matricula)

    for aluno, id_oferta in (
        (alunos[0], "POO-2026.2"),
        (alunos[1], "POO-2026.2"),
        (alunos[2], "BD-2026.2"),
    ):
        aluno = repo.buscar_aluno(aluno.matricula, com_matriculas=False)
        turma = repo.buscar_turma(id_oferta, com_alunos=False)
        repo.salvar_matricula(Matricula(aluno, turma, repo.configuracoes))
    repo.salvar_monitoria(alunos[0].matricula, "ALG-2026.2")
