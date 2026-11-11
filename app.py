import os
import sys
import time
import subprocess
from flask import Flask, render_template, request, jsonify, send_file

# Registra a pasta src no Python para os módulos internos se encontrarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer

try:
    from program_analyzer import get_program_spec
except ImportError:
    def get_program_spec(path):
        return {}

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEMP_CODE_DIR = os.path.join(os.path.dirname(__file__), "temp_code")
TESTS_DIR = os.path.join(os.path.dirname(__file__), "tests")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_CODE_DIR, exist_ok=True)

def carregar_arquivo_teste(nome_arquivo, fallback=""):
    caminho = os.path.join(TESTS_DIR, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8-sig", errors="ignore") as f:
            return f.read()
    return fallback

EXEMPLOS = {
    "fork_join": carregar_arquivo_teste("teste_fork_join.minipar", """# Exemplo Didatico: Fork / Join
func tarefa(id, limite) {
    var soma = 0;
    var i = 0;
    while (i < limite) {
        soma = soma + i;
        i = i + 1;
    }
    print("Thread ", id, " concluida. Soma = ", soma);
}

print("Disparando threads...");
fork tarefa(1, 5000000);
fork tarefa(2, 5000000);
join;
print("Sincronizacao join concluida!");
"""),
    "teste8_4cores": carregar_arquivo_teste("teste8_paralelo_4cores.minipar", """# Teste 8: Paralelismo com 4 Cores
func worker_4(id, inicio, fim) {
    var acc = 0;
    var i = inicio;
    while (i < fim) {
        acc = acc + ((i % 5) * (i % 3));
        i = i + 1;
    }
    print("Worker [", id, "] finalizou fatia. Subtotal: ", acc);
}

fork worker_4(1, 0, 25000000);
fork worker_4(2, 25000000, 50000000);
fork worker_4(3, 50000000, 75000000);
fork worker_4(4, 75000000, 100000000);
join;
print("Concluido: Todas as 4 threads finalizaram!");
"""),
    "baseline": carregar_arquivo_teste("teste_baseline_1core.minipar", """# Baseline Sequencial: 1 Nucleo
func worker_seq(inicio, fim) {
    var acc = 0;
    var i = inicio;
    while (i < fim) {
        acc = acc + ((i % 5) * (i % 3));
        i = i + 1;
    }
    print("Resultado sequencial: ", acc);
}

print("Iniciando Baseline em 1 nucleo...");
worker_seq(0, 100000000);
print("Baseline concluido!");
""")
}

def formatar_tokens(tokens):
    linhas = [
        f"Total de Tokens Reconhecidos: {len(tokens)}",
        "=" * 68,
        f"{'#':<5} | {'TIPO DO TOKEN':<20} | {'LEXEMA (VALOR)':<25} | {'LINHA'}",
        "-" * 68
    ]
    for idx, t in enumerate(tokens, 1):
        tipo = getattr(t, "type", getattr(t, "tipo", type(t).__name__))
        valor = getattr(t, "value", getattr(t, "valor", getattr(t, "lexeme", str(t))))
        linha = getattr(t, "line", getattr(t, "linha", getattr(t, "lineno", "-")))
        if str(tipo).upper() == "EOF":
            valor = "<EOF>"
        linhas.append(f"{idx:03d}   | {str(tipo):<20} | {repr(valor):<25} | {linha}")
    return "\n".join(linhas)

def desenhar_ast(no, prefixo="", eh_ultimo=True):
    marcador = "└── " if eh_ultimo else "├── "
    if no is None or isinstance(no, (str, int, float, bool)):
        return f"{prefixo}{marcador}{repr(no)}\n"

    nome_classe = no.__class__.__name__
    atributos = getattr(no, "__dict__", {})
    
    simples = []
    filhos = []
    for chave, valor in atributos.items():
        if chave.startswith("_"):
            continue
        if isinstance(valor, (str, int, float, bool)) or valor is None:
            simples.append(f"{chave}={repr(valor)}")
        elif isinstance(valor, list):
            filhos.append((chave, valor))
        elif hasattr(valor, "__dict__"):
            filhos.append((chave, [valor]))

    resumo = f" ({', '.join(simples)})" if simples else ""
    saida = f"{prefixo}{marcador}{nome_classe}{resumo}\n"
    novo_prefixo = prefixo + ("    " if eh_ultimo else "│   ")

    for idx_f, (nome_campo, lista_itens) in enumerate(filhos):
        ultimo_campo = (idx_f == len(filhos) - 1)
        m_campo = "└── " if ultimo_campo else "├── "
        saida += f"{novo_prefixo}{m_campo}[{nome_campo}]\n"
        pref_itens = novo_prefixo + ("    " if ultimo_campo else "│   ")
        for idx_i, item in enumerate(lista_itens):
            saida += desenhar_ast(item, pref_itens, idx_i == len(lista_itens) - 1)

    return saida

def gerar_relatorio_semantico(ast_raiz, obj_semantico):
    funcoes = []
    variaveis = []
    forks = []
    joins = 0

    def percorrer(no, escopo="Global"):
        nonlocal joins
        if no is None or not hasattr(no, "__dict__"):
            return
        nome_no = no.__class__.__name__
        d = no.__dict__

        if "Func" in nome_no and ("name" in d or "nome" in d):
            nome_f = d.get("name") or d.get("nome")
            params = d.get("params") or d.get("parametros") or []
            funcoes.append((nome_f, params))
            escopo = f"func:{nome_f}"
        elif "Var" in nome_no and ("name" in d or "nome" in d):
            nome_v = d.get("name") or d.get("nome")
            variaveis.append((nome_v, escopo))
        elif "Fork" in nome_no:
            alvo = d.get("func_name") or d.get("name") or d.get("call") or "thread_worker"
            if hasattr(alvo, "__dict__"):
                alvo = alvo.__dict__.get("name") or alvo.__dict__.get("func_name") or str(alvo.__class__.__name__)
            forks.append((str(alvo), escopo))
        elif "Join" in nome_no:
            joins += 1

        for val in d.values():
            if isinstance(val, list):
                for item in val:
                    percorrer(item, escopo)
            elif hasattr(val, "__dict__"):
                percorrer(val, escopo)

    percorrer(ast_raiz)

    rel = [
        "STATUS: Análise Semântica concluída com sucesso (0 erros).",
        "=" * 68,
        "\n1. TABELA DE FUNÇÕES DECLARADAS:"
    ]
    if funcoes:
        for f_nome, f_params in funcoes:
            rel.append(f"   • {f_nome}({', '.join(str(p) for p in f_params)}) -> Escopo Local Criado")
    else:
        rel.append("   • (Nenhuma função declarada)")

    rel.append("\n2. TABELA DE SÍMBOLOS (VARIÁVEIS E ESCOPOS):")
    if variaveis:
        for v_nome, v_esc in variaveis:
            rel.append(f"   • Variável '{v_nome:<12}' | Escopo: {v_esc}")
    else:
        rel.append("   • (Nenhuma variável explícita declarada com 'var')")

    rel.append("\n3. VALIDAÇÃO DE CONCORRÊNCIA (FORK / JOIN):")
    rel.append(f"   • Disparos paralelos (fork): {len(forks)} thread(s) validada(s)")
    for idx, (f_alvo, f_esc) in enumerate(forks, 1):
        rel.append(f"     [{idx}] fork -> {f_alvo} (em {f_esc})")
    rel.append(f"   • Barreiras de sincronização (join): {joins}")

    return "\n".join(rel)

# -----------------------------------------------------------------------------
# ROTAS DE PÁGINAS (HTML)
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/didatica")
def didatica():
    return render_template("didatica.html")

# -----------------------------------------------------------------------------
# ROTAS DA API UTILIZADAS PELO SCRIPT.JS (INTERFACE AVANÇADA / DIDÁTICA)
# -----------------------------------------------------------------------------
@app.route("/api/tests", methods=["GET"])
def listar_testes():
    arquivos = []
    if os.path.exists(TESTS_DIR):
        arquivos = [f for f in os.listdir(TESTS_DIR) if f.endswith(".minipar")]
    return jsonify({"tests": arquivos})

@app.route("/api/get_test", methods=["POST"])
def obter_teste():
    dados = request.get_json() or {}
    filename = dados.get("filename", "")
    caminho = os.path.join(TESTS_DIR, filename)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8-sig", errors="ignore") as f:
            return jsonify({"code": f.read()})
    return jsonify({"error": "Arquivo não encontrado"}), 404

@app.route("/api/test_spec", methods=["POST"])
def obter_test_spec():
    dados = request.get_json() or {}
    filename = dados.get("filename", "")
    caminho = os.path.join(TESTS_DIR, filename)
    if os.path.exists(caminho):
        return jsonify(get_program_spec(caminho))
    return jsonify({})

@app.route("/api/compile", methods=["POST"])
def api_compile():
    dados = request.get_json() or {}
    codigo_fonte = dados.get("code") or dados.get("codigo", "")
    
    if not codigo_fonte.strip():
        return jsonify({"success": False, "error": "O código-fonte está vazio."}), 400

    caminho_minipar = os.path.join(OUTPUT_DIR, "web_temp.minipar")
    with open(caminho_minipar, "w", encoding="utf-8") as f:
        f.write(codigo_fonte)

    try:
        processo = subprocess.run(
            [sys.executable, "main.py", caminho_minipar],
            capture_output=True,
            text=True,
            timeout=15
        )

        success = (processo.returncode == 0)
        
        tac_content = ""
        cpp_content = ""
        tac_path = os.path.join(OUTPUT_DIR, "web_temp.tac")
        cpp_path = os.path.join(OUTPUT_DIR, "web_temp.cpp")

        if os.path.exists(tac_path):
            with open(tac_path, "r", encoding="utf-8", errors="ignore") as f:
                tac_content = f.read()

        if os.path.exists(cpp_path):
            with open(cpp_path, "r", encoding="utf-8", errors="ignore") as f:
                cpp_content = f.read()

        stdout = processo.stdout
        stderr = processo.stderr

        # Se compilou C++, tenta rodar para capturar a saída real do programa
        if success and os.path.exists(cpp_path):
            exe_path = os.path.join(OUTPUT_DIR, "web_temp.exe")
            cmd_gpp = ["g++", "-O3", "-std=c++20", cpp_path, "-o", exe_path, "-lws2_32"]
            comp_proc = subprocess.run(cmd_gpp, capture_output=True, text=True, timeout=20)
            if comp_proc.returncode == 0:
                exec_proc = subprocess.run([exe_path], capture_output=True, text=True, timeout=15)
                stdout = f"{stdout}\n--- Execução ---\n{exec_proc.stdout}"

        return jsonify({
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "tac": tac_content,
            "cpp": cpp_content,
            "error": stderr if not success else None
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/download_executable", methods=["GET"])
def download_executable():
    exe_path = os.path.join(OUTPUT_DIR, "web_temp.exe")
    if os.path.exists(exe_path):
        return send_file(exe_path, as_attachment=True, download_name="minipar_app.exe")
    return "Executável não encontrado. Compile primeiro.", 404

# -----------------------------------------------------------------------------
# ROTAS DA API UTILIZADAS PELO DIDATICA.JS
# -----------------------------------------------------------------------------
@app.route("/api/exemplo/<nome>", methods=["GET"])
def carregar_exemplo(nome):
    codigo = EXEMPLOS.get(nome, "# Exemplo nao encontrado")
    return jsonify({"codigo": codigo})

@app.route("/api/compilar", methods=["POST"])
def compilar():
    dados = request.get_json() or {}
    codigo_fonte = dados.get("codigo") or dados.get("code", "")

    if not codigo_fonte.strip():
        return jsonify({"sucesso": False, "erro": "O código-fonte está vazio."}), 400

    caminho_minipar = os.path.join(OUTPUT_DIR, "web_temp.minipar")
    with open(caminho_minipar, "w", encoding="utf-8") as f:
        f.write(codigo_fonte)

    resultado = {
        "sucesso": True,
        "tokens": "",
        "ast": "",
        "semantico": "",
        "tac": "",
        "cpp": "",
        "erro": ""
    }

    try:
        processo = subprocess.run(
            [sys.executable, "main.py", caminho_minipar],
            capture_output=True,
            text=True,
            timeout=15
        )

        if processo.returncode != 0:
            resultado["sucesso"] = False
            resultado["erro"] = processo.stderr or processo.stdout
            return jsonify(resultado)

        lexer = Lexer(codigo_fonte)
        tokens = lexer.tokenize() if hasattr(lexer, "tokenize") else getattr(lexer, "tokens", [])
        resultado["tokens"] = formatar_tokens(tokens)

        parser = Parser(tokens)
        ast_raiz = parser.parse()
        resultado["ast"] = "ÁRVORE SINTÁTICA ABSTRATA (AST)\n" + ("=" * 68) + "\n" + desenhar_ast(ast_raiz)

        sem = SemanticAnalyzer()
        if hasattr(sem, "analyze"):
            sem.analyze(ast_raiz)
        resultado["semantico"] = gerar_relatorio_semantico(ast_raiz, sem)

        tac_path = os.path.join(OUTPUT_DIR, "web_temp.tac")
        cpp_path = os.path.join(OUTPUT_DIR, "web_temp.cpp")

        if os.path.exists(tac_path):
            with open(tac_path, "r", encoding="utf-8", errors="ignore") as f:
                resultado["tac"] = f.read()

        if os.path.exists(cpp_path):
            with open(cpp_path, "r", encoding="utf-8", errors="ignore") as f:
                resultado["cpp"] = f.read()

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route("/api/executar", methods=["POST"])
def executar():
    cpp_path = os.path.join(OUTPUT_DIR, "web_temp.cpp")
    exe_path = os.path.join(OUTPUT_DIR, "web_temp.exe")

    if not os.path.exists(cpp_path):
        return jsonify({"sucesso": False, "saida": "O arquivo C++ não foi gerado. Compile primeiro."}), 400

    try:
        cmd_gpp = ["g++", "-O3", "-std=c++20", cpp_path, "-o", exe_path, "-lws2_32"]
        comp_proc = subprocess.run(cmd_gpp, capture_output=True, text=True, timeout=20)

        if comp_proc.returncode != 0:
            return jsonify({"sucesso": False, "saida": f"Erro de compilação C++ (g++):\n{comp_proc.stderr}"}), 400

        inicio = time.perf_counter()
        exec_proc = subprocess.run([exe_path], capture_output=True, text=True, timeout=15)
        fim = time.perf_counter()

        tempo_ms = round((fim - inicio) * 1000, 2)

        return jsonify({
            "sucesso": True,
            "saida": exec_proc.stdout if exec_proc.stdout else "(Executado sem saídas de texto)",
            "tempo_ms": tempo_ms
        })

    except Exception as e:
        return jsonify({"sucesso": False, "saida": f"Falha na execução: {str(e)}"}), 500

if __name__ == "__main__":
    print("Iniciando servidor MiniPar em http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)