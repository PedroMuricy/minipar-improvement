func preencher(tela, linha, coluna, tamanho) {
    if (tamanho == 1) {
        tela[linha][coluna] = "#";
        return tela;
    }

    var novo = tamanho / 3;
    var i = 0;
    while (i < 3) {
        var j = 0;
        while (j < 3) {
            if (!((i == 1) && (j == 1))) {
                tela = preencher(tela, linha + (i * novo), coluna + (j * novo), novo);
            }
            j = j + 1;
        }
        i = i + 1;
    }

    return tela;
}

seq {
    print("==== Teste adicional 2: tapete de Sierpinski ====");
    var tamanho = 9;
    var tela = matrix(tamanho, tamanho, " ");
    tela = preencher(tela, 0, 0, tamanho);

    var i = 0;
    while (i < tamanho) {
        print(tela[i]);
        i = i + 1;
    }
}
