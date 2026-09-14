import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="SMBMARK - 自動車部品 貿易インテリジェンス",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====================================================================
# デザイントークン
# 題材（自動車部品・財務省貿易統計）から発想：精密機械の設計図（ブループリント）
# をベースに、機械部品の素材である真鍮・鋼のアクセントを重ねた
# 「工業レポート」のトーン。経営者が意思決定資料として開きたくなる、
# 落ち着きと信頼感を優先したダークテーマ。
# ====================================================================
COLORS = {
    "bg": "#12161D",
    "panel": "#1B212B",
    "panel2": "#212836",
    "grid": "#232B36",
    "border": "#2B3646",
    "text": "#E7EAEE",
    "muted": "#8D97A6",
    "brass": "#C69A4E",
    "brass_dark": "#9C7736",
    "steel": "#5C8AB5",
    "steel_light": "#8FB4D6",
    "rust": "#C96A50",
    "sage": "#6FA787",
}

# ------------------------------------------------------------------
# 品目マッピング（親コードレベル：時系列の連続性を保つため使用）
# 2025〜2026年の統計品目番号改正により、8708.30 / 8708.50 / 8708.70 / 8708.99 は
# 旧・単一コード（-000等）から新・細分コード（-010/-090等）へ移行している。
# 親コード（先頭7桁）でグルーピングすることで、改正前後を跨いだ連続トレンドを維持する。
# ------------------------------------------------------------------
PARENT_NAME = {
    "8708.10": "バンパー及びその部分品",
    "8708.21": "シートベルト",
    "8708.22": "フロントガラス等の安全ガラス部品",
    "8708.29": "その他の車体部分品・附属品",
    "8708.30": "ブレーキ、サーボブレーキ及び部分品",
    "8708.40": "ギヤボックス及びその部分品",
    "8708.50": "駆動軸（ディファレンシャル付き）及び部分品",
    "8708.70": "車輪及びその部分品",
    "8708.80": "サスペンションシステム及び部分品",
    "8708.91": "ラジエーター及びその部分品",
    "8708.92": "消音器（マフラー）及び排気管",
    "8708.93": "クラッチ及びその部分品",
    "8708.94": "ステアリングホイール・コラム・ボックス",
    "8708.95": "安全エアバッグ及びその部分品",
    "8708.99": "その他の部分品",
}

# 細分コード（9桁）レベルの名称。※-010/-090は税関実行関税率表で確認済み。
# 8708.50の-010/-090は他コードと同一パターン（トラクター用／その他）と推定した仮名称のため要確認。
DETAIL_NAME = {
    "8708.30-010": "ブレーキライニング（取付済）",
    "8708.30-090": "その他のブレーキ・サーボブレーキ部分品",
    "8708.50-010": "トラクター用駆動軸部分品（推定・要確認）",
    "8708.50-090": "その他の駆動軸部分品（推定・要確認）",
    "8708.70-010": "トラクター用車輪部分品",
    "8708.70-090": "その他の車輪部分品",
    "8708.99-010": "トラクター用その他部分品",
    "8708.99-090": "その他の部分品",
    "8708.99-100": "その他の部分品（特定部品・旧区分）",
    "8708.99-900": "その他の部分品（その他・旧区分）",
}


@st.cache_data
def load_item_data():
    """統計品別表（HS8708 品目別、輸出入）を読み込み"""
    file_path = "03_統計品別表_統合_20260913.csv"
    df = pd.read_csv(file_path, encoding="cp932")
    df["品目"] = df["品目"].str.strip()
    df["暦年月"] = df["暦年月"].str.replace("'", "").str.strip()
    df["親品目"] = df["品目"].str.split("-").str[0]
    df["親品目名"] = df["親品目"].map(PARENT_NAME)
    df["細分名"] = df["品目"].map(DETAIL_NAME)
    df["当月金額"] = pd.to_numeric(df["当月金額"], errors="coerce")
    df["当月第２数量"] = pd.to_numeric(df["当月第２数量"], errors="coerce")
    return df


