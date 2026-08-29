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
 - Ambientes virtuais (venv) e instalação de bibliotecas
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

## Ambiente virtual (venv)

### O que é e porquê

Ao longo do semestre vamos instalar muitas bibliotecas (OpenCV, Open3D, PyTorch,
...), algumas delas grandes e com versões específicas. Instalá-las diretamente no
Python do sistema traz dois problemas: pode entrar em conflito com outras
disciplinas ou projetos que precisem de versões diferentes, e no Linux e macOS o
Python do sistema é usado pelo próprio sistema operativo, pelo que mexer nele pode
partir outras coisas.

A solução é um **ambiente virtual** (_virtual environment_, ou `venv`): uma pasta
isolada com a sua própria cópia do Python e das suas bibliotecas. O que lá se
instala não afeta o resto do computador, e se algo correr mal basta apagar a pasta
e voltar a começar.

### Criar o ambiente

Cria-se **uma única vez**, no início do semestre. Escolha um local fora da pasta
das aulas, por exemplo `~/venvs/savi`:

```bash
python3 -m venv ~/venvs/savi
```

No Windows (PowerShell):

```powershell
python -m venv $HOME\venvs\savi
```

> **Atenção à versão do Python.** É preciso Python 3.10 ou superior. Confirme com
> `python3 --version`. Em macOS, o `python3` do sistema costuma ser antigo (3.9);
> nesse caso instale um mais recente (por exemplo com o [Homebrew](https://brew.sh/),
> `brew install python@3.12`) e use-o explicitamente ao criar o ambiente:
> `python3.12 -m venv ~/venvs/savi`.

### Ativar o ambiente

Ao contrário da criação, a ativação é feita **sempre que se abre um novo
terminal**. Linux e macOS:

```bash
source ~/venvs/savi/bin/activate
```

Windows (PowerShell):

```powershell
$HOME\venvs\savi\Scripts\Activate.ps1
```

O terminal passa a mostrar o nome do ambiente no início da linha:

```
(savi) utilizador@maquina:~$
```

Esse `(savi)` é a confirmação de que está ativo. Para verificar que o `python` em
uso é mesmo o do ambiente:

```bash
which python        # deve responder ~/venvs/savi/bin/python
python --version    # deve responder 3.10 ou superior
```

Para sair do ambiente, em qualquer sistema:

```bash
deactivate
```

### Instalar as bibliotecas

**Com o ambiente ativo** (senão os pacotes vão parar ao Python do sistema),
instale as bibliotecas da UC. A lista completa está no ficheiro
`requirements.txt` na raiz deste repositório:

```bash
pip install -r requirements.txt
```

Se preferir instalar só o necessário para as primeiras aulas:

```bash
pip install numpy matplotlib opencv-python
```

O `open3d` (Partes 7 e 8) e o `torch`/`torchvision` (Partes 9 a 13) podem ficar
para mais tarde, quando forem precisos.

Esta instalação também se faz **uma só vez**. Nas aulas seguintes basta ativar o
ambiente.

Para confirmar que ficou tudo bem:

```bash
python -c "import cv2; print(cv2.__version__)"
```

### Resumo

| Operação | Quando | Comando |
|---|---|---|
| Criar o ambiente | uma vez, no início do semestre | `python3 -m venv ~/venvs/savi` |
| Instalar bibliotecas | uma vez, com o ambiente ativo | `pip install -r requirements.txt` |
| Ativar | sempre que abre um terminal novo | `source ~/venvs/savi/bin/activate` |
| Sair | quando quiser | `deactivate` |

## Usar o ambiente no vscode

Nas aulas é cómodo correr os programas com o botão ▶ (_Run_) do vscode, em vez de
escrever o comando no terminal. Para isso o vscode tem de saber qual o Python a
usar — caso contrário usa o do sistema e os `import cv2` vão falhar, mesmo com o
ambiente criado.

1. Instale a extensão **Python** da Microsoft (`ms-python.python`), no separador
   das extensões.
2. Abra a pasta das aulas no vscode (*File > Open Folder*).
3. Prima `Ctrl+Shift+P` (`Cmd+Shift+P` no macOS) para abrir a paleta de comandos e
   escreva **`Python: Select Interpreter`**.
4. Escolha o interpretador do ambiente na lista.

> **O ambiente não aparece na lista?** É o problema mais comum, e não quer dizer
> que esteja mal criado. O vscode só procura ambientes automaticamente dentro da
> pasta do projeto e nalgumas localizações padrão — a pasta `~/venvs` **não** é
> uma delas. Há duas formas de resolver:
>
> **a) Indicar o caminho à mão** (resolve já, para este ambiente). Na mesma lista,
> escolha *Enter interpreter path...* e escreva:
> - Linux e macOS: `~/venvs/savi/bin/python`
> - Windows: `%USERPROFILE%\venvs\savi\Scripts\python.exe`
>
> **b) Ensinar o vscode a procurar em `~/venvs`** (resolve para todos os ambientes
> que venha a criar). Abra as definições com `Ctrl+Shift+P` >
> *Preferences: Open User Settings (JSON)* e acrescente a linha:
>
> ```json
> "python.venvPath": "~/venvs"
> ```
>
> Depois faça `Ctrl+Shift+P` > *Developer: Reload Window* e repita o passo 3.

