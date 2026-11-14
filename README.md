# MiniPar 2026.2 — Compilador

Compilador educacional da linguagem **MiniPar**, desenvolvido em Python para a disciplina de Compiladores da Universidade Federal de Alagoas (UFAL).

O projeto amplia a versão anterior da linguagem com suporte a **programação paralela (fork/join)** e uma segunda interface Web com finalidade didática.

## Funcionalidades

- Análise léxica e sintática.
- Construção e visualização da AST.
- Análise semântica e tabela de símbolos.
- Geração de código intermediário (TAC).
- Geração de código C++.
- Compilação e execução de programas.
- Suporte a paralelismo com `fork` e `join`.
- Interface de terminal.
- Interface Web para desenvolvedores.
- Interface Web didática para visualização das etapas de compilação.

## Tecnologias

- Python 3.14
- Flask 3.0
- C++20
- GCC
- `std::thread`

## Como Executar

Instale as dependências:

```bash
pip install Flask==3.0.0
```

Certifique-se de possuir o GCC instalado e disponível no PATH.

Inicie o projeto:

```bash
python main.py
```

Em seguida, escolha uma das opções disponíveis:

1. **Modo Terminal:** utilização pelo terminal.
2. **Modo Web:** acesso à interface Web pelo navegador.

A interface didática pode ser acessada por meio do botão disponível na interface Web principal.

## Documentação

Consulte o arquivo `BNF-grammar.md` para visualizar a gramática formal da linguagem MiniPar.

O relatório do projeto apresenta detalhes da arquitetura, implementação, interfaces e testes.

## Autores

- Caio César Medeiros Lopes
- Elton Gonçalves Alves
- Felipe Gabriel Marques dos Santos
- Pedro Henrique Vicente do Nascimento

**Universidade Federal de Alagoas — Instituto de Computação**  
Disciplina: Compiladores | 2026.2
