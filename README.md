# Widevoice Downloader GUI

Este é um aplicativo de interface gráfica (GUI) desenvolvido em Python utilizando `tkinter` e `ttkbootstrap` para baixar gravações de chamadas da API Widevoice. O objetivo é fornecer uma ferramenta amigável para interagir com a API, selecionar períodos específicos para download e organizar os arquivos baixados localmente.

## Novidades e Melhorias

Esta versão traz atualizações significativas focadas em melhorar a usabilidade, a robustez e o desempenho do downloader:

* **Interface Gráfica Moderna (ttkbootstrap)**: A GUI foi revitalizada com a integração da biblioteca `ttkbootstrap`, oferecendo um visual mais polido e moderno em comparação com o `tkinter` padrão.
* **Seleção de Data Conveniente**: Incluído um `DatePickerDialog` para permitir que o usuário selecione facilmente as datas de início e fim do período de busca através de um calendário interativo, garantindo a inserção no formato correto.
* **Obtenção Completa de Dados da API**: A lógica de comunicação com a API (`api_handler.py`) foi aprimorada para superar o limite comum de 500 registros por requisição. Agora, o aplicativo realiza múltiplas chamadas incrementais com base na data e hora para obter todos os dados disponíveis no intervalo especificado.
* **Download de Gravações com Retentativas**: O módulo responsável pelo download dos arquivos de gravação (`recording_downloader.py`) agora inclui um mecanismo robusto de retentativas. Em caso de falhas temporárias de rede ou servidor, o download será automaticamente tentado novamente, aumentando a taxa de sucesso.
* **Geração Abrangente de Metadados**: Para cada registro de chamada obtido da API, um arquivo de texto (`.txt`) contendo todos os metadados relevantes é gerado. Isso acontece mesmo para chamadas que não possuem um arquivo de gravação associado, garantindo que as informações da chamada sejam preservadas.
* **Download Paralelo de Gravações**: A performance do download foi otimizada com a implementação de processamento paralelo utilizando `concurrent.futures.ThreadPoolExecutor`. Isso permite que múltiplos arquivos de gravação sejam baixados simultaneamente, reduzindo consideravelmente o tempo total necessário para baixar grandes volumes de gravações.
* **Persistência de Configurações (incluindo Token)**: As configurações essenciais como URL do servidor, login, token de acesso e o diretório de destino são salvas em um arquivo `config.json` após a primeira execução e carregadas automaticamente nas execuções subsequentes. Isso evita a necessidade de reinserir essas informações a cada vez.
* **Sistema de Logging Aprimorado**: Um sistema de logging mais detalhado foi configurado (`main.py`, `api_handler.py`, `gui_app.py`, `recording_downloader.py`). Todas as operações importantes, avisos e erros são registrados em um arquivo de log (`logs/widevoice_downloader.log`), facilitando a identificação e resolução de problemas.
* **Tratamento Específico para Chamadas Sem Gravação**: O aplicativo agora lida explicitamente com registros de chamadas que não possuem um link de gravação. Ele informa o usuário sobre essas chamadas e garante que o arquivo de metadado correspondente seja gerado.

## Como Usar

1.  **Instalação**: Clone o repositório ou baixe os arquivos do projeto.
2.  **Configuração**: Execute o script principal (`main.py`). Na interface gráfica:
    * Preencha o campo "URL do Servidor" com o endereço base da sua API Widevoice.
    * Insira seu "Login" e "Token" de acesso à API.
    * Defina as datas de "Data Início" e "Data Fim" para o período desejado. Você pode digitar manualmente no formato `YYYY-MM-DD HH:mm:ss` ou usar o botão "..." para abrir o seletor de data.
    * Escolha o "Diretório de Salvamento" onde os arquivos serão salvos. Use o botão "Procurar" para selecionar uma pasta.
3.  **Salvar Configurações**: Clique no botão "Salvar Configurações" para armazenar as informações preenchidas (incluindo o token) no arquivo `config.json`. Isso evitará que você precise digitá-las novamente no futuro.
4.  **Iniciar Download**: Clique no botão "Iniciar Download". O aplicativo começará a obter a lista de chamadas do período especificado e a baixar as gravações e metadados correspondentes.
5.  **Acompanhamento**: A área de "Status" exibirá o progresso em tempo real, incluindo informações sobre as chamadas processadas, downloads bem-sucedidos, erros e avisos. A barra de progresso indicará o percentual de chamadas processadas.

## Estrutura de Arquivos Salvos

Os arquivos baixados (gravações `.gsm` e metadados `.txt`) são organizados em subpastas dentro do diretório de destino selecionado, seguindo a estrutura:
