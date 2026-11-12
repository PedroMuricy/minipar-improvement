const $ = i => document.getElementById(i), esc = s => String(s).replace(/[&<>]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"}[c]));
const S = [
  {k: "tokens", n: "Léxico", q: "Como o computador “lê” o texto?", w: "O lexer quebra o texto em pedaços chamados tokens. Cada pílula abaixo é um token: palavras reservadas (como fork e join) em laranja, nomes em azul, números em verde, textos em rosa."},
  {k: "ast", n: "Sintático", q: "Que estrutura o programa tem?", w: "O parser confere a gramática (BNF) e organiza os tokens numa árvore. Clique num nó para recolher ou expandir seus filhos."},
  {k: "symbols", n: "Semântico", q: "O programa faz sentido?", w: "Verifica-se se tudo que é usado foi declarado e se as chamadas estão corretas. Cada símbolo declarado entra na tabela com seu escopo."},
  {k: "tac", n: "Intermediário", q: "Como simplificar para a máquina?", w: "O código de três endereços quebra tudo em instruções com no máximo uma operação. fork inicia uma thread; join espera todas terminarem."},
  {k: "par", n: "Paralelismo", q: "O que roda ao mesmo tempo?", w: "Cada fork abre uma nova linha de execução. O join é uma barreira: a thread principal só segue quando todas as outras terminam."},
  {k: "cpp", n: "C++", q: "Qual é o programa final?", w: "A AST vira C++20: cada fork vira uma std::thread guardada numa lista, e o join chama .join() em todas."},
  {k: "run", n: "Executar", q: "E o resultado?", w: "O código é compilado com g++ -O3 e executado pelo servidor."}
];
const NEED = {par: "ast"};
let cur = 0, cache = null, cachedCode = null, coll = null, AST = null, tm;

async function analyze() {
  const code = $("src").value;
  if (cache && cachedCode === code) return cache;
  const r = await fetch("/api/stages", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({code})});
  cache = await r.json(); cachedCode = code; coll = null; marks(); return cache;
}

function marks() {
  document.querySelectorAll("#steps li").forEach((li, i) => {
    const k = S[i].k, has = k === "run" || !cache || cache.stages[NEED[k] || k] !== undefined;
    li.classList.toggle("off", !has); li.classList.toggle("bad", !!cache && cache.failed_stage === k);
  });
}

const errs = d => d.errors.map(e => `<div class="err">✖ ${e.line ? "Linha " + e.line + ": " : ""}${esc(e.msg)}</div>`).join("");
const cat = t => /STRING/.test(t.type) ? "s" : /^(NUMBER|INT|FLOAT)/.test(t.type) ? "n" : /^[A-Za-z_]/.test(t.lexeme) ? (/^ID/.test(t.type) ? "i" : "k") : "p";
const table = (h, rows) => `<table><tr>${h.map(x => `<th>${x}</th>`).join("")}</tr>${rows.join("")}</table>`;

const kids = n => Object.entries(n).filter(([k, v]) => k !== "_type" && v && typeof v === "object").flatMap(([, v]) => Array.isArray(v) ? v : [v]).filter(x => x && x._type);
const lab = n => { const m = ["name", "op", "operator", "value", "var_type"].find(k => n[k] !== undefined && typeof n[k] !== "object"); return n._type + (m ? " " + n[m] : ""); };
function init(n, d, id) { if (d >= 3 && kids(n).length) coll.add(id); kids(n).forEach((c, i) => init(c, d + 1, id + "." + i)); }
function lay(n, d, id, st) {
  const o = {n, d, id, c: [], h: kids(n).length > 0};
  if (!coll.has(id)) kids(n).forEach((c, i) => o.c.push(lay(c, d + 1, id + "." + i, st)));
  o.y = o.c.length ? (o.c[0].y + o.c[o.c.length - 1].y) / 2 : st.r++ * 30; st.all.push(o); return o;
}

