document.addEventListener("DOMContentLoaded", () => {
    const editorMinipar = CodeMirror.fromTextArea(document.getElementById("editor-minipar"), {
        mode: "clike",
        theme: "dracula",
        lineNumbers: true,
        autoCloseBrackets: true
    });

    const editorCpp = CodeMirror.fromTextArea(document.getElementById("editor-cpp"), {
        mode: "text/x-c++src",
        theme: "dracula",
        lineNumbers: true,
        readOnly: true
    });

    const editorTac = CodeMirror.fromTextArea(document.getElementById("editor-tac"), {
        mode: "clike",
        theme: "dracula",
        lineNumbers: true,
        readOnly: true
    });

    const testList         = document.getElementById("test-list");
    const currentFileLabel = document.getElementById("current-file");
    const terminalOutput   = document.getElementById("terminal-output");
    const btnRun           = document.getElementById("btn-run");
    const btnClear         = document.getElementById("btn-clear");
    const tabs             = document.querySelectorAll(".tab");

    let currentTestSpec = null;
    let progressPollTimer = null;
    let lastLogCount = 0;
    let isSessionJoiner = false;

    function stopProgressPoll() {
        if (progressPollTimer) {
            clearInterval(progressPollTimer);
            progressPollTimer = null;
        }
    }

    function formatProgressPanel(data) {
        const session = data.session;
        if (!session) return "";

        const myRole = session.participants?.find(
            p => p.terminal_id === data.terminal_id
        )?.role || "participante";

        const percent = session.progress_percent ?? 0;
        const filled = Math.floor(percent / 5);
        const bar = "█".repeat(filled) + "░".repeat(20 - filled);

        let text =
            "══ TERMINAL PARTICIPANTE — MONITOR DE PROGRESSO ══\n\n" +
            `Terminal : ${data.terminal_id}\n` +
            `Papel    : ${myRole}\n` +
            `Teste    : ${session.titulo || session.test_file}\n` +
            `Status   : ${session.phase_message || session.status}\n` +
            `[${bar}] ${percent}%\n\n` +
            "── LOG DE ATIVIDADE ──\n";

        (session.progress_log || []).forEach(entry => {
            const prefix = entry.source === "initiator" ? "→" : "•";
            text += `${prefix} [${entry.time}] ${entry.message}\n`;
        });

        if (session.execution_output) {
            text += "\n── SAÍDA DO INICIADOR ──\n";
            session.execution_output.trim().split("\n").slice(-6).forEach(line => {
                text += `  ${line}\n`;
            });
        }

        if (session.status === "completed") {
            text += "\n✓ Teste concluído pelo terminal iniciador.\n";
            stopProgressPoll();
        }

        return text;
    }

    function startProgressPoll() {
        stopProgressPoll();
        isSessionJoiner = true;
        lastLogCount = 0;

        progressPollTimer = setInterval(() => {
            fetch("/api/session")
                .then(res => res.json())
                .then(data => {
                    if (!data.active || !data.session) {
                        stopProgressPoll();
                        return;
                    }

                    const logLen = (data.session.progress_log || []).length;
                    if (logLen !== lastLogCount || data.session.status === "completed") {
                        terminalOutput.textContent = formatProgressPanel(data);
                        lastLogCount = logLen;
                    }

                    if (data.session.status === "completed") {
                        isSessionJoiner = false;
                    }
                });
        }, 500);
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.target).classList.add("active");
            editorCpp.refresh();
            editorTac.refresh();
        });
    });

    // Verifica sessão multi-terminal ativa ao carregar a IDE
    fetch("/api/session")
        .then(res => res.json())
        .then(data => {
            if (data.active && data.needs_choice) {
                showSessionChoiceDialog(data);
            } else if (data.active) {
                const isParticipant = data.session.participants?.some(
                    p => p.terminal_id === data.terminal_id
                );
                if (isParticipant && data.session.status !== "completed") {
                    startProgressPoll();
                } else {
                    terminalOutput.textContent =
                        `[Sessão ativa] Teste: ${data.session.titulo || data.session.test_file}\n` +
                        `Terminal: ${data.terminal_id}\n` +
                        `Participantes: ${data.session.participants.length}/${data.session.required_participants}`;
                }
            }
        });

    function showSessionChoiceDialog(sessionData) {
        const session = sessionData.session;
        const msg =
            `Teste em andamento: ${session.titulo || session.test_file}\n` +
            `Participantes: ${session.participants.length}/${session.required_participants}\n` +
            `Seu terminal: ${sessionData.terminal_id}\n\n` +
            `Deseja participar deste teste ou executar de forma independente?`;

        if (confirm(msg + "\n\nOK = Participar do teste\nCancelar = Modo independente")) {
            fetch("/api/session/join", { method: "POST" })
                .then(res => res.json())
                .then(result => {
                    if (result.success) {
                        const role = result.session.participants.slice(-1)[0].role;
                        terminalOutput.textContent =
                            `[OK] Você entrou como: ${role}\nIniciando monitor de progresso...\n`;
                        startProgressPoll();
                    }
                });
        }
    }

    fetch("/api/tests")
        .then(res => res.json())
        .then(data => {
            data.tests.forEach(test => {
                const li = document.createElement("li");
                li.textContent = test;
                li.onclick = () => loadTest(test, li);
                testList.appendChild(li);
            });
        });

    function loadTestSpec(filename) {
        return fetch("/api/test_spec", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename })
        })
        .then(res => res.json())
        .then(spec => {
            currentTestSpec = spec.titulo ? spec : null;
            return currentTestSpec;
        });
    }

    function loadTest(filename, element) {
        document.querySelectorAll(".test-list li").forEach(li => li.classList.remove("active"));
        if (element) element.classList.add("active");

        currentFileLabel.textContent = filename;
        terminalOutput.textContent = `Carregando ${filename}...`;
        terminalOutput.classList.remove("error-text");

        Promise.all([
            fetch("/api/get_test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename })
            }).then(res => res.json()),
            loadTestSpec(filename)
        ]).then(([data, spec]) => {
            if (data.code) {
                editorMinipar.setValue(data.code);
                editorCpp.setValue("");
                editorTac.setValue("");

                let info = "Arquivo carregado. Clique em 'Compile & Run'.";
                if (spec) {
                    const tags = [];
                    if (spec.requires_input) tags.push(`${spec.input_count || spec.inputs.length} input(s)`);
                    if (spec.multi_computer) tags.push(`${spec.multi_computer.count} terminais`);
                    if (tags.length) info += `\n[${tags.join(" | ")}]`;
                }
                terminalOutput.textContent = info;
            }
        });
    }

    async function collectInputs(spec) {
        if (!spec || !spec.requires_input || !spec.inputs.length) return [];

        let msg =
            `${spec.titulo}\n\n` +
            `Este programa possui ${spec.input_count || spec.inputs.length} entrada(s) input().\n` +
            `Informe os valores que serão enviados ao programa:\n\n`;
        spec.inputs.forEach((inp, i) => {
            const desc = inp.descricao || inp.prompt || `Entrada ${i + 1}`;
            msg += `[${i + 1}] ${desc}\n`;
        });
        alert(msg);

        const collected = [];
        for (let i = 0; i < spec.inputs.length; i++) {
            const inp = spec.inputs[i];
            const desc = inp.descricao || inp.prompt || `Entrada ${i + 1}`;
            const valor = prompt(`${desc}\n\nDigite o valor:`);
            if (valor === null) return null;
            collected.push(valor.trim());
        }
        return collected;
    }

    async function handleMultiComputer(spec, filename) {
        if (!spec || !spec.multi_computer || !spec.multi_computer.required) return true;

        const multi = spec.multi_computer;
        let msg =
            `${spec.titulo}\n\n${spec.descricao}\n\n` +
            `Este teste exige ${multi.count} computador(es/terminais).\n\n` +
            `Papéis:\n`;
        multi.roles.forEach((role, i) => { msg += `  [${i + 1}] ${role}\n`; });
        msg += `\n${multi.instrucoes}\n\n` +
            `Abra outro terminal e execute: python main.py\n` +
            `Escolha 'Continuar teste em andamento' no novo terminal.\n\n` +
            `Pressione OK quando o(s) outro(s) terminal(is) estiver(em) pronto(s).`;

        if (!confirm(msg)) return false;

        await fetch("/api/session/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename })
        });

        terminalOutput.textContent =
            "Aguardando participantes nos outros terminais...\n" +
            "Abra outro terminal com: python main.py\n";

        let connected = 1;
        const required = multi.count;
        for (let i = 0; i < 60; i++) {
            await new Promise(resolve => setTimeout(resolve, 500));
            const res = await fetch("/api/session");
            const data = await res.json();
            if (data.session) {
                connected = data.session.participants.length;
                terminalOutput.textContent =
                    `Aguardando participantes... ${connected}/${required} conectados (${i + 1}s)\n` +
                    (data.session.progress_log || []).slice(-5).map(e =>
                        `• [${e.time}] ${e.message}`
                    ).join("\n");
                if (connected >= required) break;
            }
        }

        await fetch("/api/session/ready", { method: "POST" });
        return true;
    }

    function setCompiling(state) {
        btnRun.disabled = state;
        btnRun.textContent = state ? "⏳ Compilando..." : "▶ Compile & Run";
    }

    async function runCompile(code, filename, inputs) {
        setCompiling(true);
        terminalOutput.textContent = "Rodando compilador...";
        terminalOutput.classList.remove("error-text");

        try {
            const res = await fetch("/api/compile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, filename, inputs })
            });
            const data = await res.json();

            if (data.cpp) editorCpp.setValue(data.cpp);
            if (data.tac) editorTac.setValue(data.tac);

            setTimeout(() => { editorCpp.refresh(); editorTac.refresh(); }, 50);

            if (data.success) {
                terminalOutput.textContent = data.stdout || "Compilação concluída com sucesso!";
                terminalOutput.classList.remove("error-text");
            } else {
                terminalOutput.textContent = data.stderr || data.error || "Erro na execução.";
                terminalOutput.classList.add("error-text");
            }
        } catch (err) {
            terminalOutput.textContent = "Erro de conexão com o servidor Backend.";
            terminalOutput.classList.add("error-text");
        } finally {
            setCompiling(false);
        }
    }

    btnRun.onclick = async () => {
        const code     = editorMinipar.getValue();
        const filename = currentFileLabel.textContent;

        if (!currentTestSpec) {
            await loadTestSpec(filename);
        }

        const spec = currentTestSpec;

        if (spec && spec.multi_computer && spec.multi_computer.required) {
            const proceed = await handleMultiComputer(spec, filename);
            if (!proceed) {
                terminalOutput.textContent = "[INFO] Execução cancelada — aguardando participantes.";
                return;
            }
        }

        let inputs = [];
        if (spec && spec.requires_input) {
            inputs = await collectInputs(spec);
            if (inputs === null) {
                terminalOutput.textContent = "[INFO] Execução cancelada — entrada não fornecida.";
                return;
            }
        }

        await runCompile(code, filename, inputs);
    };

    btnClear.onclick = () => {
        editorMinipar.setValue("");
        editorCpp.setValue("");
        editorTac.setValue("");
        currentFileLabel.textContent = "ide_temp.minipar";
        currentTestSpec = null;
        document.querySelectorAll(".test-list li").forEach(li => li.classList.remove("active"));
        terminalOutput.textContent = "Workspace limpo. Pode começar a digitar.";
        terminalOutput.classList.remove("error-text");
    };
});