Uma alternativa que evita o problema todo é criar o ambiente **dentro** da pasta
das aulas, com o nome `.venv` (`python3 -m venv .venv`). O vscode deteta-o
sozinho, sem qualquer configuração. Em contrapartida, o ambiente fica preso a
essa pasta e é apagado se apagar a pasta das aulas.

Feito isto:

- o botão ▶ passa a correr os _scripts_ com o Python do ambiente;
- o terminal integrado do vscode ativa o ambiente automaticamente ao abrir (verá
  o `(savi)` no prompt);
- o _autocomplete_ e a deteção de erros passam a reconhecer o `cv2`, o `open3d`,
  etc.

A escolha fica guardada na pasta, em `.vscode/settings.json`, pelo que só é
preciso fazer isto uma vez por cada pasta de trabalho.

### Caminhos relativos e a pasta de trabalho

Nos exercícios é natural escrever caminhos relativos, por exemplo:

```python
imagem = cv2.imread('../images/lake.jpg')
```

Um caminho relativo é resolvido a partir da **diretoria de trabalho** (_current
working directory_), que é o sítio de onde o programa foi lançado — e não,
necessariamente, a pasta onde o ficheiro `.py` está guardado.

É aqui que surge uma confusão frequente: por omissão, o vscode lança os
programas a partir da **raiz da pasta aberta**, não da pasta do ficheiro. O
mesmo _script_ que corre bem no terminal (onde normalmente já se fez `cd` para a
pasta do exercício) falha com o botão ▶, com um erro do género:

```
FileNotFoundError: ../images/lake.jpg
```

ou, no caso do OpenCV, um `imread` que devolve `None` sem dar erro nenhum.

Para que o vscode passe a lançar os programas a partir da pasta do ficheiro,
este repositório já traz a configuração feita em `.vscode/settings.json`:

```json
"python.terminal.executeInFileDir": true
```

Quem trabalhar noutra pasta pode acrescentar a mesma linha às suas definições
(`Ctrl+Shift+P` > *Preferences: Open User Settings (JSON)*).

Esta opção afeta o botão ▶. Para o **depurador** (tecla `F5`) é preciso indicar
a mesma coisa no `.vscode/launch.json`, que também já vem incluído:

```json
"cwd": "${fileDirname}"
```

Em caso de dúvida, o modo mais simples de perceber onde o programa está a correr
é imprimi-lo:

```python
import os
print('A correr em:', os.getcwd())
```

#### Alternativa: caminhos relativos ao ficheiro

A configuração acima resolve o problema no vscode, mas o programa continua
dependente de ser lançado do sítio certo. Para que funcione sempre,
independentemente de onde é lançado, pode construir-se o caminho a partir da
localização do próprio ficheiro `.py`:

```python
import os
import cv2

pasta = os.path.dirname(os.path.abspath(__file__))
imagem = cv2.imread(os.path.join(pasta, '..', 'images', 'lake.jpg'))
```

A variável `__file__` contém o caminho do _script_ em execução, pelo que
`pasta` é sempre a pasta onde o ficheiro está, qualquer que seja a diretoria de
trabalho. É a forma mais robusta, e a recomendada quando quiser partilhar código
com colegas.

> **Nota.** O canto inferior direito da janela do vscode mostra sempre o
> interpretador selecionado. Se os `import` estiverem a falhar, é o primeiro sítio
> a verificar.

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

