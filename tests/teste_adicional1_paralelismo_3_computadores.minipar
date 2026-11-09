func quicksort_resumo() {
    return "PC1 QuickSort: [33,12,98,5,61] -> [5,12,33,61,98]";
}

func matrizes_resumo() {
    return "PC2 Matrizes: [[1,2],[3,4]] x [[5,6],[7,8]] -> [[19,22],[43,50]]";
}

func fatorial_resumo() {
    var n = 5;
    var fat = 1;
    var i = 1;
    while (i <= n) {
        fat = fat * i;
        i = i + 1;
    }
    return "PC3 Fatorial: 5! = 120";
}

seq {
    print("==== Teste adicional 1: paralelismo real com 3 computadores ====");
    print("Menu do Computador 1");
    print("1 - Quick sort no Computador 1: 127.0.0.1:5301");
    print("2 - Multiplicacao de matrizes no Computador 2: 127.0.0.1:5302");
    print("3 - Fatorial no Computador 3: 127.0.0.1:5303");

    var canal_pc1 = c_channel("127.0.0.1", 5301);
    var canal_pc2 = c_channel("127.0.0.1", 5302);
    var canal_pc3 = c_channel("127.0.0.1", 5303);

    par {
        seq {
            var resultado1 = receive(canal_pc1);
            var resultado2 = receive(canal_pc2);
            var resultado3 = receive(canal_pc3);
            print("Resultados recolhidos no Computador 1:");
            print(resultado1);
            print(resultado2);
            print(resultado3);
        }
        seq {
            send(canal_pc1, quicksort_resumo());
        }
        seq {
            send(canal_pc2, matrizes_resumo());
        }
        seq {
            send(canal_pc3, fatorial_resumo());
        }
    }
}