function drawTree() {
  if (!coll) { coll = new Set(); init(AST, 0, "r"); }
  const st = {r: 0, all: []}; lay(AST, 0, "r", st);
  const W = (Math.max(...st.all.map(o => o.d)) + 1) * 190 + 20, H = st.r * 30 + 10; let s = `<svg width="${W}" height="${H}" font-size="12">`;
  st.all.forEach(o => o.c.forEach(c => s += `<path d="M${o.d * 190 + 170} ${o.y + 14} C${o.d * 190 + 185} ${o.y + 14} ${c.d * 190 - 15} ${c.y + 14} ${c.d * 190} ${c.y + 14}" stroke="var(--bd)" stroke-width="2" fill="none"/>`));
  st.all.forEach(o => {
    const f = /Fork|Join|ParBlock/.test(o.n._type), t = lab(o.n) + (o.h && coll.has(o.id) ? "  ＋" : "");
    s += `<g data-id="${o.id}" data-h="${o.h ? 1 : 0}" style="cursor:${o.h ? "pointer" : "default"}"><rect x="${o.d * 190}" y="${o.y + 3}" width="170" height="22" rx="7" fill="${f ? "var(--fk)" : "var(--card)"}" stroke="${f ? "var(--fk)" : "var(--ac)"}" stroke-width="1.5"/><text x="${o.d * 190 + 9}" y="${o.y + 18}" fill="${f ? "#000" : "var(--tx)"}">${esc(t.length > 25 ? t.slice(0, 24) + "…" : t)}</text></g>`;
  });
  $("viz").innerHTML = `<div class="scroll">${s}</svg></div><div class="hint">Nós com ＋ têm filhos recolhidos. Clique para abrir. Nós laranja são fork/join/par.</div>`;
  $("viz").querySelectorAll("g").forEach(g => g.onclick = () => { if (g.dataset.h !== "1") return; const id = g.dataset.id; coll.has(id) ? coll.delete(id) : coll.add(id); drawTree(); });
}

function events(n, out) {
  if (Array.isArray(n)) return n.forEach(x => events(x, out));
  if (!n || typeof n !== "object" || n._type === "FuncDecl") return;
  if (n._type === "ForkNode") { const c = n.target_call || {}; out.push({t: "f", l: (c.name || "?") + "()", line: n.line}); }
  else if (n._type === "JoinNode") out.push({t: "j", line: n.line});
  else if (n._type === "ParBlock") out.push({t: "f", l: "bloco par", line: n.line});
  Object.values(n).forEach(v => events(v, out));
}

function timeline(ev) {
  const W = 120, x0 = 60, nf = ev.filter(e => e.t === "f").length, H = 56 + nf * 40, end = x0 + (ev.length + 1) * W, pos = ev.map((e, i) => ({...e, x: x0 + (i + 1) * W}));
  let k = 0, s = `<svg width="${end + 30}" height="${H}" font-size="12"><text x="4" y="34" fill="var(--mu)">main</text><line x1="${x0}" y1="30" x2="${end}" y2="30" stroke="var(--tx)" stroke-width="3"/>`;
  pos.forEach(e => {
    if (e.t === "f") {
      const y = 30 + ++k * 40, j = pos.find(p => p.t === "j" && p.x > e.x), x2 = j ? j.x : end;
      s += `<path d="M${e.x} 30 L${e.x + 16} ${y} L${x2} ${y}" stroke="var(--fk)" stroke-width="3" fill="none"/><text x="${e.x + 20}" y="${y - 7}" fill="var(--fk)">${esc(e.l)}</text><text x="${e.x - 8}" y="20" fill="var(--fk)">fork</text>`;
      if (j) s += `<path d="M${x2} ${y} L${x2} 30" stroke="var(--fk)" stroke-width="2" stroke-dasharray="3" fill="none"/>`;
    } else s += `<line x1="${e.x}" y1="12" x2="${e.x}" y2="${H - 8}" stroke="var(--ac)" stroke-width="2" stroke-dasharray="5"/><text x="${e.x + 5}" y="${H - 12}" fill="var(--ac)">join (barreira)</text>`;
  });
  return s + "</svg>";
}

const hl = t => t.split("\n").map(l => /\bfork\b|\bjoin\b|std::thread|\.join\(\)/.test(l) ? `<span class="f">${esc(l)}</span>` : esc(l)).join("\n");

