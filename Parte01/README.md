Parte 1 - SAVI

Miguel Riem Oliveira <mriem@ua.pt>
2026-2027

# Sumário

 - Introdução
 - Apresentação
 - Objetivos
 - Avaliação
 - Introdução ao Linux - O terminal
 - Editores e IDEs
 - Tutoriais de OpenCV

# Pressupostos para a realização dos exercícios

Os exercícios desta UC podem ser feitos em **Linux, Windows ou macOS**. O requisito
real não é o sistema operativo em si, mas sim ter um ambiente onde seja possível
instalar e correr:

- uma versão recente do **Python** (3.10 ou superior);
- **OpenCV**;
- **Open3D**.

Os três sistemas operativos permitem instalar estas bibliotecas sem grandes
dificuldades, tipicamente com `pip` dentro de um ambiente virtual.

Ainda assim, **recomenda-se o Ubuntu** (26.04 LTS), por ser o ambiente em que os
exercícios foram preparados e testados, e onde é mais fácil dar apoio nas aulas.
Quem usar Windows ou macOS deve contar com pequenas diferenças pontuais nos
comandos de instalação e nos caminhos de ficheiros.

Independentemente do sistema escolhido, é ainda necessário:

- ter o acesso de rede configurado (_wireless_) — consultar as instruções do site
  dos [sTIC](http://www.ua.pt/stic/PageText.aspx?id=15224).

# Instalação do Ubuntu (opcional)

Esta secção interessa apenas a quem quiser seguir a recomendação e usar Ubuntu,
vindo de Windows ou macOS. Há várias formas de o fazer:

- **Live Ubuntu** ([Try before you install](https://ubuntu.com/tutorials/try-ubuntu-before-you-install)) —
  não mexe no disco nem no sistema operativo existente, mas todo o trabalho se
  perde no fim da sessão se não for copiado para outro local.
- **Máquina virtual** (`virtualbox` ou outra) — também não interfere com o sistema
  nativo e é uma solução intermédia que funciona relativamente bem. Precisa de
  espaço em disco no Windows (ou macOS) para a "imagem" do disco virtual e, como
  opera sobre o sistema nativo, pode ter limitações de desempenho.
- **Dual-boot** com o sistema operativo nativo (**a forma recomendada**) — é a mais
  poderosa, porque cada sistema operativo fica no seu próprio espaço e correm
  separadamente. Porém, é preciso repartir o disco que estaria todo atribuído ao
  sistema nativo. O Linux oferece esta possibilidade durante a instalação e em
  geral o processo corre bem, mas há sempre o risco de perda de informação. Por
  isso, recomenda-se guardar toda a informação importante antes de avançar.

Mais informações, por exemplo, em:

- https://ubuntu.com/tutorials
- https://ubuntu.com/tutorials/install-ubuntu-desktop

# Apresentação da UC

Ver slides de apresentação da UC.

# Introdução ao Linux e a Shell

Mostrar o terminal e os comandos mais frequentes.

# Criação do ambiente e instalação de ferramentas básicas

## Metodologia

Para melhor se desenvolver o trabalho nas aulas, deve-se
seguir uma metodologia de organização de ficheiros em diretórios
por aulas e por exercícios.

Dentro de cada aula, em especial nas primeiras, é também recomendado criar uma subpasta para cada exercício `Ex1`, `Ex2`, etc. Em certas aulas, ou aulas mais avançadas, os diversos exercícios serão feitos por acréscimo sucessivo sobre o código base dos exercícios anteriores; nessa altura serão dadas as instruções nesse sentido.

Os guiões para as aulas estarão a ser continuamente atualizados em:

https://github.com/miguelriemoliveira/SAVI_26-27

Recomenda-se que, sempre que possível, usem a versão online ou façam o update frequentemente.

## Editor

A ferramenta principal para criar e modificar ficheiros é o editor, muitas
vezes integrado num ambiente de desenvolvimento (IDE). Há inúmeras opções
desde simples editores (`gedit`, `kate`, `kwrite`, etc.) até ambientes de
desenvolvimento muito sofisticados (`codeblocks`, `eclipse`, `vscode`,`pycharm` etc.).

Além das propriedades fundamentais dos editores, hoje em dia são excelentes
_add-ons_ a "automated completion" (preenchimento automático de palavras
e estruturas) , o "syntax highlight" (realce da sintaxe da linguagem),
o "intellissense" (apresentação de todas as opções de preenchimento
automático de campos e estruturas em variáveis, funções, etc.), ou a
inserção automática de fragmentos de código padrão ("code snippets").

O editor com mais tradição por excelência é o "vim" (ou "vi" improuved)
mas a sua utilização eficaz pode requerer anos de prática continuada e
permite todas as facilidades indicadas acima, mas a sua configuração,
por ser praticamente ilimitada, pode-se tornar complexa e, por isso,
contraproducente em utilizadores iniciados.

**Recomenda-se como IDE** o [vscode](https://code.visualstudio.com/), que é gratuito, e existe para Linux, Windows e macOS.

## Ambiente Python

Recomenda-se criar um ambiente virtual dedicado à UC, para não misturar as
bibliotecas com as do sistema:

```bash
python3 -m venv ~/venvs/savi
source ~/venvs/savi/bin/activate      # Linux e macOS
# %USERPROFILE%\venvs\savi\Scripts\Activate.ps1   # Windows (PowerShell)
```

Com o ambiente ativo, a instalação das bibliotecas principais é igual nos três
sistemas operativos:

```bash
pip install opencv-python open3d numpy matplotlib
```

## OpenCV

O [OpenCV](https://opencv.org/) é a biblioteca de referência para processamento de imagem e visão por computador. É open source e gratuita.

Para além disso tem imensas funcionalidades básicas e avançadas.

Documentação de instalação, caso o `pip install` acima não chegue:

https://docs.opencv.org/4.x/da/df6/tutorial_py_table_of_contents_setup.html

## Open3D

O [Open3D](https://www.open3d.org/) é a biblioteca que usaremos para processamento
de nuvens de pontos e dados 3D, nas aulas mais avançadas.

https://www.open3d.org/docs/release/getting_started.html


# Exercícios 

## Exercício 1 - Tutoriais do OpenCV

O OpenCV tem vários tutorials que são uma ajuda valiosa para começar.

https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html

Faça os exercícios dos cinco primeiros tutoriais:

 - Introduction to OpenCV
 - Learn how to setup OpenCV-Python on your computer!
 - Gui Features in OpenCV
 - Core Operations
 - Image Processing in OpenCV

