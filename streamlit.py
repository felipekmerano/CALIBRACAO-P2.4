import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os
import pandas as pd

# ─── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SISTEMA DE TESTE E ANALISE P2.4 - HELIBRAS/AIRBUS",
    layout="wide",
    page_icon="🚁"
)

GRAFICO_BASE = "graficop2.4(1).png"
DB_NAME = "historico_calibracao.db"

for folder in ["graficos_salvos", "relatorios_pdf"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ─── BANCO DE DADOS ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn.commit()
    conn.close()

init_db()

# ─── LÓGICA (INALTERADA) ────────────────────────────────────────────────────────
def calcular_limite_manual(qfe, ng_atual):
    tabela_pontos = [(70.0, 0.420), (80.0, 0.485), (85.0, 0.530),
                     (90.0, 0.590), (95.0, 0.660), (100.0, 0.750)]
    ngs, pressoes = zip(*tabela_pontos)
    pressao_base = np.interp(ng_atual, ngs, pressoes)
    ajuste_qfe = (qfe - 1013.25) * 0.0004
    return pressao_base + ajuste_qfe

def calc_ng(t, n):
    return n * (1 / math.sqrt((t + 273.15) / 288.15))

def ma_para_bar(ma_val):
    return (ma_val - 3.9785) / 3.9951

def gerar_figura(x1, y1, x2, y2, titulo, qfe):
    fig, ax = plt.subplots(figsize=(8, 5))
    if os.path.exists(GRAFICO_BASE):
        img = mpimg.imread(GRAFICO_BASE)
        ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.5)
    eixo_ng = np.linspace(68, 100, 40)
    lim = [calcular_limite_manual(qfe, x) for x in eixo_ng]
    ax.plot(eixo_ng, lim, 'r--', label='Limite Minimo (Interp.)')
    ax.scatter([x1, x2], [y1, y2], color=['green', 'blue'], s=100,
               edgecolors='black', label='C1 / C2 Atual')
    ax.set_title(f"Performance - {titulo}")
    ax.set_xlim(68, 100)
    ax.set_ylim(0.36, 1.10)
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    return fig