async function render() {
  const {k, n, q, w} = S[cur], v = $("viz");
  document.querySelectorAll("#steps li").forEach((li, i) => li.classList.toggle("on", i === cur));
  $("q").textContent = `${cur + 1}. ${q}`; $("why").textContent = w; $("pos").textContent = `${n} · etapa ${cur + 1} de ${S.length}`;
  $("prev").disabled = cur === 0; $("next").disabled = cur === S.length - 1;
  
  if (k === "run") {
    v.innerHTML = '<div class="note">Compilando e executando…</div>';
    try {
      const code = $("src").value;
      const regexInput = /input\s*\(\s*(".*?"|'.*?'|)\s*\)/g;
      const matches = [...code.matchAll(regexInput)];
      const inputs = [];

      // Solicita os dados de entrada via prompt se houver chamadas input()
      if (matches.length > 0) {
        for (let i = 0; i < matches.length; i++) {
          const promptTexto = matches[i][1].replace(/["']/g, '').trim() || `Entrada ${i + 1}`;
          const valor = prompt(`[${i + 1}/${matches.length}] Digite o valor para:\n\n${promptTexto}`);
          if (valor === null) {
            v.innerHTML = '<div class="note">[INFO] Execução cancelada pelo usuário.</div>';
            return;
          }
          inputs.push(valor.trim());
        }
      }

      const d = await (await fetch("/api/compile", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code, filename: "didatico.minipar", inputs})
      })).json();
      
      v.innerHTML = `<pre${d.success ? "" : ' class="err"'}>${esc(d.success ? (d.stdout || "(sem saída)") : (d.stderr || d.error || "Erro na execução."))}</pre>`
      + (d.success ? `<a class="btn pri" href="/api/download_exe" download style="display:inline-block;margin-top:12px;text-decoration:none">⬇ Baixar executável</a>` : "");
    } catch (e) { v.innerHTML = '<div class="err">Servidor de compilação indisponível.</div>'; }
    return;
  }
  
  const d = await analyze(), data = d.stages[NEED[k] || k]; v.innerHTML = d.errors.length ? errs(d) : "";
  if (data === undefined) { v.innerHTML += '<div class="note">Esta etapa não foi alcançada: corrija o erro acima primeiro.</div>'; return; }
  
  if (k === "tokens") v.innerHTML += `<div class="legend">${data.filter(t => t.lexeme).length} tokens · passe o mouse para ver o tipo</div><div class="chips">${data.filter(t => t.lexeme).map((t, i, a) => `${i && t.line !== a[i - 1].line ? "<br>" : ""}<span class="chip ${cat(t)}" title="${t.type} · linha ${t.line}">${esc(t.lexeme)}</span>`).join("")}</div>`;
  else if (k === "ast") { AST = data; drawTree(); }
  else if (k === "symbols") v.innerHTML += table(["nome", "tipo", "escopo", "contexto", "linha"], data.map(s => `<tr><td>${esc(s.name)}</td><td>${esc(s.type)}</td><td>${s.scope}</td><td>${esc(s.context)}</td><td>${s.line}</td></tr>`));
  else if (k === "par") {
    const ev = []; events(data, ev);
    v.innerHTML += ev.length ? `<div class="scroll">${timeline(ev)}</div><div class="hint">${ev.filter(e => e.t === "f").length} bloco(s)/fork(s) e ${ev.filter(e => e.t === "j").length} join(s) no programa.</div>` : '<div class="note">Este programa não usa paralelismo (fork/join ou bloco par). Experimente carregar o exemplo teste_fork_join.</div>';
  } else v.innerHTML += `<pre>${hl(data)}</pre>`;
}

S.forEach((s, i) => { const li = document.createElement("li"); li.innerHTML = `<b>${i + 1}</b>${s.n}`; li.onclick = () => { cur = i; render(); }; $("steps").appendChild(li); });
$("prev").onclick = () => { if (cur > 0) { cur--; render(); } }; $("next").onclick = () => { if (cur < S.length - 1) { cur++; render(); } };
$("src").value = `func tarefa(id) {\n    print("Thread", id);\n}\n\nfork tarefa(1);\nfork tarefa(2);\njoin;\nprint("Fim");\n`;
$("src").oninput = () => { clearTimeout(tm); tm = setTimeout(() => { cache = null; render(); }, 450); };
$("clear").onclick = () => { $("src").value = ""; cache = null; render(); };
$("file").onchange = e => { const f = e.target.files[0]; if (f) f.text().then(t => { $("src").value = t.replace(/^\ufeff/, ""); cache = null; render(); }); };
fetch("/api/tests").then(r => r.json()).then(d => d.tests.forEach(t => $("examples").add(new Option(t, t)))).catch(() => { $("examples").style.display = "none"; });
$("examples").onchange = async e => { if (!e.target.value) return; const d = await (await fetch("/api/get_test", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({filename: e.target.value})})).json(); if (d.code) { $("src").value = d.code.replace(/^\ufeff/, ""); cache = null; render(); } };
render();