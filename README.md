# 🎓 Gerenciador de Cursos e Alunos

## 1. 📌 Visão Geral

O **Sistema de Gerenciamento de Cursos e Alunos** é uma solução desenvolvida para centralizar e administrar dados relacionados ao ambiente acadêmico, contemplando cursos, turmas, alunos e matrículas.

A proposta consiste em representar, de forma estruturada, processos como o controle de matrículas, a verificação de pré-requisitos, a disponibilidade de vagas e horários, além do registro de notas e frequência.

O projeto tem como foco a aplicação prática dos conceitos de **Programação Orientada a Objetos (POO)**, empregando recursos como encapsulamento, herança, métodos especiais, validações e relacionamentos entre classes para modelar os diferentes componentes e regras que compõem o ambiente acadêmico.

---

## 2. 🎯 Objetivos

### 2.1. 📎 Objetivo Geral

- Permitir que uma instituição de ensino gerencie, por linha de comando, cursos, turmas, alunos, matrículas e desempenho acadêmico. O sistema aplica automaticamente as regras acadêmicas e gera relatórios a partir dos dados.

### 2.2. 🖇️ Objetivos Específicos

- Gerenciar cursos, turmas, alunos e suas respectivas informações;
- Controlar matrículas, considerando pré-requisitos, horários, vagas e limites configurados;
- Registrar e acompanhar notas, frequência e situação acadêmica dos alunos;
- Permitir o trancamento de matrículas conforme as regras estabelecidas;
- Gerar relatórios para acompanhamento do desempenho acadêmico;
- Aplicar conceitos de POO, como encapsulamento, herança, métodos especiais e validações;
- Garantir a integridade e a persistência dos dados utilizando arquivos JSON;
- Disponibilizar uma interface de linha de comando (CLI) para interação com o sistema.

---

## 3. 📂 Estrutura do Projeto

```text
├── src/
│   ├── main.py
│   ├── config.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── menu.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── repositorio.py
│   │   ├── seed.py
│   │   └── data/                 # Dados JSON locais, ignorados pelo Git
│   │       ├── adm.json
│   │       ├── alunos.json
│   │       ├── cursos.json
│   │       ├── disciplinas.json
│   │       ├── monitores.json
│   │       ├── relatorios_alunos.json
│   │       └── turmas.json
│   ├── models/
│   │   ├── __init__.py
│   │   ├── adm.py
│   │   ├── aluno.py
│   │   ├── curso.py
│   │   ├── disciplina.py
│   │   ├── matricula.py
│   │   ├── monitor.py
│   │   ├── oferta.py
│   │   ├── pessoa.py
│   │   └── turma.py
│   └── services/
│       ├── __init__.py
│       ├── aluno_service.py
│       ├── auth_service.py
│       ├── curso_service.py
│       ├── disciplina_service.py
│       ├── matricula_service.py
│       ├── relatorio_service.py
│       └── turma_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_aluno.py
    ├── test_auth.py
    ├── test_cli.py
    ├── test_curso.py
    ├── test_matricula.py
    ├── test_relatorios.py
    └── test_turma.py
```

---

## 4. 🗂️ Organização e Classes Principais

### 4.1. 📁 Organização dos arquivos

- **main.py:** inicialização, criação inicial do administrador, login e ciclo de sessão.
- **config.py:** carrega e valida as regras acadêmicas.
- **menu.py:** menus por perfil, entrada de dados e mensagens.
- **repositorio.py:** leitura e gravação das entidades em JSON.
- **seed.py:** dados demonstrativos da opção `--demo`.
- **data:** dados locais gerados durante o uso; ficam fora do Git.
- **models:** entidades, relações e validações do domínio.
- **services:** regras e operações de negócio.
- **tests:** testes automatizados.

### 4.2. 🧩 Classes principais

- **Pessoa e ComPermissoes:** dados comuns e consulta de permissões.
- **Adm:** perfil administrativo.
- **Aluno:** perfil do aluno, matrícula institucional, CR e histórico acadêmico.
- **Monitor:** aluno com permissões e turmas de monitoria.
- **Curso e Disciplina:** catálogo e relações curriculares.
- **Oferta e Turma:** dados da oferta de uma disciplina, capacidade e horários.
- **Matricula:** vínculo acadêmico com notas, frequência, situação e trancamento.

---

## 5. 🏷️ Regras de Negócio

### 5.1. Cursos e Disciplinas

- **RN01:** Cada curso deve possuir código único e nome.
- **RN02:** Toda disciplina deve estar vinculada a um curso cadastrado e possuir código, nome, carga horária e tipo (Obrigatória ou Optativa).
- **RN03:** Os pré-requisitos e as equivalências devem corresponder a disciplinas cadastradas. Uma disciplina não pode ser pré-requisito ou equivalente a si mesma.
- **RN04:** A cadeia de pré-requisitos não pode formar ciclos.
- **RN05:** Uma disciplina equivalente pode ser utilizada para atender ao pré-requisito de outra disciplina.
- **RN06:** Uma turma só pode ser criada para uma disciplina previamente cadastrada.

### 5.2. Alunos e Contas

- **RN07:** Todo aluno deve estar vinculado a um curso cadastrado e possuir matrícula institucional única, gerada automaticamente no cadastro.
- **RN08:** O e-mail do aluno deve utilizar o domínio `@aluno.uniesquina.edu.br`.
- **RN09:** O primeiro acesso do aluno deve ser realizado com sua matrícula e seu e-mail cadastrado, permitindo a criação de uma senha com pelo menos oito caracteres.
- **RN10:** As senhas devem ser armazenadas em formato de hash.
- **RN11:** O Coeficiente de Rendimento (CR) deve permanecer entre 0 e 10.

