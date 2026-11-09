class Quicksort {
    var array = [0];

    func carregar(arr) {
        this.array = arr;
    }

    func trocar(i, j) {
        var temp = this.array[i];
        this.array[i] = this.array[j];
        this.array[j] = temp;
    }

    func particionar(inicio, fim) {
        var pivot = this.array[fim];
        var i = inicio - 1;
        var j = inicio;
        while (j < fim) {
            if (this.array[j] <= pivot) {
                i = i + 1;
                this.trocar(i, j);
            }
            j = j + 1;
        }
        i = i + 1;
        this.trocar(i, fim);
        return i;
    }

    func quicksort(inicio, fim) {
        if (inicio < fim) {
            var p = this.particionar(inicio, fim);
            this.quicksort(inicio, p - 1);
            this.quicksort(p + 1, fim);
        }
    }

    func ordenar() {
        var n = len(this.array) - 1;
        if (n >= 0) {
            this.quicksort(0, n);
        }
        return this.array;
    }
}

seq {
    print("==== Ordenacao com Quicksort ====");
    print("Insira os elementos do vetor separados por espaco:");
    var entrada = input("");
    var vetor = parse_ints(entrada);
    print("Vetor original:", vetor);
    var algoritmo = new Quicksort();
    algoritmo.carregar(vetor);
    var vetor_ordenado = algoritmo.ordenar();
    print("Vetor ordenado:", vetor_ordenado);
}
