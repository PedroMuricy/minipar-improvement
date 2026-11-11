(() => {
    const sourceTextarea = document.getElementById('source-editor');
    const exampleSelect = document.getElementById('example-select');
    const currentFile = document.getElementById('current-file');
    const compileButton = document.getElementById('btn-compile');
    const clearButton = document.getElementById('btn-clear');
    const downloadButton = document.getElementById('btn-download');
    const downloadMessage = document.getElementById('download-message');
    const outputContent = document.getElementById('output-content');
    const outputLabel = document.getElementById('output-label');
    const outputHint = document.getElementById('output-hint');
    const compileStatus = document.getElementById('compile-status');
    const backendState = document.getElementById('backend-state');

    const outputs = {
        logs: {
            label: 'LOG DE COMPILAÇÃO E EXECUÇÃO',
            hint: 'Mensagens retornadas pelo compilador e pelo programa.',
            initial: 'Aguardando compilação.'
        },
        tac: {
            label: 'CÓDIGO INTERMEDIÁRIO — TAC',
            hint: 'Three-Address Code gerado pelo compilador.',
            initial: 'O TAC será exibido aqui após a compilação.'
        },
        cpp: {
            label: 'CÓDIGO GERADO — C++',
            hint: 'Código C++ produzido pelo gerador.',
            initial: 'O código C++ será exibido aqui após a compilação.'
        },
        tokens: {
            label: 'ANÁLISE LÉXICA — TOKENS',
            hint: 'Visualização ainda não conectada ao backend.',
            initial: 'A visualização de tokens será integrada em uma próxima etapa. O analisador léxico já existe no projeto; falta disponibilizar seus resultados para esta interface.'
        },
        ast: {
            label: 'ANÁLISE SINTÁTICA — ÁRVORE AST',
            hint: 'Visualização ainda não conectada ao backend.',
            initial: 'A árvore AST será integrada em uma próxima etapa. O parser já constrói a estrutura; falta convertê-la em dados que a interface possa apresentar visualmente.'
        },
        semantic: {
            label: 'ANÁLISE SEMÂNTICA',
            hint: 'Visualização ainda não conectada ao backend.',
            initial: 'A apresentação da análise semântica será integrada em uma próxima etapa.'
        },
        assembly: {
            label: 'CÓDIGO ASSEMBLY',
            hint: 'Geração ainda não disponível no backend atual.',
            initial: 'O projeto atual gera C++ e executável por meio do g++. A geração e a apresentação de Assembly ainda precisam ser implementadas.'
        }
    };

    let editor = null;
    if (window.CodeMirror) {
        editor = CodeMirror.fromTextArea(sourceTextarea, {
            mode: 'text/x-csrc',
            theme: 'dracula',
            lineNumbers: true,
            indentUnit: 4,
            tabSize: 4,
            lineWrapping: true,
            viewportMargin: Infinity
        });
    }

    const getCode = () => editor ? editor.getValue() : sourceTextarea.value;
    const setCode = value => {
        if (editor) editor.setValue(value);
        else sourceTextarea.value = value;
    };
    const refreshEditor = () => { if (editor) editor.refresh(); };

    let currentOutput = 'logs';
    let lastCompileSucceeded = false;
    let currentSpec = null;

    function setBackendState(message, state = '') {
        backendState.textContent = '';
        const dot = document.createElement('i');
        backendState.appendChild(dot);
        backendState.append(` ${message}`);
        backendState.className = state;
    }

    function showOutput(name, content, isError = false, hintOverride = null) {
        const config = outputs[name] || outputs.logs;
        outputs[name].result = content;
        currentOutput = name;
        outputLabel.textContent = config.label;
        outputHint.textContent = hintOverride || config.hint;
        outputContent.textContent = content ?? config.initial;
        outputContent.classList.toggle('error', isError);
        document.querySelectorAll('[data-output-tab]').forEach(tab => {
            const active = tab.dataset.outputTab === name;
            tab.classList.toggle('active', active);
            tab.setAttribute('aria-selected', String(active));
        });
    }

    async function loadExamples() {
        try {
            const response = await fetch('/api/tests');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            (data.tests || []).forEach(filename => {
                const option = document.createElement('option');
                option.value = filename;
                option.textContent = filename;
                exampleSelect.appendChild(option);
            });
            setBackendState(`${(data.tests || []).length} exemplo(s) disponível(is)`);
        } catch (error) {
            setBackendState('Não foi possível carregar os exemplos', 'error');
            showOutput('logs', 'Não foi possível consultar /api/tests. Confira se o app.py original está sendo executado.', true);
        }
    }

    async function loadExample(filename) {
        if (!filename) return;
        exampleSelect.disabled = true;
        try {
            const response = await fetch('/api/get_test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            const data = await response.json();
            if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
            const specResponse = await fetch('/api/test_spec', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            currentSpec = specResponse.ok ? await specResponse.json() : null;
            setCode(data.code || '');
            currentFile.textContent = filename;
            lastCompileSucceeded = false;
            downloadButton.disabled = true;
            downloadMessage.textContent = 'Compile o programa com sucesso para habilitar o download.';
            compileStatus.textContent = 'Programa carregado';
            compileStatus.className = 'status-pill';
            showOutput('logs', `Programa "${filename}" carregado. Clique em "Compilar e executar" para iniciar.`);
            setBackendState('Programa de exemplo carregado');
            refreshEditor();
        } catch (error) {
            showOutput('logs', `Falha ao carregar o exemplo: ${error.message}`, true);
            setBackendState('Erro ao carregar exemplo', 'error');
        } finally {
            exampleSelect.disabled = false;
        }
    }

    async function compileProgram() {
        const code = getCode();
        if (!code.trim()) {
            showOutput('logs', 'O editor está vazio. Escreva um programa ou carregue um exemplo antes de compilar.', true);
            return;
        }

        compileButton.disabled = true;
        compileButton.textContent = '⏳ Compilando...';
        downloadButton.disabled = true;
        lastCompileSucceeded = false;
        compileStatus.textContent = 'Compilando';
        compileStatus.className = 'status-pill';
        setBackendState('Compilação em andamento', 'busy');
        showOutput('logs', 'Enviando código MiniPar para o compilador...');

        try {
            if (currentSpec && currentSpec.multi_computer && currentSpec.multi_computer.required) {
                throw new Error('Este exemplo exige múltiplos terminais. Nesta primeira versão, execute esse teste pela interface original.');
            }

            let inputs = [];
            if (currentSpec && currentSpec.requires_input && Array.isArray(currentSpec.inputs)) {
                for (let index = 0; index < currentSpec.inputs.length; index += 1) {
                    const inputInfo = currentSpec.inputs[index];
                    const description = inputInfo.descricao || inputInfo.prompt || `Entrada ${index + 1}`;
                    const value = window.prompt(`${description}\n\nDigite o valor para o programa:`);
                    if (value === null) {
                        showOutput('logs', 'Execução cancelada: entrada não fornecida.');
                        compileStatus.textContent = 'Execução cancelada';
                        compileStatus.className = 'status-pill';
                        setBackendState('Aguardando ação');
                        return;
                    }
                    inputs.push(value.trim());
                }
            }

            const response = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code,
                    filename: 'didatica_temp.minipar',
                    inputs
                })
            });
            const data = await response.json();

            if (data.tac) outputs.tac.result = data.tac;
            else outputs.tac.result = '';
            if (data.cpp) outputs.cpp.result = data.cpp;
            else outputs.cpp.result = '';

            if (data.success) {
                lastCompileSucceeded = true;
                downloadButton.disabled = false;
                downloadMessage.textContent = 'O executável foi gerado. Você pode baixá-lo agora.';
                compileStatus.textContent = 'Compilação concluída';
                compileStatus.className = 'status-pill success';
                setBackendState('Compilação concluída');
                showOutput('logs', data.stdout || 'Compilação e execução concluídas com sucesso.');
            } else {
                const errorText = data.stderr || data.error || 'O compilador não conseguiu concluir a compilação.';
                compileStatus.textContent = 'Falha na compilação';
                compileStatus.className = 'status-pill error';
                setBackendState('Erro na compilação', 'error');
                downloadMessage.textContent = 'Não há executável disponível para download.';
                showOutput('logs', errorText, true);
            }
        } catch (error) {
            compileStatus.textContent = 'Erro de comunicação';
            compileStatus.className = 'status-pill error';
            setBackendState('Backend indisponível', 'error');
            showOutput('logs', `Não foi possível comunicar com o Flask: ${error.message}`, true);
        } finally {
            compileButton.disabled = false;
            compileButton.innerHTML = '<span aria-hidden="true">▶</span> Compilar e executar';
        }
    }

    document.querySelectorAll('[data-output-tab]').forEach(tab => {
        tab.addEventListener('click', () => {
            const name = tab.dataset.outputTab;
            let content = outputs[name].result;
            if (name === 'logs') {
                content = outputs.logs.result || outputs.logs.initial;
            } else if (name === 'tac' || name === 'cpp') {
                content = content || outputs[name].initial;
            } else {
                content = outputs[name].initial;
            }
            const enabled = document.querySelector(`[data-view-option="${name}"]`);
            if (enabled && !enabled.checked) {
                showOutput(name, `A opção "${name.toUpperCase()}" está desmarcada. Marque-a nas opções de visualização para incluí-la.`, false);
                return;
            }
            showOutput(name, content);
        });
    });

    document.querySelectorAll('[data-view-option]').forEach(option => {
        option.addEventListener('change', () => {
            const name = option.dataset.viewOption;
            const tab = document.querySelector(`[data-output-tab="${name}"]`);
            if (tab) tab.classList.toggle('option-disabled', !option.checked);
            if (!option.checked && currentOutput === name) showOutput('logs', outputs.logs.result || outputs.logs.initial);
        });
    });

    exampleSelect.addEventListener('change', event => loadExample(event.target.value));
    compileButton.addEventListener('click', compileProgram);

    clearButton.addEventListener('click', () => {
        setCode('');
        exampleSelect.value = '';
        currentFile.textContent = 'novo_programa.minipar';
        lastCompileSucceeded = false;
        downloadButton.disabled = true;
        downloadMessage.textContent = 'Compile um programa com sucesso para habilitar o download.';
        compileStatus.textContent = 'Aguardando compilação';
        compileStatus.className = 'status-pill';
        Object.keys(outputs).forEach(key => { delete outputs[key].result; });
        showOutput('logs', 'Workspace limpo. Escreva um programa ou carregue um exemplo.');
        setBackendState('Aguardando ação');
        refreshEditor();
    });

    downloadButton.addEventListener('click', () => {
        if (!lastCompileSucceeded) return;
        window.location.assign('/api/download_executable');
    });

    loadExamples();
})();
