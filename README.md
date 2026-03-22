# CALIBRACAO-P2.4
Este software foi desenvolvido para automatizar e digitalizar o processo de calibração técnica da aeronave H-36 (H225M). Ele substitui o método tradicional (anotações em papel e cálculos manuais) por uma interface digital de alta precisão com análise de dados histórica.

🛠️ O Problema vs. A Solução
Antigamente: Os dados eram anotados em papel, calculados em calculadoras comuns e os gráficos eram traçados manualmente. Não havia armazenamento para análise de desempenho ao longo do tempo.

Com este Software: Todo o cálculo de interpolação linear é automatizado, os gráficos são gerados instantaneamente e cada calibração é salva em um banco de dados local para monitoramento de tendência (Trend Analysis).

🚀 Principais Funcionalidades
Cálculo Dinâmico: Motor de cálculo que utiliza interpolação linear para definir limites de pressão baseados na rotação (NG) e correção por QFE local.

Análise de Tendência (Trend Monitoring): Visualização gráfica da evolução de parâmetros críticos (P3, P5 e Delta P) ao longo do tempo, permitindo manutenção preditiva.

Persistência Local (Offline-First): Utiliza SQLite para armazenar o histórico completo da frota sem necessidade de internet no hangar.

Geração de Relatórios: Exportação automática de laudos técnicos em PDF com gráficos integrados via biblioteca FPDF.

Interface Gráfica (GUI): Desenvolvida em Tkinter com foco em usabilidade técnica.

💻 Tecnologias Utilizadas
Linguagem: Python 3.12

Interface: Tkinter

Matemática/Dados: NumPy, Matplotlib

Banco de Dados: SQLite

Relatórios: FPDF
