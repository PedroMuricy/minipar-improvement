"""
Orquestrador de execução MiniPar — coordenação multi-terminal e progresso.
Requisitos de cada programa são detectados automaticamente via program_analyzer.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime
from typing import Any, Optional

from program_analyzer import get_program_spec

# Estado compartilhado entre terminais via arquivo JSON (sem servidor externo)
SESSION_FILE = os.path.join("output", ".test_session.json")
_SPINNER = ["|", "/", "-", "\\"]

_PHASE_ACTIVITY = {
    "waiting_participants": "Aguardando demais terminais se conectarem...",
    "ready": "Participantes conectados — aguardando início...",
    "collecting_input": "Programa solicitará entradas no terminal iniciador...",
    "compiling": "Compilador processando código MiniPar...",
    "executing": "Programa em execução no terminal iniciador...",
    "done": "Execução finalizada.",
}


def get_terminal_id() -> str:
    # hostname + PID identifica cada terminal de forma única na sessão
    hostname = socket.gethostname()
    return f"{hostname}-{os.getpid()}"


def get_test_spec(filename: str) -> Optional[dict[str, Any]]:
    path = os.path.join("tests", os.path.basename(filename))
    if not os.path.isfile(path):
        return None
    return get_program_spec(path)


def _load_session() -> Optional[dict[str, Any]]:
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_session(session: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def clear_session() -> None:
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


def _now_short() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_separator(char: str = "=", width: int = 55) -> None:
    print(char * width)


def append_session_log(message: str, source: str = "initiator") -> None:
    session = _load_session()
    if session is None:
        return
    log = session.setdefault("progress_log", [])
    log.append({"time": _now_short(), "message": message, "source": source})
    if len(log) > 50:
        session["progress_log"] = log[-50:]
    _save_session(session)


def set_session_phase(phase: str, message: str, percent: Optional[int] = None) -> None:
    session = _load_session()
    if session is None:
        return
    session["phase"] = phase
    session["phase_message"] = message
    if percent is not None:
        session["progress_percent"] = percent
    _save_session(session)
    append_session_log(message, source="initiator")


def record_execution_output(text: str) -> None:
    session = _load_session()
    if session is None:
        return
    session["execution_output"] = text
    _save_session(session)


def _get_participant_role(session: dict[str, Any], terminal_id: str) -> str:
    for p in session.get("participants", []):
        if p["terminal_id"] == terminal_id:
            return p["role"]
    return "participante"


def _phase_activity(phase: str, role: str) -> str:
    base = _PHASE_ACTIVITY.get(phase, "Aguardando...")
    if role != "participante" and phase in ("waiting_participants", "executing"):
        return f"{role}: {base}"
    return base


def _print_joiner_header(session: dict[str, Any], my_role: str) -> None:
    _print_separator()
    print("  TERMINAL PARTICIPANTE — MONITOR DE PROGRESSO")
    _print_separator()
    print(f"\n  Terminal : {get_terminal_id()}")
    print(f"  Papel    : {my_role}")
    print(f"  Programa : {session.get('titulo', session.get('test_file', ''))}")
    print(f"  Iniciador: {session.get('initiator_terminal', '?')}")
    print(f"\n  {'─' * 50}")
    print("  LOG DE ATIVIDADE (tempo real)")
    print(f"  {'─' * 50}\n")


def _print_joiner_summary(session: dict[str, Any], my_role: str) -> None:
    _print_separator("-")
    print("  RESUMO DA EXECUÇÃO")
    _print_separator("-")
    print(f"\n  Papel deste terminal: {my_role}")
    print(f"  Status final        : {session.get('status', '?')}")
    print(f"  Participantes       : {len(session.get('participants', []))}/"
          f"{session.get('required_participants', '?')}")
    output = session.get("execution_output", "")
    if output.strip():
        print("\n  Saída registrada pelo iniciador:")
        for line in output.strip().splitlines()[-8:]:
            print(f"    {line}")
    print(f"\n  {'─' * 50}")
    print("  Participação concluída.")
    print(f"  {'─' * 50}\n")


def run_joiner_progress_monitor(session: dict[str, Any]) -> bool:
    """Terminal participante: lê SESSION_FILE em loop e exibe progresso."""
    terminal_id = get_terminal_id()
    my_role = _get_participant_role(session, terminal_id)
    last_log_count = 0
    spinner_idx = 0
    start_time = time.time()
    last_phase = ""

    _print_joiner_header(session, my_role)
    append_session_log(f"Terminal conectado: {my_role} ({terminal_id})", source="system")

    while True:
        current = _load_session()
        if current is None:
            print("\n\n  [INFO] Sessão encerrada.")
            return True

        log = current.get("progress_log", [])
        # Imprime apenas entradas novas desde a última iteração
        for entry in log[last_log_count:]:
            prefix = "→" if entry.get("source") == "initiator" else "•"
            print(f"  {prefix} [{entry['time']}] {entry['message']}")
        last_log_count = len(log)

        status = current.get("status", "waiting")
        phase = current.get("phase", "waiting_participants")
        phase_msg = current.get("phase_message", "Aguardando...")
        activity = _phase_activity(phase, my_role)
        percent = current.get("progress_percent")
        elapsed = int(time.time() - start_time)
        spinner = _SPINNER[spinner_idx % len(_SPINNER)]
        spinner_idx += 1

        if phase != last_phase:
            print(f"\n  ▶ Fase: {phase_msg}")
            last_phase = phase

        bar = ""
        if percent is not None:
            filled = int(percent / 5)
            bar = f" [{'█' * filled}{'░' * (20 - filled)}] {percent}%"

        sys.stdout.write(f"\r  {spinner} [{elapsed:>3}s]{bar} {activity}          ")
        sys.stdout.flush()

        if status == "completed":
            print("\n")
            _print_joiner_summary(current, my_role)
            return True
        if status == "cancelled":
            print("\n\n  [INFO] Execução cancelada pelo iniciador.")
            return False
        time.sleep(0.4)


def prompt_new_user_on_active_session(session: dict[str, Any]) -> str:
    titulo = session.get("titulo", session.get("test_file", "desconhecido"))
    participantes = session.get("participants", [])
    required = session.get("required_participants", 0)

    _print_separator()
    print("  SESSÃO DE EXECUÇÃO EM ANDAMENTO")
    _print_separator()
    print(f"\n  Programa: {titulo}")
    print(f"  Iniciado por: {session.get('initiator_terminal', '?')}")
    print(f"  Participantes: {len(participantes)}/{required}")
    for p in participantes:
        print(f"    - {p['role']} ({p['terminal_id']})")
    print(f"\n  Terminal identificado: {get_terminal_id()}\n")
    print("  [1] Executar de forma independente")
    print("  [2] Continuar e participar desta execução\n")

    while True:
        escolha = input("  Escolha (1 ou 2): ").strip()
        if escolha == "1":
            return "independent"
        if escolha == "2":
            return "join"
        print("  [ERRO] Digite 1 ou 2.")


def _assign_role(session: dict[str, Any]) -> Optional[str]:
    roles = session.get("roles", [])
    taken = {p["role"] for p in session.get("participants", [])}
    for role in roles:
        if role not in taken:
            return role
    return None


def join_session(session: dict[str, Any]) -> dict[str, Any]:
    terminal_id = get_terminal_id()
    participants = session.get("participants", [])

    if any(p["terminal_id"] == terminal_id for p in participants):
        print(f"\n  [INFO] Terminal {terminal_id} já participa desta sessão.")
        return session

    role = _assign_role(session)
    if role is None:
        print("\n  [AVISO] Todos os papéis atribuídos. Aguardando execução...")
        return session

    participants.append({
        "terminal_id": terminal_id,
        "role": role,
        "ready": True,
        "joined_at": datetime.now().isoformat(),
    })
    session["participants"] = participants
    _save_session(session)
    append_session_log(f"Participante entrou: {role} ({terminal_id})", source="system")
    print(f"\n  [OK] Papel atribuído: {role}")
    print(f"  Participantes: {len(participants)}/{session['required_participants']}")
    return session


def create_session(test_path: str, spec: dict[str, Any]) -> dict[str, Any]:
    multi = spec["multi_computer"]
    terminal_id = get_terminal_id()
    roles = multi.get("roles", [])

    session = {
        "test_file": os.path.basename(test_path),
        "titulo": spec.get("titulo", os.path.basename(test_path)),
        "required_participants": multi["count"],
        "roles": roles,
        "initiator_terminal": terminal_id,
        "status": "waiting",
        "phase": "waiting_participants",
        "phase_message": "Aguardando participantes adicionais...",
        "progress_percent": 0,
        "progress_log": [],
        "execution_output": "",
        "created_at": datetime.now().isoformat(),
        "participants": [{
            "terminal_id": terminal_id,
            "role": roles[0] if roles else "computador_1",
            "ready": True,
            "joined_at": datetime.now().isoformat(),
        }],
    }
    _save_session(session)
    append_session_log(
        f"Sessão iniciada — aguardando {multi['count'] - 1} terminal(is) adicional(is).",
        source="system",
    )
    return session


def _wait_for_participants(session: dict[str, Any], spec: dict[str, Any]) -> bool:
    multi = spec["multi_computer"]
    required = multi["count"]

    _print_separator()
    print("  EXECUÇÃO MULTI-TERMINAL DETECTADA")
    _print_separator()
    print(f"\n  Programa: {spec.get('titulo', '')}")
    print(f"  Canais c_channel: {spec.get('channel_count', '?')}")
    print(f"  Terminais necessários: {required}\n")
    print(f"  {multi.get('instrucoes', '')}\n")
    print("  Papéis:")
    for i, role in enumerate(multi.get("roles", []), 1):
        print(f"    [{i}] {role}")
    print(f"\n  Terminal iniciador: {get_terminal_id()}")
    print("  Execute python main.py nos outros terminais e escolha opção [2].\n")
    input("  Pressione ENTER quando os demais terminais estiverem prontos... ")

    print("\n  Monitorando conexões...\n")
    last_count = 1
    for tick in range(60):
        current = _load_session()
        if not current:
            break
        connected = len(current.get("participants", []))
        if connected > last_count:
            for p in current["participants"][last_count:]:
                print(f"  ✓ {p['role']} ({p['terminal_id']})")
            last_count = connected
            set_session_phase(
                "waiting_participants",
                f"{connected}/{required} participantes conectados",
                percent=min(int(connected / required * 40), 40),
            )
        sys.stdout.write(
            f"\r  Aguardando... {connected}/{required} ({tick + 1}s)   "
        )
        sys.stdout.flush()
        if connected >= required:
            print(f"\n\n  [OK] {required} participantes conectados.\n")
            current["status"] = "ready"
            set_session_phase("ready", "Todos os participantes conectados", percent=40)
            _save_session(current)
            return True
        time.sleep(0.5)

    current = _load_session()
    connected = len(current.get("participants", [])) if current else 1
    print(f"\n  [AVISO] Apenas {connected}/{required} participante(s).")
    if input("  Continuar mesmo assim? (s/n): ").strip().lower() in ("s", "sim", "y", "yes"):
        if current:
            current["status"] = "ready"
            _save_session(current)
        return True
    clear_session()
    return False


def _wait_as_joiner(session: dict[str, Any]) -> bool:
    return run_joiner_progress_monitor(session)


def _announce_input_requirement(spec: dict[str, Any]) -> None:
    count = spec.get("input_count", 0)
    _print_separator()
    print("  ENTRADA DO USUÁRIO")
    _print_separator()
    print(f"\n  Programa: {spec.get('titulo', '')}")
    print(f"  O código MiniPar possui {count} chamada(s) input().")
    print("  As entradas serão solicitadas pelo programa durante a execução.\n")
    if spec.get("inputs"):
        print("  Prompts detectados no código:")
        for i, inp in enumerate(spec["inputs"], 1):
            desc = inp.get("descricao") or inp.get("prompt") or f"Entrada {i}"
            print(f"    [{i}] {desc}")
    print()
    input("  Pressione ENTER para compilar e executar... ")
    print()


def check_active_session_for_new_terminal() -> tuple[Optional[str], Optional[dict]]:
    session = _load_session()
    if session is None or session.get("status") in ("completed", "cancelled"):
        return None, session

    if session.get("status") == "running":
        return prompt_new_user_on_active_session(session), session

    if session.get("status") in ("waiting", "ready"):
        terminal_id = get_terminal_id()
        participants = session.get("participants", [])
        if any(p["terminal_id"] == terminal_id for p in participants):
            return None, session
        if len(participants) < session.get("required_participants", 0):
            return prompt_new_user_on_active_session(session), session

    return None, session


def prepare_test_execution(test_path: str) -> tuple[bool, bool, bool]:
    """
    Prepara execução. Retorna (proceed, interactive_input, is_joiner).

    - interactive_input: True quando o .minipar usa input() — stdin fica no terminal
    - is_joiner: True quando este terminal só acompanha (não compila nem executa)
    """
    spec = get_program_spec(test_path)
    is_joiner = False

    # Terminal abriu outro programa enquanto há sessão ativa
    active_session = _load_session()
    if active_session and active_session.get("test_file") != os.path.basename(test_path):
        action, _ = check_active_session_for_new_terminal()
        if action == "join":
            join_session(active_session)
            if not _wait_as_joiner(active_session):
                return False, False, True
            return True, False, True
        if action == "independent":
            pass

    multi = spec.get("multi_computer")
    if multi and multi.get("required"):
        session = _load_session()
        terminal_id = get_terminal_id()
        filename = os.path.basename(test_path)

        if session and session.get("test_file") == filename:
            participants = session.get("participants", [])
            # Quem criou a sessão (ou primeiro participante) conduz compilação/execução
            is_initiator = session.get("initiator_terminal") == terminal_id or (
                participants and participants[0]["terminal_id"] == terminal_id
            )

            if not is_initiator:
                # Demais terminais entram na sessão e aguardam o monitor de progresso
                if not any(p["terminal_id"] == terminal_id for p in participants):
                    action, _ = check_active_session_for_new_terminal()
                    if action == "join":
                        join_session(session)
                    elif action == "independent":
                        clear_session()
                        session = create_session(test_path, spec)
                        is_initiator = True
                    else:
                        return False, False, False
                if not is_initiator:
                    if not _wait_as_joiner(session):
                        return False, False, True
                    return True, False, True
            elif not _wait_for_participants(session, spec):
                return False, False, False
        else:
            session = create_session(test_path, spec)
            if not _wait_for_participants(session, spec):
                return False, False, False

        session = _load_session()
        if session:
            session["status"] = "running"
            set_session_phase("compiling", "Preparando compilação...", percent=45)
            _save_session(session)

    interactive = spec.get("requires_input", False)
    if interactive:
        set_session_phase("collecting_input", "Entradas serão lidas pelo programa...", percent=50)
        _announce_input_requirement(spec)

    return True, interactive, is_joiner


def finalize_test_execution(test_path: str, output: str = "") -> None:
    filename = os.path.basename(test_path)
    session = _load_session()
    if session and session.get("test_file") == filename:
        if output:
            session["execution_output"] = output
        session["status"] = "completed"
        session["phase"] = "done"
        session["phase_message"] = "Execução concluída."
        session["progress_percent"] = 100
        session.setdefault("progress_log", []).append({
            "time": _now_short(),
            "message": "Execução finalizada pelo terminal iniciador.",
            "source": "initiator",
        })
        _save_session(session)
        time.sleep(2)  # tempo para terminais participantes lerem status "completed"
        clear_session()


def get_spec_summary(filename: str) -> Optional[dict[str, Any]]:
    path = os.path.join("tests", os.path.basename(filename))
    if not os.path.isfile(path):
        return None
    spec = get_program_spec(path)
    return {
        "titulo": spec.get("titulo", ""),
        "descricao": spec.get("descricao", ""),
        "requires_input": spec.get("requires_input", False),
        "input_count": spec.get("input_count", 0),
        "inputs": spec.get("inputs", []),
        "multi_computer": spec.get("multi_computer"),
        "channel_count": spec.get("channel_count", 0),
    }