def gerar_pdf(anv, data, insp, p, delta, status, qfe, img_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RELATORIO DE CALIBRACAO P2.4", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 8, f"Aeronave: {anv}")
    pdf.cell(100, 8, f"Data: {data}", ln=True)
    pdf.cell(100, 8, f"Inspetor: {insp}")
    pdf.cell(100, 8, f"QFE: {qfe} hPa", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, f"STATUS FINAL: {status}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(60, 8, "Parametro", 1, 0, 'C', True)
    pdf.cell(60, 8, "Valor (bar)", 1, 1, 'C', True)
    labels = ["P1 (Parado)", "P2 (Girando)", "P3 (Opening C1)",
              "P4 (Closing C1)", "P5 (Opening C2)", "P6 (Closing C2)", "Delta P (P6-P1)"]
    vals = [p[0], p[1], p[2], p[3], p[4], p[5], delta]
    pdf.set_font("Arial", '', 10)
    for l, v in zip(labels, vals):
        pdf.cell(60, 7, l, 1)
        pdf.cell(60, 7, f"{v:.4f}", 1, 1, 'R')
    if os.path.exists(img_path):
        pdf.ln(10)
        pdf.image(img_path, x=15, w=170)
    pdf_path = f"relatorios_pdf/Relatorio_{anv}_{datetime.now().strftime('%H%M%S')}.pdf"
    pdf.output(pdf_path)
    return pdf_path

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, anv, data_cal, realizador, p3_bar, p5_bar, delta_p, status "
        "FROM registros ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_anvs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT anv FROM registros")
    anvs = [r[0] for r in cursor.fetchall()]
    conn.close()
    return anvs

def deletar_registro(rec_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (rec_id,))
    conn.commit()
    conn.close()

# ─── CSS (apenas elementos customizados, sem sobrescrever inputs do Streamlit) ──
st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(135deg, #1a3a5c, #0d1b2a);
        border: 1px solid #1f6feb;
        border-radius: 12px;
        padding: 20px 30px;
        text-align: center;
        margin-bottom: 16px;
    }
    .header-banner h1 {
        font-size: 22px;
        font-weight: 700;
        color: #58a6ff;
        letter-spacing: 3px;
        margin: 0;
    }
    .header-banner p {
        color: #adb5bd;
        font-size: 12px;
        margin: 4px 0 0;
        letter-spacing: 2px;
    }
    .section-label {
        font-weight: 700;
        font-size: 12px;
        color: #1f6feb;
        letter-spacing: 2px;
        text-transform: uppercase;
        border-bottom: 2px solid #1f6feb;
        padding-bottom: 4px;
        margin-bottom: 8px;
        margin-top: 12px;
    }
    .status-aprovado {
        background: #d4edda;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        color: #155724;
        font-size: 18px;
        font-weight: bold;
        font-family: monospace;
        line-height: 2;
        margin-bottom: 16px;
    }
    .status-reprovado {
        background: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        color: #721c24;
        font-size: 18px;
        font-weight: bold;
        font-family: monospace;
        line-height: 2;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
    <h1>🚁 SISTEMA DE TESTE E ANÁLISE P2.4</h1>
    <p>HELIBRAS / AIRBUS HELICOPTERS — FULL VERSION</p>
</div>
""", unsafe_allow_html=True)

# ─── ABAS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 FORMULÁRIO", "📊 RESULTADO", "🗄️ HISTÓRICO", "🎯 DISPERSÃO", "📉 TENDÊNCIA"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FORMULÁRIO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    c_esq, c_dir = st.columns(2)

    with c_esq:
        st.markdown('<div class="section-label">IDENTIFICAÇÃO</div>', unsafe_allow_html=True)
        anv      = st.text_input("Matrícula", key="anv").upper()
        data_cal = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"), key="data_cal")
        pn       = st.text_input("P/N Valise", key="pn")
        nome     = st.text_input("Realizador", key="nome")

        st.markdown('<div class="section-label">① PREPARAÇÃO (mA / hPa)</div>', unsafe_allow_html=True)
        qfe   = st.number_input("QFE Local (hPa)", value=1013.25, format="%.2f", key="qfe")
        p1_ma = st.number_input("P1 Parado (mA)", value=0.0, format="%.4f", key="p1")
        p2_ma = st.number_input("P2 Girando (mA)", value=0.0, format="%.4f", key="p2")

    with c_dir:
        st.markdown('<div class="section-label">② CONFIGURAÇÃO 1</div>', unsafe_allow_html=True)
        t1_c1 = st.number_input("T1 C1 (°C)", value=0.0, format="%.2f", key="t1c1")
        n1_c1 = st.number_input("N1 C1 (%)",  value=0.0, format="%.2f", key="n1c1")
        p3_ma = st.number_input("P3 (mA)", value=0.0, format="%.4f", key="p3")
        p4_ma = st.number_input("P4 (mA)", value=0.0, format="%.4f", key="p4")

        st.markdown('<div class="section-label">③ CONFIGURAÇÃO 2</div>', unsafe_allow_html=True)
        t1_c2 = st.number_input("T1 C2 (°C)", value=0.0, format="%.2f", key="t1c2")
        n1_c2 = st.number_input("N1 C2 (%)",  value=0.0, format="%.2f", key="n1c2")
        p5_ma = st.number_input("P5 (mA)", value=0.0, format="%.4f", key="p5")
        p6_ma = st.number_input("P6 (mA)", value=0.0, format="%.4f", key="p6")

    st.divider()

    if st.button("⚙️ CALCULAR, SALVAR E GERAR PDF", use_container_width=True):
        if not anv:
            st.error("Insira a Matrícula.")
        else:
            try:
                p = [ma_para_bar(v) for v in [p1_ma, p2_ma, p3_ma, p4_ma, p5_ma, p6_ma]]

                ng1 = calc_ng(t1_c1, n1_c1)
                ng2 = calc_ng(t1_c2, n1_c2)

                lim3 = calcular_limite_manual(qfe, ng1)
                lim5 = calcular_limite_manual(qfe, ng2)

                diff   = p[5] - p[0]
                status = "APROVADO" if (diff <= 0.03 and p[2] >= lim3 and p[4] >= lim5) else "REPROVADO"

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO registros (anv, data_cal, pn_valise, realizador, "
                    "p1_bar, p2_bar, ng1, p3_bar, p4_bar, ng2, p5_bar, p6_bar, "
                    "delta_p, status, qfe_local, timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (anv, data_cal, pn, nome,
                     p[0], p[1], ng1, p[2], p[3], ng2, p[4], p[5],
                     diff, status, qfe, datetime.now())
                )
                conn.commit()
                conn.close()

                fig = gerar_figura(ng1, p[2], ng2, p[4], anv, qfe)
                img_path = f"graficos_salvos/Gr_{anv}_{datetime.now().strftime('%H%M%S')}.png"
                fig.savefig(img_path, bbox_inches='tight')

                pdf_path = gerar_pdf(anv, data_cal, nome, p, diff, status, qfe, img_path)

                st.session_state["resultado"] = {
                    "anv": anv, "status": status, "diff": diff,
                    "lim3": lim3, "p3": p[2], "lim5": lim5, "p5": p[4],
                    "ng1": ng1, "ng2": ng2, "fig": fig, "pdf_path": pdf_path
                }

                st.success("✅ Dados salvos com sucesso! Acesse a aba 📊 RESULTADO.")

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Relatório PDF",
                        data=f.read(),
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RESULTADO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if "resultado" not in st.session_state:
        st.info("Aguardando dados... Preencha o formulário e clique em CALCULAR.")
    else:
        r = st.session_state["resultado"]
        css_class = "status-aprovado" if r["status"] == "APROVADO" else "status-reprovado"
        st.markdown(f"""
        <div class="{css_class}">
            AERONAVE: {r['anv']}<br>
            STATUS: {r['status']}<br>
            &Delta;P: {r['diff']:.4f} bar<br>
            Limite P3: {r['lim3']:.4f} &nbsp;|&nbsp; P3 Real: {r['p3']:.4f}<br>
            Limite P5: {r['lim5']:.4f} &nbsp;|&nbsp; P5 Real: {r['p5']:.4f}
        </div>
        """, unsafe_allow_html=True)

        st.pyplot(r["fig"])

        with open(r["pdf_path"], "rb") as f:
            st.download_button(
                label="⬇️ Baixar Relatório PDF",
                data=f.read(),
                file_name=os.path.basename(r["pdf_path"]),
                mime="application/pdf",
                use_container_width=True
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    rows = carregar_dados()
    if not rows:
        st.info("Nenhum registro encontrado.")
    else:
        df = pd.DataFrame(rows, columns=["ID", "ANV", "DATA", "RESP", "P3", "P5", "ΔP", "STATUS"])
        for col in ["P3", "P5", "ΔP"]:
            df[col] = df[col].apply(lambda x: f"{x:.4f}")
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("**Excluir registro pelo ID:**")
    col_del1, col_del2 = st.columns([1, 3])
    with col_del1:
        del_id = st.number_input("ID", min_value=1, step=1, key="del_id", label_visibility="collapsed")
    with col_del2:
        if st.button("🗑️ EXCLUIR REGISTRO", key="btn_del"):
            deletar_registro(int(del_id))
            st.success(f"Registro ID {del_id} excluído.")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DISPERSÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    anvs = get_anvs()
    sel_anv_disp = st.selectbox("Filtrar Aeronave", ["TODAS"] + anvs, key="disp_anv")

    if st.button("📊 GERAR GRÁFICO DE DISPERSÃO", key="btn_disp", use_container_width=True):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT anv, ng1, p3_bar, ng2, p5_bar FROM registros")
        dados = cursor.fetchall()
        conn.close()

        fig, ax = plt.subplots(figsize=(10, 5))
        if os.path.exists(GRAFICO_BASE):
            img = mpimg.imread(GRAFICO_BASE)
            ax.imshow(np.rot90(img, k=3), extent=[68, 100, 0.36, 1.10], aspect='auto', alpha=0.3)
        for d in dados:
            if sel_anv_disp == "TODAS" or d[0] == sel_anv_disp:
                ax.scatter(d[1], d[2], color='green', s=20)
                ax.scatter(d[3], d[4], color='blue', s=20)
        ax.set_title("Dispersão Histórica")
        ax.set_xlim(68, 100)
        ax.set_ylim(0.36, 1.10)
        ax.grid(True)
        plt.tight_layout()
        st.pyplot(fig)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TENDÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    anvs = get_anvs()
    col_a, col_b = st.columns(2)
    with col_a:
        sel_anv_tend = st.selectbox("Aeronave", anvs if anvs else ["—"], key="tend_anv")
    with col_b:
        sel_p_tend = st.selectbox("Parâmetro", ["P3", "P5", "Delta P"], key="tend_p")

    if st.button("📉 GERAR GRÁFICO DE TENDÊNCIA", key="btn_tend", use_container_width=True):
        p_col = "p3_bar" if sel_p_tend == "P3" else ("p5_bar" if sel_p_tend == "P5" else "delta_p")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT data_cal, {p_col} FROM registros WHERE anv = ? ORDER BY timestamp",
            (sel_anv_tend,)
        )
        d = cursor.fetchall()
        conn.close()

        if not d:
            st.warning("Sem dados para esta aeronave.")
        else:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot([x[0] for x in d], [x[1] for x in d], marker='o', color='red')
            ax.grid(True)
            plt.setp(ax.get_xticklabels(), rotation=30)
            ax.set_title(f"Evolução {sel_p_tend} - {sel_anv_tend}")
            plt.tight_layout()
            st.pyplot(fig)