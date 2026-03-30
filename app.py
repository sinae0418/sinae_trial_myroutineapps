import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="코스맥스 시제품 안정성 대시보드", layout="wide")

# ──────────────────────────── 테마 CSS ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600&display=swap');

    .stApp { background-color: #f7f5fb; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ede4f7 0%, #dce8fa 100%);
    }

    /* KPI 카드 - 각각 다른 색상 */
    div[data-testid="stMetric"] {
        border-radius: 16px;
        padding: 18px 22px;
        border: none;
        box-shadow: 0 4px 16px rgba(100, 80, 160, 0.10);
    }
    div[data-testid="stMetric"] label {
        color: #ffffff !important; font-size: 0.82rem !important;
        font-weight: 500 !important; text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important; font-weight: 700 !important;
        font-size: 1.6rem !important; text-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }

    /* 각 KPI 카드 개별 그라데이션 */
    div[data-testid="stMetric"]:nth-of-type(1) {
        background: linear-gradient(135deg, #7c6fcd, #a78bfa);
    }
    div[data-testid="stMetric"]:nth-of-type(2) {
        background: linear-gradient(135deg, #6b8fd4, #7cb3f0);
    }
    div[data-testid="stMetric"]:nth-of-type(3) {
        background: linear-gradient(135deg, #5dab8e, #7dd3b0);
    }
    div[data-testid="stMetric"]:nth-of-type(4) {
        background: linear-gradient(135deg, #d4837a, #f0a299);
    }
    div[data-testid="stMetric"]:nth-of-type(5) {
        background: linear-gradient(135deg, #c78f5d, #e8b88a);
    }

    hr { border-color: #ddd5eb !important; }
    h1 { color: #4a3d6e !important; font-weight: 700 !important; }
    h3 { color: #5b4f80 !important; font-weight: 600 !important; }

    /* 슬라이더 트랙 */
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: #7c6fcd !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("코스맥스 시제품 안정성 분석 대시보드")

# 파일 업로드
uploaded_file = st.file_uploader("Excel 파일을 업로드하세요", type=["xlsx"])

if uploaded_file is None:
    st.info("cosmax_day3_dummy_v2.xlsx 파일을 업로드해주세요.")
    st.stop()

# 데이터 로드
df_product = pd.read_excel(uploaded_file, sheet_name="시제품정보")
df_test = pd.read_excel(uploaded_file, sheet_name="안정성테스트결과")
df_merged = df_test.merge(df_product, on="시제품코드", how="left")

# ──────────────────────────── 색상 팔레트 (선명한 파스텔) ────────────────────────────
COLOR_RESULT = {"적합": "#6bc89b", "경미변화": "#f0b86e", "재검토": "#e87f7f"}
COLOR_SEQ = ["#7ba7e0", "#a688d4", "#f0b86e", "#6bc89b", "#e87f7f", "#6bcaba"]
COLOR_PAIR = ["#b07fd4", "#6bc89b"]
COLOR_CONDITION = {"상온": "#7ba7e0", "고온": "#e87f7f", "저온": "#6bcaba", "반복온도변화": "#a688d4"}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#ffffff",
    font=dict(color="#4a4a6a", size=13, family="Noto Sans KR, sans-serif"),
    margin=dict(t=30, b=30, l=50, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#e0d8ee", borderwidth=1),
)

# ──────────────────────────── 사이드바 필터 ────────────────────────────
st.sidebar.markdown("### 필터")

product_types = ["전체"] + sorted(df_product["제품유형"].unique().tolist())
sel_product_type = st.sidebar.selectbox("제품유형", product_types, index=0)

conditions = ["전체"] + sorted(df_test["테스트조건"].unique().tolist())
sel_condition = st.sidebar.selectbox("테스트조건", conditions, index=0)

results = ["전체"] + sorted(df_test["판정결과"].unique().tolist())
sel_result = st.sidebar.selectbox("판정결과", results, index=0)

# 점도 범위 슬라이더
st.sidebar.markdown("---")
viscosity_min = int(df_test["점도_cP"].min() // 500) * 500          # 500 단위로 내림
viscosity_max = (int(df_test["점도_cP"].max() // 500) + 1) * 500    # 500 단위로 올림
slider_opts = list(range(viscosity_min, viscosity_max + 1, 500))
sel_viscosity = st.sidebar.select_slider(
    "점도 범위 (cP)",
    options=slider_opts,
    value=(slider_opts[0], slider_opts[-1]),
)

# 필터 적용
mask = pd.Series(True, index=df_merged.index)
if sel_result != "전체":
    mask &= df_merged["판정결과"] == sel_result
if sel_condition != "전체":
    mask &= df_merged["테스트조건"] == sel_condition
if sel_product_type != "전체":
    mask &= (df_merged["제품유형"] == sel_product_type) | df_merged["제품유형"].isna()
mask &= df_merged["점도_cP"].between(sel_viscosity[0], sel_viscosity[1])

df = df_merged[mask]

# ──────────────────────────── KPI 카드 ────────────────────────────
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 시제품 수", f"{df_product.shape[0]}개")
c2.metric("총 테스트 수", f"{df.shape[0]}건")
c3.metric("적합률", f"{(df['판정결과']=='적합').mean()*100:.1f}%" if len(df) else "N/A")
c4.metric("평균 pH", f"{df['pH'].mean():.2f}" if len(df) else "N/A")
c5.metric("평균 점도", f"{df['점도_cP'].mean():,.0f} cP" if len(df) else "N/A")

# ──────────────────────────── 빈 데이터 가드 ────────────────────────────
if df.empty:
    st.warning("선택한 필터 조건에 해당하는 데이터가 없습니다. 필터를 조정해주세요.")
    st.stop()

# ──────────────────────────── 1행: 판정 & 조건별 ────────────────────────────
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("판정결과 분포")
    result_counts = df["판정결과"].value_counts().reset_index()
    result_counts.columns = ["판정결과", "건수"]
    fig1 = px.pie(
        result_counts, names="판정결과", values="건수",
        color="판정결과", color_discrete_map=COLOR_RESULT, hole=0.45
    )
    fig1.update_traces(
        textfont_size=14, textfont_color="#4a4a6a",
        textinfo="label+percent",
        marker=dict(line=dict(color="#ffffff", width=2.5)),
        pull=[0.03] * len(result_counts),
    )
    fig1.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("테스트조건별 판정결과")
    ct = pd.crosstab(df["테스트조건"], df["판정결과"])
    fig2 = px.bar(
        ct.reset_index().melt(id_vars="테스트조건", var_name="판정결과", value_name="건수"),
        x="테스트조건", y="건수", color="판정결과",
        color_discrete_map=COLOR_RESULT, barmode="group",
        text_auto=True
    )
    fig2.update_traces(
        marker_line_width=0, opacity=0.92,
        textfont=dict(color="#4a4a6a", size=12), textposition="outside"
    )
    fig2.update_layout(**PLOTLY_LAYOUT,
                       xaxis=dict(showgrid=False, linecolor="#d0c8e0"),
                       yaxis=dict(gridcolor="#f0ecf5", gridwidth=1, linecolor="#d0c8e0"))
    st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────── 2행: pH & 점도 ────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("보관온도별 pH 분포")
    fig3 = px.box(df, x="보관온도", y="pH", color="판정결과", color_discrete_map=COLOR_RESULT)
    fig3.update_traces(marker=dict(opacity=0.7, size=6), line=dict(width=1.8))
    fig3.update_layout(**PLOTLY_LAYOUT,
                       xaxis=dict(showgrid=False, linecolor="#d0c8e0"),
                       yaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("보관기간(주)에 따른 점도 변화")
    fig4 = px.scatter(
        df, x="보관기간_주", y="점도_cP", color="판정결과",
        color_discrete_map=COLOR_RESULT, size="색상변화등급",
        hover_data=["시제품코드", "테스트조건"]
    )
    fig4.update_traces(marker=dict(opacity=0.8, line=dict(width=1.5, color="#ffffff")))
    fig4.update_layout(**PLOTLY_LAYOUT,
                       xaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"),
                       yaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"))
    st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────── 3행: 향변화 & 색상변화 ────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.subheader("향변화 / 분리현상 발생 비율")
    agg = pd.DataFrame({
        "항목": ["향변화", "분리현상"],
        "발생률(%)": [
            (df["향변화여부"] == "Y").mean() * 100,
            (df["분리현상여부"] == "Y").mean() * 100,
        ]
    })
    fig5 = px.bar(agg, x="항목", y="발생률(%)", text_auto=".1f",
                  color="항목", color_discrete_sequence=COLOR_PAIR)
    fig5.update_traces(
        marker_line_width=0, opacity=0.9,
        textfont=dict(color="#4a4a6a", size=13), textposition="outside"
    )
    fig5.update_layout(**PLOTLY_LAYOUT, showlegend=False,
                       xaxis=dict(showgrid=False, linecolor="#d0c8e0"),
                       yaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"))
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("색상변화등급 분포 (테스트조건별)")
    fig6 = px.histogram(
        df, x="색상변화등급", color="테스트조건", barmode="group",
        nbins=5, color_discrete_map=COLOR_CONDITION
    )
    fig6.update_traces(marker_line_width=0, opacity=0.9)
    fig6.update_layout(**PLOTLY_LAYOUT,
                       xaxis=dict(showgrid=False, linecolor="#d0c8e0"),
                       yaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"))
    st.plotly_chart(fig6, use_container_width=True)

# ──────────────────────────── 점도 구간 분석 ────────────────────────────
st.markdown("---")
st.subheader("점도 구간별 판정 분석")

v_max = int(df["점도_cP"].max())
bins = [0, 5000, 10000, 15000, max(20000, v_max + 1)]
labels = ["~5,000", "5,000~10,000", "10,000~15,000", "15,000~"]
df["점도구간"] = pd.cut(df["점도_cP"], bins=bins, labels=labels, right=False)

vc_col1, vc_col2 = st.columns(2)
with vc_col1:
    vc_data = df.groupby(["점도구간", "판정결과"], observed=False).size().reset_index(name="건수")
    vc_data = vc_data[vc_data["건수"] > 0]
    fig_vc = px.bar(
        vc_data, x="점도구간", y="건수", color="판정결과",
        color_discrete_map=COLOR_RESULT, barmode="stack", text_auto=True
    )
    fig_vc.update_traces(marker_line_width=0, opacity=0.9,
                         textfont=dict(color="#ffffff", size=11))
    fig_vc.update_layout(**PLOTLY_LAYOUT,
                         xaxis_title="점도 구간 (cP)",
                         xaxis=dict(showgrid=False, linecolor="#d0c8e0"),
                         yaxis=dict(gridcolor="#f0ecf5", linecolor="#d0c8e0"))
    st.plotly_chart(fig_vc, use_container_width=True)

with vc_col2:
    vc_summary = df.groupby("점도구간", observed=False).agg(
        건수=("테스트ID", "count"),
        평균pH=("pH", "mean"),
        적합률=("판정결과", lambda x: (x == "적합").mean() * 100 if len(x) else 0),
    ).reset_index()
    vc_summary = vc_summary[vc_summary["건수"] > 0]
    vc_summary["평균pH"] = vc_summary["평균pH"].round(2)
    vc_summary["적합률"] = vc_summary["적합률"].round(1).astype(str) + "%"
    st.dataframe(vc_summary, use_container_width=True, hide_index=True)

# ──────────────────────────── 시제품별 요약 ────────────────────────────
st.markdown("---")
st.subheader("시제품별 안정성 요약 (시제품정보 매칭)")

df_with_info = df.dropna(subset=["제품유형"])
if not df_with_info.empty:
    summary = df_with_info.groupby(["시제품코드", "제품유형", "제형", "개발단계", "담당팀"]).agg(
        테스트수=("테스트ID", "count"),
        적합수=("판정결과", lambda x: (x == "적합").sum()),
        평균pH=("pH", "mean"),
        평균점도=("점도_cP", "mean"),
    ).reset_index()
    summary["적합률(%)"] = (summary["적합수"] / summary["테스트수"] * 100).round(1)
    st.dataframe(summary, use_container_width=True, hide_index=True)
else:
    st.warning("매칭되는 시제품이 없습니다.")

# ──────────────────────────── 원본 데이터 조회 ────────────────────────────
st.markdown("---")
with st.expander("원본 데이터 조회"):
    tab1, tab2 = st.tabs(["시제품정보", "안정성테스트결과"])
    with tab1:
        st.dataframe(df_product, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(df_test, use_container_width=True, hide_index=True)
