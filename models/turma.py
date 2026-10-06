from models.oferta import Oferta

class Turma(Oferta):

    def __init__(self, id_oferta: str, disciplina, professor: str, periodo: str,
    vagas: int, horario: str = "",):
        super().__init__(id_oferta, disciplina, professor, periodo, vagas)
        self.horario = horario
        self.lista_alunos = []

    def adicionar_aluno(self, aluno) -> bool:
        if not self.tem_vagas_disponiveis():
            print(f"Não é possível adicionar o aluno {aluno.nome_completo}. Não há vagas disponíveis.")
            return False

        if aluno in self.lista_alunos:
            print(f"O aluno {aluno.nome_completo} já está matriculado na turma.")
            return False

        self.lista_alunos.append(aluno)
        self.vagas -= 1
        return True

    def remover_aluno(self, aluno) -> bool:
        if aluno not in self.lista_alunos:
            raise ValueError("O aluno não está matriculado na turma.")

        self.lista_alunos.remove(aluno)
        self.vagas += 1
        return True

    def __len__(self) -> int:
        return len(self.lista_alunos)

    def __str__(self) -> str:
        return f"Turma {self.id_oferta} - {self.disciplina} | Matriculados: {len(self)}/{len(self) + self.vagas}"