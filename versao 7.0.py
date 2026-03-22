import tkinter as tk
from tkinter import ttk, messagebox
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
import numpy as np
import os
import sqlite3
from datetime import datetime
from fpdf import FPDF  

class ValiseP24App:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE CALIBRAÇÃO P2.4")
        self.root.geometry("1100x950") 
        self.root.configure(bg="#f4f6f9")
        
        self.GRAFICO_BASE = "graficop2.4(1).png" 
        self.DB_NAME = "historico_calibracao.db"
        
        # Cria pastas necessárias
        for folder in ["graficos_salvos", "relatorios_pdf"]:
            if not os.path.exists(folder): os.makedirs(folder)

        self.init_db()
        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[15, 5])
        style.configure("TLabelframe", font=("Segoe UI", 11, "bold"), background="#f4f6f9")
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground="#2c3e50", background="#f4f6f9")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f4f6f9", foreground="#34495e")
        style.configure("TFrame", background="#f4f6f9")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), foreground="white", background="#0078D7")
        style.map("Accent.TButton", background=[('active', '#005A9E')])
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background="#e74c3c")
        style.map("Danger.TButton", background=[('active', '#c0392b')])

    def init_db(self):
        conn = sqlite3.connect(self.DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anv TEXT, data_cal TEXT, pn_valise TEXT, realizador TEXT,
                p1_bar REAL, p2_bar REAL, 
                ng1 REAL, p3_bar REAL, p4_bar REAL,
                ng2 REAL, p5_bar REAL, p6_bar REAL,
                delta_p REAL, status TEXT, timestamp DATETIME
            )
        ''')
        try:
            cursor.execute("ALTER TABLE registros ADD COLUMN qfe_local REAL")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute("SELECT COUNT(*) FROM registros")
        if cursor.fetchone()[0] == 0:
            exemplos = [
                ("ANV 8520", "01/10/2025", "PN-1001", "Inspetor Silva", 0.0, 0.0, 85.0, 0.88, 0.0, 95.0, 1.02, 0.01, 0.01, "APROVADO", 1013.25, "2025-10-01 10:00:00"),
                ("ANV 8520", "01/11/2025", "PN-1001", "Inspetor Silva", 0.0, 0.0, 85.0, 0.86, 0.0, 95.0, 0.99, 0.01, 0.01, "APROVADO", 1012.00, "2025-11-01 10:00:00"),
                ("ANV 8520", "01/12/2025", "PN-1001", "Inspetor Silva", 0.0, 0.0, 85.2, 0.84, 0.0, 95.1, 0.96, 0.01, 0.01, "APROVADO", 1015.50, "2025-12-01 10:00:00"),
                ("ANV 8520", "01/01/2026", "PN-1001", "Inspetor Silva", 0.0, 0.0, 84.8, 0.81, 0.0, 94.8, 0.93, 0.01, 0.01, "APROVADO", 1010.00, "2026-01-01 10:00:00"),
                ("ANV 8520", "01/02/2026", "PN-1001", "Inspetor Silva", 0.0, 0.0, 85.0, 0.78, 0.0, 95.0, 0.89, 0.01, 0.01, "REPROV. (PERFORMANCE < QFE)", 1013.25, "2026-02-01 10:00:00"),
                ("ANV 8520", "15/02/2026", "PN-1001", "Inspetor Silva", 0.0, 0.0, 85.0, 0.90, 0.0, 95.0, 1.05, 0.01, 0.01, "APROVADO", 1014.00, "2026-02-15 10:00:00"),
                ("PR-ABC", "10/01/2026", "PN-2005", "Sgt Costa", 0.0, 0.0, 86.0, 0.92, 0.0, 96.0, 1.08, 0.02, 0.02, "APROVADO", 1018.00, "2026-01-10 14:00:00"),
                ("PR-ABC", "10/02/2026", "PN-2005", "Sgt Costa", 0.0, 0.0, 85.8, 0.91, 0.0, 95.8, 1.06, 0.01, 0.01, "APROVADO", 1016.00, "2026-02-10 14:00:00")
            ]
            cursor.executemany('''INSERT INTO registros 
                              (anv, data_cal, pn_valise, realizador, p1_bar, p2_bar, ng1, p3_bar, p4_bar, ng2, p5_bar, p6_bar, delta_p, status, qfe_local, timestamp)
                              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', exemplos)
        conn.commit(); conn.close()

    def setup_ui(self):
        header = tk.Label(self.root, text="SISTEMA DE CALIBRAÇÃO E ANÁLISE P2.4", 
                          font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white", pady=15)
        header.pack(fill='x')

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.tab1, self.tab2, self.tab3, self.tab4, self.tab5 = ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb)
        
        self.nb.add(self.tab1, text=" 📝 FORMULÁRIO DE ENTRADA ")
        self.nb.add(self.tab2, text=" 📊 RESULTADOS DA CALIBRAÇÃO ")
        self.nb.add(self.tab3, text=" 🗄️ HISTÓRICO DE DADOS ")
        self.nb.add(self.tab4, text=" 🎯 ANÁLISE DE DISPERSÃO ")
        self.nb.add(self.tab5, text=" 📉 ANÁLISE DE TENDÊNCIA ")
        
        # Criação dos widgets (A ordem agora garante que cb_anv_tend exista antes de atualizar)
        self.create_widgets()
        self.create_history_widgets()
        self.create_dispersion_widgets()
        self.create_trend_widgets()
        
        # Agora sim, atualizamos as listas com os dados do banco
        self.atualizar_combobox_anvs()

    def create_widgets(self):
        form_container = ttk.Frame(self.tab1)
        form_container.pack(fill='both', expand=True, padx=10, pady=10)
        col_esq, col_dir = ttk.Frame(form_container), ttk.Frame(form_container)
        col_esq.pack(side='left', fill='both', expand=True, padx=5)
        col_dir.pack(side='right', fill='both', expand=True, padx=5)

        f_id = ttk.LabelFrame(col_esq, text=" ✈️ IDENTIFICAÇÃO DA AERONAVE ", padding=15)
        f_id.pack(fill='x', pady=10)
        self.ent_tail = self.create_input(f_id, "Matrícula (Ex: PR-ABC):", 0)
        self.ent_date = self.create_input(f_id, "Data:", 1)
        self.ent_pn   = self.create_input(f_id, "P/N Valise:", 2)
        self.ent_nome = self.create_input(f_id, "Realizador:", 3)
        self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y"))

        f_pre = ttk.LabelFrame(col_esq, text=" 1️⃣ PREPARAÇÃO (mA / hPa) ", padding=15)
        f_pre.pack(fill='x', pady=10)
        self.ent_qfe = self.create_input(f_pre, "QFE Local (hPa):", 0); self.ent_qfe.insert(0, "1013.25")
        self.ent_p1_ma = self.create_input(f_pre, "P1 (Parado):", 1)
        self.ent_p2_ma = self.create_input(f_pre, "P2 (Girando):", 2)

        f_c1 = ttk.LabelFrame(col_dir, text=" 2️⃣ CONFIGURAÇÃO 1 ", padding=15)
        f_c1.pack(fill='x', pady=10)
        self.ent_t1_c1 = self.create_input(f_c1, "T1 (°C):", 0)
        self.ent_n1_c1 = self.create_input(f_c1, "N1 (%):", 1)
        self.ent_p3_ma = self.create_input(f_c1, "P3 Opening (mA):", 2)
        self.ent_p4_ma = self.create_input(f_c1, "P4 Closing (mA):", 3)

        f_c2 = ttk.LabelFrame(col_dir, text=" 3️⃣ CONFIGURAÇÃO 2 ", padding=15)
        f_c2.pack(fill='x', pady=10)
        self.ent_t1_c2 = self.create_input(f_c2, "T1 (°C):", 0)
        self.ent_n1_c2 = self.create_input(f_c2, "N1 (%):", 1)
        self.ent_p5_ma = self.create_input(f_c2, "P5 Opening (mA):", 2)
        self.ent_p6_ma = self.create_input(f_c2, "P6 Closing (mA):", 3)

        btn_frame = ttk.Frame(self.tab1); btn_frame.pack(fill='x', pady=15)
        ttk.Button(btn_frame, text="⚙️ CALCULAR E SALVAR", command=lambda: self.processar() and self.nb.select(self.tab2), style="Accent.TButton").pack(pady=10, ipadx=20, ipady=10)

        res_container = ttk.Frame(self.tab2, padding=30); res_container.pack(fill='both', expand=True)
        self.res_label = tk.Label(res_container, text="Aguardando dados...", font=("Courier", 16, "bold"), bg="#1e1e1e", fg="white", pady=40, padx=40, relief="ridge", bd=4)
        self.res_label.pack(fill='both', expand=True)

    def create_history_widgets(self):
        f_search = ttk.Frame(self.tab3, padding=15); f_search.pack(fill='x')
        ttk.Label(f_search, text="🔍 Buscar Matrícula:", font=("Segoe UI", 10, "bold")).pack(side='left', padx=5)
        self.ent_busca = ttk.Entry(f_search, width=20); self.ent_busca.pack(side='left', padx=10)
        ttk.Button(f_search, text="Filtrar", command=self.carregar_dados).pack(side='left')
        
        tree_frame = ttk.Frame(self.tab3); tree_frame.pack(fill='both', expand=True, padx=15, pady=5)
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical"); scroll_y.pack(side='right', fill='y')
        self.tree = ttk.Treeview(tree_frame, columns=('ID', 'ANV', 'DATA', 'REALIZADOR', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'DP', 'QFE', 'STATUS'), show='headings', yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)
        for col in ('ID', 'ANV', 'DATA', 'REALIZADOR', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'DP', 'QFE', 'STATUS'):
            self.tree.heading(col, text=col); self.tree.column(col, width=70, anchor="center")
        self.tree.pack(side='left', fill='both', expand=True)
        ttk.Button(self.tab3, text="🗑️ EXCLUIR REGISTRO", command=self.deletar_registro, style="Danger.TButton").pack(pady=15)
        self.carregar_dados()

    def create_dispersion_widgets(self):
        f_filtros = ttk.LabelFrame(self.tab4, text=" 🎯 Filtros de Dispersão ", padding=15)
        f_filtros.pack(fill='x', padx=15, pady=10)
        ttk.Label(f_filtros, text="Matrícula:").pack(side='left', padx=5)
        self.cb_anv_disp = ttk.Combobox(f_filtros, width=15, state="readonly"); self.cb_anv_disp.pack(side='left', padx=10)
        
        self.ent_data_ini = ttk.Entry(f_filtros, width=12); self.ent_data_ini.pack(side='left', padx=5); self.ent_data_ini.insert(0, "01/01/2025")
        self.ent_data_fim = ttk.Entry(f_filtros, width=12); self.ent_data_fim.pack(side='left', padx=5); self.ent_data_fim.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ttk.Button(f_filtros, text="📊 GERAR DISPERSÃO", command=self.gerar_grafico_dispersao, style="Accent.TButton").pack(side='left', padx=20)
        self.canvas_disp_frame = ttk.Frame(self.tab4); self.canvas_disp_frame.pack(fill='both', expand=True, padx=15, pady=10)

    def create_trend_widgets(self):
        f_filtros = ttk.LabelFrame(self.tab5, text=" 📉 Filtros de Tendência ", padding=15)
        f_filtros.pack(fill='x', padx=15, pady=10)
        ttk.Label(f_filtros, text="Aeronave:").pack(side='left', padx=5)
        self.cb_anv_tend = ttk.Combobox(f_filtros, width=15, state="readonly"); self.cb_anv_tend.pack(side='left', padx=10)
        self.cb_param_tend = ttk.Combobox(f_filtros, values=["P3", "P5", "Delta P"], width=10, state="readonly"); self.cb_param_tend.pack(side='left', padx=10); self.cb_param_tend.current(0)
        ttk.Button(f_filtros, text="📉 GERAR TENDÊNCIA", command=self.gerar_grafico_tendencia, style="Accent.TButton").pack(side='left', padx=20)
        self.canvas_tend_frame = ttk.Frame(self.tab5); self.canvas_tend_frame.pack(fill='both', expand=True, padx=15, pady=10)

    def atualizar_combobox_anvs(self):
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT anv FROM registros ORDER BY anv")
        anvs = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        self.cb_anv_disp['values'] = ["TODAS"] + anvs
        if self.cb_anv_disp['values']: self.cb_anv_disp.current(0)
        self.cb_anv_tend['values'] = anvs
        if self.cb_anv_tend['values']: self.cb_anv_tend.current(0)

    def create_input(self, master, text, row):
        ttk.Label(master, text=text).grid(row=row, column=0, sticky="e", pady=8, padx=10)
        ent = ttk.Entry(master, width=28); ent.grid(row=row, column=1, sticky="w", padx=10, pady=8)
        return ent

    def converter_ma_para_bar(self, ma_val):
        try: return (float(ma_val.replace(',', '.')) - 3.9785) / 3.9951
        except: return 0.0

    def calcular_limite_qfe(self, qfe, ng):
        return (qfe * 0.0004) + (0.005 * ng) - 0.045

    def processar(self):
        try:
            anv = self.ent_tail.get().upper()
            if not anv: raise ValueError("Matrícula ausente.")
            qfe_val = float(self.ent_qfe.get().replace(',', '.'))
            p1, p2, p3, p4, p5, p6 = [self.converter_ma_para_bar(x.get()) for x in [self.ent_p1_ma, self.ent_p2_ma, self.ent_p3_ma, self.ent_p4_ma, self.ent_p5_ma, self.ent_p6_ma]]
            
            def get_ng(t_ent, n_ent):
                t, n = float(t_ent.get().replace(',', '.')), float(n_ent.get().replace(',', '.'))
                return n * (1 / math.sqrt((t + 273.15) / 288.15))

            ng1, ng2 = get_ng(self.ent_t1_c1, self.ent_n1_c1), get_ng(self.ent_t1_c2, self.ent_n1_c2)
            diff = p6 - p1
            limite_p3, limite_p5 = self.calcular_limite_qfe(qfe_val, ng1), self.calcular_limite_qfe(qfe_val, ng2)
            
            status = "APROVADO" if (diff <= 0.03 and p3 >= limite_p3 and p5 >= limite_p5) else "REPROVADO"
            
            conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
            cursor.execute("INSERT INTO registros (anv, data_cal, pn_valise, realizador, p1_bar, p2_bar, ng1, p3_bar, p4_bar, ng2, p5_bar, p6_bar, delta_p, status, qfe_local, timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (anv, self.ent_date.get(), self.ent_pn.get(), self.ent_nome.get(), p1, p2, ng1, p3, p4, ng2, p5, p6, diff, status, qfe_val, datetime.now()))
            conn.commit(); conn.close()

            fig = self.gerar_figura(ng1, p3, ng2, p5, anv, qfe_val)
            caminho_img = f"graficos_salvos/Grafico_{anv}_{datetime.now().strftime('%H%M%S')}.png"; fig.savefig(caminho_img)
            
            self.res_label.config(text=f"STATUS: {status}\nΔP: {diff:.4f} bar", fg="#2ecc71" if status=="APROVADO" else "#e74c3c")
            self.carregar_dados(); self.atualizar_combobox_anvs()
            return True
        except Exception as e: messagebox.showerror("Erro", str(e)); return False

    def gerar_figura(self, x1, y1, x2, y2, titulo, qfe):
        fig = plt.Figure(figsize=(7, 5), dpi=100); ax = fig.add_subplot(111)
        if os.path.exists(self.GRAFICO_BASE):
            img = mpimg.imread(self.GRAFICO_BASE); ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.8)
        eixo_ng = np.linspace(68, 100, 40); linha_qfe = [(qfe * 0.0004) + (0.005 * x) - 0.045 for x in eixo_ng]
        ax.plot(eixo_ng, linha_qfe, 'r--', label=f'Min. QFE {qfe}')
        ax.plot(x1, y1, 'go', label='P3'); ax.plot(x2, y2, 'bo', label='P5')
        ax.set_title(f"Resultado - {titulo}"); ax.set_xlim(68, 100); ax.set_ylim(0.36, 1.10); ax.legend(); ax.grid(True)
        return fig

    def carregar_dados(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        cursor.execute("SELECT id, anv, data_cal, realizador, p1_bar, p2_bar, p3_bar, p4_bar, p5_bar, p6_bar, delta_p, qfe_local, status FROM registros WHERE anv LIKE ? ORDER BY timestamp DESC", (f"%{self.ent_busca.get()}%",))
        for row in cursor.fetchall(): self.tree.insert('', tk.END, values=row)
        conn.close()

    def gerar_grafico_dispersao(self):
        for widget in self.canvas_disp_frame.winfo_children(): widget.destroy()
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        cursor.execute("SELECT anv, ng1, p3_bar, ng2, p5_bar FROM registros"); dados = cursor.fetchall(); conn.close()
        fig = plt.Figure(figsize=(10, 6), dpi=100); ax = fig.add_subplot(111)
        if os.path.exists(self.GRAFICO_BASE):
            img = mpimg.imread(self.GRAFICO_BASE); ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.4)
        for d in dados:
            if self.cb_anv_disp.get() == "TODAS" or d[0] == self.cb_anv_disp.get():
                ax.scatter(d[1], d[2], color='green', s=30); ax.scatter(d[3], d[4], color='blue', s=30)
        ax.set_title("Gráfico de Dispersão (S/ ISA)"); ax.set_xlim(68, 100); ax.set_ylim(0.36, 1.10); ax.grid(True)
        FigureCanvasTkAgg(fig, master=self.canvas_disp_frame).get_tk_widget().pack(fill='both', expand=True)

    def gerar_grafico_tendencia(self):
        for widget in self.canvas_tend_frame.winfo_children(): widget.destroy()
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        p = "p3_bar" if self.cb_param_tend.get() == "P3" else ("p5_bar" if self.cb_param_tend.get() == "P5" else "delta_p")
        cursor.execute(f"SELECT data_cal, {p} FROM registros WHERE anv = ? ORDER BY timestamp", (self.cb_anv_tend.get(),))
        dados = cursor.fetchall(); conn.close()
        if not dados: return
        fig = plt.Figure(figsize=(10, 6), dpi=100); ax = fig.add_subplot(111)
        ax.plot([d[0] for d in dados], [d[1] for d in dados], marker='o', linestyle='-', color='red')
        ax.set_title(f"Tendência {self.cb_param_tend.get()} - {self.cb_anv_tend.get()}"); plt.setp(ax.get_xticklabels(), rotation=30)
        FigureCanvasTkAgg(fig, master=self.canvas_tend_frame).get_tk_widget().pack(fill='both', expand=True)

    def deletar_registro(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Confirmar", "Excluir?"):
            conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
            cursor.execute("DELETE FROM registros WHERE id = ?", (self.tree.item(sel)['values'][0],))
            conn.commit(); conn.close(); self.carregar_dados(); self.atualizar_combobox_anvs()

if __name__ == "__main__":
    root = tk.Tk(); app = ValiseP24App(root); root.mainloop()

    