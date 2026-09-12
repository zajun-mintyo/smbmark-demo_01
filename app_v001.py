import pandas as pd
import plotly.express as px
import streamlit as st

# ページ基本設定
st.set_page_config(
    page_title="SMBMARK - 自動車部品 貿易インテリジェンス", layout="wide"
)

st.title("SMBMARK｜中小製造業のための貿易インテリジェンス")
st.caption("対象: 自動車部品（HSコード 8708）/ データソース: 財務省 貿易統計")

# データ読み込み・マッピング処理
@st.cache_data
def load_and_process_data():
    file_path = "2026091020080628330477.csv"
    df = pd.read_csv(file_path, encoding="cp932", skiprows=9)
    df["品目"] = df["品目"].str.strip()
    df["暦年月"] = df["暦年月"].str.replace("'", "").str.strip()

    mapping = {
        "8708.10-000": "バンパー及びその部分品",
        "8708.21-000": "シートベルト",
        "8708.22-000": "フロントガラス等の安全ガラス部品",
        "8708.29-000": "その他の車体部分品・附属品",
        "8708.30-000": "ブレーキ、サーボブレーキ及び部分品",
        "8708.40-000": "ギヤボックス及びその部分品",
        "8708.50-000": "駆動軸（ディファレンシャル付き）",
        "8708.70-000": "車輪（ホイール）及びその部分品",
        "8708.80-000": "サスペンションシステム及び部分品",
        "8708.91-000": "ラジエーター及びその部分品",
        "8708.92-000": "消音器（マフラー）及び排気管",
        "8708.93-000": "クラッチ及びその部分品",
        "8708.94-000": "ステアリングホイール・コラム・ボックス",
        "8708.95-000": "安全エアバッグ及びその部分品",
        "8708.99-100": "その他の部分品（特定部品）",
        "8708.99-900": "その他の部分品（その他）",
    }
    df["品目名"] = df["品目"].map(mapping)
    df["当月金額"] = pd.to_numeric(df["当月金額"], errors="coerce")
    df["当月第２数量"] = pd.to_numeric(df["当月第２数量"], errors="coerce")
    return df


df = load_and_process_data()

# サイドバー設定
st.sidebar.header("条件絞り込み")
selected_item = st.sidebar.selectbox(
    "分析対象の品目を選択", ["全品目（全体概況）"] + list(df["品目名"].unique())
)

# メインダッシュボードエリア
if selected_item == "全品目（全体概況）":
    st.subheader("全国 自動車部品 輸出額の推移（千円）")
    monthly_total = df.groupby("暦年月")["当月金額"].sum().reset_index()
    fig = px.line(
        monthly_total,
        x="暦年月",
        y="当月金額",
        markers=True,
        title="全体輸出額トレンド",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Tier2/3製造業への『来月のアクション提言』")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**1. 価格交渉の打診**\n\n数量減・金額増の品目を中心に、単価転嫁の交渉データを準備してください。")
    with col2:
        st.warning(
            "**2. 駆動系ラインの生産調整**\n\nギヤボックス関連の前年比減産に合わせ、プレス・加工ラインの稼働を調整してください。"
        )
    with col3:
        st.success(
            "**3. 熱・排気系パーツへの営業強化**\n\n伸び率が顕著なラジエーター・マフラー周辺の金型・加工案件を獲得しに行きましょう。"
        )
else:
    sub_df = df[df["品目名"] == selected_item]
    st.subheader(f"{selected_item} の月次動向")
    fig = px.bar(
        sub_df,
        x="暦年月",
        y="当月金額",
        title=f"{selected_item} 輸出金額推移（千円）",
    )
    st.plotly_chart(fig, use_container_width=True)

# 登録フォーム（リード獲得用）
st.markdown("---")
st.subheader("有料詳細レポート・個別診断の事前登録")
st.write("他業種のデータ閲覧や、自社工場に特化した分析レポートをご希望の方は下記よりお申し込みください。")
st.text_input("メールアドレスを入力")
if st.button("事前登録する"):
    st.success("ご登録ありがとうございます。順次ご案内いたします。")