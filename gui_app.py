import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
import tkinter.filedialog as filedialog
from tkinter import scrolledtext

import threading # Ainda necessário para a thread principal que chama o controlador
from datetime import datetime
import os
import logging
# Removido import concurrent.futures pois o executor está no DownloadController
# import concurrent.futures

# Importa os módulos necessários
import security_manager
import config
# Importa o novo controlador de download
from download_controller import DownloadController

# Remove definição de MAX_WORKERS pois está no DownloadController
# MAX_WORKERS = 5

logger = logging.getLogger(__name__)


class WidevoiceDownloaderGUI:
    def __init__(self, master):
        self.master = master
        master.title("Baixador de Gravações Widevoice")

        # --- Componentes da GUI ---
        self.frame_inputs = ttk.LabelFrame(master, text="Configurações de Acesso e Período")
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(self.frame_inputs, text="URL do Servidor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(self.frame_inputs, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(self.frame_inputs, text="Login:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.login_entry = ttk.Entry(self.frame_inputs, width=50)
        self.login_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(self.frame_inputs, text="Token:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.token_entry = ttk.Entry(self.frame_inputs, show="*", width=50)
        self.token_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(self.frame_inputs, text="Data Início (YYYY-MM-DD):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.datainicio_entry = DateEntry(
            self.frame_inputs,
            bootstyle="primary",
            dateformat="%Y-%m-%d",
            startdate=datetime.now().date()
        )
        self.datainicio_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        ttk.Label(self.frame_inputs, text="Data Fim (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.datafim_entry = DateEntry(
            self.frame_inputs,
            bootstyle="primary",
            dateformat="%Y-%m-%d",
            startdate=datetime.now().date()
        )
        self.datafim_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        self.frame_inputs.columnconfigure(1, weight=1)
        self.frame_inputs.columnconfigure(2, weight=0)

        self.frame_destino = ttk.LabelFrame(master, text="Diretório de Destino")
        self.frame_destino.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.diretorio_label = ttk.Label(self.frame_destino, text="Diretório de Salvamento:")
        self.diretorio_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.diretorio_var = tk.StringVar()
        self.diretorio_entry = ttk.Entry(self.frame_destino, width=40, textvariable=self.diretorio_var)
        self.diretorio_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.diretorio_var.set(config.DIRETORIO_BASE_GRAVACOES)


        self.browse_button = ttk.Button(self.frame_destino, text="Procurar", command=self.selecionar_diretorio)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.frame_destino.columnconfigure(1, weight=1)

        self.frame_botoes_acao = ttk.Frame(master)
        self.frame_botoes_acao.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.frame_botoes_acao.columnconfigure(0, weight=1)
        self.frame_botoes_acao.columnconfigure(1, weight=0)
        self.frame_botoes_acao.columnconfigure(2, weight=0)

        self.progress_bar = ttk.Progressbar(self.frame_botoes_acao, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.save_button = ttk.Button(self.frame_botoes_acao, text="Salvar Configurações", command=self.salvar_configuracoes_button_click)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        self.download_button = ttk.Button(self.frame_botoes_acao, text="Iniciar Download", command=self.iniciar_download)
        self.download_button.grid(row=0, column=2, padx=5, pady=5)

        # Área de Status/Log da GUI
        self.status_label = ttk.Label(master, text="Status:")
        self.status_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")
        self.status_text = scrolledtext.ScrolledText(master, wrap=ttk.WORD, width=80, height=15)
        self.status_text.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        # --- Configurar Tags para Status ---
        self.status_text.tag_configure('info', foreground='black')  # Cor padrão para informações
        self.status_text.tag_configure('warning', foreground='orange')  # Cor para avisos
        self.status_text.tag_configure('error', foreground='red')  # Cor para erros
        # Você pode adicionar outros estilos aqui, como negrito, etc.
        # Exemplo: self.status_text.tag_configure('error', foreground='red', font=('Arial', 9, 'bold'))

        # Configurações para redimensionamento da janela principal
        master.columnconfigure(0, weight=1)
        master.rowconfigure(4, weight=1)

        # Configurações para redimensionamento da janela principal
        master.columnconfigure(0, weight=1)
        master.rowconfigure(4, weight=1)

        # Cria uma instância do DownloadController, passando os callbacks da GUI
        self.download_controller = DownloadController(
            status_callback=self.atualizar_status,
            progress_callback=self.atualizar_progresso,
            completion_callback=self._process_download_completed, # Novo callback de conclusão
            directory_getter=self._get_download_directory # Callback para obter o diretório
        )


        # Carregar configurações ao iniciar
        self.carregar_configuracoes()


    # --- Métodos Auxiliares para Gerenciar Botões (seguro para thread - chamados via after) ---
    # Estes métodos são agora callbacks para o DownloadController
    def _enable_download_button(self):
        """Habilita o botão de download na thread principal."""
        logger.info("GUI: Habilitando botão 'Iniciar Download'.")
        try:
            self.download_button.config(state=tk.NORMAL)
        except Exception as e:
            logger.error(f"GUI: Erro ao habilitar botão 'Iniciar Download': {e}")

    def _enable_save_button(self):
        """Habilita o botão de salvar na thread principal."""
        logger.info("GUI: Habilitando botão 'Salvar Configurações'.")
        try:
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            logger.error(f"GUI: Erro ao habilitar botão 'Salvar Configurações': {e}")

    def _process_download_completed(self):
         """Callback chamado pelo DownloadController quando o processo termina."""
         logger.info("GUI: Callback de conclusão do processo de download recebido.")
         # Agenda a reabilitação dos botões na thread principal
         self.master.after(0, self._enable_download_button)
         self.master.after(0, self._enable_save_button)
         logger.info("GUI: Reabilitação de botões agendada.")


    # --- Métodos Auxiliares para Atualizar GUI (seguro para thread - chamados via after) ---
    # Estes métodos são agora callbacks para o DownloadController
    def atualizar_status(self, mensagem, level=logging.INFO):
        """
        Atualiza a área de texto de status (seguro para chamar de qualquer thread).
        Mapeia o nível de log para uma tag de formatação.
        """
        # Mapeia o nível de log para o nome da tag
        tag = 'info'  # Tag padrão
        if level == logging.WARNING:
            tag = 'warning'
        elif level == logging.ERROR:
            tag = 'error'
        # Adicione outros mapeamentos conforme necessário

        try:
            # Usa after(0, ...) para agendar a execução na thread principal, passando a tag
            self.master.after(0, self._inserir_status, mensagem, tag)
        except Exception as e:
            logger.error(f"GUI: Erro ao agendar atualização de status: {e} - Mensagem: {mensagem}, Nível: {level}",
                         exc_info=True)

    # O metodo _inserir_status foi modificado para aceitar 'tag'.
    # def _inserir_status(self, mensagem, tag=None): ...

    def _inserir_status(self, mensagem, tag=None):
        """
        Metodo interno para inserir texto no widget de status e logar.
        Aceita um argumento 'tag' para aplicar formatação.
        """
        try:
            # Insere a mensagem e a quebra de linha
            self.status_text.insert(tk.END, mensagem + "\n", tag)  # Aplica a tag aqui
            self.status_text.see(tk.END)  # Rola para ver a última mensagem
            # Logging da mensagem de status já acontece dentro do _log_and_status do controlador ou aqui se for chamado diretamente
            # logger.info(f"STATUS GUI: {mensagem}") # Evita logar a mesma mensagem duas vezes se vindo do controlador
        except Exception as e:
            logger.error(f"GUI: Erro ao inserir status na GUI: {e} - Mensagem: {mensagem}", exc_info=True)

    # O metodo atualizar_status precisará ser ajustado para passar a tag/nível
    # Faremos isso depois de definir as tags na GUI e ajustar o controlador.


    def atualizar_progresso(self, valor):
         """Atualiza o valor da barra de progresso (seguro para chamar de qualquer thread)."""
         try:
            # Usa after(0, ...) para agendar a execução na thread principal
            self.master.after(0, self._configurar_progresso, valor)
         except Exception as e:
             logger.error(f"GUI: Erro ao agendar atualização de progresso: {e} - Valor: {valor}")


    def _configurar_progresso(self, valor):
         """Método interno para configurar o valor da barra de progresso."""
         try:
             self.progress_bar['value'] = valor
         except Exception as e:
             logger.error(f"GUI: Erro ao configurar barra de progresso: {e} - Valor: {valor}")

    # Nota: A atualização do valor máximo da barra de progresso ainda precisa ser feita na GUI,
    # pois é um widget da GUI. A GUI receberá o total_chamadas do controlador
    # e agendará essa atualização na thread principal. Vamos ajustar iniciar_download para isso.


    # --- Métodos de Interação da GUI ---
    def selecionar_diretorio(self):
        """Abre uma caixa de diálogo para o usuário selecionar o diretório de destino."""
        diretorio_selecionado = filedialog.askdirectory(
            initialdir=self.diretorio_var.get() or os.path.expanduser("~"),
            title="Selecione o Diretório para Salvar Gravações"
        )
        if diretorio_selecionado:
            self.diretorio_var.set(diretorio_selecionado)
            logger.info(f"GUI: Diretório de destino selecionado via GUI: {diretorio_selecionado}")

    def _get_download_directory(self):
        """Método getter para o DownloadController obter o diretório de destino atual da GUI."""
        return self.diretorio_var.get().strip()


    def iniciar_download(self):
        """
        Coleta dados da GUI, valida e passa a solicitação de download para o DownloadController.
        """
        # Desabilita botões durante o processo
        self.download_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.atualizar_status("GUI: Coletando dados e validando para iniciar download...")
        logger.info("GUI: Botão 'Iniciar Download' clicado. Coletando dados.")

        # Limpa status e progresso para um novo download
        try:
            self.status_text.delete(1.0, tk.END)
            self.atualizar_progresso(0)
            self.progress_bar['maximum'] = 100 # Reseta o máximo inicialmente
        except Exception as e:
             logger.error(f"GUI: Erro ao limpar status ou progresso antes de iniciar download: {e}")


        # Coleta os dados da GUI
        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        token = self.token_entry.get().strip() # Pega o token diretamente da GUI (já deobfuscado ao carregar)

        # Obtém apenas a data dos DateEntry e adiciona a hora padrão
        datainicio_date_str = self.datainicio_entry.entry.get().strip()
        datafim_date_str = self.datafim_entry.entry.get().strip()

        # Adiciona a parte da hora para formar a string completa no formato esperado pela API
        datainicio_str = f"{datainicio_date_str} 00:00:00" if datainicio_date_str else ""
        datafim_str = f"{datafim_date_str} 23:59:59" if datafim_date_str else ""

        # Não precisamos coletar o diretorio_destino aqui diretamente,
        # o DownloadController irá obtê-lo via self._get_download_directory()

        logger.info(f"GUI: Dados coletados para passar ao controlador - URL: {url_base}, Login: {login}, Data Início (com hora): {datainicio_str}, Data Fim (com hora): {datafim_str}")

        # Validação básica dos campos necessários antes de passar para o controlador
        # O controlador fará validações internas mais específicas da lógica de download/API.
        if not all([url_base, login, token, datainicio_str, datafim_str]): # Diretório é validado pelo controlador via getter
            mensagem_erro = "Erro GUI: Preencha URL, Login, Token e as Datas para iniciar o download."
            self.atualizar_status(mensagem_erro)
            logger.warning(mensagem_erro)
            # Agenda habilitação dos botões na thread principal
            self.master.after(0, self._enable_download_button)
            self.master.after(0, self._enable_save_button)
            return

        # Validação básica de formato de data/hora completa antes de passar para a API (no controlador)
        try:
            datetime.strptime(datainicio_str, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(datafim_str, '%Y-%m-%d %H:%M:%S')
            logger.info("GUI: Formato de data/hora validado localmente.")
        except ValueError:
            mensagem_erro = "Erro GUI: Formato de data/hora inválido no campo. Use YYYY-MM-DD."
            self.atualizar_status(mensagem_erro)
            logger.error(f"GUI: Falha na validação de formato de data/hora local: '{datainicio_str}' ou '{datafim_str}'")
            # Agenda habilitação dos botões na thread principal
            self.master.after(0, self._enable_download_button)
            self.master.after(0, self._enable_save_button)
            return


        # Passa os dados para o DownloadController iniciar o processo.
        # O controlador irá executar a lógica em sua própria thread.
        self.atualizar_status("GUI: Passando solicitação para o controlador de download...")
        logger.info("GUI: Chamando download_controller.start_download.")
        self.download_controller.start_download(
            url_base,
            login,
            token,
            datainicio_str,
            datafim_str
            # O diretório é obtido pelo controlador via self._get_download_directory()
        )
        # O método iniciar_download retorna, a thread de processamento agora está no controlador.


    # --- Lógica de Salvamento e Carregamento de Configurações ---
    def salvar_configuracoes_button_click(self):
        """
        Coleta dados da GUI e solicita ao security_manager que salve a configuração.
        """
        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        token = self.token_entry.get().strip() # Pega o token diretamente da GUI
        diretorio_destino = self.diretorio_var.get().strip() # Pega o valor da StringVar

        # Obtém apenas a data dos DateEntry para salvar.
        datainicio_date_str_save = self.datainicio_entry.entry.get().strip()
        datafim_date_str_save = self.datafim_entry.entry.get().strip()

        # Validação básica antes de salvar
        if not all([url_base, login, token, diretorio_destino, datainicio_date_str_save, datafim_date_str_save]):
             mensagem_aviso = "Aviso GUI: Preencha URL, Login, Token, Diretório de Destino e as Datas para salvar as configurações."
             self.atualizar_status(mensagem_aviso)
             logger.warning(mensagem_aviso)
             return

        # Prepara o dicionário de configuração para salvar
        config_data_to_save = {
            "url_base": url_base,
            "login": login,
            "token": token, # Este token será obfuscado pelo security_manager antes de escrever no arquivo
            "diretorio_destino": diretorio_destino,
            "datainicio": datainicio_date_str_save,
            "datafim": datafim_date_str_save
        }

        # Chama a função do security_manager para salvar
        logger.info("GUI: Chamando security_manager.save_configuration.")
        if security_manager.save_configuration(config_data_to_save):
             self.atualizar_status("GUI: Configurações salvas com sucesso.")
             logger.info("GUI: Configurações salvas via security_manager.")
        else:
             # Mensagem de erro se o salvamento falhar (erro já logado pelo security_manager)
             mensagem_erro = "Erro GUI: Falha ao salvar configurações. Verifique os logs."
             self.atualizar_status(mensagem_erro)
             logger.error("GUI: Falha ao chamar security_manager.save_configuration.")


    def carregar_configuracoes(self):
        """
        Carrega as configurações usando o security_manager e preenche a GUI.
        """
        logger.info("GUI: Tentando carregar configurações via security_manager.")
        config_data = security_manager.load_configuration()

        if config_data:
            # Se security_manager.load_configuration retornou um dicionário (sucesso)
            try:
                # Usa .get() com valor padrão "" (string vazia) para chaves que podem não existir
                # para evitar KeyErrors e preencher os campos vazios se a chave estiver faltando.
                self.url_entry.insert(0, config_data.get("url_base", ""))
                self.login_entry.insert(0, config_data.get("login", ""))
                # O token já foi deobfuscado pelo security_manager ao carregar, insere diretamente
                self.token_entry.insert(0, config_data.get("token", ""))
                # Define o diretório na StringVar, usando o padrão do config se a chave não existir
                self.diretorio_var.set(config_data.get("diretorio_destino", config.DIRETORIO_BASE_GRAVACOES))

                # Carrega as datas salvas nos campos DateEntry
                saved_datainicio = config_data.get("datainicio", "")
                if saved_datainicio:
                     # Limpa o Entry interno do DateEntry antes de inserir
                     self.datainicio_entry.entry.delete(0, tk.END)
                     self.datainicio_entry.entry.insert(0, saved_datainicio)

                saved_datafim = config_data.get("datafim", "")
                if saved_datafim:
                     # Limpa o Entry interno do DateEntry antes de inserir
                     self.datafim_entry.entry.delete(0, tk.END)
                     self.datafim_entry.entry.insert(0, saved_datafim)

                logger.info("GUI: Configurações carregadas pelo security_manager e GUI preenchida.")

            except Exception as e:
                 # Captura erros durante o preenchimento da GUI após carregar as configurações
                 mensagem_erro = f"Erro GUI: Erro ao preencher a GUI com configurações carregadas: {e}. Configurações podem estar corrompidas ou incompletas."
                 self.atualizar_status(mensagem_erro)
                 logger.error(mensagem_erro, exc_info=True)
                 # Limpa os campos para evitar carregar dados parciais ou incorretos
                 self._clear_gui_fields()
                 # Define as datas iniciais padrão nos DateEntry após limpar
                 self._set_default_dates_in_dateentry()


        else:
            # Se security_manager.load_configuration retornou None (arquivo não encontrado ou erro de carregamento no manager)
            # A mensagem de erro (se houver) já foi logada pelo security_manager.
            # Garantimos que os campos da GUI estejam vazios (exceto pelo diretório padrão e datas padrão nos DateEntry).
            logger.info("GUI: Carregamento de configurações via security_manager retornou None. GUI inicializada com padrões/vazio.")
            self._clear_gui_fields() # Limpa todos os campos
            # Garante que os campos DateEntry mostrem a data atual
            self._set_default_dates_in_dateentry()


    def _clear_gui_fields(self):
        """Limpa todos os campos de entrada na GUI."""
        self.url_entry.delete(0, tk.END)
        self.login_entry.delete(0, tk.END)
        self.token_entry.delete(0, tk.END)
        self.diretorio_var.set(config.DIRETORIO_BASE_GRAVACOES)
        self.datainicio_entry.entry.delete(0, tk.END)
        self.datafim_entry.entry.delete(0, tk.END)
        logger.debug("GUI: Campos da GUI limpos.")


    def _set_default_dates_in_dateentry(self):
         """Define as datas padrão (data atual) nos widgets DateEntry."""
         try:
             today_date_str = datetime.now().strftime("%Y-%m-%d")
             self.datainicio_entry.entry.delete(0, tk.END)
             self.datainicio_entry.entry.insert(0, today_date_str)
             self.datafim_entry.entry.delete(0, tk.END)
             self.datafim_entry.entry.insert(0, today_date_str)
             logger.debug(f"GUI: Datas padrão ({today_date_str}) definidas nos campos DateEntry.")
         except Exception as e:
              logger.error(f"GUI: Erro ao definir datas padrão nos campos DateEntry: {e}")


    # --- Métodos de Processamento em Thread (REMOVIDOS - Agora no DownloadController) ---
    # As funções processar_download e _processar_sem_gravacao foram movidas para download_controller.py.
    # def processar_download(self, ...): pass
    # def _processar_sem_gravacao(self, ...): pass