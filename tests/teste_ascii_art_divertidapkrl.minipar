seq {
    print("========================================");
    print("  FRACTAL DE SIERPINSKI (Automato)      ");
    print("========================================");

    var linhas = 32;
    var colunas = 64;
    
    # 1. Cria matriz para a tela (desenho final com os caracteres)
    var tela = matrix(linhas, colunas, " ");
    
    # 2. Cria matriz logica de controle (0 = vazio, 1 = preenchido)
    var controle = matrix(linhas, colunas, 0);

    # Define o ponto de origem (o topo da pirâmide) no meio da tela
    var meio = 31;
    controle[0][meio] = 1;
    tela[0][meio] = "A";

    var i = 1;
    # Percorre de cima para baixo
    while (i < linhas) {
        var j = 1;
        # Percorre da esquerda para a direita
        while (j < (colunas - 1)) {
            
            # Pega os valores da esquerda e da direita da linha de cima
            var esq = controle[i - 1][j - 1];
            var dir = controle[i - 1][j + 1];
            
            # Regra do Fractal: Se apenas UM dos vizinhos for 1, nasce uma celula
            if ((esq + dir) == 1) {
                controle[i][j] = 1;
                tela[i][j] = "A";
            }
            
            j = j + 1;
        }
        i = i + 1;
    }

    print("Calculo finalizado. Renderizando...");
    
    # Imprime o fractal linha por linha
    var k = 0;
    while (k < linhas) {
        print(tela[k]);
        k = k + 1;
    }
    
    print("========================================");
}