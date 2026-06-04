import io
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from PIL import Image as PILImage
from sklearn.metrics import mean_absolute_error, r2_score

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

import aws_alertas as aws
import fase1_clima as fclima
import fase1_culturas as f1
import fase2_iot as f2
import fase3_banco as f3
import fase6_visao as f6

st.set_page_config(
    page_title="FarmTech AI4Success - Fase 7",
    page_icon="🌱",
    layout="wide",
)

st.markdown("""
<style>
  .block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1180px; }

  h1 { font-weight: 700; letter-spacing: -0.015em; }
  h2, h3 { letter-spacing: -0.01em; }

  /* Métricas como cards com acento agro */
  [data-testid="stMetric"] {
      background: #FFFFFF;
      border: 1px solid #E2E8DA;
      border-left: 4px solid #2E7D32;
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 1px 2px rgba(20, 40, 15, 0.04);
  }
  [data-testid="stMetricLabel"] p { opacity: 0.78; font-weight: 500; }

  /* Abas: mais legíveis, ativo em verde */
  .stTabs [data-baseweb="tab-list"] { gap: 2px; }
  .stTabs [data-baseweb="tab"] { font-weight: 600; padding: 8px 14px; }

  /* Botões */
  .stButton button { border-radius: 8px; font-weight: 600; }

  /* Expanders como cartões suaves */
  [data-testid="stExpander"] {
      border: 1px solid #E2E8DA;
      border-radius: 10px;
  }

  /* Divisórias mais discretas */
  hr { margin: 0.7rem 0; border-color: #E2E8DA; }

  /* Limpeza para apresentação */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

CAMINHO_DADOS  = ROOT / 'data'   / 'dados_agricolas.csv'
CAMINHO_MODELO = ROOT / 'models' / 'regressor_model.pkl'

IDEAIS = {
    'Umidade_Solo': (50.0, 70.0),
    'pH_Solo':      (6.0,  7.0),
    'Nivel_N':      (150.0, 300.0),
}
LIMIAR_PRODUTIVIDADE_CRITICO = 3500.0

f3.init_db()


@st.cache_data(ttl=900)
def previsao_clima(lat, lon):
    return fclima.obter_previsao(lat, lon)


# Leitura da estação ESP32 — estável durante a sessão (simulação).
# Só muda quando o usuário pede "Simular nova leitura" na aba Sensores.
if 'leitura_atual' not in st.session_state:
    st.session_state.leitura_atual = f2.gerar_leitura_sensor()
leitura_atual  = st.session_state.leitura_atual
alertas_atuais = f2.verificar_alertas(leitura_atual)

# ── Cabeçalho ────────────────────────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    logo_path = ROOT / 'assets' / 'logo-fiap.png'
    if logo_path.exists():
        st.image(str(logo_path), width=120)
with col_titulo:
    st.title("FarmTech Solutions — Sistema Integrado Fase 7")
    st.caption("Grupo AI4Success | Turma 1TIAOR | FIAP")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌾 Visão Geral",
    "🌱 Fase 1 — Culturas",
    "📡 Fase 2/3 — Sensores & BD",
    "🤖 Fase 4/5 — Machine Learning",
    "👁️ Fase 6 — Visão Computacional",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — VISÃO GERAL (status da fazenda + alertas)
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Painel da Fazenda")
    st.caption("Estado atual da lavoura, consolidando as Fases 1 a 6 do FarmTech Solutions.")

    culturas = f1.get_culturas()
    stats    = f3.estatisticas_sql()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌱 Culturas cadastradas", len(culturas))
    c2.metric("💧 Umidade do solo",      f"{leitura_atual['umidade']:.1f}%")
    c3.metric("⚗️ pH do solo",           f"{leitura_atual['ph']:.2f}")
    c4.metric("🚿 Bomba de irrigação",   "Ligada" if leitura_atual['bomba_ativa'] else "Desligada")

    st.markdown("---")
    st.markdown("#### Alertas da fazenda")
    if not alertas_atuais:
        st.success("✅ Todos os sensores dentro dos limites normais.")
    else:
        for a in alertas_atuais:
            st.warning(f"**{a['tipo']}** ({a['valor']}) — ação: {a['acao']}")
        if st.button("📧 Enviar estes alertas via AWS SNS", type="primary"):
            enviados, falhas = 0, []
            for a in alertas_atuais:
                ok, msg = aws.enviar_alerta(a['tipo'], str(a['valor']), a['acao'])
                if ok:
                    enviados += 1
                else:
                    falhas.append(msg)
            if enviados:
                st.success(f"{enviados} alerta(s) enviado(s).")
            if falhas:
                st.error(falhas[0])

    with st.expander("🔧 Por baixo dos panos — arquitetura e integração técnica"):
        st.markdown("""
| Fase | Módulo | Tecnologia |
|:----:|--------|-----------|
| 1 | CRUD de Culturas | Python + JSON |
| 2 | Sensores IoT | ESP32 simulado (DHT22, LDR, NPK) |
| 3 | Banco de Dados | SQLite (equivalente Oracle) |
| 4 | Machine Learning | Random Forest (R² = 0.97) |
| 5 | Cloud AWS | SNS — alertas por e-mail/SMS |
| 6 | Visão Computacional | YOLOv8-cls (Ultralytics) |
""")
        st.caption("Validar conexão com o serviço de mensageria AWS SNS:")
        if st.button("Enviar alerta de teste (AWS SNS)"):
            ok, msg = aws.enviar_alerta(
                "TESTE DO SISTEMA",
                f"pH={leitura_atual['ph']:.2f}, Umidade={leitura_atual['umidade']:.1f}%",
                "Verificar condições da lavoura",
            )
            st.success(msg) if ok else st.error(msg)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — FASE 1 CULTURAS
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🌱 Fase 1 — Gestão de Culturas e Insumos")
    st.caption("Cadastre culturas, calcule a área de plantio e dimensione os insumos necessários.")

    col_form, col_lista = st.columns([1, 1.3], gap="large")

    with col_form:
        st.markdown("#### Adicionar cultura")
        tipo = st.selectbox(
            "Tipo de cultura",
            ["soja", "café"],
            help="Soja é cultivada em área retangular; café, em área circular.",
        )

        if tipo == "soja":
            forma  = "retangulo"
            cc1, cc2 = st.columns(2)
            comprimento = cc1.number_input("Comprimento (m)", min_value=0.1, value=100.0, step=1.0)
            largura     = cc2.number_input("Largura (m)",     min_value=0.1, value=50.0,  step=1.0)
            dimensoes   = {"comprimento": comprimento, "largura": largura}
        else:
            forma     = "circulo"
            raio      = st.number_input("Raio (m)", min_value=0.1, value=30.0, step=1.0)
            dimensoes = {"raio": raio}

        area_preview = f1.calcular_area(forma, dimensoes)
        st.metric("Área de plantio", f"{area_preview:.2f} m²")

        add_insumo = st.checkbox("Incluir insumo")
        produto, qtd_por_metro, total_insumo = "", 0.0, 0.0
        if add_insumo:
            produto       = st.text_input("Produto", value="Fertilizante NPK")
            qtd_por_metro = st.number_input(
                "Quantidade por m²",
                min_value=0.01, value=0.5, step=0.1,
                help="Unidades do produto aplicadas por metro quadrado.",
            )
            total_insumo = round(area_preview * qtd_por_metro, 2)
            st.caption(f"Total necessário: {total_insumo:.2f} unidades")

        if st.button("Adicionar cultura", use_container_width=True, type="primary"):
            insumos = []
            if add_insumo and produto:
                insumos = [{
                    "produto":          produto,
                    "qtd_por_metro":    qtd_por_metro,
                    "total_necessario": total_insumo,
                }]
            nova = f1.adicionar_cultura(tipo, forma, dimensoes, insumos)
            st.success(f"Cultura #{nova['id']} ({tipo}) cadastrada — {nova['area_calculada_m2']:.2f} m².")
            st.rerun()

    with col_lista:
        culturas = f1.get_culturas()
        st.markdown(f"#### Culturas cadastradas ({len(culturas)})")
        if not culturas:
            st.info("Nenhuma cultura cadastrada ainda. Use o formulário ao lado para começar.")
        else:
            for c in culturas:
                titulo = f"#{c['id']}  ·  {c['tipo_cultura'].capitalize()}  ·  {c['area_calculada_m2']:.1f} m²"
                with st.expander(titulo):
                    if c['forma_area'] == 'retangulo':
                        st.write(f"**Retângulo** — {c['dimensoes']['comprimento']:g} m × {c['dimensoes']['largura']:g} m")
                    else:
                        st.write(f"**Círculo** — raio {c['dimensoes']['raio']:g} m")
                    if c['insumos']:
                        for ins in c['insumos']:
                            st.write(f"🧪 {ins['produto']} — {ins['total_necessario']:.2f} unidades")
                    else:
                        st.caption("Sem insumos cadastrados.")
                    if st.button("Deletar", key=f"del_{c['id']}", use_container_width=True):
                        f1.deletar_cultura(c['id'])
                        st.rerun()

    st.markdown("---")
    st.markdown("#### Clima & Irrigação (Open-Meteo)")
    st.caption("Previsão meteorológica real cruzada com a umidade do solo para recomendar irrigação.")

    cidade = st.selectbox("Localização da fazenda", list(fclima.CIDADES))
    lat, lon = fclima.CIDADES[cidade]
    clima = previsao_clima(lat, lon)

    if clima.get('erro'):
        st.warning(clima['erro'])
    else:
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("🌡️ Temperatura",   f"{clima['temperatura'] or 0:.1f}°C")
        pc2.metric("💧 Umidade do ar",  f"{clima['umidade_ar'] or 0:.0f}%")
        pc3.metric("🌧️ Chuva agora",    f"{clima['chuva_agora'] or 0:.1f} mm")

        datas = clima.get('datas') or []
        if datas:
            st.markdown("**Previsão dos próximos dias**")
            for col, data, chuva, tmax, tmin in zip(
                st.columns(len(datas)),
                datas, clima['chuva_prevista'],
                clima['temp_max'], clima['temp_min'],
            ):
                col.metric(data, f"{chuva:.1f} mm", f"{tmin:.0f}–{tmax:.0f}°C", delta_color="off")

        nivel, msg = fclima.recomendar_irrigacao(clima, leitura_atual['umidade'])
        if nivel == 'irrigar':
            st.warning(f"🚿 {msg}")
        elif nivel == 'adiar':
            st.info(f"⏸️ {msg}")
        else:
            st.success(f"✅ {msg}")

    st.markdown("---")
    with st.expander("📊 Análise Estatística em R (Fase 1)"):
        st.caption("Estatística descritiva e correlações geradas pelo script "
                   "`analise_r/analise_culturas.R` sobre o dataset agrícola.")
        saidas_r = ROOT / 'analise_r' / 'saidas'
        graficos = sorted(saidas_r.glob('*.png')) if saidas_r.exists() else []
        if graficos:
            for g in graficos:
                st.image(str(g), use_column_width=True)
            txt = saidas_r / 'estatisticas.txt'
            if txt.exists():
                st.code(txt.read_text(encoding='utf-8'), language='text')
        else:
            st.caption("Rode `Rscript analise_r/analise_culturas.R` para gerar os gráficos e estatísticas.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — FASE 2/3 SENSORES & BANCO
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("📡 Fase 2/3 — Sensores IoT e Banco de Dados")

    col_sensor, col_bd = st.columns(2, gap="large")

    with col_sensor:
        st.markdown("#### Estação ESP32 — leitura atual")
        st.caption("Dados simulados. Em produção, o ESP32 envia leituras automaticamente via Wi-Fi.")

        if st.button("🎲 Simular nova leitura", use_container_width=True):
            st.session_state.leitura_atual = f2.gerar_leitura_sensor()
            st.rerun()

        col_a, col_b = st.columns(2)
        col_a.metric("💧 Umidade do solo", f"{leitura_atual['umidade']:.1f}%")
        col_a.metric("🌡️ Temperatura",     f"{leitura_atual['temperatura']:.1f}°C")
        col_b.metric("⚗️ pH (via LDR)",     f"{leitura_atual['ph']:.2f}")
        col_b.metric("🚿 Bomba",            "Ligada 💧" if leitura_atual['bomba_ativa'] else "Desligada")

        npk_ok = lambda v: "🟢" if v else "🔴"
        st.write(
            f"**NPK** — N {npk_ok(leitura_atual['nivel_N'] > 80)} "
            f"({leitura_atual['nivel_N']:.0f} ppm)  ·  "
            f"P {npk_ok(leitura_atual['nivel_P'])}  ·  K {npk_ok(leitura_atual['nivel_K'])}"
        )

        if st.button("💾 Registrar leitura no banco", use_container_width=True, type="primary"):
            f3.inserir_leitura(leitura_atual)
            st.success("Leitura registrada no banco de dados.")
            st.rerun()

        st.markdown("#### Histórico — últimas 24h (simulado)")
        historico = f2.gerar_historico(n=50)

        fig, axes = plt.subplots(1, 2, figsize=(10, 3))
        axes[0].plot(historico['timestamp'], historico['umidade'], color='steelblue', linewidth=1.5)
        axes[0].axhline(y=40, color='red', linestyle='--', alpha=0.7, label='Threshold irrigação')
        axes[0].set_title("Umidade do Solo (%)")
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].legend(fontsize=7)

        axes[1].plot(historico['timestamp'], historico['ph'], color='green', linewidth=1.5)
        axes[1].axhline(y=5.5, color='orange', linestyle='--', alpha=0.7, label='pH mín (5.5)')
        axes[1].axhline(y=7.5, color='orange', linestyle='--', alpha=0.7, label='pH máx (7.5)')
        axes[1].set_title("pH do Solo")
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].legend(fontsize=7)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col_bd:
        st.markdown("#### Banco de dados (SQLite)")
        st.caption("Equivalente ao Oracle SQL Developer da Fase 3.")

        stats = f3.estatisticas_sql()
        if stats.get('total', 0) > 0:
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Total de registros", int(stats['total']))
            col_s1.metric("Umidade média",      f"{stats.get('avg_umidade', 0):.1f}%")
            col_s2.metric("pH máximo",          f"{stats.get('max_ph', 0):.2f}")
            col_s2.metric("pH mínimo",          f"{stats.get('min_ph', 0):.2f}")
        else:
            st.info("Banco vazio. Clique em 'Registrar leitura' para começar.")

        st.markdown("**Últimas leituras**")
        df_bd = f3.consultar_ultimas(10)
        if not df_bd.empty:
            st.dataframe(df_bd, use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhuma leitura registrada ainda.")

        with st.expander("🔧 Ver query SQL de estatísticas"):
            st.code(
                """SELECT AVG(umidade)     AS avg_umidade,
       MAX(ph)          AS max_ph,
       MIN(ph)          AS min_ph,
       AVG(temperatura) AS avg_temp,
       COUNT(*)         AS total
FROM LEITURAS_SENSOR;""",
                language="sql",
            )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — FASE 4/5 MACHINE LEARNING
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("🤖 Fase 4/5 — Machine Learning e Cloud Computing")

    try:
        df    = pd.read_csv(CAMINHO_DADOS)
        model = joblib.load(CAMINHO_MODELO)

        features_cols = ['Umidade_Solo', 'pH_Solo', 'Temperatura_Ambiente', 'Nivel_N', 'Historico_Irrigacao_mm']

        col_ctrl, col_res = st.columns([1, 1.4], gap="large")

        with col_ctrl:
            st.markdown("#### Parâmetros de cultivo")
            umidade        = st.slider("Umidade do solo (%)",          float(df['Umidade_Solo'].min()),         float(df['Umidade_Solo'].max()),         55.0)
            ph             = st.slider("pH do solo",                   float(df['pH_Solo'].min()),              float(df['pH_Solo'].max()),              6.5, 0.1)
            temp           = st.slider("Temperatura (°C)",             float(df['Temperatura_Ambiente'].min()), float(df['Temperatura_Ambiente'].max()), 25.0)
            nitrogenio     = st.slider("Nitrogênio (ppm)",             float(df['Nivel_N'].min()),              float(df['Nivel_N'].max()),              150.0)
            irrigacao_hist = st.slider("Irrigação histórica (mm/sem)", float(df['Historico_Irrigacao_mm'].min()), float(df['Historico_Irrigacao_mm'].max()), 20.0)

        dados_entrada = pd.DataFrame(
            [[umidade, ph, temp, nitrogenio, irrigacao_hist]],
            columns=features_cols,
        )
        previsao = model.predict(dados_entrada)[0]

        y_true     = df['Produtividade_Esperada']
        y_pred_all = model.predict(df[features_cols])
        r2  = r2_score(y_true, y_pred_all)
        mae = mean_absolute_error(y_true, y_pred_all)

        with col_res:
            st.markdown("#### Previsão de produtividade")
            m1, m2 = st.columns(2)
            m1.metric("Rendimento previsto", f"{previsao:.0f} kg/ha")
            m2.metric("Algoritmo",           "Random Forest")
            m3, m4 = st.columns(2)
            m3.metric("R² do modelo", f"{r2:.4f}")
            m4.metric("MAE",          f"{mae:.1f} kg/ha")

            checagens = [
                ("Umidade do solo", umidade,    IDEAIS['Umidade_Solo'], "%",
                 "aumentar a irrigação",              "reduzir a irrigação e melhorar a drenagem"),
                ("pH do solo",      ph,         IDEAIS['pH_Solo'],      "",
                 "aplicar calcário para elevar o pH", "aplicar enxofre para reduzir o pH"),
                ("Nitrogênio",      nitrogenio, IDEAIS['Nivel_N'],      " ppm",
                 "aplicar fertilizante nitrogenado",  "reduzir a adubação nitrogenada"),
            ]
            recomendacoes = []
            for nome, valor, (lo, hi), un, acao_baixo, acao_alto in checagens:
                if valor < lo:
                    recomendacoes.append(f"⬇️ **{nome}** em {valor:g}{un} (ideal {lo:g}–{hi:g}{un}) → {acao_baixo}.")
                elif valor > hi:
                    recomendacoes.append(f"⬆️ **{nome}** em {valor:g}{un} (ideal {lo:g}–{hi:g}{un}) → {acao_alto}.")

            if previsao < LIMIAR_PRODUTIVIDADE_CRITICO:
                st.error(f"🚨 Rendimento crítico ({previsao:.0f} kg/ha). Corrija os pontos abaixo.")
            elif previsao < 5000:
                st.warning(f"⚠️ Rendimento abaixo do ideal ({previsao:.0f} kg/ha). Ajustes recomendados.")
            else:
                st.success(f"✅ Bom rendimento previsto ({previsao:.0f} kg/ha).")

            if recomendacoes:
                for rec in recomendacoes:
                    st.markdown(f"- {rec}")
            else:
                st.caption("Todos os parâmetros estão dentro da faixa ideal — manter o manejo atual.")

        st.markdown("---")
        fig, ax = plt.subplots(1, 2, figsize=(14, 5))

        corr_df = df[features_cols + ['Produtividade_Esperada']].corr()
        sns.heatmap(corr_df, annot=True, cmap='coolwarm', fmt=".2f", ax=ax[0])
        ax[0].set_title("Correlação entre variáveis")

        ax[1].scatter(df['Umidade_Solo'], df['Produtividade_Esperada'], alpha=0.3, label='Histórico')
        ax[1].scatter(umidade, previsao, color='red', s=200, marker='X', zorder=5, label='Sua simulação')
        ax[1].axvspan(IDEAIS['Umidade_Solo'][0], IDEAIS['Umidade_Solo'][1], color='green', alpha=0.1, label='Faixa ideal')
        ax[1].set_xlabel("Umidade do Solo (%)")
        ax[1].set_ylabel("Produtividade (kg/ha)")
        ax[1].legend()
        ax[1].set_title("Sua posição vs. histórico")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        with st.expander("☁️ Fase 5 — Cloud Computing AWS (análise de custos)"):
            st.markdown("""
Análise comparativa de custos AWS realizada na Fase 5:
- **Região São Paulo (BR):** ~USD 0.096/hora (t3.micro)
- **Região Virgínia Norte (EUA):** ~USD 0.0116/hora
- **Decisão:** São Paulo — menor latência + conformidade LGPD para dados de sensores agrícolas

O serviço de alertas SNS usa a infraestrutura AWS para notificar funcionários da fazenda por e-mail/SMS.
""")

    except Exception as e:
        st.error(f"Erro ao carregar modelo ML: {e}")
        st.info("Execute: `python models/gerar_dados.py && python models/train_model.py`")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — FASE 6 VISÃO COMPUTACIONAL
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("👁️ Fase 6 — Visão Computacional para Saúde do Cafezal")
    st.caption("Modelo YOLOv8 de classificação treinado para identificar doenças e pragas na folha de café.")

    col_upload, col_resultado = st.columns(2, gap="large")

    with col_upload:
        st.markdown("#### Analisar imagem")
        fonte = st.radio("Fonte da imagem:", ["Upload", "Imagem de exemplo"], horizontal=True)

        img_bytes = None

        if fonte == "Upload":
            uploaded = st.file_uploader("Selecione uma foto da folha de café", type=["jpg", "jpeg", "png"])
            if uploaded:
                img_bytes = uploaded.read()
        else:
            teste_dir = ROOT / 'data' / 'fase6_cafe' / 'test'
            base = teste_dir if teste_dir.exists() else ROOT / 'data' / 'fase6_amostras'
            amostras = sorted(base.glob("**/*.jpg"))[:300] + sorted(base.glob("**/*.png"))[:300]
            if amostras:
                rotulos = {f"{a.parent.name}/{a.name}": a for a in amostras}
                escolha = st.selectbox("Escolha uma imagem:", list(rotulos))
                try:
                    img_bytes = rotulos[escolha].read_bytes()
                except OSError as e:
                    st.error(f"Não foi possível abrir a imagem: {e}")
            else:
                st.warning("Nenhuma imagem de exemplo encontrada.")

        if img_bytes:
            img_pil = PILImage.open(io.BytesIO(img_bytes))
            st.image(img_pil, caption="Imagem selecionada", use_column_width=True)

    with col_resultado:
        if not img_bytes:
            st.info("Selecione ou carregue uma imagem para analisar.")
        else:
            st.markdown("#### Resultado da análise")
            try:
                resultado = f6.analisar_imagem(img_bytes)
            except FileNotFoundError:
                st.error("Modelo ainda não treinado. Rode `python train_fase6.py` "
                         "para gerar `models/fase6_cafe.pt`.")
                resultado = None

            if resultado:
                cor    = resultado['cor_card']
                status = resultado['status']
                msg    = f"**{status}** — confiança {resultado['confianca']*100:.1f}%"

                if cor == 'green':
                    st.success(msg)
                elif cor == 'orange':
                    st.warning(msg)
                elif cor == 'red':
                    st.error(msg)
                else:
                    st.info(msg)

                st.markdown("**Distribuição das classes:**")
                for nome, p in sorted(resultado['probabilidades'].items(),
                                      key=lambda x: x[1], reverse=True):
                    st.progress(p, text=f"{nome}: {p*100:.1f}%")

                st.markdown(f"**Ação recomendada:** {resultado['acao_recomendada']}")

                if not resultado['saudavel']:
                    if st.button("📧 Enviar alerta visual via AWS SNS", use_container_width=True):
                        ok, msg_aws = aws.enviar_alerta(
                            f"VISÃO COMPUTACIONAL — {status}",
                            f"Classe: {resultado['classe']} (confiança {resultado['confianca']*100:.1f}%)",
                            resultado['acao_recomendada'],
                        )
                        st.success(msg_aws) if ok else st.error(msg_aws)

    st.markdown("---")
    with st.expander("🔧 Por baixo dos panos — modelo e treino"):
        st.markdown("""
**Arquitetura:** YOLOv8-cls (classificação por transfer learning a partir do `yolov8n-cls.pt`).
**Dataset:** [coffee-leaf-diseases](https://huggingface.co/datasets/brainer-fp66/coffee-leaf-diseases) — 2.164 imagens de folha de café, 5 classes (saudável, ferrugem, bicho-mineiro, Phoma, ácaro-vermelho).
**Treino:** `python train_fase6.py` — split train/val/test já definido pelo dataset.

Continuidade da Fase 6: o mesmo pipeline de transfer learning com YOLO, agora aplicado à classificação da saúde real do cafezal (doenças e pragas).
""")
        metrics_dir = ROOT / 'models' / 'fase6_metrics'
        res_png = metrics_dir / 'results.png'
        cm_png  = metrics_dir / 'confusion_matrix.png'
        if res_png.exists():
            st.image(str(res_png), caption="Curvas de treino (histórico real)")
        if cm_png.exists():
            st.image(str(cm_png), caption="Matriz de confusão (validação)")
        if not res_png.exists():
            st.caption("As métricas aparecerão aqui após rodar o treino.")
