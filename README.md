# Widevoice Downloader GUI

Este é um aplicativo de desktop com interface gráfica (GUI) desenvolvido em Python usando Tkinter e ttkbootstrap para baixar gravações de chamadas de uma API Widevoice. Ele permite configurar os dados de acesso à API, selecionar o período desejado e o diretório de destino para salvar os arquivos de gravação.

## Funcionalidades

* **Interface Gráfica Moderna:** Utiliza `ttkbootstrap` para uma aparência mais agradável e profissional.
* **Configurações de Acesso à API:** Campos dedicados para inserir a URL do servidor, Login e Token de acesso.
* **Seleção de Período:** Definição da data e hora de início e fim para buscar as chamadas.
* **Seletor Visual de Datas:** Botões auxiliares (`...`) para abrir um calendário visual e selecionar as datas de início e fim de forma mais prática.
* **Seleção de Diretório de Destino:** Campo para especificar onde as gravações baixadas serão salvas, com um botão "Procurar" para navegar no sistema de arquivos.
* **Salvar e Carregar Configurações:** Permite salvar as configurações inseridas (URL, Login, Token e Diretório) em um arquivo (`config.json`) e carregá-las automaticamente ao iniciar o aplicativo.
* **Download Paralelo:** Baixa múltiplas gravações simultaneamente (configurável com `MAX_WORKERS` no código) para otimizar o processo.
* **Acompanhamento do Processo:** Uma barra de progresso indica o andamento geral do download e uma área de status exibe mensagens informativas, avisos e erros.
* **Sistema de Logging:** Registra as atividades do aplicativo em um arquivo de log (`logs/widevoice_downloader.log`) para facilitar a depuração.

## Requisitos

* Python 3.6 ou superior.
* As seguintes bibliotecas Python:
    * `tkinter` (geralmente incluído na instalação padrão do Python)
    * `ttkbootstrap`
    * `requests`
    * Outras bibliotecas padrão do Python (`os`, `json`, `threading`, `datetime`, `calendar`, `concurrent.futures`, `time`, `logging`)

## Instalação

1.  **Clone o repositório** (ou baixe os arquivos `.py` e `.config`):
    ```bash
    # Se estiver usando Git
    git clone <url_do_seu_repositorio>
    cd <nome_da_pasta>
    ```
    (Se você apenas baixou os arquivos, certifique-se de que estejam todos na mesma pasta).

2.  **Crie e ative um ambiente virtual** (altamente recomendado para isolar as dependências do projeto):
    ```bash
    python -m venv .venv
    # No Windows:
    .venv\Scripts\activate
    # No macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Instale as bibliotecas necessárias:**
    Crie um arquivo chamado `requirements.txt` no diretório do projeto com o seguinte conteúdo:
    ```
    requests
    ttkbootstrap
    ```
    Em seguida, no terminal (com o ambiente virtual ativado), execute:
    ```bash
    pip install -r requirements.txt
    ```

## Como Executar

### Executar a partir do código fonte

No terminal (com o ambiente virtual ativado), execute o script principal:

```bash
python main.py
