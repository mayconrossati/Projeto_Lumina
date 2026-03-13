# ==============================================================================
# PROJETO LÚMINA - MVP SPRINT 3 (Single File Application)
# Para rodar: streamlit run lumina_app.py
# ==============================================================================

import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime
import time
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lúmina | Score & Oracle", page_icon="🔮", layout="wide")


# --- MÓDULOS DE BACKEND SIMULADOS ---
def gerar_dados_amostra():
    dados = {
        "cnpj_fundo": ["11.111.111/0001-11", "22.222.222/0001-22", "33.333.333/0001-33"],
        "nome_fundo": ["FIDC ALPHA TECH", "FIDC BETA AGRO", "FUNDO GAMA MULTIMERCADO"],
        "tipo": ["FIDC", "FIDC", "FIM"],
        "patrimonio_liquido": [50000000, 12000000, 8000000],
        "inadimplencia_perc": [0.8, 4.2, 0.1],
        "indice_liquidez": [2.5, 1.8, 3.0]
    }
    return pd.DataFrame(dados)


def motor_score_lumina(df):
    df_fidc = df[df['tipo'].str.upper() == 'FIDC'].copy()  # Proteção para ler 'FIDC' ou 'fidc'
    scores = []
    for _, row in df_fidc.iterrows():
        if row['inadimplencia_perc'] < 1.5 and row['indice_liquidez'] > 2.0:
            scores.append("A (Baixo Risco)")
        elif row['inadimplencia_perc'] < 5.0:
            scores.append("B (Risco Moderado)")
        else:
            scores.append("C (Alto Risco)")
    df_fidc['score_lumina'] = scores
    return df_fidc


def api_oraculo_lumina(dados_fundo):
    payload = {
        "fundo": dados_fundo['nome_fundo'],
        "cnpj": dados_fundo['cnpj_fundo'],
        "score": dados_fundo['score_lumina'],
        "timestamp": datetime.utcnow().isoformat(),
        "emissor": "Lumina Oracle Engine v1.0"
    }
    payload_str = json.dumps(payload, sort_keys=True)
    assinatura = hashlib.sha256(f"{payload_str}_CHAVE_PRIVADA_LUMINA".encode()).hexdigest()
    payload['signature_hash'] = f"0x{assinatura}"
    return payload


# --- INTERFACE DO USUÁRIO (FRONTEND) ---
st.title("🔮 Lúmina: Plataforma de Risco B2B & Web3 Oracle")
st.markdown("Solução integrada de Data Science para o mercado de crédito (FIDC).")
st.markdown("---")

with st.sidebar:
    # --- LOGO ADICIONADA AQUI ---
    st.image("https://dummyimage.com/600x200/1e1e1e/a200ff&text=L%C3%9AMINA", use_container_width=True)
    st.markdown("---")
    # ----------------------------

    st.header("📂 Ingestão de Dados")
    st.info("Faça o upload do arquivo CVM ou use nossos dados de demonstração.")

    arquivo_upload = st.file_uploader("Carregar CSV CVM", type=['csv'])
    usar_amostra = st.button("Usar Dados de Demonstração (Mock)")

    # LÓGICA DE ESTADO CORRIGIDA AQUI:
    if usar_amostra:
        st.session_state['df_bruto'] = gerar_dados_amostra()
        st.session_state['dados_calculados'] = False
        st.session_state['fonte_atual'] = "amostra_mock"  # Memoriza a fonte
        st.success("Dados de demonstração carregados!")

    if arquivo_upload is not None:
        # Só lê o arquivo e reseta o cálculo se for um arquivo NOVO
        if st.session_state.get('fonte_atual') != arquivo_upload.name:
            arquivo_upload.seek(0)  # Garante que está lendo do início
            st.session_state['df_bruto'] = pd.read_csv(arquivo_upload)
            st.session_state['dados_calculados'] = False
            st.session_state['fonte_atual'] = arquivo_upload.name  # Memoriza o nome do CSV
            st.success(f"Arquivo {arquivo_upload.name} carregado!")

