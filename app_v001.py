import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# ============================================================
# 基本設定
# ============================================================
st.set_page_config(
    page_title="SMBMARK - 自動車部品 貿易インテリジェンス",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "03_統計品別表_統合_20260913.csv"

# 品目コード（先頭7文字）→ 日本語表示名
# 輸入データのみ細分化されている 010/090 系のコードは、対応する親カテゴリに
# 集約して表示する（8708.99 は輸出側の -100/-900 も統合）。
ITEM_NAME_MAP = {
    "8708.10": "バンパー及びその部分品",
    "8708.21": "シートベルト",
    "8708.22": "フロントガラス等の安全ガラス部品",
    "8708.29": "その他の車体部分品・附属品",
    "8708.30": "ブレーキ、サーボブレーキ及び部分品",
    "8708.40": "ギヤボックス及びその部分品",
    "8708.50": "駆動軸（ディファレンシャル付き）",
    "8708.70": "車輪（ホイール）及びその部分品",
    "8708.80": "サスペンションシステム及び部分品",
    "8708.91": "ラジエーター及びその部分品",
    "8708.92": "消音器（マフラー）及び排気管",
    "8708.93": "クラッチ及びその部分品",
    "8708.94": "ステアリングホイール・コラム・ボックス",
    "8708.95": "安全エアバッグ及びその部分品",
    "8708.99": "その他の部分品（特定・その他）",
}


# ============================================================
# データ読み込み・前処理
# ============================================================
@st.cache_data
def load_data(path: Path, mtime: float) -> pd.DataFrame:
    """財務省貿易統計CSV（品目別表）を読み込み、分析用に整形する。

    mtime をキャッシュキーに含めることで、data/trade_items.csv を
    月次更新した際に古いキャッシュが残り続けるのを防ぐ。
    """
    df = pd.read_csv(path, encoding="cp932")

    # 品目コードを親カテゴリ単位（先頭7文字）に丸めて、輸入側だけ
    # 細分化されているコード（例: 8708.30-010）を親（8708.30）に集約する
    df["品目大分類"] = df["品目"].str.split("-").str[0]
    df["品目表示名"] = df["品目大分類"].map(ITEM_NAME_MAP)

    df["年"] = df["暦年月"].str.replace("'", "").str[:4].astype(int)
    df["月"] = df["暦年月"].str.replace("'", "").str[-2:].astype(int)
    df["年月日"] = pd.to_datetime(
        df["年"].astype(str) + "-" + df["月"].astype(str).str.zfill(2) + "-01"
    )

    agg = (
        df.groupby(
            ["品目大分類", "品目表示名", "輸出入", "年月日", "年", "月"], as_index=False
        ).agg(
            金額=("当月金額", "sum"),
            数量=("当月第２数量", "sum"),
        )
    )
    return agg


def to_oku(v: float) -> float:
    """千円 → 億円"""
    return v / 100_000


def pct_change_safe(new: float, old: float):
    if old == 0 or pd.isna(old) or pd.isna(new):
        return None
    return (new - old) / old * 100


# ============================================================
# データロード
# ============================================================
if not DATA_PATH.exists():
    st.error(
        f"データファイルが見つかりません: {DATA_PATH}\n"
        "data/trade_items.csv を配置してください。"
    )
    st.stop()

mtime = DATA_PATH.stat().st_mtime
data = load_data(DATA_PATH, mtime)

latest_date = data["年月日"].max()
prev_month_date = latest_date - pd.DateOffset(months=1)
prev_year_date = latest_date - pd.DateOffset(years=1)

items = sorted(data["品目表示名"].dropna().unique())

# ============================================================
# ヘッダー
# ============================================================
st.title("SMBMARK｜自動車部品 貿易インテリジェンス")
st.caption(
    f"財務省 貿易統計（HSコード 8708）に基づく月次動向・経営アクション　"
    f"｜ データ最終月: {latest_date.strftime('%Y年%m月')}"
)

# ============================================================
# 1. 全体サマリー（輸出・輸入・貿易収支）
# ============================================================
st.subheader("① 全体推移：輸出・輸入・貿易収支")

overview = (
    data.groupby(["年月日", "輸出入"], as_index=False)["金額"].sum()
    .pivot(index="年月日", columns="輸出入", values="金額")
    .fillna(0)
    .reset_index()
)
overview["収支"] = overview.get("輸出", 0) - overview.get("輸入", 0)

col_a, col_b, col_c = st.columns(3)
latest_row = overview[overview["年月日"] == latest_date].iloc[0]
prev_row = overview[overview["年月日"] == prev_month_date]
prev_year_row = overview[overview["年月日"] == prev_year_date]

exp_latest = latest_row.get("輸出", 0)
imp_latest = latest_row.get("輸入", 0)
bal_latest = latest_row.get("収支", 0)

exp_mom = pct_change_safe(exp_latest, prev_row["輸出"].iloc[0]) if not prev_row.empty else None
exp_yoy = pct_change_safe(exp_latest, prev_year_row["輸出"].iloc[0]) if not prev_year_row.empty else None

col_a.metric(
    "当月 輸出額",
    f"{to_oku(exp_latest):,.1f} 億円",
    f"前月比 {exp_mom:+.1f}%" if exp_mom is not None else None,
)
col_b.metric(
    "当月 輸入額",
    f"{to_oku(imp_latest):,.1f} 億円",
    (
        f"前月比 {pct_change_safe(imp_latest, prev_row['輸入'].iloc[0]):+.1f}%"
        if not prev_row.empty
        else None
    ),
)
col_c.metric(
    "貿易収支（輸出－輸入）",
    f"{to_oku(bal_latest):,.1f} 億円",
    f"前年同月比 {exp_yoy:+.1f}%（輸出）" if exp_yoy is not None else None,
)

fig_overview = go.Figure()
fig_overview.add_trace(
    go.Scatter(x=overview["年月日"], y=overview.get("輸出", 0), name="輸出額", mode="lines+markers")
)
fig_overview.add_trace(
    go.Scatter(x=overview["年月日"], y=overview.get("輸入", 0), name="輸入額", mode="lines+markers")
)
fig_overview.add_trace(
    go.Bar(x=overview["年月日"], y=overview["収支"], name="貿易収支", opacity=0.3)
)
fig_overview.update_layout(
    title="輸出額・輸入額・貿易収支の推移（千円）",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_overview, use_container_width=True)

st.markdown("---")

# ============================================================
# 2. 品目別ドリルダウン
# ============================================================
st.subheader("② 品目別ドリルダウン")

selected_item = st.selectbox("品目を選択してください", items, index=0)

item_df = data[data["品目表示名"] == selected_item]
item_pivot = (
    item_df.pivot_table(index="年月日", columns="輸出入", values="金額", fill_value=0)
    .reset_index()
)
item_pivot["収支"] = item_pivot.get("輸出", 0) - item_pivot.get("輸入", 0)

fig_item = go.Figure()
fig_item.add_trace(
    go.Scatter(x=item_pivot["年月日"], y=item_pivot.get("輸出", 0), name="輸出額", mode="lines+markers")
)
fig_item.add_trace(
    go.Scatter(x=item_pivot["年月日"], y=item_pivot.get("輸入", 0), name="輸入額", mode="lines+markers")
)
fig_item.update_layout(
    title=f"「{selected_item}」の輸出入推移（千円）",
    hovermode="x unified",
)
st.plotly_chart(fig_item, use_container_width=True)

st.markdown("---")

# ============================================================
# 3. 輸入急増アラート（競合圧力チェック）
# ============================================================
st.subheader("③ 輸入急増アラート（競合圧力チェック）")
st.caption("前年同月比で輸入が急増している品目＝海外製品との価格競争が強まっている可能性があります。")

import_latest = data[(data["輸出入"] == "輸入") & (data["年月日"] == latest_date)]
import_prev_year = data[(data["輸出入"] == "輸入") & (data["年月日"] == prev_year_date)]

import_compare = import_latest.merge(
    import_prev_year[["品目大分類", "金額"]],
    on="品目大分類",
    suffixes=("", "_前年"),
    how="left",
)
import_compare["前年比%"] = import_compare.apply(
    lambda r: pct_change_safe(r["金額"], r["金額_前年"]), axis=1
)
import_compare = import_compare.dropna(subset=["前年比%"]).sort_values("前年比%", ascending=False)

if not import_compare.empty:
    top_surge = import_compare.head(3)
    surge_cols = st.columns(len(top_surge)) if len(top_surge) > 0 else []
    for col, (_, row) in zip(surge_cols, top_surge.iterrows()):
        col.metric(
            row["品目表示名"],
            f"{to_oku(row['金額']):,.1f} 億円",
            f"前年比 {row['前年比%']:+.1f}%",
            delta_color="inverse",
        )
else:
    st.info("前年同月データが不足しているため、比較できません。")

st.markdown("---")

# ============================================================
# 4. 伸長・縮小ランキング
# ============================================================
st.subheader("④ 品目別 伸長・縮小ランキング（輸出額・前年同月比）")

export_latest = data[(data["輸出入"] == "輸出") & (data["年月日"] == latest_date)]
export_prev_year = data[(data["輸出入"] == "輸出") & (data["年月日"] == prev_year_date)]

export_compare = export_latest.merge(
    export_prev_year[["品目大分類", "金額"]],
    on="品目大分類",
    suffixes=("", "_前年"),
    how="left",
)
export_compare["前年比%"] = export_compare.apply(
    lambda r: pct_change_safe(r["金額"], r["金額_前年"]), axis=1
)
export_compare = export_compare.dropna(subset=["前年比%"]).sort_values("前年比%", ascending=False)

rank_col1, rank_col2 = st.columns(2)
with rank_col1:
    st.markdown("**伸びている品目 トップ3**")
    st.dataframe(
        export_compare.head(3)[["品目表示名", "金額", "前年比%"]]
        .rename(columns={"金額": "当月輸出額（千円）"})
        .style.format({"当月輸出額（千円）": "{:,.0f}", "前年比%": "{:+.1f}%"}),
        hide_index=True,
        use_container_width=True,
    )
with rank_col2:
    st.markdown("**減少している品目 ワースト3**")
    st.dataframe(
        export_compare.tail(3).sort_values("前年比%")[["品目表示名", "金額", "前年比%"]]
        .rename(columns={"金額": "当月輸出額（千円）"})
        .style.format({"当月輸出額（千円）": "{:,.0f}", "前年比%": "{:+.1f}%"}),
        hide_index=True,
        use_container_width=True,
    )

st.markdown("---")

# ============================================================
# 5. 季節性グラフ
# ============================================================
st.subheader("⑤ 季節性の確認（年ごとの月別推移比較）")

season_scope = st.radio(
    "対象範囲",
    ["全品目合計"] + items,
    horizontal=True,
    label_visibility="collapsed",
)
season_direction = st.radio("輸出／輸入", ["輸出", "輸入"], horizontal=True)

if season_scope == "全品目合計":
    season_df = data[data["輸出入"] == season_direction]
else:
    season_df = data[(data["輸出入"] == season_direction) & (data["品目表示名"] == season_scope)]

season_agg = season_df.groupby(["年", "月"], as_index=False)["金額"].sum()
current_year = latest_date.year

fig_season = px.line(
    season_agg,
    x="月",
    y="金額",
    color="年",
    markers=True,
    title=f"{season_scope}｜{season_direction}額の月別推移（年比較・千円）",
)
fig_season.update_xaxes(dtick=1, range=[0.5, 12.5])
st.plotly_chart(fig_season, use_container_width=True)
st.caption(
    f"※ {current_year}年は{latest_date.month}月までのデータです。年間を通した比較にはご注意ください。"
)

st.markdown("---")

# ============================================================
# 6. 経営アクション提言
# ============================================================
st.subheader("⑥ Tier2/3製造業への『来月のアクション提言』")

# 数量が減って金額が増えている＝単価上昇している品目を検出
qty_latest = data[(data["輸出入"] == "輸出") & (data["年月日"] == latest_date)][
    ["品目大分類", "品目表示名", "数量", "金額"]
]
qty_prev_year = data[(data["輸出入"] == "輸出") & (data["年月日"] == prev_year_date)][
    ["品目大分類", "数量", "金額"]
]
qty_compare = qty_latest.merge(qty_prev_year, on="品目大分類", suffixes=("", "_前年"), how="left")
qty_compare["数量前年比%"] = qty_compare.apply(
    lambda r: pct_change_safe(r["数量"], r["数量_前年"]), axis=1
)
qty_compare["金額前年比%"] = qty_compare.apply(
    lambda r: pct_change_safe(r["金額"], r["金額_前年"]), axis=1
)
price_up_items = qty_compare[
    (qty_compare["数量前年比%"] < 0) & (qty_compare["金額前年比%"] > 0)
]["品目表示名"].tolist()

surge_items = import_compare.head(3)["品目表示名"].tolist() if not import_compare.empty else []
growth_items = export_compare.head(3)["品目表示名"].tolist() if not export_compare.empty else []

action_col1, action_col2, action_col3 = st.columns(3)
with action_col1:
    st.info(
        "**1. 価格交渉の打診**\n\n"
        + (
            f"{'、'.join(price_up_items[:3])} は数量減・金額増（単価上昇）の傾向。"
            if price_up_items
            else "現時点で明確な単価上昇品目は検出されていません。"
        )
    )
with action_col2:
    st.warning(
        "**2. 輸入動向を踏まえた生産調整**\n\n"
        + (
            f"{'、'.join(surge_items)} は輸入が前年比で急増しており、国内での価格競争激化に注意。"
            if surge_items
            else "輸入急増品目は検出されていません。"
        )
    )
with action_col3:
    st.success(
        "**3. 営業強化・案件獲得**\n\n"
        + (
            f"{'、'.join(growth_items)} は輸出が伸長中。関連する加工・案件の獲得を狙いましょう。"
            if growth_items
            else "伸長品目データが不足しています。"
        )
    )

st.markdown("---")

# ============================================================
# 7. リード獲得（モックアップ）
# ============================================================
st.subheader("有料詳細レポート・個別診断の事前登録")
st.caption("※ 現在はモックアップです。入力内容は保存されません。")
st.write("他業種のデータ閲覧や、自社工場に特化した分析レポートをご希望の方は下記よりお申し込みください。")
st.text_input("メールアドレスを入力")
if st.button("事前登録する"):
    st.success("ご登録ありがとうございます。順次ご案内いたします。")
