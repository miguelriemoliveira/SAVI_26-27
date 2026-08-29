# Parte 11 — Funcionalidades de Treino e novas Arquiteturas de redes

As redes neurais são compostas por diversas camadas, cada uma com uma função específica, e utilizam funções de ativação para introduzir não-linearidade e permitir o aprendizado de padrões complexos. De seguida apresenta-se uma introdução aos tipos mais comuns de camadas de redes e funções de ativação mencionadas:

## Tipos de Camadas de Redes

- **Camadas Totalmente Conectadas (Fully Connected / Linear)**
Nestas camadas, cada neurônio está conectado a todos os neurônios da camada anterior.
São frequentemente usadas em redes neurais mais simples, como a ModelFullyConnected inicial, ou nas camadas finais de redes mais complexas para realizar a classificação.
A camada de saída mapeia as representações aprendidas para as classes finais (por exemplo, 10 valores para 10 dígitos possíveis).

- **Camadas Convolucionais (Conv2d)**
São essenciais em Redes Neurais Convolucionais (CNNs), especialmente para dados de imagem como o MNIST. O seu propósito é extrair características (features) das imagens, aplicando filtros (kernels) que fazer a análise da imagem para destacar padrões específicos.
Camadas convolucionais iniciais podem detectar padrões de baixo nível (como bordas), enquanto camadas mais profundas combinam esses padrões para detectar características de nível mais alto (como curvas ou partes de dígitos).

- **Camadas de Pooling (MaxPool2d)**
Estas camadas são utilizadas para reduzir as dimensões espaciais (largura e altura) dos mapas de características produzidos pelas camadas convolucionais.
A redução de dimensionalidade diminui a quantidade de computação necessária e ajuda a tornar o modelo mais robusto a pequenas variações na posição das características (invariância translacional).
Um exemplo comum é o MaxPool2d, que recolhe o valor máximo em janelas (por exemplo, 2x2), reduzindo o tamanho pela metade.

- **Flattening (Achatamento)**
É uma operação que converte os mapas de características 2D (a saída das camadas convolucionais e de pooling) em um vetor 1D.
Esta etapa é necessária para alimentar as camadas totalmente conectadas, que esperam uma entrada unidimensional.

## Funções de Ativação

As funções de ativação são componentes que introduzem não-linearidade nas camadas de uma rede neural, permitindo que ela aprenda e represente relações mais complexas nos dados.

- **Linear (ou Identidade)**
A função de ativação linear, também conhecida como função identidade, simplesmente retorna o valor de entrada sem qualquer modificação, ou seja, $f(x) = x$. Não introduz não-linearidade na rede.
É tipicamente usada na camada de saída de uma rede neural quando o objetivo é realizar uma tarefa de regressão, onde se pretende prever um valor contínuo em vez de uma classe. Se usada em camadas ocultas, uma rede com apenas ativações lineares seria equivalente a uma única camada linear, independentemente do número de camadas, o que limitaria a sua capacidade de aprender padrões complexos.

- **ReLU (Rectified Linear Unit)**
A função ReLU é uma ativação popular que adiciona não-linearidade à rede, permitindo que ela aprenda relações mais complexas nos dados do que apenas transformações lineares.
Matematicamente, a função ReLU retorna o valor de entrada se for positivo, e zero caso contrário. Pode ser formulado como: $f(x) = max(0, x)$.

- **Sigmoid**
A função Sigmoid mapeia os valores de entrada para um intervalo entre 0 e 1, sendo frequentemente usada em camadas de saída para problemas de classificação binária ou em camadas ocultas em redes mais antigas. MAtematicamente, pode ser formulada por: $f(x) = \sigma(x) = \frac{1}{1 + e^{-x}}$.

- **Tanh (Tangente Hiperbólica)**
Semelhante à Sigmoid, a função Tanh também é uma função de ativação não-linear.
No entanto, ela mapeia os valores de entrada para um intervalo entre -1 e 1.
A Tanh é "zero-centrada" (tem uma média de 0), o que pode facilitar o treino em certas arquiteturas de rede em comparação com a Sigmoid.
Matematicamente, a função Tanh é definida como: $f(x) = (e^x - e^-x) / (e^x + e^-x).$

---

## Exercícios

Partindo do código realizado na última aula, vamos explorar vários aspetos do treino das redes. 

### Ex1 Gestão de várias experiências

** a)**

Crie uma funcionalidade para graqvar várias experiências em **`~/data/savi_experiments/...`**

