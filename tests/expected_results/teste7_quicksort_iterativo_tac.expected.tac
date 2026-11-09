t0 = 0                    // início do array
t1 = 4                    // fim do array
S[0] = t0                 // empilha start
S[1] = t1                 // empilha end
sp = 2                  // topo da pilha (próxima posição livre)
LOOP:
  if sp == 0 goto END     // pilha vazia → fim
  sp = sp - 1
  t2 = S[sp]              // end
  sp = sp - 1
  t3 = S[sp]              // start
  if t3 >= t2 goto LOOP   // intervalo inválido → ignora
  t4 = A[t2]              // pivot = A[end]
  t5 = t3 - 1             // i = start - 1
  t6 = t3                 // j = start
PARTITION_LOOP:
  if t6 >= t2 goto PARTITION_END
  t7 = A[t6]
  if t7 <= t4 goto SWAP
  t6 = t6 + 1
  goto PARTITION_LOOP
SWAP:
  t5 = t5 + 1
  t8 = A[t5]
  A[t5] = A[t6]
  A[t6] = t8
  t6 = t6 + 1
  goto PARTITION_LOOP
PARTITION_END:
  t5 = t5 + 1
  t9 = A[t5]
  A[t5] = A[t2]
  A[t2] = t9
  t10 = t5 - 1
  S[sp] = t3              // empilha start
  sp = sp + 1
  S[sp] = t10             // empilha i - 1
  sp = sp + 1
  t11 = t5 + 1
  S[sp] = t11             // empilha i + 1
  sp = sp + 1
  S[sp] = t2              // empilha end
  sp = sp + 1
  goto LOOP
END:
  // Array A[0..4] está ordenado
