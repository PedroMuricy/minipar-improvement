"""Modulo didatico do Minipar: expoe cada etapa do compilador como JSON.
Uso no app.py:  from didatico import didatico_bp ; app.register_blueprint(didatico_bp)"""
import contextlib, io, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator
from codegen import CppCodeGenerator


class TracingAnalyzer(SemanticAnalyzer):
    """Mesmo analisador semantico, mas registra cada simbolo definido."""
    def __init__(self):
        self.symbols = []
        super().__init__()

    def _define_symbol(self, name, type_, line, params=None):
        self.symbols.append({"name": name, "type": type_, "line": line,
                             "scope": len(self._scopes) - 1,
                             "context": self._current_function or self._current_class or "global",
                             "params": params or []})
        super()._define_symbol(name, type_, line, params)


def to_dict(n):
    if isinstance(n, list):
        return [to_dict(x) for x in n]
    if hasattr(n, "__dict__"):
        d = {"_type": type(n).__name__}
        d.update({k: to_dict(v) for k, v in vars(n).items()})
        return d
    return n


def _capture(fn):
    """Roda uma fase capturando stderr e o sys.exit() dos erros do compilador."""
    buf = io.StringIO()
    ok, result = True, None
    with contextlib.redirect_stderr(buf):
        try:
            result = fn()
        except SystemExit:
            ok = False
    return ok, result, buf.getvalue()


def _errors(stage, text):
    out = []
    for ln in text.strip().splitlines():
        m = re.search(r"Linha (\d+)[^:]*: (.*)", ln)
        out.append({"stage": stage, "line": int(m.group(1)) if m else None,
                    "msg": (m.group(2) if m else ln)})
    return out


def analyze(code):
    res = {"ok": False, "stages": {}, "errors": [], "failed_stage": None}

    def fail(stage, text):
        res["failed_stage"] = stage
        res["errors"] = _errors(stage, text)
        return res

    ok, toks, err = _capture(lambda: Lexer(code).tokenize())
    res["stages"]["tokens"] = [{"type": t.type.name, "lexeme": t.lexeme, "line": t.line, "col": t.col} for t in toks]
    bad = [t for t in toks if t.type.name == "UNKNOWN"]
    if bad:
        res["errors"] = [{"stage": "tokens", "line": t.line, "msg": f"Caractere invalido {t.lexeme!r}"} for t in bad]
        res["failed_stage"] = "tokens"
        return res

    ok, prog, err = _capture(lambda: Parser(toks).parse())
    if not ok:
        return fail("ast", err)
    res["stages"]["ast"] = to_dict(prog)

    sem = TracingAnalyzer()
    ok, passed, err = _capture(lambda: sem.analyze(prog))
    res["stages"]["symbols"] = sem.symbols
    if not passed:
        return fail("symbols", err)

    res["stages"]["tac"] = TACGenerator().generate_text(prog)
    res["stages"]["cpp"] = CppCodeGenerator().build_cpp(prog)
    res["ok"] = True
    return res


try:
    from flask import Blueprint, jsonify, request, render_template
    didatico_bp = Blueprint("didatico", __name__)

    @didatico_bp.route("/didatico")
    def pagina():
        return render_template("didatico.html")

    @didatico_bp.route("/api/stages", methods=["POST"])
    def stages():
        code = (request.get_json(silent=True) or {}).get("code", "")
        return jsonify(analyze(code.lstrip("\ufeff")))
except ImportError:
    didatico_bp = None
