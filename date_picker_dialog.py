import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, timedelta

class DatePickerDialog(tk.Toplevel):
    def __init__(self, parent, target_entry, initial_date=None):
        super().__init__(parent)
        self.parent = parent
        self.target_entry = target_entry
        self.initial_date = initial_date if initial_date else datetime.now()
        self.transient(parent) # Mantém a janela do seletor acima da principal
        self.grab_set()      # Bloqueia interação com outras janelas do aplicativo
        self.title("Selecionar Data")
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Lida com o fechamento da janela

        # Atributos para o calendário
        self._year = self.initial_date.year
        self._month = self.initial_date.month

        # Frame principal para o calendário
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(padx=10, pady=10)

        # Frame para navegação (Mês/Ano e botões)
        self.nav_frame = ttk.Frame(self.calendar_frame)
        self.nav_frame.pack(fill="x")

        self.btn_prev_year = ttk.Button(self.nav_frame, text="<<", command=self._prev_year)
        self.btn_prev_year.pack(side="left", padx=2)

        self.btn_prev_month = ttk.Button(self.nav_frame, text="<", command=self._prev_month)
        self.btn_prev_month.pack(side="left", padx=2)

        self.month_year_label = ttk.Label(self.nav_frame, text="", width=20, anchor="center")
        self.month_year_label.pack(side="left", expand=True, fill="x")

        self.btn_next_month = ttk.Button(self.nav_frame, text=">", command=self._next_month)
        self.btn_next_month.pack(side="left", padx=2)

        self.btn_next_year = ttk.Button(self.nav_frame, text=">>", command=self._next_year)
        self.btn_next_year.pack(side="left", padx=2)

        # Frame para os nomes dos dias da semana
        self.days_of_week_frame = ttk.Frame(self.calendar_frame)
        self.days_of_week_frame.pack(fill="x")

        # Nomes dos dias da semana (domingo a sábado)
        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for dia in dias_semana:
            ttk.Label(self.days_of_week_frame, text=dia, width=4, anchor="center").pack(side="left", padx=1)

        # Frame para os dias do mês (será preenchido dinamicamente)
        self.days_frame = ttk.Frame(self.calendar_frame)
        self.days_frame.pack()

        # Inicializa o calendário
        self._update_calendar()

    def _update_calendar(self):
        """Atualiza a exibição do calendário para o mês/ano atual."""
        # Limpa os botões de dias existentes
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self._month]} {self._year}")

        cal = calendar.monthcalendar(self._year, self._month)

        for week in cal:
            week_frame = ttk.Frame(self.days_frame)
            week_frame.pack(fill="x")
            for day in week:
                if day == 0:
                    # Dias de outros meses no início/fim da semana
                    ttk.Label(week_frame, text="", width=4, anchor="center").pack(side="left", padx=1)
                else:
                    day_button = ttk.Button(week_frame, text=str(day), width=3)
                    day_button.config(command=lambda d=day: self._select_date(d)) # Usa lambda para passar o dia
                    day_button.pack(side="left", padx=1)

                    # Destaca o dia selecionado se for o mês/ano e dia corretos
                    if self.initial_date and self.initial_date.year == self._year and \
                       self.initial_date.month == self._month and self.initial_date.day == day:
                       day_button.config(state="disabled", text=f"[{day}]") # Exemplo de destaque

    def _select_date(self, day):
        """Seleciona uma data, atualiza o campo de entrada e fecha a janela."""
        selected_date = datetime(self._year, self._month, day)
        # Mantém a hora atual do campo de entrada se ela existir
        current_time_str = ""
        current_value = self.target_entry.get()
        if " " in current_value:
            time_part = current_value.split(" ")[1]
            try:
                 datetime.strptime(time_part, '%H:%M:%S') # Valida o formato da hora
                 current_time_str = f" {time_part}"
            except ValueError:
                 current_time_str = " 00:00:00" # Usa hora padrão se a hora no campo for inválida
        else:
             current_time_str = " 00:00:00" # Usa hora padrão se não houver hora no campo


        # Formata a data selecionada e a hora (existente ou padrão)
        formatted_date = selected_date.strftime('%Y-%m-%d') + current_time_str

        # Atualiza o campo de entrada na janela principal
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, formatted_date)

        # Fecha a janela do seletor de data
        self._on_close()

    def _prev_month(self):
        """Navega para o mês anterior."""
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._update_calendar()

    def _next_month(self):
        """Navega para o próximo mês."""
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._update_calendar()

    def _prev_year(self):
        """Navega para o ano anterior."""
        self._year -= 1
        self._update_calendar()

    def _next_year(self):
        """Navega para o próximo ano."""
        self._year += 1
        self._update_calendar()

    def _on_close(self):
        """Fecha a janela do seletor de data e libera a interação."""
        self.parent.grab_release() # Libera a interação com a janela principal
        self.destroy() # Destrói a janela