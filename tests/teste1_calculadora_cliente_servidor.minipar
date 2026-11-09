# Calcula operação aritmética recebida como string (ex.: "+", "-", "*", "/")
func calcular(op, v1, v2) {
    if (op == "+") {
        return v1 + v2;
    }
    if (op == "-") {
        return v1 - v2;
    }
    if (op == "*") {
        return v1 * v2;
    }
    if (op == "/") {
        return v1 / v2;
    }
    return 0.0;
}

seq {
    print("==== Calculadora cliente-servidor ====");
    print("Opcoes: +, -, *, /");
    var requisicao = c_channel("127.0.0.1", 5101);
    var resposta = c_channel("127.0.0.1", 5102);

    par {
        # Thread servidor: recebe operação e operandos, devolve resultado
        seq {
            var op = receive(requisicao);
            var s_v1 = receive(requisicao);
            var s_v2 = receive(requisicao);
            var v1 = to_number(s_v1);
            var v2 = to_number(s_v2);
            print("Servidor recebeu:", op, s_v1, s_v2);
            var res = calcular(op, v1, v2);
            send(resposta, res);
        }
        # Thread cliente: lê input do usuário e envia ao servidor
        seq {
            var operacao = input("Operacao (+,-,*,/): ");
            var operando1 = input("Operando 1: ");
            var operando2 = input("Operando 2: ");
            send(requisicao, operacao);
            send(requisicao, operando1);
            send(requisicao, operando2);
            var resultado = receive(resposta);
            print("Resultado:", resultado);
        }
    }
}
