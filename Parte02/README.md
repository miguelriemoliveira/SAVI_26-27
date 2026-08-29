Parte 2 - SAVI

Miguel Riem Oliveira <mriem@ua.pt>
2026-2027

# Sumário

- Exercícios de processamento de imagem 


# Exercícios

## Exercício 1 - Nightfall

O objetivo é carregar a imagem _lake.png_ do disco e mostrá-la.

![Image](images/lake.jpg)

Depois deve-se diminuir a intensidade dos píxeis da metade direita da imagem para simular uma fotografia noturna.

Finalmente, faça um efeito de anoitecer progressivo variando o valor do divisor.

![Image](images/nightfall.png)

Grave um vídeo com o processo de anoitecer da imagem.

## Exercício 2 - Classificação

O dataset cat_dog_savi é um dataset com 6 imagens de gatos e cães.

Implemente a leitura das imagens e do ficheiro de `labels.txt`, mostrando para cada imagem o label correspondente.

Depois, implemente um algoritmo que analise a imagem e faça a classificaçãp em `cat` ou `dog`. 

## Exercício 3 - Segmentação

Faça a segmentação da areia na imagem `praia.png`.

![Image](images/praia.png)

## Exercício 4 - Deteção

Onde está o Wally?

Carregue a imagem *scene.png* e o modelo *wally.png*

Utilizando template matching encontre o Wally na imagem.

Anote a posição do Wally desenhando um círculo à volta da sua cara.

![Exemplo de deteção do Wally](images/finding_wally.png)

## Exercício 5 - Ainda o Wally?

Experimente o programa do exercício anterior para as novas imagens **school.png** e **beach.png**. Porque não funciona? 

Crie um sistema de carregar e arrastar com o rato que permita ao utilizador rapidamente criar um novo template para utilizar.

## Exercício 6 - Destaca o Wally?

Destaque o Wally detetado colocando todas as zonas da imagem que não são o Wally a cinzento.

![Resultado esperado](images/Ex4.png)


