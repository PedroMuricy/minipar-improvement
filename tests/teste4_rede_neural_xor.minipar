func sigmoid(x) {
    return 1 / (1 + exp(0 - x));
}

func derivada_sigmoid(saida) {
    return saida * (1 - saida);
}

class RedeNeuralXOR {
    var taxa_aprendizado = 0.5;

    var h1_w1 = 0.2;
    var h1_w2 = -0.4;
    var h1_bias = 0.0;

    var h2_w1 = -0.3;
    var h2_w2 = 0.6;
    var h2_bias = 0.1;

    var h3_w1 = 0.7;
    var h3_w2 = 0.5;
    var h3_bias = -0.2;

    var out_w1 = 0.4;
    var out_w2 = -0.5;
    var out_w3 = 0.3;
    var out_bias = 0.0;

    var h1 = 0.0;
    var h2 = 0.0;
    var h3 = 0.0;
    var saida = 0.0;

    func feedforward(x1, x2) {
        this.h1 = sigmoid((x1 * this.h1_w1) + (x2 * this.h1_w2) + this.h1_bias);
        this.h2 = sigmoid((x1 * this.h2_w1) + (x2 * this.h2_w2) + this.h2_bias);
        this.h3 = sigmoid((x1 * this.h3_w1) + (x2 * this.h3_w2) + this.h3_bias);

        this.saida = sigmoid(
            (this.h1 * this.out_w1) +
            (this.h2 * this.out_w2) +
            (this.h3 * this.out_w3) +
            this.out_bias
        );

        return this.saida;
    }

    func treinar_amostra(x1, x2, desejado) {
        var previsto = this.feedforward(x1, x2);
        var erro = desejado - previsto;
        var delta_saida = erro * derivada_sigmoid(previsto);

        var antigo_out_w1 = this.out_w1;
        var antigo_out_w2 = this.out_w2;
        var antigo_out_w3 = this.out_w3;

        this.out_w1 = this.out_w1 + ((this.h1 * delta_saida) * this.taxa_aprendizado);
        this.out_w2 = this.out_w2 + ((this.h2 * delta_saida) * this.taxa_aprendizado);
        this.out_w3 = this.out_w3 + ((this.h3 * delta_saida) * this.taxa_aprendizado);
        this.out_bias = this.out_bias + (delta_saida * this.taxa_aprendizado);

        var delta_h1 = (delta_saida * antigo_out_w1) * derivada_sigmoid(this.h1);
        var delta_h2 = (delta_saida * antigo_out_w2) * derivada_sigmoid(this.h2);
        var delta_h3 = (delta_saida * antigo_out_w3) * derivada_sigmoid(this.h3);

        this.h1_w1 = this.h1_w1 + ((x1 * delta_h1) * this.taxa_aprendizado);
        this.h1_w2 = this.h1_w2 + ((x2 * delta_h1) * this.taxa_aprendizado);
        this.h1_bias = this.h1_bias + (delta_h1 * this.taxa_aprendizado);

        this.h2_w1 = this.h2_w1 + ((x1 * delta_h2) * this.taxa_aprendizado);
        this.h2_w2 = this.h2_w2 + ((x2 * delta_h2) * this.taxa_aprendizado);
        this.h2_bias = this.h2_bias + (delta_h2 * this.taxa_aprendizado);

        this.h3_w1 = this.h3_w1 + ((x1 * delta_h3) * this.taxa_aprendizado);
        this.h3_w2 = this.h3_w2 + ((x2 * delta_h3) * this.taxa_aprendizado);
        this.h3_bias = this.h3_bias + (delta_h3 * this.taxa_aprendizado);
    }

    func treinar() {
        var epoca = 0;

        while (epoca < 20000) {
            this.treinar_amostra(0, 0, 0);
            this.treinar_amostra(0, 1, 1);
            this.treinar_amostra(1, 0, 1);
            this.treinar_amostra(1, 1, 0);
            epoca = epoca + 1;
        }
    }

    func testar() {
        print("==== Teste 4: rede neural XOR com backpropagation ====");
        print("Input: [0, 0], Predicted Output:", this.feedforward(0, 0));
        print("Input: [0, 1], Predicted Output:", this.feedforward(0, 1));
        print("Input: [1, 0], Predicted Output:", this.feedforward(1, 0));
        print("Input: [1, 1], Predicted Output:", this.feedforward(1, 1));
    }
}

seq {
    var rede = new RedeNeuralXOR();
    rede.treinar();
    rede.testar();
}
