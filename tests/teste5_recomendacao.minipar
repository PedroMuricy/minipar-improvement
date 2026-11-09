func relu(x) {
    if (x > 0) {
        return x;
    }
    return 0.0;
}

func sigmoid(x) {
    return 1 / (1 + exp(0 - x));
}

func peso_entrada_oculta(produto, neuronio) {
    var base = ((produto + 1) * (neuronio + 2)) % 7;
    return (base + 1) / 20.0;
}

func bias_oculto(neuronio) {
    return (neuronio % 3) / 20.0;
}

func peso_oculta_saida(neuronio, produto) {
    var base = ((neuronio + 3) * (produto + 1)) % 5;
    return (base + 1) / 25.0;
}

func bias_saida(produto, historico) {
    if (historico[produto] == 1) {
        return -0.25;
    }
    return -0.10;
}

func nome_produto(indice) {
    if (indice == 0) {
        return "Smartphone";
    }
    if (indice == 1) {
        return "Laptop";
    }
    if (indice == 2) {
        return "Tablet";
    }
    if (indice == 3) {
        return "Fones de ouvido";
    }
    if (indice == 4) {
        return "Camisa";
    }
    if (indice == 5) {
        return "Jeans";
    }
    if (indice == 6) {
        return "Jaqueta";
    }
    if (indice == 7) {
        return "Sapatos";
    }
    if (indice == 8) {
        return "Geladeira";
    }
    if (indice == 9) {
        return "Micro-ondas";
    }
    if (indice == 10) {
        return "Maquina de lavar";
    }
    if (indice == 11) {
        return "Ar condicionado";
    }
    if (indice == 12) {
        return "Ficcao";
    }
    if (indice == 13) {
        return "Nao-ficcao";
    }
    if (indice == 14) {
        return "Ficcao cientifica";
    }
    return "Fantasia";
}

func ler_historico_compras() {
    # Vetor binário: 1 = comprou, 0 = não comprou (16 produtos do catálogo)
    var historico = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    print("==== Teste 5: recomendacao e-commerce com rede neural ====");
    print("Informe o historico de compras (1 = comprou, 0 = nao comprou):");
    var i = 0;
    while (i < 16) {
        print(nome_produto(i), "- comprou? (0/1):");
        historico[i] = to_number(input(""));
        i = i + 1;
    }
    return historico;
}

class RedeNeuralRecomendacao {
    var input_size = 16;
    var hidden_size = 10;   # camada oculta com ReLU
    var output_size = 16;   # uma saída sigmoid por produto

    func forward(historico) {
        var ocultas = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        var saidas = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

        # Camada oculta: entrada × pesos + bias → ReLU
        var h = 0;
        while (h < this.hidden_size) {
            var soma_oculta = 0.0;
            var entrada = 0;

            while (entrada < this.input_size) {
                soma_oculta = soma_oculta + (historico[entrada] * peso_entrada_oculta(entrada, h));
                entrada = entrada + 1;
            }

            ocultas[h] = relu(soma_oculta + bias_oculto(h));
            h = h + 1;
        }

        var produto = 0;
        # Camada de saída: ocultas × pesos + bias → sigmoid (probabilidade 0–1)
        while (produto < this.output_size) {
            var soma_saida = 0.0;
            var neuronio = 0;

            while (neuronio < this.hidden_size) {
                soma_saida = soma_saida + (ocultas[neuronio] * peso_oculta_saida(neuronio, produto));
                neuronio = neuronio + 1;
            }

            saidas[produto] = sigmoid(soma_saida + bias_saida(produto, historico));
            produto = produto + 1;
        }

        return saidas;
    }
}

class Recomendador {
    func recomendar(historico) {
        var rede = new RedeNeuralRecomendacao();
        var probabilidades = rede.forward(historico);

        print("Produtos recomendados para voce:");

        var produto = 0;
        while (produto < 16) {
            # Recomenda apenas produtos não comprados com probabilidade > 0.55
            if ((historico[produto] == 0) && (probabilidades[produto] > 0.55)) {
                print(nome_produto(produto), "probabilidade:", probabilidades[produto]);
            }
            produto = produto + 1;
        }
    }
}

seq {
    var historico = ler_historico_compras();
    var recomendador = new Recomendador();
    recomendador.recomendar(historico);
}