### 5.3. Turmas e Horários

- **RN12:** Uma turma representa a oferta de uma disciplina em determinado período e deve possuir professor, capacidade, horários e local.
- **RN13:** A capacidade de uma turma não pode ser inferior à quantidade de alunos com matrículas ativas.
- **RN14:** Uma turma fechada não pode receber novas matrículas.
- **RN15:** Os horários devem utilizar dias válidos da semana e o formato `HH:MM-HH:MM`, com horário final posterior ao inicial.
- **RN16:** Não são permitidas sobreposições de horários entre turmas de um mesmo aluno, inclusive durante a atualização de uma turma já ocupada.

### 5.4. Matrículas

- **RN17:** A matrícula acadêmica estabelece o vínculo entre um aluno e uma turma, não podendo existir mais de uma matrícula do mesmo aluno na mesma turma.
- **RN18:** A matrícula só pode ser realizada se a turma estiver aberta e possuir vagas disponíveis.
- **RN19:** O aluno deve cumprir os pré-requisitos da disciplina, diretamente ou por meio de uma disciplina equivalente.
- **RN20:** O sistema deve respeitar o limite de turmas cursadas pelo aluno no mesmo período, quando configurado.
- **RN21:** Matrículas trancadas não ocupam vagas e não são consideradas em conflitos de horário.
- **RN22:** O trancamento só pode ocorrer enquanto a matrícula estiver com situação Cursando e dentro do prazo configurado.

### 5.5. Notas, Frequência e Situação Acadêmica

- **RN23:** As notas devem estar entre 0 e 10, e a frequência deve ser um percentual entre 0 e 100.
- **RN24:** A média só deve ser calculada após o lançamento das duas notas, utilizando a fórmula: `média = (nota1 + nota2) / 2`.
- **RN25:** A aprovação exige que a média e a frequência atinjam os limites mínimos definidos nas configurações do sistema.
- **RN26:** A situação acadêmica deve ser atualizada conforme os resultados, podendo ser: Cursando, Aprovado, Reprovado por nota, Reprovado por frequência, Reprovado por nota e frequência ou Trancado.
- **RN27:** Não é permitido lançar notas em matrículas trancadas.
- **RN28:** O CR deve ser recalculado após a finalização das matrículas, considerando as médias obtidas e as respectivas cargas horárias como pesos. Caso não existam resultados finalizados, o CR será 0.

### 5.6. Monitoria e Permissões

- **RN29:** Somente administradores autenticados podem cadastrar cursos, disciplinas, alunos e turmas, lançar notas e designar monitores.
- **RN30:** O administrador deve utilizar um e-mail com o domínio `@adm.uniesquina.edu.br`, sendo permitido o cadastro de uma conta administrativa inicial.
- **RN31:** Para ser designado monitor, o aluno deve ter sido aprovado anteriormente na disciplina correspondente e não pode estar matriculado na turma monitorada.
- **RN32:** O monitor pode consultar apenas os relatórios das turmas para as quais foi designado.
- **RN33:** O aluno pode consultar somente seu próprio histórico acadêmico.
- **RN34:** Sessões ausentes ou inválidas não concedem permissões administrativas.

### 5.7. Relatórios

- **RN35:** O sistema deve calcular a taxa de aprovação por turma e por curso, considerando somente matrículas finalizadas.
- **RN36:** O sistema deve apresentar a distribuição das médias finais por turma, incluindo quantidade, média, mediana e desvio-padrão populacional.
- **RN37:** O sistema deve gerar um ranking dos alunos por CR (Top N), utilizando nome e matrícula como critérios de desempate.
- **RN38:** O sistema deve identificar alunos em risco com base em notas parciais ou frequência abaixo dos limites estabelecidos.
- **RN39:** Os relatórios individuais devem apresentar a situação acadêmica do aluno e indicar quando notas ou frequência ainda não tiverem sido lançadas.

---

## 6. ⚙️ Instruções para Executar o Projeto

### 6.1. 🐧 Linux ou macOS

**1.** Abra um terminal na pasta raiz do projeto.

**2.** Crie um ambiente virtual:

```bash
python3 -m venv .venv
```

**3.** Ative o ambiente:

```bash
source .venv/bin/activate
```

**4.** Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

**5.** Inicie o sistema:

```bash
PYTHONPATH=src python src/main.py
```

Na primeira execução, crie a conta de administrador quando solicitado. Depois, use Entrar para abrir o menu administrativo.

### 6.2. 🪟 Windows PowerShell

**1.** Abra o PowerShell na pasta raiz do projeto.

**2.** Crie e ative o ambiente:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**3.** Instale as dependências e configure os imports:

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

**4.** Inicie a aplicação:

```powershell
python src/main.py
```

---

## 7. 🔐 Primeiro Acesso do Aluno

Depois que o administrador cadastrar um aluno:

1. Volte à tela de login.
2. Escolha **Primeiro acesso do aluno**.
3. Informe a matrícula gerada e o e-mail cadastrado.
4. Defina e confirme a senha.
5. Entre com matrícula e senha.

---

## 8. ⌨️ Atalhos da CLI

- Digite `0` durante uma operação para cancelá-la e retornar ao menu principal.
- No menu principal, digite `000` para encerrar a sessão e voltar ao login.
- No menu principal, digite `0` para sair da aplicação.

---

## 9. 🧪 Executar os Testes

Com o ambiente virtual ativado e na raiz do projeto, execute:

```bash
python -m pytest
```
----
- **Universidade:** Universidade Federal do Cariri (UFCA)
- **Aluno:** Grazielly Bibiano
- **Professor:** Jayr Alencar
---
