"""
Dashboard Macroeconómico — Cabo Verde
Streamlit port of the original HTML dashboard, powered by the real CSV.

Run:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ───────────────────────── 1. CONFIG ─────────────────────────
st.set_page_config(
    page_title="Cabo Verde · Indicadores Macroeconómicos",
    page_icon="📈",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "cabo_verde_indicadores_limpo.csv"

# Column names in the CSV
UNEMP, INFL, GDP, REMIT = "Desemprego (%)", "Inflação (%)", "PIB per capita (US$)", "Remessas (% PIB)"
INDICATORS = [UNEMP, INFL, GDP, REMIT]

# Colour palette (taken from the original Tailwind config)
C = dict(primary="#b4c5ff", blue="#2563eb", cyan="#4cd7f6", green="#4edea3",
         red="#ffb4ab", card="#131b2e", card2="#171f33", muted="#c3c6d7", grid="#434655")
COLORS = {UNEMP: C["blue"], INFL: C["red"], GDP: C["green"], REMIT: C["cyan"]}

PAGES = ["Visão Geral & Indicadores", "Análise de Correlação", "Séries Temporais"]

st.markdown(f"""
<style>
  .block-container {{ padding-top: 2rem; max-width: 1500px; }}
  .kpi {{ background:{C['card']}; border-radius:12px; padding:1.1rem 1.3rem; height:100%;
          box-shadow:0 2px 8px rgba(0,0,0,.35); }}
  .kpi .label {{ font-size:.72rem; letter-spacing:.08em; text-transform:uppercase;
                 color:{C['muted']}; font-weight:600; }}
  .kpi .value {{ font-size:2rem; font-weight:700; line-height:1.2; }}
  .kpi .badge {{ font-size:.75rem; font-weight:600; margin-left:.5rem; }}
  .kpi .note  {{ font-size:.78rem; color:{C['muted']}; }}
  .up {{ color:{C['green']}; }} .down {{ color:{C['red']}; }} .flat {{ color:{C['cyan']}; }}
  .tag {{ font-size:.72rem; letter-spacing:.1em; text-transform:uppercase;
          color:{C['cyan']}; font-weight:600; }}
  .insight {{ background:{C['card2']}; border-radius:12px; padding:1rem 1.2rem;
              font-size:.9rem; margin-top:.5rem; }}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── 2. DATA ─────────────────────────
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).sort_values("ano").reset_index(drop=True)
    return df


def last_valid(df: pd.DataFrame, col: str):
    """Latest non-null value, its year, and the change vs the previous valid value."""
    s = df.dropna(subset=[col])
    if s.empty:
        return None, None, None
    cur = s.iloc[-1]
    delta = cur[col] - s.iloc[-2][col] if len(s) > 1 else None
    return cur[col], int(cur["ano"]), delta


def pct_change_last(df: pd.DataFrame, col: str):
    s = df.dropna(subset=[col])
    if len(s) < 2:
        return None
    return (s.iloc[-1][col] / s.iloc[-2][col] - 1) * 100


def fmt(v, suffix="%", dec=1, sign=False):
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:+,.{dec}f}" if sign else f"{v:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",") + suffix


# ───────────────────────── 3. UI HELPERS ─────────────────────────
def style_fig(fig: go.Figure, height=360) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["muted"]), hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0),
    )
    fig.update_xaxes(gridcolor=C["grid"], showgrid=False)
    fig.update_yaxes(gridcolor="rgba(67,70,85,.35)")
    return fig


