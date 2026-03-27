import tkinter as tk
from tkinter import ttk, messagebox
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
import numpy as np
import sqlite3
from datetime import datetime
from fpdf import FPDF  
import os 

class ValiseP24App:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE TESTE E ANALISE P2.4 - HELIBRAS/AIRBUS (FULL VERSION)")
        self.root.geometry("1200x950") 
        self.root.configure(bg="#f4f6f9")
        
        # Arquivos e Pastas
        self.GRAFICO_BASE = "graficop2.4(1).png" 
        self.DB_NAME = "historico_calibracao.db"
        
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
                delta_p REAL, status TEXT, qfe_local REAL, timestamp DATETIME
            )
        ''')
    def setup_ui(self):
        header = tk.Label(self.root, text="SISTEMA DE TESTE E ANÁLISE P2.4", font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white", pady=15)
        header.pack(fill='x')

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.tab1, self.tab2, self.tab3, self.tab4, self.tab5 = ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb), ttk.Frame(self.nb)
        
        self.nb.add(self.tab1, text=" 📝 FORMULÁRIO ")
        self.nb.add(self.tab2, text=" 📊 RESULTADO ")
        self.nb.add(self.tab3, text=" 🗄️ HISTÓRICO ")
        self.nb.add(self.tab4, text=" 🎯 DISPERSÃO ")
        self.nb.add(self.tab5, text=" 📉 TENDÊNCIA ")
        
        # Criação dos widgets 
        self.create_widgets()
        self.create_history_widgets()
        self.create_dispersion_widgets()
        self.create_trend_widgets()
        
        # Atualiza dados após tudo criado
        self.atualizar_combobox_anvs()

    # --- FUNÇÃO 1: INTERPOLAÇÃO LINEAR ---
    def calcular_limite_manual(self, qfe, ng_atual):
        tabela_pontos = [(70.0, 0.420), (80.0, 0.485), (85.0, 0.530), (90.0, 0.590), (95.0, 0.660), (100.0, 0.750)]
        ngs, pressoes = zip(*tabela_pontos)
        pressao_base = np.interp(ng_atual, ngs, pressoes)
        ajuste_qfe = (qfe - 1013.25) * 0.0004
        return pressao_base + ajuste_qfe

    def create_widgets(self):
        f_main = ttk.Frame(self.tab1); f_main.pack(fill='both', expand=True, padx=10, pady=10)
        c_esq, c_dir = ttk.Frame(f_main), ttk.Frame(f_main)
        c_esq.pack(side='left', fill='both', expand=True); c_dir.pack(side='right', fill='both', expand=True)

        f_id = ttk.LabelFrame(c_esq, text=" IDENTIFICAÇÃO ", padding=15); f_id.pack(fill='x', pady=10)
        self.ent_tail = self.create_input(f_id, "Matrícula:", 0)
        self.ent_date = self.create_input(f_id, "Data:", 1); self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_pn = self.create_input(f_id, "P/N Valise:", 2); self.ent_nome = self.create_input(f_id, "Realizador:", 3)

        f_pre = ttk.LabelFrame(c_esq, text=" 1️⃣ PREPARAÇÃO (mA / hPa) ", padding=15); f_pre.pack(fill='x', pady=10)
        self.ent_qfe = self.create_input(f_pre, "QFE Local:", 0); self.ent_qfe.insert(0, "1013.25")
        self.ent_p1_ma = self.create_input(f_pre, "P1 (Parado):", 1); self.ent_p2_ma = self.create_input(f_pre, "P2 (Girando):", 2)

        f_c1 = ttk.LabelFrame(c_dir, text=" 2️⃣ CONFIGURAÇÃO 1 ", padding=15); f_c1.pack(fill='x', pady=10)
        self.ent_t1_c1, self.ent_n1_c1 = self.create_input(f_c1, "T1 (°C):", 0), self.create_input(f_c1, "N1 (%):", 1)
        self.ent_p3_ma, self.ent_p4_ma = self.create_input(f_c1, "P3 (mA):", 2), self.create_input(f_c1, "P4 (mA):", 3)

        f_c2 = ttk.LabelFrame(c_dir, text=" 3️⃣ CONFIGURAÇÃO 2 ", padding=15); f_c2.pack(fill='x', pady=10)
        self.ent_t1_c2, self.ent_n1_c2 = self.create_input(f_c2, "T1 (°C):", 0), self.create_input(f_c2, "N1 (%):", 1)
        self.ent_p5_ma, self.ent_p6_ma = self.create_input(f_c2, "P5 (mA):", 2), self.create_input(f_c2, "P6 (mA):", 3)

        ttk.Button(self.tab1, text="⚙️ CALCULAR, SALVAR E PDF", command=self.processar, style="Accent.TButton").pack(pady=15, ipadx=20, ipady=10)
        self.res_label = tk.Label(self.tab2, text="Aguardando dados...", font=("Courier", 16, "bold"), bg="#1e1e1e", fg="white", pady=60, relief="ridge", bd=4)
        self.res_label.pack(fill='both', expand=True, padx=20, pady=20)

    def create_input(self, master, text, row):
        ttk.Label(master, text=text).grid(row=row, column=0, sticky="e", pady=5, padx=5)
        ent = ttk.Entry(master, width=25); ent.grid(row=row, column=1, sticky="w", padx=5); return ent

    def processar(self):
        try:
            anv = self.ent_tail.get().upper()
            if not anv: raise ValueError("Insira a Matrícula.")
            
            qfe = float(self.ent_qfe.get().replace(',', '.'))
            p = [((float(x.get().replace(',', '.')) - 3.9785) / 3.9951) for x in [self.ent_p1_ma, self.ent_p2_ma, self.ent_p3_ma, self.ent_p4_ma, self.ent_p5_ma, self.ent_p6_ma]]
            
            def calc_ng(t_e, n_e):
                t, n = float(t_e.get().replace(',', '.')), float(n_e.get().replace(',', '.'))
                return n * (1 / math.sqrt((t + 273.15) / 288.15))

            ng1, ng2 = calc_ng(self.ent_t1_c1, self.ent_n1_c1), calc_ng(self.ent_t1_c2, self.ent_n1_c2)
            
            lim3 = self.calcular_limite_manual(qfe, ng1)
            lim5 = self.calcular_limite_manual(qfe, ng2)
            
            diff = p[5] - p[0]
            status = "APROVADO" if (diff <= 0.03 and p[2] >= lim3 and p[4] >= lim5) else "REPROVADO"
            
            # Banco de Dados
            conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
            cursor.execute("INSERT INTO registros (anv, data_cal, pn_valise, realizador, p1_bar, p2_bar, ng1, p3_bar, p4_bar, ng2, p5_bar, p6_bar, delta_p, status, qfe_local, timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (anv, self.ent_date.get(), self.ent_pn.get(), self.ent_nome.get(), p[0], p[1], ng1, p[2], p[3], ng2, p[4], p[5], diff, status, qfe, datetime.now()))
            conn.commit(); conn.close()

            # Gráfico Atual
            fig = self.gerar_figura(ng1, p[2], ng2, p[4], anv, qfe)
            path_img = f"graficos_salvos/Gr_{anv}_{datetime.now().strftime('%H%M%S')}.png"; fig.savefig(path_img)
            
            # PDF
            self.gerar_pdf(anv, self.ent_date.get(), self.ent_nome.get(), p, diff, status, qfe, path_img)
            
            self.res_label.config(text=f"AERONAVE: {anv}\nSTATUS: {status}\nΔP: {diff:.4f} bar\nLimite P3: {lim3:.4f}\nP3 Real: {p[2]:.4f}", fg="#2ecc71" if status=="APROVADO" else "#e74c3c")
            self.carregar_dados(); self.atualizar_combobox_anvs(); self.nb.select(self.tab2)
            messagebox.showinfo("Sucesso", "Relatório e PDF gerados com sucesso!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    def gerar_pdf(self, anv, data, insp, p, delta, status, qfe, img):
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", 'B', 16); pdf.cell(200, 10, "RELATÓRIO DE CALIBRAÇÃO P2.4", ln=True, align='C')
        pdf.ln(10); pdf.set_font("Arial", '', 11)
        pdf.cell(100, 8, f"Aeronave: {anv}"); pdf.cell(100, 8, f"Data: {data}", ln=True)
        pdf.cell(100, 8, f"Inspetor: {insp}"); pdf.cell(100, 8, f"QFE: {qfe} hPa", ln=True)
        pdf.set_font("Arial", 'B', 12); pdf.cell(200, 10, f"STATUS FINAL: {status}", ln=True, align='C')
        pdf.ln(5); pdf.set_fill_color(220, 220, 220); pdf.cell(60, 8, "Parâmetro", 1, 0, 'C', True); pdf.cell(60, 8, "Valor (bar)", 1, 1, 'C', True)
        labels = ["P1 (Parado)", "P2 (Girando)", "P3 (Opening C1)", "P4 (Closing C1)", "P5 (Opening C2)", "P6 (Closing C2)", "Delta P (P6-P1)"]
        vals = [p[0], p[1], p[2], p[3], p[4], p[5], delta]
        pdf.set_font("Arial", '', 10)
        for l, v in zip(labels, vals): pdf.cell(60, 7, l, 1); pdf.cell(60, 7, f"{v:.4f}", 1, 1, 'R')
        if os.path.exists(img): pdf.ln(10); pdf.image(img, x=15, w=170)
        pdf.output(f"relatorios_pdf/Relatorio_{anv}_{datetime.now().strftime('%H%M%S')}.pdf")

    def gerar_figura(self, x1, y1, x2, y2, titulo, qfe):
        fig = plt.Figure(figsize=(6, 4), dpi=100); ax = fig.add_subplot(111)
        if os.path.exists(self.GRAFICO_BASE):
            img = mpimg.imread(self.GRAFICO_BASE); ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.5)
        eixo_ng = np.linspace(68, 100, 40); lim = [self.calcular_limite_manual(qfe, x) for x in eixo_ng]
        ax.plot(eixo_ng, lim, 'r--', label='Limite Mínimo (Interp.)')
        ax.scatter([x1, x2], [y1, y2], color=['green', 'blue'], s=100, edgecolors='black', label='C1 / C2 Atual')
        ax.set_title(f"Performance - {titulo}"); ax.set_xlim(68, 100); ax.set_ylim(0.36, 1.10); ax.legend(); ax.grid(True)
        return fig

    def create_history_widgets(self):
        f = ttk.Frame(self.tab3, padding=10); f.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(f, columns=('ID', 'ANV', 'DATA', 'RESP', 'P3', 'P5', 'DP', 'STATUS'), show='headings')
        for c in ('ID', 'ANV', 'DATA', 'RESP', 'P3', 'P5', 'DP', 'STATUS'): self.tree.heading(c, text=c); self.tree.column(c, width=95, anchor="center")
        self.tree.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview); self.tree.configure(yscroll=sb.set); sb.pack(side='right', fill='y')
        ttk.Button(self.tab3, text="🗑️ EXCLUIR", command=self.deletar, style="Danger.TButton").pack(pady=5)
        self.carregar_dados()

    def carregar_dados(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        cursor.execute("SELECT id, anv, data_cal, realizador, p3_bar, p5_bar, delta_p, status FROM registros ORDER BY timestamp DESC")
        for r in cursor.fetchall():
            r_l = list(r)
            for i in [4, 5, 6]: r_l[i] = f"{r_l[i]:.4f}"
            self.tree.insert('', tk.END, values=r_l)
        conn.close()

    def create_dispersion_widgets(self):
        f = ttk.LabelFrame(self.tab4, text=" FILTROS ", padding=10); f.pack(fill='x', padx=15, pady=5)
        self.cb_anv_disp = ttk.Combobox(f, state="readonly"); self.cb_anv_disp.pack(side='left', padx=10)
        ttk.Button(f, text="📊 DISPERSÃO", command=self.plot_disp).pack(side='left')
        self.f_disp = ttk.Frame(self.tab4); self.f_disp.pack(fill='both', expand=True)

    def create_trend_widgets(self):
        f = ttk.LabelFrame(self.tab5, text=" TENDÊNCIA ", padding=10); f.pack(fill='x', padx=15, pady=5)
        self.cb_anv_tend = ttk.Combobox(f, state="readonly"); self.cb_anv_tend.pack(side='left', padx=10)
        self.cb_p_tend = ttk.Combobox(f, values=["P3", "P5", "Delta P"], state="readonly"); self.cb_p_tend.pack(side='left', padx=10); self.cb_p_tend.current(0)
        ttk.Button(f, text="📉 TENDÊNCIA", command=self.plot_tend).pack(side='left')
        self.f_tend = ttk.Frame(self.tab5); self.f_tend.pack(fill='both', expand=True)

    def plot_disp(self):
        for w in self.f_disp.winfo_children(): w.destroy()
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT anv, ng1, p3_bar, ng2, p5_bar FROM registros"); dados = cursor.fetchall(); conn.close()
        fig = plt.Figure(figsize=(10, 5)); ax = fig.add_subplot(111)
        if os.path.exists(self.GRAFICO_BASE):
            img = mpimg.imread(self.GRAFICO_BASE); ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.3)
        for d in dados:
            if self.cb_anv_disp.get() == "TODAS" or d[0] == self.cb_anv_disp.get():
                ax.scatter(d[1], d[2], color='green', s=20); ax.scatter(d[3], d[4], color='blue', s=20)
        ax.set_title("Dispersão Histórica"); ax.set_xlim(68, 100); ax.set_ylim(0.36, 1.10); ax.grid(True)
        FigureCanvasTkAgg(fig, master=self.f_disp).get_tk_widget().pack(fill='both', expand=True)

    def plot_tend(self):
        for w in self.f_tend.winfo_children(): w.destroy()
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor()
        p = "p3_bar" if self.cb_p_tend.get() == "P3" else ("p5_bar" if self.cb_p_tend.get() == "P5" else "delta_p")
        cursor.execute(f"SELECT data_cal, {p} FROM registros WHERE anv = ? ORDER BY timestamp", (self.cb_anv_tend.get(),))
        d = cursor.fetchall(); conn.close()
        if not d: return
        fig = plt.Figure(figsize=(10, 5)); ax = fig.add_subplot(111)
        ax.plot([x[0] for x in d], [x[1] for x in d], marker='o', color='red'); ax.grid(True); plt.setp(ax.get_xticklabels(), rotation=30)
        ax.set_title(f"Evolução {self.cb_p_tend.get()} - {self.cb_anv_tend.get()}")
        FigureCanvasTkAgg(fig, master=self.f_tend).get_tk_widget().pack(fill='both', expand=True)

    def atualizar_combobox_anvs(self):
        conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor(); cursor.execute("SELECT DISTINCT anv FROM registros"); anvs = [r[0] for r in cursor.fetchall()]; conn.close()
        self.cb_anv_disp['values'] = ["TODAS"] + anvs; self.cb_anv_tend['values'] = anvs
        if anvs: self.cb_anv_disp.current(0); self.cb_anv_tend.current(0)

    def deletar(self):
        s = self.tree.selection()
        if s and messagebox.askyesno("Confirmação", "Excluir permanentemente?"):
            conn = sqlite3.connect(self.DB_NAME); cursor = conn.cursor(); cursor.execute("DELETE FROM registros WHERE id = ?", (self.tree.item(s)['values'][0],))
            conn.commit(); conn.close(); self.carregar_dados(); self.atualizar_combobox_anvs()

if __name__ == "__main__":
    root = tk.Tk(); app = ValiseP24App(root); root.mainloop()