A experiência pode ter um nome dado pelo utilizador, ou gerado automaticamente, e todos os ficheiros com resultados relativos a essa experiência devem ser colocados dentro dessa pasta.

### Ex2 Retomar um treino

**a)**  

Defina uma função **`sigintHanler`** no script **main.py** e registe-a para o sinal SIGINT. Depois experimente terminar um treino prematuramente pressionando em **CTRL+C**.

**b)**  

Crie um novo método **`saveTrain`** na class trainer para fazer a gravação do estado atual do modelo e do progresso do treino.

Crie um dicionário com a seguinte estrutura:

```python
 d = {'epoch_idx': self.epoch_idx,
      'train_losses': self.train_losses,
      'test_losses': self.test_losses,
```

e grave-o usando a função **`torch.save`**. Nota, o ficheiro deverá ser gravado no final de cada época. O formato usado pelo torch,save é o formato pickle, por isso nomeie o ficheiro como **status.pkl**. .

**c)**  

Acrescente ao dicionário a informação necessária para gravar o estado do modelo **`model_state_dict`** e do progresso do treino **`optimizer_state_dict`**.

```python
 d = {'epoch_idx': self.epoch_idx,
      'train_losses': self.train_losses,
      'test_losses': self.test_losses,
      'model_state_dict': self.model.state_dict(),
      'optimizer_state_dict': self.optimizer.state_dict()}
```


**d)**  
Usando estas [instruções](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html#saving-loading-a-general-checkpoint-for-inference-and-or-resuming-training), implemente a funcionalidade de carregar o ficheiro **state.pkl** para resumir um treino gravado anteriormente.

---

### Ex3 Gravação do checkpoint

Como já foi possível observar a performance de um modelo não melhora constantemente, sobretudo se considerarmos o dataset de teste.
O chekpoint é o termo utilizado para designar a versão (a época) em que o modelo se comportou melhor.

**a)**  

Crie um mecanismo para guardar o checkpoint modelo no ficheiro **best.pkl**-
Deve ter em conta apenas o dataset de teste para decidir quando gravar o modelo. Assinale a época do checkpoint no gráfico da loss vs epochs.om uma linha tracejada vertical.

### Ex4 Redes convolucionais

A rede que foi construída na classe model é uma rede com duas camadas fully connected. 

```bash
==========================================================================================
Layer (type:depth-idx)                   Output Shape              Param #
==========================================================================================
ModelFullyConnected                      [1, 10]                   --
├─Linear: 1-1                            [1, 128]                  100,480
├─Sigmoid: 1-2                           [1, 128]                  --
├─Linear: 1-3                            [1, 10]                   1,290
==========================================================================================
Total params: 101,770
Trainable params: 101,770
Non-trainable params: 0
Total mult-adds (Units.MEGABYTES): 0.10
==========================================================================================
Input size (MB): 0.00
Forward/backward pass size (MB): 0.00
Params size (MB): 0.41
Estimated Total Size (MB): 0.41
==========================================================================================
```

A ideia inicial era ter uma rede simples sem acrescentar mais complexidade à aula, que estava focada noutros aspetos. Foi por isso desenhada uma rede simples com duas camadas fully connected.

No entanto, este rede não é a mais adequada para classificar imagens. Para dados de imagem como MNIST, as Redes Neuronais Convolucionais (CNNs) são de fato muito mais eficientes e geralmente alcançam melhor desempenho do que redes fully connected porque podem aprender hierarquias espaciais de recursos diretamente dos dados de pixels.

Estas redes são habitualmente designadas de profundas e convolucionais. Profundas porque têm um número significativo de camadas escondidas, e convolucionais porque têm algumas dessas camadas (geralmente as primeiras) do tipo convolução.

Os resultados obtidos para a rede fully connected que temos vindo a usar foram os seguintes:

```json
  "global": {
    "precision": 0.95,
    "recall": 0.95,
    "f1_score": 0.95
  }
```

Para referência foi utilizado o comando:

    clear && ./main.py -bs 512  -ne 10  


**a)**  

Usando a biblioteca onnx e a app de visualização https://netron.app/, inspecione a a rede anterior e as que irá desenvolver nas alíneas seguintes.

Crie na classe **`model`** um novo método **`exportToOnxx`** para mostrar o sumário da rede e produzir um ficheiro onxx.

