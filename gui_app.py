import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
from datetime import datetime
import os
import json
import logging
import concurrent.futures

# Importa o novo módulo do seletor de data
from date_picker_dialog import DatePickerDialog

# Importa as funcionalidades de outros módulos
from api_handler import construir_url_api, obter_dados_chamadas
from recording_downloader import baixar_gravacao
import config

CONFIG_FILE = "config.json"

logger = logging.getLogger(__name__)

MAX_WORKERS = 5 # Número máximo de downloads paralelos

class WidevoiceDownloaderGUI:
    def __init__(self, master):
        self.master = master
        master.title("Baixador de Gravações Widevoice")

        # --- Componentes da GUI ---
        self.frame_inputs = ttk.LabelFrame(master, text="Configurações de Acesso e Período")
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(self.frame_inputs, text="URL do Servidor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(self.frame_inputs, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Ajuste columnspan


        ttk.Label(self.frame_inputs, text="Login:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.login_entry = ttk.Entry(self.frame_inputs, width=50)
        self.login_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Ajuste columnspan


        ttk.Label(self.frame_inputs, text="Token:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.token_entry = ttk.Entry(self.frame_inputs, show="*", width=50)
        self.token_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Ajuste columnspan


        # Campo e Botão para Data Início
        ttk.Label(self.frame_inputs, text="Data Início (YYYY-MM-DD HH:mm:ss):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.datainicio_entry = ttk.Entry(self.frame_inputs, width=40)
        self.datainicio_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.datainicio_entry.insert(0, datetime.now().strftime('%Y-%m-%d 00:00:00'))

        self.btn_selecionar_data_inicio = ttk.Button(self.frame_inputs, text="...", width=3, command=lambda: self.abrir_seletor_data(self.datainicio_entry))
        self.btn_selecionar_data_inicio.grid(row=3, column=2, padx=0, pady=5)


        # Campo e Botão para Data Fim
        ttk.Label(self.frame_inputs, text="Data Fim (YYYY-MM-DD HH:mm:ss):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.datafim_entry = ttk.Entry(self.frame_inputs, width=40)
        self.datafim_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.datafim_entry.insert(0, datetime.now().strftime('%Y-%m-%d 23:59:59'))

        self.btn_selecionar_data_fim = ttk.Button(self.frame_inputs, text="...", width=3, command=lambda: self.abrir_seletor_data(self.datafim_entry))
        self.btn_selecionar_data_fim.grid(row=4, column=2, padx=0, pady=5)

        # Ajuste as colunas que expandem dentro de frame_inputs
        self.frame_inputs.columnconfigure(1, weight=1) # Coluna dos Entries de data
        self.frame_inputs.columnconfigure(2, weight=0) # Coluna dos botões de data
        # As colunas 1 (Entries) das linhas 0, 1, 2 (URL, Login, Token) também devem expandir, agora com columnspan=2


        # --- Diretório de Destino ---
        self.frame_destino = ttk.LabelFrame(master, text="Diretório de Destino")
        self.frame_destino.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.diretorio_label = ttk.Label(self.frame_destino, text="Diretório de Salvamento:")
        self.diretorio_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.diretorio_entry = ttk.Entry(self.frame_destino, width=40)
        self.diretorio_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.diretorio_entry.insert(0, config.DIRETORIO_BASE_GRAVACOES)

        self.browse_button = ttk.Button(self.frame_destino, text="Procurar", command=self.selecionar_diretorio)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.frame_destino.columnconfigure(1, weight=1)


        # --- Botões de Ação ---
        self.frame_botoes_acao = ttk.Frame(master)
        self.frame_botoes_acao.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.frame_botoes_acao.columnconfigure(0, weight=1) # Coluna para barra de progresso
        self.frame_botoes_acao.columnconfigure(1, weight=0) # Coluna para botão Salvar
        self.frame_botoes_acao.columnconfigure(2, weight=0) # Coluna para botão Download


        # Barra de Progresso
        self.progress_bar = ttk.Progressbar(self.frame_botoes_acao, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Botão Salvar Configurações
        self.save_button = ttk.Button(self.frame_botoes_acao, text="Salvar Configurações", command=self.salvar_configuracoes_button_click)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        # Botão de Download
        self.download_button = ttk.Button(self.frame_botoes_acao, text="Iniciar Download", command=self.iniciar_download)
        self.download_button.grid(row=0, column=2, padx=5, pady=5)


        # Área de Status/Log da GUI
        self.status_label = ttk.Label(master, text="Status:")
        self.status_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")
        self.status_text = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=80, height=15)
        self.status_text.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        # Configurações para redimensionamento da janela principal
        master.columnconfigure(0, weight=1)
        master.rowconfigure(4, weight=1)


        # Carregar configurações ao iniciar
        self.carregar_configuracoes()


    def atualizar_status(self, mensagem):
        """Atualiza a área de texto de status (seguro para chamar de qualquer thread)."""
        self.master.after(0, self._inserir_status, mensagem)

    def _inserir_status(self, mensagem):
         """Método interno para inserir texto no widget de status e logar."""
         self.status_text.insert(tk.END, mensagem + "\n")
         self.status_text.see(tk.END)
         logger.info(f"STATUS GUI: {mensagem}")


    def atualizar_progresso(self, valor):
         """Atualiza o valor da barra de progresso (seguro para chamar de qualquer thread)."""
         self.master.after(0, self._configurar_progresso, valor)

    def _configurar_progresso(self, valor):
         """Método interno para configurar o valor da barra de progresso."""
         self.progress_bar['value'] = valor


    def selecionar_diretorio(self): # <-- Nome do método corrigido aqui!
        """Abre uma caixa de diálogo para o usuário selecionar o diretório de destino."""
        diretorio_selecionado = filedialog.askdirectory(
            initialdir=self.diretorio_entry.get() or os.path.expanduser("~"),
            title="Selecione o Diretório para Salvar Gravações"
        )
        if diretorio_selecionado:
            self.diretorio_entry.delete(0, tk.END)
            self.diretorio_entry.insert(0, diretorio_selecionado)
            logger.info(f"Diretório de destino selecionado via GUI: {diretorio_selecionado}")


    def abrir_seletor_data(self, entry_widget):
        """Cria e exibe a janela do seletor de data."""
        from date_picker_dialog import DatePickerDialog

        current_date_str = entry_widget.get().split(" ")[0] # Pega só a parte da data
        try:
            initial_date = datetime.strptime(current_date_str, '%Y-%m-%d')
            logger.debug(f"Data inicial para o seletor: {initial_date.strftime('%Y-%m-%d')}")
        except (ValueError, TypeError):
            initial_date = datetime.now() # Usa data atual como padrão se a data no campo for inválvida
            logger.debug("Data no campo inválida, usando data atual para o seletor.")


        date_picker = DatePickerDialog(self.master, entry_widget, initial_date)


    def iniciar_download(self):
        """Inicia o processo de download em uma thread separada."""
        self.download_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.atualizar_status("Iniciando processo de download...")
        logger.info("Botão 'Iniciar Download' clicado.")


        self.status_text.delete(1.0, tk.END)
        self.atualizar_progresso(0)


        # Coleta os dados da GUI
        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        token = self.token_entry.get().strip()
        datainicio_str = self.datainicio_entry.get().strip()
        datafim_str = self.datafim_entry.get().strip()
        diretorio_destino = self.diretorio_entry.get().strip()

        logger.info(f"Dados coletados da GUI para download - URL: {url_base}, Login: {login}, Data Início: {datainicio_str}, Data Fim: {datafim_str}, Diretório: {diretorio_destino}")


        # Validação básica
        if not all([url_base, login, token, datainicio_str, datafim_str, diretorio_destino]):
            mensagem_erro = "Erro: Todos os campos precisam ser preenchidos para iniciar o download."
            self.atualizar_status(mensagem_erro)
            logger.warning(mensagem_erro)
            self.master.after(0, self.download_button.config, state=tk.NORMAL)
            self.master.after(0, self.save_button.config, state=tk.NORMAL)
            return

        # Validação básica de formato de data
        try:
            datetime.strptime(datainicio_str, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(datafim_str, '%Y-%m-%d %H:%M:%S')
            logger.info("Formato de data validado com sucesso.")
        except ValueError:
            mensagem_erro = "Erro: Formato de data/hora inválido. Use YYYY-MM-DD HH:mm:ss."
            self.atualizar_status(mensagem_erro)
            logger.warning(mensagem_erro)
            self.master.after(0, self.download_button.config, state=tk.NORMAL)
            self.master.after(0, self.save_button.config, state=tk.NORMAL)
            return

        # Cria e inicia a thread para o download
        logger.info("Criando e iniciando thread para processar download.")
        download_thread = threading.Thread(
            target=self.processar_download,
            args=(url_base, login, token, datainicio_str, datafim_str, diretorio_destino)
        )
        download_thread.start()


    def salvar_configuracoes_button_click(self):
        """Coleta dados da GUI e chama o método para salvar configurações."""
        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        diretorio_destino = self.diretorio_entry.get().strip()

        if not all([url_base, login, diretorio_destino]):
             mensagem_aviso = "Aviso: Preencha URL, Login e Diretório de Destino para salvar as configurações."
             self.atualizar_status(mensagem_aviso)
             logger.warning(mensagem_aviso)
             return

        self.salvar_configuracoes(url_base, login, diretorio_destino)
        self.atualizar_status("Configurações salvas com sucesso.")
        logger.info("Botão 'Salvar Configurações' clicado. Configurações coletadas e salvando.")


    def processar_download(self, url_base, login, token, datainicio_str, datafim_str, diretorio_destino):
        """
        Lógica principal de download a ser executada em uma thread separada.
        Implementa download paralelo.
        """
        logger.info("Thread de download iniciada.")
        try:
            url_api = construir_url_api(url_base, login, token)
            dados_chamadas = obter_dados_chamadas(url_api, datainicio_str, datafim_str, status_callback=self.atualizar_status)

            if dados_chamadas is None:
                self.atualizar_status("Falha ao obter dados da API. Verifique logs para mais detalhes.")
                logger.error("Falha ao obter dados da API.")
                self.atualizar_progresso(0)
                return

            if not isinstance(dados_chamadas, list) or not dados_chamadas:
                self.atualizar_status("Nenhum resultado encontrado ou resposta da API em formato inesperado.")
                logger.info("Nenhum resultado encontrado ou resposta da API em formato inesperado.")
                self.atualizar_progresso(100)
                return

            total_chamadas = len(dados_chamadas)
            self.atualizar_status(f"\nEncontrados {total_chamadas} registros de chamadas.")
            logger.info(f"Encontrados {total_chamadas} registros de chamadas.")

            self.progress_bar['maximum'] = total_chamadas
            self.atualizar_progresso(0)

            gravacoes_baixadas_count = 0
            erros_download_count = 0
            processados_count = 0


            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_chamada = {}

                for chamada in dados_chamadas:
                     if 'gravacao' in chamada and chamada['gravacao']:
                          future = executor.submit(baixar_gravacao, url_base, chamada, diretorio_destino, self.atualizar_status)
                          future_to_chamada[future] = chamada
                     else:
                          future = executor.submit(self._processar_sem_gravacao, chamada, self.atualizar_status)
                          future_to_chamada[future] = chamada


                for future in concurrent.futures.as_completed(future_to_chamada):
                    processados_count += 1
                    self.atualizar_progresso(processados_count)

                    chamada_original = future_to_chamada[future]

                    try:
                        download_successful = future.result()

                    except Exception as exc:
                        chamada_id = chamada_original.get('id', 'desconhecido')
                        mensagem_erro = f"Ocorreu uma exceção ao processar a chamada ID {chamada_id}: {exc}"
                        self.atualizar_status(mensagem_erro)
                        logger.exception(mensagem_erro)


            gravacoes_baixadas_count = 0
            erros_download_count = 0
            for future in future_to_chamada:
                try:
                    if future.result() is True:
                        chamada_original = future_to_chamada[future]
                        if 'gravacao' in chamada_original and chamada_original['gravacao']:
                            gravacoes_baixadas_count += 1
                    else:
                         chamada_original = future_to_chamada[future]
                         if 'gravacao' in chamada_original and chamada_original['gravacao']:
                              erros_download_count += 1

                except Exception:
                    chamada_original = future_to_chamada[future]
                    if 'gravacao' in chamada_original and chamada_original['gravacao']:
                         erros_download_count += 1


            self.atualizar_status("\n--- Processo Finalizado ---")
            self.atualizar_status(f"Gravações baixadas com sucesso: {gravacoes_baixadas_count}")
            if erros_download_count > 0:
                self.atualizar_status(f"Erros durante o download: {erros_download_count}")
                self.atualizar_status("Verifique as mensagens de erro acima para detalhes.")
                logger.warning(f"Processo finalizado com {erros_download_count} erros de download.")
            else:
                 logger.info("Processo finalizado com sucesso.")


            self.atualizar_progresso(total_chamadas)


        except Exception as e:
            mensagem_erro_inesperado = f"Ocorreu um erro inesperado durante o processamento principal: {e}"
            self.atualizar_status(mensagem_erro_inesperado)
            logger.exception(mensagem_erro_inesperado) # Corrigido erro de digitação aqui


        finally:
            logger.info("Processo de download finalizado. Habilitando botões.")
            self.master.after(0, self.download_button.config, state=tk.NORMAL)
            self.master.after(0, self.save_button.config, state=tk.NORMAL)


    def _processar_sem_gravacao(self, chamada, status_callback):
        """Método auxiliar para processar chamadas sem gravação (para contagem e status)."""
        numero_chamada = chamada.get('numero', 'desconhecido')
        datahora_chamada = chamada.get('datahora', 'desconhecido')
        mensagem = f"Chamada: Número {numero_chamada} em {datahora_chamada} - Não possui gravação."
        if status_callback:
             status_callback(mensagem)
        logger.info(mensagem)
        return True


    def salvar_configuracoes(self, url_base, login, diretorio_destino):
        """Salva as configurações em um arquivo JSON (token não é salvo por segurança básica)."""
        config_data = {
            "url_base": url_base,
            "login": login,
            "diretorio_destino": diretorio_destino
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Configurações salvas em {CONFIG_FILE}")
        except Exception as e:
            mensagem_erro = f"Erro ao salvar configurações em {CONFIG_FILE}: {e}"
            self.atualizar_status(mensagem_erro)
            logger.error(mensagem_erro, exc_info=True)


    def carregar_configuracoes(self):
        """Carrega as configurações de um arquivo JSON."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    self.url_entry.insert(0, config_data.get("url_base", ""))
                    self.login_entry.insert(0, config_data.get("login", ""))
                    self.diretorio_entry.insert(0, config_data.get("diretorio_destino", config.DIRETORIO_BASE_GRAVACOES))
                logger.info(f"Configurações carregadas de {CONFIG_FILE}")
            else:
                 logger.info(f"Arquivo de configuração {CONFIG_FILE} não encontrado.")
        except Exception as e:
            mensagem_erro = f"Erro ao carregar configurações de {CONFIG_FILE}: {e}"
            self.atualizar_status(mensagem_erro)
            logger.error(mensagem_erro, exc_info=True)