def sparkline(values, color) -> go.Figure:
    fig = go.Figure(go.Scatter(y=values, mode="lines", line=dict(color=color, width=2.5)))
    fig.add_trace(go.Scatter(x=[len(values) - 1], y=[values[-1]], mode="markers",
                             marker=dict(color=color, size=8)))
    fig.update_layout(height=50, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def kpi_card(col, label, value, badge, badge_cls, note, series, color):
    with col:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">{label}</div>
          <div><span class="value">{value}</span>
               <span class="badge {badge_cls}">{badge}</span></div>
          <div class="note">{note}</div>
        </div>""", unsafe_allow_html=True)
        if len(series) > 1:
            st.plotly_chart(sparkline(series, color), width="stretch",
                            config={"displayModeBar": False}, key=f"spark_{label}")


def section(tag, title):
    st.markdown(f"<div class='tag'>{tag}</div>", unsafe_allow_html=True)
    st.subheader(title)


def corr_text(r):
    a = abs(r)
    strength = "muito fraca" if a < .2 else "fraca" if a < .4 else "moderada" if a < .6 \
        else "forte" if a < .8 else "muito forte"
    return f"{'negativa' if r < 0 else 'positiva'} {strength}"


# ───────────────────────── 4. SIDEBAR ─────────────────────────
df_all = load_data(DATA_PATH)
y_min, y_max = int(df_all["ano"].min()), int(df_all["ano"].max())

with st.sidebar:
    st.markdown("### 📈 Cabo Verde")
    st.caption("Apresentação Macroeconómica & Indicadores")
    page = st.radio("Navegação", PAGES, label_visibility="collapsed")
    st.divider()

    preset = st.radio("Janela temporal", ["5A", "10A", "20A", "Tudo"], index=3, horizontal=True)
    span = {"5A": 5, "10A": 10, "20A": 20, "Tudo": y_max - y_min}[preset]
    default_start = max(y_min, y_max - span)
    # key depends on the preset so that changing the preset resets the slider
    year_range = st.slider("Intervalo cronológico", y_min, y_max,
                           (default_start, y_max), key=f"yr_{preset}")
    st.divider()
    st.download_button("⬇️ Exportar dados (CSV)",
                       df_all.to_csv(index=False).encode("utf-8"),
                       "cabo_verde_indicadores.csv", "text/csv", width="stretch")
    st.caption(f"Dados consolidados ({y_min} — {y_max}) · {len(df_all)} observações anuais")

df = df_all[df_all["ano"].between(*year_range)].reset_index(drop=True)
if df.empty:
    st.warning("Sem dados para o intervalo selecionado.")
    st.stop()

st.title(page)
st.caption(f"🟢 Intervalo selecionado: **{year_range[0]} — {year_range[1]}**")


# ───────────────────────── 5. PAGE: VISÃO GERAL ─────────────────────────
def page_overview():
    # ---- KPI deck ----
    u, u_y, u_d = last_valid(df, UNEMP)
    i, i_y, i_d = last_valid(df, INFL)
    g, g_y, _ = last_valid(df, GDP)
    g_pct = pct_change_last(df, GDP)
    r, r_y, r_d = last_valid(df, REMIT)

    def cls(delta, good_when_down=False):
        if delta is None or abs(delta) < 1e-9:
            return "flat"
        return ("down" if delta > 0 else "up") if good_when_down else ("up" if delta > 0 else "down")

    def arrow(d):
        return "—" if d is None else ("▲" if d > 0 else "▼")

    k = st.columns(4)
    kpi_card(k[0], "Taxa de Desemprego", fmt(u), f"{arrow(u_d)} {fmt(u_d, ' p.p.', sign=True)}",
             cls(u_d, True), f"Último dado: {u_y}", df[UNEMP].dropna().tolist(), C["green"])
    kpi_card(k[1], "Remessas / % do PIB", fmt(r), f"{arrow(r_d)} {fmt(r_d, ' p.p.', sign=True)}",
             cls(r_d), f"Último dado: {r_y}", df[REMIT].dropna().tolist(), C["cyan"])
    kpi_card(k[2], "Inflação (IPC)", fmt(i), f"{arrow(i_d)} {fmt(i_d, ' p.p.', sign=True)}",
             cls(i_d, True), f"Último dado: {i_y}", df[INFL].dropna().tolist(), C["red"])
    kpi_card(k[3], "PIB per Capita", fmt(g, " US$", 0), f"{arrow(g_pct)} {fmt(g_pct, '%', sign=True)}",
             cls(g_pct), f"Último dado: {g_y}", df[GDP].dropna().tolist(), C["green"])

    st.write("")
    left, right = st.columns([5, 7], gap="large")

    # ---- Unemployment history ----
    with left:
        section("Trajetória estrutural", "Evolução histórica do desemprego (%)")
        d = df.dropna(subset=[UNEMP])
        if d.empty:
            st.info("Sem dados de desemprego neste intervalo.")
        else:
            fig = go.Figure(go.Scatter(x=d["ano"], y=d[UNEMP], mode="lines+markers",
                                       line=dict(color=C["primary"], width=3),
                                       fill="tozeroy", fillcolor="rgba(180,197,255,.12)",
                                       name="Desemprego"))
            hi, lo = d.loc[d[UNEMP].idxmax()], d.loc[d[UNEMP].idxmin()]
            fig.add_trace(go.Scatter(x=[hi["ano"]], y=[hi[UNEMP]], mode="markers+text",
                                     marker=dict(color=C["red"], size=11),
                                     text=[f"Pico: {fmt(hi[UNEMP])} ({int(hi['ano'])})"],
                                     textposition="top center", showlegend=False))
            fig.add_trace(go.Scatter(x=[lo["ano"]], y=[lo[UNEMP]], mode="markers+text",
                                     marker=dict(color=C["green"], size=11),
                                     text=[f"Mínimo: {fmt(lo[UNEMP])} ({int(lo['ano'])})"],
                                     textposition="bottom center", showlegend=False))
            fig.update_yaxes(range=[max(0, d[UNEMP].min() - 2), d[UNEMP].max() + 2], ticksuffix="%")
            st.plotly_chart(style_fig(fig, 340), width="stretch")
            st.markdown(f"<div class='insight'>✅ Variação entre o pico ({int(hi['ano'])}) e o último dado "
                        f"({int(d.iloc[-1]['ano'])}): <b>{fmt(d.iloc[-1][UNEMP] - hi[UNEMP], ' p.p.', sign=True)}</b>."
                        f"</div>", unsafe_allow_html=True)

    # ---- Unemployment vs remittances dual axis ----
    with right:
        section("Análise de transmissão macro", "Desemprego vs. remessas (% PIB)")
        d = df.dropna(subset=[UNEMP, REMIT])
        if len(d) < 3:
            st.info("Dados insuficientes neste intervalo.")
        else:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=d["ano"], y=d[REMIT], name="Remessas (% PIB)",
                                 marker_color="rgba(76,215,246,.55)"), secondary_y=True)
            fig.add_trace(go.Scatter(x=d["ano"], y=d[UNEMP], name="Desemprego (%)",
                                     line=dict(color=C["blue"], width=4)), secondary_y=False)
            fig.update_yaxes(title_text="Desemprego (%)", secondary_y=False, ticksuffix="%")
            fig.update_yaxes(title_text="Remessas (% PIB)", secondary_y=True, ticksuffix="%",
                             showgrid=False)
            st.plotly_chart(style_fig(fig, 340), width="stretch")
            rho = d[UNEMP].corr(d[REMIT])
            st.markdown(f"<div class='insight'>🧠 <b>Correlação {corr_text(rho)} ({fmt(rho, '', 2)})</b> "
                        f"entre desemprego e remessas em {len(d)} anos com dados em ambas as séries "
                        f"({int(d['ano'].min())}–{int(d['ano'].max())}).</div>", unsafe_allow_html=True)

    # ---- Comparison table by decade ----
    st.write("")
    section("Desagregação temporal & comparativo", "Métricas médias por década")
    t = df_all.copy()
    t["Década"] = (t["ano"] // 10 * 10).astype(str) + "s"
    tbl = t.groupby("Década")[INDICATORS].mean().round(2)
    st.dataframe(
        tbl.style.format("{:.2f}", na_rep="—")
           .background_gradient(cmap="Blues", axis=0),
        width="stretch",
    )
    st.caption("Médias anuais por década sobre a série completa (independente do filtro de anos).")


# ───────────────────────── 6. PAGE: CORRELAÇÃO ─────────────────────────
def page_correlation():
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        x_var = st.selectbox("Variável X", INDICATORS, index=3)
        y_var = st.selectbox("Variável Y", INDICATORS, index=0)
        colour_by_year = st.toggle("Colorir por ano", value=True)

    d = df.dropna(subset=[x_var, y_var])
    if x_var == y_var:
        st.info("Escolha duas variáveis diferentes.")
    elif len(d) < 3:
        st.warning("Dados insuficientes no intervalo selecionado (mínimo 3 anos com ambas as séries).")
    else:
        rho = d[x_var].corr(d[y_var])
        slope, intercept = np.polyfit(d[x_var], d[y_var], 1)
        xs = np.linspace(d[x_var].min(), d[x_var].max(), 50)
        with c1:
            st.metric("Correlação de Pearson", fmt(rho, "", 2))
            st.metric("Observações (anos)", len(d))
            st.metric("Inclinação da regressão", fmt(slope, "", 3))
        with c2:
            fig = go.Figure(go.Scatter(
                x=d[x_var], y=d[y_var], mode="markers+text", text=d["ano"].astype(int),
                textposition="top center", textfont=dict(size=9),
                marker=dict(size=10, color=d["ano"] if colour_by_year else C["primary"],
                            colorscale="Viridis", showscale=colour_by_year,
                            colorbar=dict(title="Ano") if colour_by_year else None),
                name="Anos"))
            fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines",
                                     line=dict(color=C["red"], dash="dash"), name="Regressão linear"))
            fig.update_layout(xaxis_title=x_var, yaxis_title=y_var, hovermode="closest")
            st.plotly_chart(style_fig(fig, 420), width="stretch")
        st.markdown(f"<div class='insight'>🧠 Correlação <b>{corr_text(rho)} ({fmt(rho, '', 2)})</b> "
                    f"entre <i>{x_var}</i> e <i>{y_var}</i>. Correlação não implica causalidade — "
                    f"com poucas observações anuais, interprete com cautela.</div>", unsafe_allow_html=True)

    st.write("")
    section("Visão global", "Matriz de correlação")
    m = df[INDICATORS].corr()
    fig = go.Figure(go.Heatmap(z=m.values, x=m.columns, y=m.columns, zmin=-1, zmax=1,
                               colorscale="RdBu", text=m.round(2).values, texttemplate="%{text}",
                               colorbar=dict(title="ρ")))
    fig.update_layout(hovermode="closest")
    st.plotly_chart(style_fig(fig, 420), width="stretch")


# ───────────────────────── 7. PAGE: SÉRIES TEMPORAIS ─────────────────────────
def page_timeseries():
    c1, c2, c3 = st.columns([3, 1, 1])
    chosen = c1.multiselect("Indicadores", INDICATORS, default=[UNEMP, REMIT])
    normalize = c2.toggle("Base 100", help="Normaliza cada série para 100 no primeiro valor disponível")
    ma = c3.number_input("Média móvel (anos)", 1, 10, 1)

    if not chosen:
        st.info("Selecione pelo menos um indicador.")
        return

    fig = go.Figure()
    for col in chosen:
        s = df.set_index("ano")[col].dropna()
        if s.empty:
            continue
        if ma > 1:
            s = s.rolling(ma, min_periods=1).mean()
        if normalize:
            s = s / s.iloc[0] * 100
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=col, mode="lines+markers",
                                 line=dict(color=COLORS[col], width=3)))
    fig.update_xaxes(dtick=2 if len(df) > 15 else 1)
    st.plotly_chart(style_fig(fig, 460), width="stretch")
    if not normalize and len(chosen) > 1:
        st.caption("⚠️ Séries com escalas diferentes no mesmo eixo — use “Base 100” para comparar variações.")

    section("Estatísticas", "Resumo do intervalo selecionado")
    st.dataframe(df[chosen].describe().T.round(2), width="stretch")
    with st.expander("Ver dados brutos"):
        st.dataframe(df, width="stretch", hide_index=True)


# ───────────────────────── 8. ROUTER ─────────────────────────
{PAGES[0]: page_overview, PAGES[1]: page_correlation, PAGES[2]: page_timeseries}[page]()

st.divider()
st.caption("Fonte: indicadores macroeconómicos de Cabo Verde (ficheiro CSV ) · Dashboard em Streamlit")
