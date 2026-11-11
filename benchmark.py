"""Benchmark de speedup do Minipar (fork/join).

Uso:  python benchmark.py            (no Windows com MinGW, na raiz do projeto)
Gera: benchmark_results.md e benchmark_results.json

Metodologia:
  - A COMPILACAO nao entra na medida: so o tempo de execucao do .exe.
  - 1 execucao de aquecimento (descartada) + N execucoes medidas; usa-se a MEDIANA.
  - Os testes nao fazem o mesmo trabalho (o teste 10 faz 120M iteracoes, os outros 100M),
    entao o speedup e calculado sobre a VAZAO (iteracoes por segundo) em relacao ao baseline.
  - Speedup ideal = numero de threads; eficiencia = speedup / threads.
"""
import json, os, platform, statistics, subprocess, sys, time

RUNS = 7
# (arquivo, threads, iteracoes totais)
CASES = [
    ("teste_baseline_1core", 1, 100_000_000),
    ("teste8_paralelo_4cores", 4, 100_000_000),
    ("teste9_paralelo_5cores", 5, 100_000_000),
    ("teste10_paralelo_6cores", 6, 120_000_000),
]


def build(stem):
    r = subprocess.run([sys.executable, "main.py", os.path.join("tests", stem + ".minipar")],
                       capture_output=True, text=True)
    for ext in (".exe", ""):
        p = os.path.join("output", stem + ext)
        if r.returncode == 0 and os.path.isfile(p):
            return os.path.abspath(p)
    sys.exit(f"[ERRO] Falha ao compilar {stem}:\n{r.stdout[-600:]}\n{r.stderr[-600:]}")


def measure(exe):
    subprocess.run([exe], stdout=subprocess.DEVNULL)  # aquecimento
    ts = []
    for _ in range(RUNS):
        t = time.perf_counter()
        subprocess.run([exe], stdout=subprocess.DEVNULL)
        ts.append(time.perf_counter() - t)
    return ts


def main():
    cores = os.cpu_count()
    print(f"Maquina: {platform.processor() or platform.machine()} | nucleos logicos: {cores} | {RUNS} execucoes por teste\n")
    rows = []
    for stem, threads, work in CASES:
        print(f"-> {stem} ({threads} thread(s)) ...", flush=True)
        ts = measure(build(stem))
        rows.append({"teste": stem, "threads": threads, "iteracoes": work,
                     "mediana_ms": statistics.median(ts) * 1000, "min_ms": min(ts) * 1000,
                     "max_ms": max(ts) * 1000})
    base = rows[0]["iteracoes"] / rows[0]["mediana_ms"]
    for r in rows:
        r["vazao_Miter_s"] = r["iteracoes"] / r["mediana_ms"] / 1000
        r["speedup"] = (r["iteracoes"] / r["mediana_ms"]) / base
        r["eficiencia_pct"] = r["speedup"] / r["threads"] * 100

    md = [f"Nucleos logicos da maquina: {cores}. Mediana de {RUNS} execucoes (so execucao, sem compilacao).\n",
          "| Teste | Threads | Iteracoes | Mediana (ms) | Min-Max (ms) | Vazao (M it/s) | Speedup | Eficiencia |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['teste']} | {r['threads']} | {r['iteracoes']:,} | {r['mediana_ms']:.1f} | "
                  f"{r['min_ms']:.1f}-{r['max_ms']:.1f} | {r['vazao_Miter_s']:.0f} | {r['speedup']:.2f}x | {r['eficiencia_pct']:.0f}% |")
    if cores and max(r["threads"] for r in rows) > cores:
        md.append(f"\nAviso: ha testes com mais threads que nucleos logicos ({cores}); o speedup deles nao pode passar de {cores}x.")
    open("benchmark_results.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump({"cores": cores, "runs": RUNS, "rows": rows}, open("benchmark_results.json", "w", encoding="utf-8"), indent=2)
    print("\n" + "\n".join(md) + "\n\nSalvo em benchmark_results.md e benchmark_results.json")


if __name__ == "__main__":
    main()