if 'df_bruto' in st.session_state:
    df_raw = st.session_state['df_bruto']

    tab1, tab2 = st.tabs(["🧠 1. Score Lúmina (Análise de Risco)", "🔗 2. Oráculo Lúmina (Integração Web3)"])

    # --- ABA 1: SCORE LÚMINA ---
    with tab1:
        st.header("Motor de Risco & Ingestão")
        st.write("Visão geral dos dados brutos recebidos da CVM/Núclea antes do processamento:")
        st.dataframe(df_raw, use_container_width=True)

        if st.button("Processar Dados e Calcular Scores", key="btn_score"):
            with st.spinner("Higienizando dados e aplicando regras de negócio..."):
                time.sleep(1)
                df_processado = motor_score_lumina(df_raw)
                st.session_state['df_processado'] = df_processado
                st.session_state['dados_calculados'] = True

        if st.session_state.get('dados_calculados', False):
            df_processado = st.session_state['df_processado']

            st.success(f"Cálculo concluído! {len(df_processado)} FIDCs qualificados e analisados.")

            st.subheader("Resultados do Score Lúmina")
            col1, col2 = st.columns([1.2, 1])

            with col1:
                st.write("**Carteira Analisada**")
                st.dataframe(df_processado[['nome_fundo', 'inadimplencia_perc', 'score_lumina']],
                             use_container_width=True)

            with col2:
                st.write("**Distribuição de Risco (Dashboard)**")
                tipo_grafico = st.radio("Selecione a visualização:", ["Gráfico de Pizza", "Gráfico de Barras"],
                                        horizontal=True)

                contagem_scores = df_processado['score_lumina'].value_counts().reset_index()
                contagem_scores.columns = ['Score', 'Quantidade']

                cores_risco = {
                    "A (Baixo Risco)": "#28a745",
                    "B (Risco Moderado)": "#ffc107",
                    "C (Alto Risco)": "#dc3545"
                }

                if tipo_grafico == "Gráfico de Pizza":
                    fig = px.pie(contagem_scores, names='Score', values='Quantidade', color='Score',
                                 color_discrete_map=cores_risco, hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.bar(contagem_scores, x='Score', y='Quantidade', color='Score',
                                 color_discrete_map=cores_risco, text_auto=True)
                    st.plotly_chart(fig, use_container_width=True)

    # --- ABA 2: ORÁCULO LÚMINA ---
    with tab2:
        st.header("Empacotamento e Assinatura para Blockchain")
        st.write(
            "O Oráculo Lúmina pega o resultado do Score e o transforma em um dado confiável (criptografado) para ser lido por Smart Contracts.")

        if st.session_state.get('dados_calculados', False):
            df_proc = st.session_state['df_processado']
            fundo_selecionado = st.selectbox("Selecione um FIDC para gerar o payload do Oráculo:",
                                             df_proc['nome_fundo'])

            if st.button("Gerar Assinatura Web3 (Oráculo)", key="btn_oraculo"):
                with st.spinner("Gerando Hash SHA-256 e assinando pacote..."):
                    time.sleep(1.5)
                    dados_fundo = df_proc[df_proc['nome_fundo'] == fundo_selecionado].iloc[0]
                    payload_final = api_oraculo_lumina(dados_fundo)

                st.subheader("✅ Payload Assinado e Pronto para Entrega")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric(label="Status do Oráculo", value="Online", delta="Conectado à Mainnet")
                    st.metric(label="Score Final Transmitido", value=payload_final['score'])
                with c2:
                    st.markdown("**JSON de Resposta da API (Com Assinatura de Integridade)**")
                    st.json(payload_final)
                    st.info(f"🔑 **Hash de Validação:** `{payload_final['signature_hash']}`")
        else:
            st.warning("⚠️ Volte na aba 'Score Lúmina' e processe os dados primeiro!")

else:
    st.write("👈 Comece carregando os dados na barra lateral para iniciar o fluxo da plataforma Lúmina.")