```python
    def exportToOnxx(self):

        dummy_input = torch.randn(1, 3, 256, 256)
        filename = os.path.join(self.params['experiment_path'], 'model.onnx')

        # Export to ONNX
        torch.onnx.export(
            self,
            dummy_input,  # type: ignore
            filename,
            verbose=False,  # Set to True for more details during export
            input_names=["input"],
            output_names=["output"],
            opset_version=14  # You might need to adjust opset_version based on your PyTorch version
            # A common version like 11, 12, 13, 14, 15, 16, or 17 should work.
        )
        print("Model exported to " + Fore.BLUE + filename + Fore.RESET)
        print("Go to " + Fore.BLUE + "https://netron.app/" + Fore.RESET + " to view the model.")
```

Deverá conseguir visualizar qualquer coisa como:


![alt text](docs/fully_connected.png)


**b)**  

Implemente a classe **`ModelConvNet`** com a seguinte arquitetura:

```bash
==========================================================================================
Layer (type:depth-idx)                   Output Shape              Param #
==========================================================================================
ModelConvNet                             [1, 10]                   --
├─Conv2d: 1-1                            [1, 32, 28, 28]           320
├─MaxPool2d: 1-2                         [1, 32, 14, 14]           --
├─Conv2d: 1-3                            [1, 64, 14, 14]           18,496
├─MaxPool2d: 1-4                         [1, 64, 7, 7]             --
├─Linear: 1-5                            [1, 128]                  401,536
├─Linear: 1-6                            [1, 10]                   1,290
==========================================================================================
Total params: 421,642
Trainable params: 421,642
Non-trainable params: 0
Total mult-adds (Units.MEGABYTES): 4.28
==========================================================================================
Input size (MB): 0.00
Forward/backward pass size (MB): 0.30
Params size (MB): 1.69
Estimated Total Size (MB): 1.99
==========================================================================================
```

Esta arquitetura de CNN é projetada para classificar dígitos do MNIST aproveitando a estrutura espacial das imagens, o que redes totalmente conectadas (FC) não fazem tão bem. Pontos a destacar nesta arquitetura:

- **Camadas Convolucionais (conv1, conv2):** 
Extraem características (features) da imagem. conv1 detecta padrões de baixo nível (ex: bordas), enquanto conv2 (com mais filtros e após o conv1) combina essas para detectar padrões de nível mais alto (ex: curvas, partes de dígitos). Aplicam filtros (kernels) que fazer a análise da imagem, destacando padrões específicos. O padding=1 ajuda a manter o tamanho da imagem de saída após a convolução.

- **Ativação ReLU (F.relu):**
Adiciona não-linearidade à rede, permitindo que ela aprenda relações mais complexas nos dados do que apenas transformações lineares. 

- **Camadas de Pooling (pool1, pool2):**
Reduzem as dimensões espaciais (largura e altura) dos mapas de características. Isso diminui a quantidade de computação e ajuda a tornar o modelo mais robusto a pequenas variações na posição das características (invariância translacional). MaxPool2d recolhe o valor máximo em janelas 2x2, reduzindo o tamanho pela metade (stride=2).

- **Flattening (x.view(-1, ...)):**
Converte os mapas de características 2D (saída das camadas convolucionais/pooling) em um vetor 1D. Isso é necessário para alimentar as camadas totalmente conectadas.

- **Camadas Totalmente Conectadas (fc1, fc2):**
Usam as características de alto nível extraídas para realizar a classificação final. fc1 atua como uma camada oculta que combina as características para formar representações mais abstratas, e fc2 (a camada de saída) mapeia essas representações para as 10 classes de dígitos.Cada neurônio nesta camada está conectado a todos os neurônios da camada anterior. A camada de saída (fc2) produz 10 valores ("logits"), um para cada dígito possível.

Em resumo, a CNN primeiro extrai características hierárquicas da imagem usando convoluções e pooling, e depois classifica essas características em uma das 10 categorias de dígitos através de camadas totalmente conectadas.

Com esta rede foi possível obter melhores resultados que a anterior versão fully connected.

```json
  "global": {
    "precision": 0.99,
    "recall": 0.99,
    "f1_score": 0.99
  }
```

## O que aprendemos nesta aula?

- A importância da visualização do progresso do treino (curvas de loss).
- Como gerir e retomar o treino de modelos (gravar/carregar estado, sigintHandler).
- A importância de guardar o checkpoint do melhor modelo (melhor desempenho no teste).
- Os tipos de camadas de redes mais comuns: Fully Connected, Convolucionais (Conv2d), Pooling (MaxPool2d) e Flattening.
- As principais funções de ativação e o seu papel na introdução de não-linearidade (Linear, ReLU, Sigmoid, Tanh).
- As vantagens e a implementação de Redes Neuronais Convolucionais (CNNs) para tarefas de classificação de imagens.
