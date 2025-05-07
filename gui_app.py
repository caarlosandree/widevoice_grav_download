# gui_app.py
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.widgets import DateEntry
import tkinter.filedialog as filedialog
from tkinter import scrolledtext
import tkinter.messagebox as messagebox

import threading
from datetime import datetime
import os
import logging

import security_manager
import config
from download_controller import DownloadController


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

        # --- Frame para Opções de Download (Agora com dois checkboxes) ---
        self.frame_opcoes = ttk.LabelFrame(master, text="Opções de Download")
        self.frame_opcoes.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.frame_opcoes.columnconfigure(0, weight=1)

        # Checkbox para Metadados COM gravação
        self.download_metadata_with_recording_var = tk.BooleanVar(value=True)
        self.download_metadata_with_recording_checkbox = ttk.Checkbutton(
            self.frame_opcoes,
            text="Baixar Metadados (Com Gravação)",
            variable=self.download_metadata_with_recording_var,
            bootstyle="round-toggle"
        )
        self.download_metadata_with_recording_checkbox.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        # Checkbox para Metadados SEM gravação
        self.download_metadata_without_recording_var = tk.BooleanVar(value=True)
        self.download_metadata_without_recording_checkbox = ttk.Checkbutton(
            self.frame_opcoes,
            text="Baixar Metadados (Sem Gravação)",
            variable=self.download_metadata_without_recording_var,
            bootstyle="round-toggle"
        )
        self.download_metadata_without_recording_checkbox.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        # --- Fim do Frame para Opções de Download ---


        self.frame_botoes_acao = ttk.Frame(master)
        self.frame_botoes_acao.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.frame_botoes_acao.columnconfigure(0, weight=1)
        self.frame_botoes_acao.columnconfigure(1, weight=0)
        self.frame_botoes_acao.columnconfigure(2, weight=0)


        self.progress_text_label = ttk.Label(self.frame_botoes_acao, text="Progresso: 0/0")
        self.progress_text_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")


        self.progress_bar = ttk.Progressbar(self.frame_botoes_acao, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=1)


        self.save_button = ttk.Button(self.frame_botoes_acao, text="Salvar Configurações", command=self.salvar_configuracoes_button_click)
        self.save_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")


        self.download_button = ttk.Button(self.frame_botoes_acao, text="Iniciar Download", command=self.iniciar_download)

        self.cancel_button = ttk.Button(self.frame_botoes_acao, text="Cancelar Download", command=self.cancel_download, state=tk.DISABLED, bootstyle="danger")


        # Área de Status/Log da GUI
        self.status_label = ttk.Label(master, text="Status:")
        self.status_label.grid(row=4, column=0, padx=10, pady=2, sticky="w")
        self.status_text = scrolledtext.ScrolledText(master, wrap=ttk.WORD, width=80, height=15)
        self.status_text.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")

        # --- Configurar Tags para Status ---
        self.status_text.tag_configure('info', foreground='black')
        self.status_text.tag_configure('warning', foreground='orange')
        self.status_text.tag_configure('error', foreground='red')
        self.status_text.tag_configure('cancelled', foreground='blue')
        self.status_text.tag_configure('debug', foreground='gray')


        # Configurações para redimensionamento da janela principal
        master.columnconfigure(0, weight=1)
        master.rowconfigure(5, weight=1)

        # Flag e Evento de Cancelamento
        self._cancel_event = threading.Event()


        # Cria uma instância do DownloadController, passando os callbacks da GUI
        self.download_controller = DownloadController(
            status_callback=self.atualizar_status,
            progress_callback=self.atualizar_progresso,
            completion_callback=self._process_download_completed,
            directory_getter=self._get_download_directory,
            progress_maximum_callback=self.atualizar_progresso_maximo
        )


        # Carregar configurações ao iniciar
        self.carregar_configuracoes()

        # Garantir que o botão "Iniciar Download" esteja visível ao iniciar
        self._hide_cancel_button()


    # --- Métodos Auxiliares para Gerenciar Botões e Estado (seguro para thread - chamados via after) ---

    def _set_button_state(self, button, state):
        """Método interno para configurar o estado de um botão na thread principal."""
        try:
            button.config(state=state)
        except Exception as e:
            logger.error(f"GUI: Erro ao configurar estado do botão {button.cget('text')}: {e}")

    def _process_download_completed(self):
         """Callback chamado pelo DownloadController quando o processo termina (sucesso, falha ou cancelamento)."""
         logger.info("GUI: Callback de conclusão do processo de download recebido.")
         self._cancel_event.clear()
         self.master.after(0, self._enable_start_button)
         self.master.after(0, self._enable_save_button)
         self.master.after(0, self._hide_cancel_button)
         logger.info("GUI: Reabilitação de botões agendada.")


    def _enable_start_button(self):
        """Habilita o botão de download na thread principal."""
        self._set_button_state(self.download_button, tk.NORMAL)

    def _enable_save_button(self):
        """Habilita o botão de salvar na thread principal."""
        self._set_button_state(self.save_button, tk.NORMAL)

    def _disable_start_button(self):
         """Desabilita o botão de download na thread principal."""
         self._set_button_state(self.download_button, tk.DISABLED)

    def _disable_save_button(self):
         """Desabilita o botão de salvar na thread principal."""
         self._set_button_state(self.save_button, tk.DISABLED)

    def _show_cancel_button(self):
         """Mostra o botão de cancelar e esconde o de iniciar na thread principal."""
         self._set_button_state(self.cancel_button, tk.NORMAL)
         self.download_button.grid_forget()
         self.cancel_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

    def _hide_cancel_button(self):
         """Esconde o botão de cancelar e mostra o de iniciar na thread principal."""
         self._set_button_state(self.cancel_button, tk.DISABLED)
         self.cancel_button.grid_forget()
         self.download_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")


    # --- Métodos Auxiliares para Atualizar GUI (seguro para thread - chamados via after) ---

    def atualizar_status(self, mensagem, level=logging.INFO):
        """
        Atualiza a área de texto de status (seguro para chamar de qualquer thread).
        Mapeia o nível de log para uma tag de formatação.
        """
        tag = 'info'
        if level == logging.WARNING:
            tag = 'warning'
        elif level == logging.ERROR:
            tag = 'error'
        elif level == logging.INFO and ("Cancelamento solicitado" in mensagem or "Processo de download cancelado" in mensagem):
             tag = 'cancelled'
        elif level == logging.DEBUG:
             tag = 'debug'


        try:
            self.master.after(0, self._inserir_status, mensagem, tag)
        except Exception as e:
            logger.error(f"GUI: Erro ao agendar atualização de status: {e} - Mensagem: {mensagem}, Nível: {level}",
                         exc_info=True)

    def _inserir_status(self, mensagem, tag=None):
        """
        Metodo interno para inserir texto no widget de status.
        """
        try:
            self.status_text.insert(tk.END, mensagem + "\n", tag)
            self.status_text.see(tk.END)
        except Exception as e:
            logger.error(f"GUI: Erro ao inserir status na GUI: {e} - Mensagem: {mensagem}", exc_info=True)


    def atualizar_progresso(self, valor, total=None):
         """
         Atualiza o valor da barra de progresso e o texto de progresso.
         'valor' é o número de itens processados.
         'total' é o número total de itens (opcional, para texto).
         (seguro para chamar de qualquer thread).
         """
         try:
            self.master.after(0, self._configurar_progresso, valor, total)
         except Exception as e:
             logger.error(f"GUI: Erro ao agendar atualização de progresso: {e} - Valor: {valor}, Total: {total}", exc_info=True)


    def _configurar_progresso(self, valor, total=None):
         """Método interno para configurar a barra e o texto de progresso."""
         try:
             self.progress_bar['value'] = valor

             if total is not None:
                  self.progress_text_label.config(text=f"Progresso: {valor}/{total}")
             else:
                  current_max = self.progress_bar['maximum'] if self.progress_bar['maximum'] > 0 else 0
                  self.progress_text_label.config(text=f"Progresso: {valor}/{int(current_max)}")


         except Exception as e:
             logger.error(f"GUI: Erro ao configurar barra/texto de progresso: {e} - Valor: {valor}, Total: {total}", exc_info=True)


    def atualizar_progresso_maximo(self, maximum):
         """Define o valor máximo para a barra de progresso (seguro para thread)."""
         try:
              self.master.after(0, self._configurar_progresso_maximo, maximum)
         except Exception as e:
              logger.error(f"GUI: Erro ao agendar configuração de progresso máximo: {e} - Máximo: {maximum}", exc_info=True)

    def _configurar_progresso_maximo(self, maximum):
         """Método interno para configurar o valor máximo da barra de progresso."""
         try:
             self.progress_bar['maximum'] = maximum
             current_value = self.progress_bar['value']
             self.progress_text_label.config(text=f"Progresso: {current_value}/{maximum}")
         except Exception as e:
             logger.error(f"GUI: Erro ao configurar máximo da barra de progresso: {e} - Máximo: {maximum}", exc_info=True)


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
        self._disable_start_button()
        self._disable_save_button()
        self._show_cancel_button()
        self.atualizar_status("GUI: Coletando dados e validando para iniciar download...")
        logger.info("GUI: Botão 'Iniciar Download' clicado. Coletando dados.")

        try:
            self.status_text.delete(1.0, tk.END)
            self.atualizar_progresso(0, 0)
            self.progress_bar['maximum'] = 100
        except Exception as e:
             logger.error(f"GUI: Erro ao limpar status ou progresso antes de iniciar download: {e}", exc_info=True)


        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        token = self.token_entry.get().strip()

        datainicio_date_str = self.datainicio_entry.entry.get().strip()
        datafim_date_str = self.datafim_entry.entry.get().strip()

        datainicio_str = f"{datainicio_date_str} 00:00:00" if datainicio_date_str else ""
        datafim_str = f"{datafim_date_str} 23:59:59" if datafim_date_str else ""

        # --- Obter o estado dos checkboxes de metadado ---
        download_metadata_with_recording = self.download_metadata_with_recording_var.get()
        download_metadata_without_recording = self.download_metadata_without_recording_var.get()
        logger.info(f"GUI: Opção 'Baixar Metadados (Com Gravação)' selecionada: {download_metadata_with_recording}")
        logger.info(f"GUI: Opção 'Baixar Metadados (Sem Gravação)' selecionada: {download_metadata_without_recording}")
        # --- Fim da obtenção do estado dos checkboxes ---

        logger.info(f"GUI: Dados coletados para passar ao controlador - URL: {url_base}, Login: {login}, Data Início (com hora): {datainicio_str}, Data Fim (com hora): {datafim_str}")

        if not all([url_base, login, token, datainicio_str, datafim_str]):
            mensagem_erro = "Erro GUI: Preencha URL, Login, Token e as Datas para iniciar o download."
            self.atualizar_status(mensagem_erro, level=logging.ERROR)
            messagebox.showerror("Erro de Validação", mensagem_erro)
            logger.warning(mensagem_erro)
            self.master.after(0, self._enable_start_button)
            self.master.after(0, self._enable_save_button)
            self.master.after(0, self._hide_cancel_button)
            return

        try:
            datetime.strptime(datainicio_str, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(datafim_str, '%Y-%m-%d %H:%M:%S')
            logger.info("GUI: Formato de data/hora validado localmente.")
        except ValueError:
            mensagem_erro = "Erro GUI: Formato de data/hora inválido no campo. Use %Y-%m-%d." # Corrigido a mensagem
            self.atualizar_status(mensagem_erro, level=logging.ERROR)
            messagebox.showerror("Erro de Validação", mensagem_erro)
            logger.error(f"GUI: Falha na validação de formato de data/hora local: '{datainicio_str}' ou '{datafim_str}'", exc_info=True)
            self.master.after(0, self._enable_start_button)
            self.master.after(0, self._enable_save_button)
            self.master.after(0, self._hide_cancel_button)
            return

        self._cancel_event.clear()

        self.atualizar_status("GUI: Passando solicitação para o controlador de download...")
        logger.info("GUI: Chamando download_controller.start_download.")
        self.download_controller.start_download(
            url_base,
            login,
            token,
            datainicio_str,
            datafim_str,
            cancel_event=self._cancel_event,
            download_metadata_with_recording=download_metadata_with_recording, # --- Passa a opção 1 ---
            download_metadata_without_recording=download_metadata_without_recording # --- Passa a opção 2 ---
        )


    def cancel_download(self):
        """Método chamado quando o botão Cancelar é clicado."""
        logger.info("GUI: Botão 'Cancelar Download' clicado. Sinalizando cancelamento.")
        self.atualizar_status("GUI: Cancelamento solicitado. Aguardando tarefas em execução finalizarem...", level=logging.WARNING)
        self._set_button_state(self.cancel_button, tk.DISABLED)
        self._cancel_event.set()


    # --- Lógica de Salvamento e Carregamento de Configurações ---
    def salvar_configuracoes_button_click(self):
        """
        Coleta dados da GUI e solicita ao security_manager que salve a configuração.
        """
        url_base = self.url_entry.get().strip()
        login = self.login_entry.get().strip()
        token = self.token_entry.get().strip()
        diretorio_destino = self.diretorio_var.get().strip()
        datainicio_date_str_save = self.datainicio_entry.entry.get().strip()
        datafim_date_str_save = self.datafim_entry.entry.get().strip()

        # --- Obter o estado dos checkboxes de metadado para salvar ---
        download_metadata_with_recording_save = self.download_metadata_with_recording_var.get()
        download_metadata_without_recording_save = self.download_metadata_without_recording_var.get()
        # --- Fim da obtenção do estado ---


        if not all([url_base, login, token, diretorio_destino, datainicio_date_str_save, datafim_date_str_save]):
             mensagem_aviso = "Aviso GUI: Preencha URL, Login, Token, Diretório de Destino e as Datas para salvar as configurações."
             self.atualizar_status(mensagem_aviso, level=logging.WARNING)
             messagebox.showwarning("Aviso", mensagem_aviso)
             logger.warning(mensagem_aviso)
             return

        config_data_to_save = {
            "url_base": url_base,
            "login": login,
            "token": token,
            "diretorio_destino": diretorio_destino,
            "datainicio": datainicio_date_str_save,
            "datafim": datafim_date_str_save,
            "download_metadata_with_recording": download_metadata_with_recording_save, # --- Salvar opção 1 ---
            "download_metadata_without_recording": download_metadata_without_recording_save # --- Salvar opção 2 ---
        }

        logger.info("GUI: Chamando security_manager.save_configuration.")
        if security_manager.save_configuration(config_data_to_save):
             self.atualizar_status("GUI: Configurações salvas com sucesso.")
             logger.info("GUI: Configurações salvas via security_manager.")
             messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        else:
             mensagem_erro = "Erro GUI: Falha ao salvar configurações. Verifique os logs."
             self.atualizar_status(mensagem_erro, level=logging.ERROR)
             messagebox.showerror("Erro ao Salvar", mensagem_erro)
             logger.error("GUI: Falha ao chamar security_manager.save_configuration.")


    def carregar_configuracoes(self):
        """
        Carrega as configurações usando o security_manager e preenche a GUI.
        """
        logger.info("GUI: Tentando carregar configurações via security_manager.")
        config_data = security_manager.load_configuration()

        if config_data:
            try:
                self.url_entry.insert(0, config_data.get("url_base", ""))
                self.login_entry.insert(0, config_data.get("login", ""))
                self.token_entry.insert(0, config_data.get("token", ""))
                self.diretorio_var.set(config_data.get("diretorio_destino", config.DIRETORIO_BASE_GRAVACOES))

                saved_datainicio = config_data.get("datainicio", "")
                if saved_datainicio:
                     self.datainicio_entry.entry.delete(0, tk.END)
                     self.datainicio_entry.entry.insert(0, saved_datainicio)
                else:
                     self._set_default_dates_in_dateentry()

                saved_datafim = config_data.get("datafim", "")
                if saved_datafim:
                     self.datafim_entry.entry.delete(0, tk.END)
                     self.datafim_entry.entry.insert(0, saved_datafim)
                else:
                     self._set_default_dates_in_dateentry()

                # --- Carregar o estado dos checkboxes de metadado ---
                # Usa .get(key, default_value) para compatibilidade com arquivos antigos
                loaded_metadata_with_recording = config_data.get("download_metadata_with_recording", True) # Default é True
                loaded_metadata_without_recording = config_data.get("download_metadata_without_recording", True) # Default é True
                self.download_metadata_with_recording_var.set(loaded_metadata_with_recording)
                self.download_metadata_without_recording_var.set(loaded_metadata_without_recording)
                # --- Fim do carregamento do estado dos checkboxes ---


                logger.info("GUI: Configurações carregadas pelo security_manager e GUI preenchida.")

            except Exception as e:
                 mensagem_erro = f"Erro GUI: Erro ao preencher a GUI com configurações carregadas: {e}. Configurações podem estar corrompidas ou incompletas."
                 self.atualizar_status(mensagem_erro, level=logging.ERROR)
                 messagebox.showerror("Erro ao Carregar Configurações", mensagem_erro)
                 logger.error(mensagem_erro, exc_info=True)
                 self._clear_gui_fields()
                 self._set_default_dates_in_dateentry()
                 # Define o valor padrão para os checkboxes em caso de erro no carregamento
                 self.download_metadata_with_recording_var.set(True)
                 self.download_metadata_without_recording_var.set(True)


        else:
            logger.info("GUI: Carregamento de configurações via security_manager retornou None. GUI inicializada com padrões/vazio.")
            self._clear_gui_fields()
            self._set_default_dates_in_dateentry()
            # Define o valor padrão para os checkboxes se não houver configuração
            self.download_metadata_with_recording_var.set(True)
            self.download_metadata_without_recording_var.set(True)


    def _clear_gui_fields(self):
        """Limpa campos de entrada específicos na GUI."""
        self.url_entry.delete(0, tk.END)
        self.login_entry.delete(0, tk.END)
        self.token_entry.delete(0, tk.END)
        self.datainicio_entry.entry.delete(0, tk.END)
        self.datafim_entry.entry.delete(0, tk.END)
        logger.debug("GUI: Campos de URL, Login, Token e Datas limpos.")


    def _set_default_dates_in_dateentry(self):
         """Define as datas padrão (data atual) nos widgets DateEntry se estiverem vazios."""
         try:
             today_date_str = datetime.now().strftime("%Y-%m-%d")
             if not self.datainicio_entry.entry.get().strip():
                 self.datainicio_entry.entry.delete(0, tk.END)
                 self.datainicio_entry.entry.insert(0, today_date_str)
             if not self.datafim_entry.entry.get().strip():
                 self.datafim_entry.entry.delete(0, tk.END)
                 self.datafim_entry.entry.insert(0, today_date_str)
             logger.debug(f"GUI: Datas padrão ({today_date_str}) definidas nos campos DateEntry, se vazios.")
         except Exception as e:
              logger.error(f"GUI: Erro ao definir datas padrão nos campos DateEntry: {e}", exc_info=True)