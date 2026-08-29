# Parte 09 — Introdução ao PyTorch e Classificação de Dígitos

Nesta primeira aula vamos explorar o **PyTorch**, uma das bibliotecas mais populares para *Deep Learning*.  
O objetivo é construir, treinar e avaliar uma rede neural simples para classificação de dígitos manuscritos utilizando o dataset **MNIST**.  

---

## Organização de um Projeto PyTorch

Um projeto em PyTorch deve ser estruturado de forma modular e orientada a objetos.  
O PyTorch fornece classes base que devemos herdar e adaptar:  

- **Dataset** — para representar e aceder a conjuntos de dados personalizados.  
- **DataLoader** — para dividir os dados em *batches*, embaralhar exemplos e facilitar o treino.  
- **nn.Module** — para definir arquiteturas de redes neurais.  
- **Optimizers** — para implementar algoritmos de otimização como SGD ou Adam.  

Esta abordagem garante maior clareza, reutilização de código e facilidade de expansão.  

---

## Instalação do PyTorch

A instalação depende da máquina e da disponibilidade de GPU com CUDA.  
De forma geral, pode ser feita através de *pip* ou *conda*.  

### Instalação com pip em linux:

Para instalar com suporte cpu:

    pip install torch torchvision torchaudio

com suporte para cuda (exemplo para CUDA 11.8):

    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

### Instalação com conda:

Com suporte cpu:

    conda install pytorch torchvision torchaudio cpuonly -c pytorch

Para suporte gpu:

    conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia


Após a instalação, é boa prática verificar a versão do PyTorch e confirmar se o suporte a GPU está ativo.  

```python
import torch

print("Versão do PyTorch:", torch.__version__)
print("CUDA disponível:", torch.cuda.is_available())
print("Dispositivo em uso:", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
```

---

## Exercícios

Ao longo desta aula, iremos implementar três classes que compõem o esqueleto de um programa em PyTorch:  
- uma classe **Dataset**, responsável por carregar e preparar os dados,  
- uma classe **Model**, que define a arquitetura da rede neural,  
- e uma classe **Trainer**, que organiza todo o processo de treino da rede.  

Em conjunto, estas três classes formam a base de qualquer projeto PyTorch bem estruturado.

### Ex1 — Construção de um leitor de datasets com a classe Dataset

**a)**  
Faça o download do dataset **mnist_aapi** do e-learning e coloque-o numa pasta conhecida, por exemplo:  

    ~/datasets/mnist_aapi


**b)**  
Crie uma classe `Dataset` que faça a leitura das imagens e dos *labels*.  
Implemente obrigatoriamente os métodos **`__init__`**, **`__len__`** e **`__getitem__`**.  

Os *labels* devem ser representados no formato *one-hot encoding*.  

**c)**  
Para testar, escolha um índice arbitrário e obtenha a imagem e o *label* através do método **`__getitem__`**.  
Visualize a imagem com recurso ao Matplotlib.  

**d)**  
Construa um mosaico **5x5** com exemplos sorteados aleatoriamente do dataset para ter uma visão geral da sua diversidade.  

---

### Ex2 — Construção de uma rede com a classe Model

**a)**  
Crie uma classe `Model` que herda de `nn.Module`.  
Implemente os métodos **`__init__`** (definição das camadas) e **`forward`** (definição do fluxo dos dados).  

Dica: ao imprimir o tamanho dos tensores após carregar uma imagem, deverá surgir `1 x 28 x 28`:  
- `1` → número de canais de cor (imagem a preto e branco)  
- `28 x 28` → dimensão da imagem em pixeis  

Implemente uma rede *fully connected* com **10 saídas**, correspondentes aos 10 dígitos possíveis.  

**b)**  
No método **forward**, utilize a função *view* para achatar (flatten) o vetor de entrada e permitir a sua passagem pela camada *fully connected*.  

**c)**  
Utilize a rede para prever um dígito a partir de uma imagem.  
Imprima os valores obtidos para os *labels* da imagem.  

**d)**  
Os valores obtidos pela rede são chamados **logits**.  
Para convertê-los em probabilidades, utilize a função *softmax*.  
Verifique que a soma de todas as probabilidades é igual a 1.  

**e)**  
Obtenha a classe prevista identificando o índice com maior probabilidade.  
Compare o resultado com a *ground truth* (classe real).  

*Questão:* porque é que a classe prevista não é sempre a mesma antes do treino?  
*Resposta esperada:* devido à inicialização aleatória dos pesos da rede, que gera variação nos logits iniciais.  

---

### Ex3 — Implementação de um treino com a classe Trainer

**a)**  
Construa uma classe `Trainer` com métodos como **`__init__`** e **`train`**, entre outros que irão estruturar o processo de treino.  

**b)**  
Construa *data loaders* para treino e teste com um parâmetro **batch_size** de `10000`, passado como argumento de linha de comandos.  
No método `train`, verifique com um ciclo `for` os tamanhos dos tensores obtidos em cada iteração e explique-os:  
- imagens → `batch_size x 1 x 28 x 28`  
- labels → `batch_size x 10`  

**c)**  
Dentro do ciclo de treino:  
- Obtenha as previsões da rede;
- Calcule as probabilidades correspondentes;
- Calcule a *loss* para cada batch (batch_loss) com **`nn.BCEWithLogitsLoss`**.  

Observe a evolução da *batch_loss*. 

**d)**  
Defina um otimizador **Adam** com *learning rate* de `0.0001`.  
Use-o para atualizar os pesos através de *backpropagation*.  

Questão: se reiniciar o programa, qual será o comportamento da *batch_loss*?  É diferente da alínea anterior? Porquê?

**e)**  
Cada ciclo completo do *data loader* corresponde a **uma época**.  
Calcule a *epoch loss* como a média das *batch_losses* dessa época.  

**g)**  
Introduza um novo parâmetro **num_epochs** (por exemplo, `5`) e adapte o código para que o treino decorra durante esse número de épocas.  

---

## O que aprendemos nesta aula?

- Estrutura modular de um projeto em PyTorch (`Dataset`, `DataLoader`, `Model`, `Trainer`).  
- Leitura e visualização de dados do MNIST.  
- Definição de uma rede *fully connected* simples.  
- Cálculo de logits, conversão em probabilidades e comparação com *labels*.  
- Ciclo de treino com *loss function*, *optimizer* e atualização de pesos.  
- Evolução da *loss* ao longo das épocas de treino.  