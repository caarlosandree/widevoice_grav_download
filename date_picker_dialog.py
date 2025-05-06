# import tkinter as tk # Remova esta linha
# from tkinter import ttk # Remova esta linha

import ttkbootstrap as ttk # Importe ttkbootstrap
# from ttkbootstrap.dialogs import DatePickerDialog # Importe DatePickerDialog do ttkbootstrap (se quiser usar a versão pronta)
# Ou, se quiser manter sua implementação, mude apenas as importações:
from tkinter import Toplevel # Para usar a janela Toplevel padrão com widgets ttkbootstrap dentro

import calendar
from datetime import datetime, timedelta

# Opção 1: Usar o DatePickerDialog pronto do ttkbootstrap (mais simples e recomendado)
# class DatePickerDialog(ttk.DatePickerDialog):
#     def __init__(self, parent, target_entry, initial_date=None):
#         super().__init__(parent, initialdate=initial_date)
#         self.target_entry = target_entry
#         self.parent = parent
#         self.transient(parent)
#         self.grab_set()
#
#         # O DatePickerDialog do ttkbootstrap tem um método para retornar a data selecionada
#         # Precisamos adaptar para atualizar o self.target_entry
#         self.date_selected = None
#         self.protocol("WM_DELETE_WINDOW", self._on_close)
#
#     def _on_close(self):
#         # Obtém a data selecionada (se houver) e atualiza o campo
#         selected_date = self.get_date()
#         if selected_date:
#             # Mantém a hora atual do campo de entrada se ela existir
#             current_time_str = ""
#             current_value = self.target_entry.get()
#             if " " in current_value:
#                 time_part = current_value.split(" ")[1]
#                 try:
#                      datetime.strptime(time_part, '%H:%M:%S') # Valida o formato da hora
#                      current_time_str = f" {time_part}"
#                 except ValueError:
#                      current_time_str = " 00:00:00" # Usa hora padrão se a hora no campo for inválvida
#             else:
#                  current_time_str = " 00:00:00" # Usa hora padrão se não houver hora no campo
#
#             formatted_date = selected_date.strftime('%Y-%m-%d') + current_time_str
#             self.target_entry.delete(0, tk.END) # Use tk.END ou ttk.END
#             self.target_entry.insert(0, formatted_date)
#
#         self.parent.grab_release()
#         self.destroy()


# Opção 2: Adaptar sua implementação existente para usar ttkbootstrap (requer mais mudanças internas)
# Mantenha a estrutura da sua classe, mas use widgets ttkbootstrap e Toplevel padrão para evitar conflitos
class DatePickerDialog(Toplevel): # Use Toplevel padrão
    def __init__(self, parent, target_entry, initial_date=None):
        super().__init__(parent)
        self.parent = parent
        self.target_entry = target_entry
        self.initial_date = initial_date if initial_date else datetime.now()
        self.transient(parent)
        self.grab_set()
        self.title("Selecionar Data")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Atributos para o calendário
        self._year = self.initial_date.year
        self._month = self.initial_date.month

        # Frame principal para o calendário
        self.calendar_frame = ttk.Frame(self) # Use ttk.Frame
        self.calendar_frame.pack(padx=10, pady=10)

        # Frame para navegação (Mês/Ano e botões)
        self.nav_frame = ttk.Frame(self.calendar_frame) # Use ttk.Frame
        self.nav_frame.pack(fill="x")

        self.btn_prev_year = ttk.Button(self.nav_frame, text="<<", command=self._prev_year) # Use ttk.Button
        self.btn_prev_year.pack(side="left", padx=2)

        self.btn_prev_month = ttk.Button(self.nav_frame, text="<", command=self._prev_month) # Use ttk.Button
        self.btn_prev_month.pack(side="left", padx=2)

        self.month_year_label = ttk.Label(self.nav_frame, text="", width=20, anchor="center") # Use ttk.Label
        self.month_year_label.pack(side="left", expand=True, fill="x")

        self.btn_next_month = ttk.Button(self.nav_frame, text=">", command=self._next_month) # Use ttk.Button
        self.btn_next_month.pack(side="left", padx=2)

        self.btn_next_year = ttk.Button(self.nav_frame, text=">>", command=self._next_year) # Use ttk.Button
        self.btn_next_year.pack(side="left", padx=2)

        # Frame para os nomes dos dias da semana
        self.days_of_week_frame = ttk.Frame(self.calendar_frame) # Use ttk.Frame
        self.days_of_week_frame.pack(fill="x")

        # Nomes dos dias da semana (domingo a sábado)
        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for dia in dias_semana:
            ttk.Label(self.days_of_week_frame, text=dia, width=4, anchor="center").pack(side="left", padx=1) # Use ttk.Label

        # Frame para os dias do mês (será preenchido dinamicamente)
        self.days_frame = ttk.Frame(self.calendar_frame) # Use ttk.Frame
        self.days_frame.pack()

        # Inicializa o calendário
        self._update_calendar()

    def _update_calendar(self):
        """Atualiza a exibição do calendário para o mês/ano atual."""
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self._month]} {self._year}")

        cal = calendar.monthcalendar(self._year, self._month)

        for week in cal:
            week_frame = ttk.Frame(self.days_frame) # Use ttk.Frame
            week_frame.pack(fill="x")
            for day in week:
                if day == 0:
                    ttk.Label(week_frame, text="", width=4, anchor="center").pack(side="left", padx=1) # Use ttk.Label
                else:
                    day_button = ttk.Button(week_frame, text=str(day), width=3) # Use ttk.Button
                    day_button.config(command=lambda d=day: self._select_date(d))
                    day_button.pack(side="left", padx=1)

                    # Destaque para o dia selecionado
                    if self.initial_date and self.initial_date.year == self._year and \
                       self.initial_date.month == self._month and self.initial_date.day == day:
                       # Use style para destacar (opcional, pode requerer configuração de estilo)
                       # Uma alternativa simples é mudar o texto ou estado como você já fez
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
                 datetime.strptime(time_part, '%H:%M:%S')
                 current_time_str = f" {time_part}"
            except ValueError:
                 current_time_str = " 00:00:00"
        else:
             current_time_str = " 00:00:00"

        formatted_date = selected_date.strftime('%Y-%m-%d') + current_time_str

        self.target_entry.delete(0, ttk.END) # Use ttk.END
        self.target_entry.insert(0, formatted_date)

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
        self.parent.grab_release()
        self.destroy()