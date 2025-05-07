# Widevoice Downloader GUI

Este é um aplicativo com interface gráfica para baixar gravações e metadados de chamadas de uma API Widevoice. Ele permite configurar credenciais de acesso, selecionar um período e um diretório de destino, e gerenciar o processo de download, incluindo opções para tratamento de metadados e funcionalidade de cancelamento.

## Funcionalidades

* **Interface Gráfica Moderna:** Utiliza `ttkbootstrap` para uma aparência moderna e responsiva.
* **Configurações de Acesso:** Permite inserir a URL do servidor Widevoice, login e token de acesso à API.
* **Seleção de Período:** Interface intuitiva para selecionar as datas de início e fim para buscar as chamadas.
* **Diretório de Destino Customizável:** Escolha facilmente o diretório onde as gravações e metadados serão salvos.
* **Download Paralelo:** Baixa múltiplas gravações simultaneamente para otimizar o tempo. (Configurável via `MAX_WORKERS` em `download_controller.py`)
* **Gerenciamento de Metadados Flexível:**
    * Opção para baixar arquivos de metadado (`.txt`) junto com as gravações correspondentes.
    * Opção para gerar arquivos de metadado (`.txt`) *apenas* para chamadas que não possuem gravação associada, salvando-os em uma pasta separada (`Metadata_Only`) para facilitar a identificação.
* **Retentativas de Download:** Tenta baixar gravações falhas várias vezes antes de desistir. (Configurável via `MAX_RETRIES` e `RETRY_DELAY` em `recording_downloader.py`)
* **Cancelamento do Processo:** Botão dedicado para cancelar o processo de download a qualquer momento.
* **Status e Progresso em Tempo Real:** Exibe mensagens de status detalhadas e atualiza uma barra de progresso na interface.
* **Log de Atividades:** Registra o processo, erros e avisos em um arquivo de log (`logs/widevoice_downloader.log`) e no console.
* **Persistência de Configurações:** Salva automaticamente (se o usuário clicar em "Salvar Configurações") as credenciais, datas, diretório e opções de metadado inseridas em um arquivo (`config.json`) para uso futuro.
* **Ofuscação de Token:** O token de acesso é ofuscado usando Base64 no arquivo de configuração para maior segurança (não é criptografia forte, apenas ofuscação básica).
* **Tratamento de Erros Robustos:** Lida com falhas na comunicação com a API, erros de download e outros problemas, reportando-os ao usuário e no log.
* **Organização de Arquivos:** Salva gravações e metadados em subpastas organizadas por Ano/Mês/Dia no diretório de destino escolhido.

## Como Usar

1.  **Instalação:**
    * Certifique-se de ter Python instalado (versão 3.6+ recomendada).
    * Instale as dependências necessárias:
        ```bash
        pip install requests ttkbootstrap
        ```

2.  **Execução:**
    * Execute o script principal:
        ```bash
        python main.py
        ```

3.  **Interface do Usuário:**
    * Preencha os campos **URL do Servidor**, **Login** e **Token** com suas credenciais de acesso à API Widevoice.
    * Utilize os seletores de data ou digite as datas nos campos **Data Início** e **Data Fim** no formato `YYYY-MM-DD`.
    * Selecione o **Diretório de Salvamento** clicando no botão "Procurar". O diretório padrão é `Documentos/Gravacoes_Widevoice` na sua pasta de usuário.
    * Marque ou desmarque as opções em **Opções de Download** conforme sua preferência para o gerenciamento de metadados:
        * `Baixar Metadados (Com Gravação)`: Se marcada, gera um arquivo `.txt` com os detalhes da chamada para cada gravação baixada com sucesso ou que falhou o download.
        * `Baixar Metadados (Sem Gravação)`: Se marcada, gera um arquivo `.txt` com os detalhes da chamada *apenas* para os registros da API que não possuem um arquivo de gravação associado, salvando-os na pasta `Metadata_Only`.
    * Clique em **"Salvar Configurações"** para persistir as configurações atuais no arquivo `config.json`. Elas serão carregadas automaticamente na próxima vez que você abrir o aplicativo.
    * Clique em **"Iniciar Download"** para começar o processo.
    * Acompanhe o status e o progresso na área de texto e na barra de progresso.
    * Clique em **"Cancelar Download"** (botão que aparece durante o download) para interromper o processo.

4.  **Visualizando Logs:**
    * Detalhes sobre o processo, avisos e erros são registrados no arquivo `logs/widevoice_downloader.log` (criado na pasta `logs` no mesmo diretório do executável/script).

## Configuração Adicional (Opcional)

* Você pode modificar as constantes em `config.py`, `download_controller.py` (MAX_WORKERS) e `recording_downloader.py` (MAX_RETRIES, RETRY_DELAY) para ajustar o comportamento do aplicativo.