@st.cache_data
def load_country_data():
    """国別総額表（全品目・国別、参考情報用）を読み込み"""
    file_path = "国別総額表_統合_20260913.csv"
    df = pd.read_csv(file_path, encoding="cp932")
    df["当月輸出金額"] = pd.to_numeric(df["当月輸出金額"], errors="coerce")
    df["当月輸入金額"] = pd.to_numeric(df["当月輸入金額"], errors="coerce")
    return df


# ====================================================================
# スタイル注入
# ====================================================================
def inject_style():
    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700;900&display=swap');

        html {{ scroll-behavior: smooth; }}

        /* ベース背景：ブループリント風の極薄グリッド */
        [data-testid="stAppViewContainer"] {{
            background-color: {c['bg']};
            background-image:
                linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
            background-size: 42px 42px;
        }}
        [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

        .block-container {{
            max-width: 1280px;
            padding-top: 1.6rem;
            padding-bottom: 5rem;
        }}

        html, body, [class*="css"] {{
            font-family: 'Zen Kaku Gothic New', 'Noto Sans JP', sans-serif;
            color: {c['text']};
        }}

        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2 {{
            font-family: 'Shippori Mincho', serif;
            font-weight: 700;
            color: {c['text']};
        }}
        [data-testid="stMarkdownContainer"] h3 {{
            font-family: 'Zen Kaku Gothic New', sans-serif;
            font-weight: 700;
            font-size: 17px;
            color: {c['text']};
            letter-spacing: 0.01em;
            margin-top: 0.2rem;
        }}
        [data-testid="stCaptionContainer"] {{ color: {c['muted']}; }}

        /* サイドバー */
        [data-testid="stSidebar"] {{
            background-color: {c['panel']};
            border-right: 1px solid {c['border']};
        }}
        [data-testid="stSidebar"] * {{ color: {c['text']}; }}
        [data-testid="stSidebar"] label {{ color: {c['muted']} !important; font-size: 13px; }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: {c['bg']};
            border-color: {c['border']};
        }}
        .sidebar-brand {{
            font-family: 'Shippori Mincho', serif;
            font-size: 20px;
            font-weight: 700;
            color: {c['brass']};
            letter-spacing: 0.04em;
            padding-bottom: 2px;
        }}
        .sidebar-brand-sub {{
            font-size: 12px;
            color: {c['muted']};
            border-bottom: 1px solid {c['border']};
            padding-bottom: 16px;
            margin-bottom: 18px;
            line-height: 1.6;
        }}

        /* 区切り線 */
        .section-divider {{
            height: 1px;
            background: linear-gradient(90deg, {c['border']}, transparent);
            margin: 40px 0 32px 0;
        }}

        /* ヒーロー */
        .hero {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 32px;
            padding-bottom: 26px;
            border-bottom: 1px solid {c['border']};
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .hero-eyebrow {{
            font-size: 12.5px;
            color: {c['steel_light']};
            margin-bottom: 10px;
        }}
        .hero-title {{
            font-family: 'Shippori Mincho', serif;
            font-size: 32px;
            color: {c['text']};
            margin: 0 0 10px 0;
            line-height: 1.4;
        }}
        .hero-sub {{
            font-size: 13.5px;
            color: {c['muted']};
            max-width: 460px;
            line-height: 1.8;
        }}
        .hero-stat {{ text-align: right; min-width: 220px; }}
        .hero-stat-label {{ font-size: 12.5px; color: {c['muted']}; margin-bottom: 8px; }}
        .hero-stat-value {{
            font-family: 'Shippori Mincho', serif;
            font-size: 40px;
            color: {c['brass']};
            line-height: 1;
        }}
        .hero-stat-delta {{ font-size: 13px; margin-top: 8px; }}
        .hero-stat-delta.up {{ color: {c['sage']}; }}
        .hero-stat-delta.down {{ color: {c['rust']}; }}
        .hero-stat-delta.flat {{ color: {c['muted']}; }}

        /* KPIカード */
        .kpi-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }}
        .kpi-card {{
            flex: 1;
            min-width: 220px;
            background: {c['panel']};
            border: 1px solid {c['border']};
            border-left: 3px solid {c['steel']};
            border-radius: 4px;
            padding: 18px 20px;
        }}
        .kpi-card.brass {{ border-left-color: {c['brass']}; }}
        .kpi-card.rust {{ border-left-color: {c['rust']}; }}
        .kpi-card.sage {{ border-left-color: {c['sage']}; }}
        .kpi-label {{ font-size: 12.5px; color: {c['muted']}; margin-bottom: 8px; }}
        .kpi-value {{
            font-family: 'Shippori Mincho', serif;
            font-size: 25px;
            color: {c['text']};
        }}
        .kpi-sub {{ font-size: 12px; color: {c['muted']}; margin-top: 6px; line-height: 1.6; }}

        /* チャートを囲むパネル */
        .chart-panel {{
            background: {c['panel']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 18px 20px 4px 20px;
            margin-bottom: 6px;
        }}

        /* アクション提言カード */
        .action-card {{
            background: {c['panel']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 20px 22px;
            height: 100%;
        }}
        .action-card .tag {{
            display: inline-block;
            font-size: 11.5px;
            color: {c['muted']};
            border: 1px solid {c['border']};
            border-radius: 3px;
            padding: 2px 8px;
            margin-bottom: 12px;
        }}
        .action-card h4 {{
            font-family: 'Zen Kaku Gothic New', sans-serif;
            font-weight: 700;
            font-size: 14.5px;
            color: {c['text']};
            margin: 0 0 8px 0;
        }}
        .action-card p {{
            font-size: 13px;
            color: {c['muted']};
            line-height: 1.75;
            margin: 0;
        }}
        .action-card.negotiate {{ border-left: 3px solid {c['brass']}; }}
        .action-card.risk {{ border-left: 3px solid {c['rust']}; }}
        .action-card.sales {{ border-left: 3px solid {c['sage']}; }}

        /* データフレーム */
        [data-testid="stDataFrame"] {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            overflow: hidden;
        }}

        /* CTAパネル */
        .cta-panel {{
            background: linear-gradient(135deg, {c['panel2']}, {c['panel']});
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 30px 34px;
        }}
        .cta-title {{
            font-family: 'Shippori Mincho', serif;
            font-size: 21px;
            color: {c['text']};
            margin-bottom: 8px;
        }}
        .cta-sub {{ font-size: 13.5px; color: {c['muted']}; line-height: 1.8; margin-bottom: 4px; }}

        [data-testid="stTextInput"] input {{
            background-color: {c['bg']};
            border: 1px solid {c['border']};
            color: {c['text']};
            border-radius: 4px;
        }}
        .stButton > button {{
            background: linear-gradient(135deg, {c['brass']}, {c['brass_dark']});
            color: #14171c;
            border: none;
            border-radius: 4px;
            font-weight: 700;
            padding: 0.55rem 1.6rem;
            font-family: 'Zen Kaku Gothic New', sans-serif;
        }}
        .stButton > button:hover {{ filter: brightness(1.08); }}

        [data-testid="stAlert"] {{
            background-color: {c['panel']};
            border: 1px solid {c['border']};
            color: {c['text']};
        }}

        /* 参考セクション */
        .ref-note {{ font-size: 12.5px; color: {c['muted']}; margin-top: 6px; line-height: 1.7; }}

        /* トップへ戻るボタン */
        .scroll-top-btn {{
            position: fixed;
            bottom: 34px;
            right: 34px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, {c['brass']}, {c['brass_dark']});
            color: #14171c;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            text-decoration: none;
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            z-index: 9999;
            opacity: 0.82;
            transition: opacity 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .scroll-top-btn:hover {{
            opacity: 1;
            transform: translateY(-4px);
            box-shadow: 0 8px 22px rgba(0,0,0,0.5);
        }}
        </style>
        <div id="top"></div>
        """,
        unsafe_allow_html=True,
    )


def divider():
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def apply_chart_theme(fig, height=360, title=None):
    c = COLORS
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Zen Kaku Gothic New, sans-serif", color=c["muted"], size=12.5),
        title=dict(text=title, font=dict(family="Shippori Mincho, serif", color=c["text"], size=16), x=0.01, xanchor="left"),
        margin=dict(l=10, r=10, t=44 if title else 14, b=10),
        height=height,
        hoverlabel=dict(bgcolor=c["panel2"], font_color=c["text"], bordercolor=c["border"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["muted"])),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=c["border"], tickfont=dict(color=c["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor=c["grid"], zeroline=False, tickfont=dict(color=c["muted"]))
    return fig


def kpi_card(label, value, sub="", tone="steel"):
    return f'<div class="kpi-card {tone}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>'


# ====================================================================
# アプリ本体
# ====================================================================
inject_style()

df = load_item_data()
country_df = load_country_data()

# --------------------------------------------------------------
# サイドバー：検索条件
# --------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">SMBMARK</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-brand-sub">自動車部品（HS 8708）貿易インテリジェンス<br>'
        "データソース：財務省貿易統計・日本銀行</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**分析条件**")
    item_options = ["全品目（全体概況）"] + sorted(df["親品目名"].dropna().unique().tolist())
    selected_item = st.selectbox("分析対象の品目", item_options, label_visibility="visible")
    show_detail = st.checkbox("細分コードごとの内訳を表示する", value=False)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    latest_available = df["暦年月"].max()
    st.caption(f"データ最終更新月：{latest_available}")
    st.caption("品目コードは統計品目番号改正の前後で親コード単位に統合し、時系列の連続性を保っています。")

if selected_item == "全品目（全体概況）":
    view_df = df.copy()
else:
    view_df = df[df["親品目名"] == selected_item].copy()

exp_df = view_df[view_df["輸出入"] == "輸出"].copy()
imp_df = view_df[view_df["輸出入"] == "輸入"].copy()

monthly_total = exp_df.groupby("暦年月")["当月金額"].sum().reset_index()

# --------------------------------------------------------------
# ヒーロー
# --------------------------------------------------------------
hero_value_html = "データなし"
hero_delta_html = ""
if not monthly_total.empty:
    latest_val = monthly_total["当月金額"].iloc[-1]
    hero_value_html = f"{latest_val:,.0f} <span style='font-size:16px;color:{COLORS['muted']}'>千円</span>"
    if len(monthly_total) >= 2:
        prev_val = monthly_total["当月金額"].iloc[-2]
        if prev_val != 0:
            hero_change = (latest_val / prev_val - 1) * 100
            tone = "up" if hero_change > 0 else ("down" if hero_change < 0 else "flat")
            arrow = "▲" if hero_change > 0 else ("▼" if hero_change < 0 else "―")
            hero_delta_html = (
                f'<div class="hero-stat-delta {tone}">{arrow} 前月比 {hero_change:+.1f}%</div>'
            )

st.markdown(
    f"""
    <div class="hero">
        <div>
            <div class="hero-eyebrow">Tier2 / Tier3 製造業のための貿易分析</div>
            <div class="hero-title">{selected_item}</div>
            <div class="hero-sub">財務省貿易統計をもとに、単価・輸入依存度・仕向地動向を
            一目で把握できるように整理しています。価格交渉や仕入れ判断の材料としてご活用ください。</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-label">直近月の輸出額（{monthly_total['暦年月'].iloc[-1] if not monthly_total.empty else '-'}）</div>
            <div class="hero-stat-value">{hero_value_html}</div>
            {hero_delta_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------
# 単価トレンド・輸入依存度（先に計算し、KPIとチャート両方で使う）
# --------------------------------------------------------------
change = None
price_df = exp_df.dropna(subset=["当月第２数量"])
price_df = price_df[price_df["当月第２数量"] > 0].copy()
price_df["単価（円/KG）"] = price_df["当月金額"] / price_df["当月第２数量"] * 1000
price_trend = price_df.groupby("暦年月")["単価（円/KG）"].mean().reset_index()

if not price_trend.empty:
    first_price = price_trend["単価（円/KG）"].iloc[0]
    if first_price != 0:
        change = (price_trend["単価（円/KG）"].iloc[-1] / first_price - 1) * 100

exp_m = exp_df.groupby("暦年月")["当月金額"].sum()
imp_m = imp_df.groupby("暦年月")["当月金額"].sum()
total_m = exp_m.add(imp_m, fill_value=0)
dep = (imp_m.reindex(total_m.index, fill_value=0) / total_m).reset_index()
dep.columns = ["暦年月", "輸入依存度"]
dep = dep[total_m.values > 0]

# --------------------------------------------------------------
# KPIストリップ
# --------------------------------------------------------------
kpi_html = '<div class="kpi-row">'
if not price_trend.empty and change is not None:
    kpi_html += kpi_card(
        "単価変化（期間累計）",
        f"{change:+.1f}%",
        f"{price_trend['暦年月'].iloc[0]} → {price_trend['暦年月'].iloc[-1]}",
        tone="brass",
    )
else:
    kpi_html += kpi_card("単価変化", "算出不可", "数量データが不足しています", tone="brass")

if not dep.empty:
    latest_dep_val = dep["輸入依存度"].iloc[-1]
    tone = "rust" if latest_dep_val > 0.5 else "steel"
    kpi_html += kpi_card(
        "輸入依存度（直近月）",
        f"{latest_dep_val:.1%}",
        f"{dep['暦年月'].iloc[-1]} 時点",
        tone=tone,
    )
else:
    kpi_html += kpi_card("輸入依存度", "算出不可", "輸出入データが不足しています", tone="rust")

if not monthly_total.empty:
    kpi_html += kpi_card(
        "対象期間の月平均輸出額",
        f"{monthly_total['当月金額'].mean():,.0f} 千円",
        f"{monthly_total['暦年月'].iloc[0]} 〜 {monthly_total['暦年月'].iloc[-1]}",
        tone="sage",
    )
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)

divider()

# --------------------------------------------------------------
# 1. 輸出額の推移
# --------------------------------------------------------------
st.markdown("### 輸出額の推移（千円）")
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
fig1 = px.line(monthly_total, x="暦年月", y="当月金額", markers=True)
fig1.update_traces(line_color=COLORS["brass"], marker=dict(color=COLORS["brass"], size=7))
fig1 = apply_chart_theme(fig1, height=340)
st.plotly_chart(fig1, width="stretch")
st.markdown("</div>", unsafe_allow_html=True)

divider()

# --------------------------------------------------------------
# 2 / 3. 単価トレンド・輸入依存度
# --------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 単価トレンド（輸出額 ÷ 数量）")
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    if not price_trend.empty:
        fig2 = px.line(price_trend, x="暦年月", y="単価（円/KG）", markers=True)
        fig2.update_traces(line_color=COLORS["steel_light"], marker=dict(color=COLORS["steel_light"], size=6))
        fig2 = apply_chart_theme(fig2, height=300)
        st.plotly_chart(fig2, width="stretch")
        if change is not None:
            st.caption(
                f"{price_trend['暦年月'].iloc[0]} → {price_trend['暦年月'].iloc[-1]} の単価変化：{change:+.1f}%"
            )
        else:
            st.caption("初月の単価データが0のため、変化率は算出できません。")
    else:
        st.info("数量データが不足しており、単価トレンドを算出できません。")
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown("### 輸入依存度の推移")
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    if not dep.empty:
        fig3 = px.line(dep, x="暦年月", y="輸入依存度", markers=True)
        fig3.update_traces(line_color=COLORS["rust"], marker=dict(color=COLORS["rust"], size=6))
        fig3.update_yaxes(tickformat=".0%")
        fig3 = apply_chart_theme(fig3, height=300)
        st.plotly_chart(fig3, width="stretch")
        st.caption(f"直近（{dep['暦年月'].iloc[-1]}）の輸入依存度：{dep['輸入依存度'].iloc[-1]:.1%}")
    else:
        st.info("輸出入データが不足しており、輸入依存度を算出できません。")
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------
# 4. 細分コード内訳（任意表示）
# --------------------------------------------------------------
if show_detail:
    divider()
    st.markdown("### 細分コードごとの内訳（直近月・輸出）")
    latest_month = df["暦年月"].max()
    detail_df = exp_df[
        (exp_df["暦年月"] == latest_month) & (exp_df["細分名"].notna())
    ][["品目", "細分名", "当月金額", "当月第２数量"]]
    if not detail_df.empty:
        st.dataframe(
            detail_df.rename(columns={"当月金額": "輸出額（千円）", "当月第２数量": "数量（KG）"}),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("選択した品目には、この月の細分コード内訳データがありません。")

divider()

# --------------------------------------------------------------
# 5. 来月のアクション提言
# --------------------------------------------------------------
st.markdown("### Tier2 / Tier3 製造業への、来月のアクション提言")
c1, c2, c3 = st.columns(3)

with c1:
    if not price_trend.empty and change is not None:
        if change > 0:
            body = f"単価が{change:+.1f}%動いています。単価転嫁の交渉データとして活用してください。"
        else:
            body = "単価が伸び悩んでいます。コスト削減や高付加価値化を検討してください。"
    else:
        body = "数量減・金額増の品目を中心に、単価転嫁の交渉データを準備してください。"
    st.markdown(
        f"""<div class="action-card negotiate">
            <div class="tag">価格交渉</div>
            <h4>価格交渉の打診</h4>
            <p>{body}</p>
        </div>""",
        unsafe_allow_html=True,
    )

with c2:
    if not dep.empty and dep["輸入依存度"].iloc[-1] > 0.5:
        body = f"輸入依存度が{dep['輸入依存度'].iloc[-1]:.0%}と高水準です。為替・供給網リスクに備えてください。"
        title = "仕入れ先の分散検討"
    else:
        body = "ギヤボックス関連の前年比動向に合わせ、プレス・加工ラインの稼働を調整してください。"
        title = "駆動系ラインの生産調整"
    st.markdown(
        f"""<div class="action-card risk">
            <div class="tag">供給リスク</div>
            <h4>{title}</h4>
            <p>{body}</p>
        </div>""",
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """<div class="action-card sales">
            <div class="tag">営業機会</div>
            <h4>熱・排気系パーツへの営業強化</h4>
            <p>伸び率が顕著なラジエーター・マフラー周辺の金型・加工案件を獲得しに行きましょう。</p>
        </div>""",
        unsafe_allow_html=True,
    )

divider()

# --------------------------------------------------------------
# 6. 主要輸出先国の景気動向（参考情報）
# --------------------------------------------------------------
st.markdown("### 参考｜主要輸出先国の貿易動向（全品目・8708限定ではありません）")
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
latest_c_month = int(country_df["年月"].max())
top_countries = (
    country_df[country_df["年月"] == latest_c_month]
    .nlargest(8, "当月輸出金額")[["国名", "当月輸出金額"]]
)
fig4 = px.bar(top_countries, x="国名", y="当月輸出金額")
fig4.update_traces(marker_color=COLORS["steel"])
fig4 = apply_chart_theme(fig4, height=320, title=f"{latest_c_month}　対主要国 輸出総額（全品目・千円）")
st.plotly_chart(fig4, width="stretch")
st.markdown(
    '<div class="ref-note">※このグラフは日本の貿易総額（全品目）であり、自動車部品（8708）に限定した数値ではありません。'
    "仕向地の景気動向を把握する参考情報としてご覧ください。</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

divider()

# --------------------------------------------------------------
# 7. リード獲得フォーム
# --------------------------------------------------------------
st.markdown('<div class="cta-panel">', unsafe_allow_html=True)
st.markdown('<div class="cta-title">有料詳細レポート・個別診断の事前登録</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="cta-sub">他業種のデータ閲覧や、自社工場に特化した分析レポートをご希望の方は下記よりお申し込みください。</div>',
    unsafe_allow_html=True,
)
email_col, btn_col = st.columns([3, 1])
with email_col:
    st.text_input("メールアドレス", label_visibility="collapsed", placeholder="メールアドレスを入力")
with btn_col:
    if st.button("事前登録する →", width="stretch"):
        st.success("ご登録ありがとうございます。順次ご案内いたします。")
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------
# トップへ戻るボタン（常設・フローティング）
# --------------------------------------------------------------
st.markdown('<a href="#top" class="scroll-top-btn" title="ページ上部に戻る">↑</a>', unsafe_allow_html=True)
