import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os

# Instalar a biblioteca groq (em ambiente local ou cloud com requirements.txt)
from groq import Groq

# Configurar API Key da Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Análise Financeira com IA", layout="wide")
st.title("📊 Analisador Financeiro com IA Generativa")
st.markdown("Carregue um arquivo `.xlsx` com os dados financeiros da empresa para gerar gráficos e um relatório automático com insights.")

# Upload do arquivo Excel
arquivo = st.file_uploader("Faça upload do arquivo Excel", type=["xlsx"])

if arquivo:
    dados = pd.read_excel(arquivo, index_col=0)
    dados.index.name = "Categoria"

    st.success("✅ Dados carregados com sucesso!")

    # Converter colunas para datas
    dados.columns = pd.to_datetime(dados.columns, format="%b-%Y", errors="coerce")

    # Análises
    texto_analises = ""

    with st.expander("1. Crescimento Anual da Receita Bruta", expanded=True):
        receita_bruta = dados.loc["Receita Bruta"]
        receita_anual = receita_bruta.resample("YE").sum()
        crescimento_anual = receita_anual.pct_change() * 100

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(receita_anual.index.year, receita_anual.values, color="skyblue", label="Receita Anual (R$)")
        ax.plot(receita_anual.index.year, receita_anual.values, marker="o", color="blue", label="Receita Bruta")
        ax.set_title("Crescimento Anual da Receita Bruta")
        ax.set_xlabel("Ano")
        ax.set_ylabel("Valores (em R$)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()

        for i, bar in enumerate(bars):
            valor = f"{receita_anual.values[i]:,.2f}"
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05*bar.get_height(), valor, ha="center", fontsize=10)
            if i > 0 and not np.isnan(crescimento_anual.values[i]):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f"{crescimento_anual.values[i]:.2f}%", ha="center", va="bottom", fontsize=10, color="red")

        st.pyplot(fig)

        analise1 = "### Análise:\n"
        for ano, crescimento in zip(receita_anual.index.year[1:], crescimento_anual.values[1:]):
            analise1 += f"- Em {ano}, o crescimento foi de {crescimento:.2f}%.\n"
        st.markdown(analise1)
        texto_analises += analise1 + "\n"

    with st.expander("2. Tendência do Lucro Bruto e Lucro Líquido", expanded=True):
        lucro_bruto = dados.loc["(=) Lucro Bruto"]
        lucro_liquido = dados.loc["(=) Resultado Líquido"]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(lucro_bruto.index, lucro_bruto.values, label="Lucro Bruto", marker="o", color="green")
        ax.plot(lucro_liquido.index, lucro_liquido.values, label="Lucro Líquido", marker="o", color="orange")
        ax.set_title("Tendência do Lucro Bruto e Lucro Líquido")
        ax.set_xlabel("Período")
        ax.set_ylabel("Valores (em R$)")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)
        plt.xticks(rotation=45)

        st.pyplot(fig)

        crescimento_bruto = ((lucro_bruto.iloc[-1] / lucro_bruto.iloc[0]) - 1) * 100
        crescimento_liquido = ((lucro_liquido.iloc[-1] / lucro_liquido.iloc[0]) - 1) * 100
        analise2 = f"""
### Análise:
- O Lucro Bruto cresceu {crescimento_bruto:.2f}% durante o período.
- O Lucro Líquido cresceu {crescimento_liquido:.2f}% durante o período.
"""
        st.markdown(analise2)
        texto_analises += analise2 + "\n"

    with st.expander("3. Despesas Relativas à Receita Bruta (%)", expanded=True):
        categorias_despesas = [
            "(-) Despesas com Vendas",
            "(-) Despesas Administrativas",
            "(-) Despesas Financeiras"
        ]

        despesas_percentuais = dados.loc[categorias_despesas].div(dados.loc["Receita Bruta"]) * 100

        fig, ax = plt.subplots(figsize=(12, 6))
        for categoria in categorias_despesas:
            ax.plot(despesas_percentuais.columns, despesas_percentuais.loc[categoria], label=categoria, marker="o")
        ax.set_title("Despesas Relativas à Receita Bruta")
        ax.set_xlabel("Período")
        ax.set_ylabel("Percentual (%)")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        analise3 = "### Análise:\n"
        for categoria in categorias_despesas:
            max_periodo = despesas_percentuais.loc[categoria].idxmax()
            max_valor = despesas_percentuais.loc[categoria].max()
            analise3 += f"- {categoria} atingiu o maior valor relativo em {max_periodo.strftime('%b-%Y')} ({max_valor:.2f}%).\n"
        st.markdown(analise3)
        texto_analises += analise3 + "\n"

    # Relatório gerado pela IA
    with st.expander("🤖 Relatório Inteligente com IA Groq", expanded=True):
        with st.spinner("Gerando relatório com IA..."):
            prompt = f"""
Você é um analista financeiro com conhecimento em Inteligência Artificial. Com base na análise abaixo, escreva um relatório em linguagem natural com insights estratégicos, resumindo as tendências e sugerindo possíveis ações ou pontos de atenção:

{texto_analises}

Seja direto e claro em sua análise, usando uma linguagem acessível para tomadores de decisão.
"""
            resposta = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "Você é um analista financeiro especialista em gerar relatórios com base em dados contábeis e financeiros."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            st.markdown(resposta.choices[0].message.content)
