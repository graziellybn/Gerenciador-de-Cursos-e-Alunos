# Gerenciador-de-Cursos-e-Alunos
- **Universidade Federal do Cariri (UFCA)**
- **Aluno:** Grazielly Bibiano 
- **Professor:** Jayr Alencar

---

## 📌​ Visão Geral
O **Sistema de Gerenciamento de Cursos e Alunos** é uma solução desenvolvida para centralizar e administrar dados relacionados ao ambiente acadêmico, contemplando cursos, turmas, alunos e matrículas. A proposta consiste em representar, de forma estruturada, processos como o controle de matrículas, a verificação de pré-requisitos, a disponibilidade de vagas e horários, além do registro de notas e frequência. O projeto tem como foco a aplicação prática dos conceitos de **Programação Orientada a Objetos (POO)**, empregando recursos como encapsulamento, herança, métodos especiais, validações e relacionamentos entre classes para modelar os diferentes componentes e regras que compõem o ambiente acadêmico. 

----

## 📎​ Objetivo Geral
- Permitir que uma instituição de ensino gerencie, por linha de comando, cursos, turmas, alunos, matrículas e desempenho acadêmico. O sistema aplica automaticamente as regras acadêmicas e gera relatórios a partir dos dados.

## 🖇️​ Objetivos Específicos
- Gerenciar cursos, turmas, alunos e suas respectivas informações;
- Controlar matrículas, considerando pré-requisitos, horários, vagas e limites configurados;
- Registrar e acompanhar notas, frequência e situação acadêmica dos alunos;
- Permitir o trancamento de matrículas conforme as regras estabelecidas;
- Gerar relatórios para acompanhamento do desempenho acadêmico;
- Aplicar conceitos de POO, como encapsulamento, herança, métodos especiais e validações;
- Garantir a integridade e a persistência dos dados utilizando SQLite;
- Disponibilizar uma interface de linha de comando (CLI) para interação com o sistema.

---

## 📂 Estrutura do Projeto

```
gerenciador_de_cursos_e_alunos/
│
├── main.py
├── settings.json
├── config.py
│
├── models/
│   ├── __init__.py
│   ├── aluno.py
│   ├── curso.py
│   ├── matricula.py
│   ├── monitor.py
│   ├── pessoa.py
│   └── turma.py
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── curso_service.py
│   ├── matricula_service.py
│   └── relatorio_service.py
│
├── database/
│   ├── __init__.py
│   ├── repositorio.py
│   ├── schema.sql
│   └── seed.py
│
├── cli/
│   ├── __init__.py
│   └── menu.py
│
├── tests/
│   ├── conftest.py
│   ├── test_aluno.py
│   ├── test_curso.py
│   ├── test_matricula.py
│   ├── test_monitor.py
│   ├── test_relatorios.py
│   └── test_turma.py
│
├── .gitignore
├── README.md
└── requirements.txt
```
