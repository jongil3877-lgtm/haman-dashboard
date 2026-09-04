import streamlit as st
import pandas as pd
from datetime import date
import os
import plotly.express as px
import urllib.request
import ssl
import io

# 1. 홈페이지 기본 설정
st.set_page_config(
    page_title="RKG 함안센터 통합관리 시스템",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 모던 엔터프라이즈 디자인 CSS
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        padding-top: 20px;
    }
    [data-testid="stSidebar"] .stRadio label p {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 0;
        cursor: pointer;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        border-top: 4px solid #1e3a8a; 
        transition: all 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1.7rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    [data-testid="stSelectbox"] label p {
        font-size: 20px !important;      
        font-weight: 900 !important;     
        color: #0f172a !important;       
        margin-bottom: 10px !important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] span {
        font-size: 20px !important;      
        font-weight: 800 !important;     
        color: #1e3a8a !important;       
    }
    
    div[data-baseweb="popover"] ul li,
    div[data-baseweb="menu"] ul li,
    li[role="option"],
    li[role="option"] span {
        font-size: 22px !important;      
        font-weight: 900 !important;     
        padding-top: 12px !important;    
        padding-bottom: 12px !important;
    }

    h1, h2, h3 {
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🔐 [신규] 보안 로그인 (Security Login) 로직
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # 화면 가운데에 예쁘게 로그인 창 배치
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1e3a8a; font-weight: 900;'>🔒 RKG 함안센터 통합 대시보드</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>인가된 관리자 및 직원만 접근할 수 있습니다.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        entered_pwd = st.text_input("접속 비밀번호를 입력하세요.", type="password", placeholder="비밀번호 입력")
        
        if st.button("로그인 (Login)", use_container_width=True):
            # 🔥 아래 "rkg2026" 글자를 원하시는 비밀번호로 자유롭게 바꾸시면 됩니다!
            if entered_pwd == "rkg2026": 
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다. 다시 확인해 주세요.")
                
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 13px; margin-top: 30px;'>ⓒ 2026 Samwoo F&G RKG Haman Center.</p>", unsafe_allow_html=True)
    
    # 비밀번호를 맞추기 전까지는 아래쪽 코드가 절대 실행되지 않도록 막아줍니다!
    st.stop()


# --- 폴더 및 데이터 파일 설정 ---
EDU_LOGS_DIR = "edu_logs_archive"
if not os.path.exists(EDU_LOGS_DIR):
    os.makedirs(EDU_LOGS_DIR)

TBM_FILE = "tbm_history.csv"
EDU_FILE = "edu_links.csv" 
KPI_FILE = "kpi_data.csv"
SALES_FILE = "sales_data.csv" 
CONFIG_FILE = "kpi_sheet_url.txt"
SALES_CONFIG_FILE = "sales_sheet_url.txt"
NOTICE_FILE = "notice_history.csv"

def get_kpi_url():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def get_sales_url():
    if os.path.exists(SALES_CONFIG_FILE):
        with open(SALES_CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def load_notice_data():
    if not os.path.exists(NOTICE_FILE):
        initial_notice = pd.DataFrame([
            {"등록일자": "2026-09-01", "작성자": "신종일 부장", "공지내용": "지게차 운행 구역 사각지대 일단정지 철저 및 도크(Dock) 접안 시 고임목 설치 확인 후 상하차 작업을 진행해 주시기 바랍니다."}
        ])
        initial_notice.to_csv(NOTICE_FILE, index=False, encoding="utf-8-sig")
    return pd.read_csv(NOTICE_FILE, encoding="utf-8-sig")

def save_notice_record(new_notice):
    df = load_notice_data()
    new_df = pd.DataFrame([new_notice])
    df = pd.concat([new_df, df], ignore_index=True)
    df.to_csv(NOTICE_FILE, index=False, encoding="utf-8-sig")

def load_tbm_data():
    if not os.path.exists(TBM_FILE):
        initial_df = pd.DataFrame([
            {"실시일자": "2026-09-02", "구분": "주간 정기 TBM", "중점 점검 주제": "도크(Dock) 접안 차량 안전 고임목 확인", "점검 리더": "신종일 부장", "확인자": "한진미 대리"},
            {"실시일자": "2026-09-01", "구분": "주간 정기 TBM", "중점 점검 주제": "보행자 통로 파렛트 방치 금지", "점검 리더": "신종일 부장", "확인자": "한진미 대리"},
        ])
        initial_df.to_csv(TBM_FILE, index=False, encoding="utf-8-sig")
    return pd.read_csv(TBM_FILE, encoding="utf-8-sig")

def save_tbm_record(new_record):
    df = load_tbm_data()
    new_df = pd.DataFrame([new_record])
    df = pd.concat([new_df, df], ignore_index=True)
    df.to_csv(TBM_FILE, index=False, encoding="utf-8-sig")

def load_edu_data():
    if not os.path.exists(EDU_FILE):
        initial_edu = pd.DataFrame([
            {"월": "9월", "유튜브_주소": "https://youtu.be/03oVgmC3So4?si=IU22SbQG8PZ2Gxso", "구글폼_주소": "https://docs.google.com/forms/d/e/1FAIpQLScy4COyCProsPjgTdqnx4zkfWBaLJ4b0NW1NP_FHcnXrae-gw/viewform?usp=dialog"},
            {"월": "8월", "유튜브_주소": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "구글폼_주소": "https://forms.google.com/"},
        ])
        initial_edu.to_csv(EDU_FILE, index=False, encoding="utf-8-sig")
    return pd.read_csv(EDU_FILE, encoding="utf-8-sig")

def process_kpi_dataframe(df):
    if 'Claims' in df.columns:
        df = df.rename(columns={'Claims': '클레임'})
        
    def format_kpi_month(x):
        val = str(x).strip()
        if val.endswith('월') and len(val) <= 3: 
            return f"2026년 {val}"
        return val
        
    if '월' in df.columns:
        df['월'] = df['월'].apply(format_kpi_month)
    return df

def load_kpi_data():
    kpi_url = get_kpi_url()
    is_live = False
    error_msg = ""
    
    if kpi_url:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(kpi_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as response:
                csv_data = response.read().decode('utf-8')
            
            df = pd.read_csv(io.StringIO(csv_data))
            df = process_kpi_dataframe(df)
            is_live = True
            return df, is_live, error_msg
        except Exception as e:
            error_msg = str(e)
            pass

    if not os.path.exists(KPI_FILE):
        initial_kpi = pd.DataFrame([
            {"월": "2026년 1월", "클레임": 0.61, "배송정확도": 0.0, "상차율": 15.8, "가동율": 75.0, "실가동율": 95.1, "정시출하율": 100.0, "정시도착율": 99.7},
            {"월": "2026년 2월", "클레임": 0.56, "배송정확도": 0.0, "상차율": 16.2, "가동율": 76.3, "실가동율": 95.2, "정시출하율": 100.0, "정시도착율": 99.7},
            {"월": "2026년 3월", "클레임": 0.50, "배송정확도": 0.0, "상차율": 16.2, "가동율": 75.0, "실가동율": 94.6, "정시출하율": 100.0, "정시도착율": 99.7},
            {"월": "2026년 4월", "클레임": 0.72, "배송정확도": 0.0, "상차율": 14.5, "가동율": 74.9, "실가동율": 95.1, "정시출하율": 100.0, "정시도착율": 99.6},
            {"월": "2026년 5월", "클레임": 0.63, "배송정확도": 0.0, "상차율": 15.2, "가동율": 75.1, "실가동율": 94.4, "정시출하율": 100.0, "정시도착율": 99.5},
            {"월": "2026년 6월", "클레임": 0.59, "배송정확도": 0.0, "상차율": 14.7, "가동율": 75.0, "실가동율": 95.4, "정시출하율": 100.0, "정시도착율": 99.7},
            {"월": "2026년 7월", "클레임": 0.57, "배송정확도": 0.0, "상차율": 13.2, "가동율": 75.1, "실가동율": 94.2, "정시출하율": 100.0, "정시도착율": 99.7},
        ])
        initial_kpi.to_csv(KPI_FILE, index=False, encoding="utf-8-sig")
    
    df = pd.read_csv(KPI_FILE, encoding="utf-8-sig")
    df = process_kpi_dataframe(df)
    return df, is_live, error_msg

def load_sales_data():
    sales_url = get_sales_url()
    is_live = False
    error_msg = ""
    df = None
    
    if sales_url:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(sales_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as response:
                csv_data = response.read().decode('utf-8')
            
            df = pd.read_csv(io.StringIO(csv_data))
            is_live = True
        except Exception as e:
            error_msg = str(e)
            pass

    if not is_live:
        if not os.path.exists(SALES_FILE):
            data = []
            for year in [2025, 2026]:
                for month in range(1, 13):
                    ym = f"{year}-{month:02d}"
                    data.append({"연월": ym, "매출(만원)": None, "O/B": None, "I/B": None, "BMPR": None})
            df_default = pd.DataFrame(data)
            df_default.to_csv(SALES_FILE, index=False, encoding="utf-8-sig")
        df = pd.read_csv(SALES_FILE, encoding="utf-8-sig")
    
    def fix_date(val):
        val_str = str(val).strip()
        if val_str.lower() in ['nan', 'none', '']: return val_str
        try:
            if '-' in val_str and val_str.split('-')[0].isalpha():
                dt = pd.to_datetime(val_str, format='%b-%y')
            else:
                dt = pd.to_datetime(val_str)
            if dt.year < 2000:
                dt = pd.to_datetime(val_str, format='%m-%y')
            return dt.strftime('%Y-%m')
        except:
            return val_str
            
    if '연월' in df.columns:
        df['연월'] = df['연월'].apply(fix_date)
    
    cols = ["매출(만원)", "O/B", "I/B", "BMPR"]
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.strip(), errors='coerce')
            
    valid_ym = [str(x) for x in df['연월'].dropna() if '-' in str(x)]
    years = sorted(list(set([int(x.split('-')[0]) for x in valid_ym])))
    if not years: years = [2025, 2026]
        
    full_months = [f"{year}-{month:02d}" for year in years for month in range(1, 13)]
    full_df = pd.DataFrame({"연월": full_months})
    df_merged = pd.merge(full_df, df, on="연월", how="left")
    
    return df_merged, is_live, error_msg

# 3. 사이드바 메뉴 디자인
logo_candidates = ["로고.jpg", "로고.JPG", "logo.jpg", "logo.JPG", "로고.png", "로고.PNG"]
found_logo = None
for candidate in logo_candidates:
    if os.path.exists(candidate):
        found_logo = candidate
        break

if found_logo:
    st.sidebar.image(found_logo, width=160)
else:
    st.sidebar.markdown('<p style="color: #38bdf8; font-size: 13px; font-weight: 700; letter-spacing: 1px; margin: 0;">삼우F&G</p>', unsafe_allow_html=True)
    uploaded_logo = st.sidebar.file_uploader("📂 회사 로고 이미지 업로드", type=["jpg", "jpeg", "png"])
    if uploaded_logo is not None:
        with open("로고.jpg", "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.success("로고가 성공적으로 등록되었습니다!")
        st.rerun()

st.sidebar.markdown("""
    <div style="padding: 5px 0 15px 0; border-bottom: 1px solid #1e293b; margin-bottom: 15px;">
        <h2 style="color: #ffffff; font-size: 19px; font-weight: 800; margin: 5px 0 0 0;">RKG 함안센터</h2>
    </div>
    """, unsafe_allow_html=True)

menu = st.sidebar.radio(
    "메뉴 선택",
    ["대시보드 (Home)", "안전 교육 (Safety Edu)", "작업일지 (TBM Log)", "운영 현황 (실적 관리)"]
)

# --- [메뉴 1] 홈 및 대시보드 ---
if menu == "대시보드 (Home)":
    st.markdown("## RKG 함안센터 KPI 및 안전·품질 현황")
    st.markdown("---")
    
    kpi_df, is_live, error_msg = load_kpi_data()
    
    notice_df = load_notice_data()
    latest_notice = notice_df.iloc[0]['공지내용'] if not notice_df.empty else "등록된 공지사항이 없습니다."
    
    st.info(f"💡 **센터 주요 공지사항:** {latest_notice}")
    
    with st.expander("📢 공지사항 수정 및 이전 이력 보기", expanded=False):
        with st.form("notice_form", clear_on_submit=True):
            new_notice_text = st.text_area("새로운 공지사항 입력", placeholder="센터 직원들에게 전달할 공지 내용을 입력하세요.", height=80)
            notice_author = st.text_input("작성자", value="신종일 부장")
            submit_notice = st.form_submit_button("📢 공지사항 업데이트")
            
            if submit_notice:
                if not new_notice_text.strip():
                    st.error("공지 내용을 입력해 주세요.")
                else:
                    new_notice_entry = {"등록일자": str(date.today()), "작성자": notice_author, "공지내용": new_notice_text}
                    save_notice_record(new_notice_entry)
                    st.success("공지사항이 성공적으로 업데이트되었습니다!")
                    st.rerun()
                    
        st.markdown("**📜 역대 공지사항 이력 목록**")
        st.dataframe(notice_df, use_container_width=True, height=200)

    st.markdown("---")
    
    month_list = kpi_df['월'].tolist()
    col_filter, _ = st.columns([1, 2])
    with col_filter:
        selected_month = st.selectbox("📅 실적 조회 연월 선택", month_list, index=len(month_list)-1)
    
    curr_idx = kpi_df[kpi_df['월'] == selected_month].index[0]
    curr = kpi_df.iloc[curr_idx]
    prev = kpi_df.iloc[curr_idx - 1] if curr_idx > 0 else curr
    curr_month = curr["월"]
    
    st.markdown(f"**📌 KPI ({curr_month} 실적 기준)**")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        c_val = curr["클레임"]
        c_prev = prev["클레임"]
        c_delta = c_val - c_prev
        st.metric(label="클레임 (#6,7) [목표: 2.00]", value=f"{c_val:.2f}", delta=f"{c_delta:+.2f}", delta_color="inverse")
    
    with kpi2:
        d_val = curr["배송정확도"]
        d_prev = prev["배송정확도"]
        d_delta = d_val - d_prev
        st.metric(label="배송정확도 [목표: 3]", value=f"{d_val:.0f}", delta=f"{d_delta:+.0f}", delta_color="inverse")
    
    with kpi3:
        l_val = curr["상차율"]
        l_prev = prev["상차율"]
        l_delta = l_val - l_prev
        st.metric(label="상차율 (CBM) [목표: 23.0]", value=f"{l_val:.1f}", delta=f"{l_delta:+.1f}")

    kpi4, kpi5, kpi6 = st.columns(3)
    with kpi4:
        o_val = curr["가동율"]
        o_prev = prev["가동율"]
        o_delta = o_val - o_prev
        r_val = curr["실가동율"]
        r_prev = prev["실가동율"]
        r_delta = r_val - r_prev
        st.metric(label="(실)가동율 [목표: 75.0 (90.0)]", value=f"({r_val:.1f}%) {o_val:.1f}%", delta=f"({r_delta:+.1f}%p) {o_delta:+.1f}%p")
    
    with kpi5:
        s_val = curr["정시출하율"]
        s_prev = prev["정시출하율"]
        s_delta = s_val - s_prev
        st.metric(label="정시출하율 [목표: 99.5%]", value=f"{s_val:.1f}%", delta=f"{s_delta:+.1f}%p")
    
    with kpi6:
        a_val = curr["정시도착율"]
        a_prev = prev["정시도착율"]
        a_delta = a_val - a_prev
        st.metric(label="정시도착율 [목표: 97.5%]", value=f"{a_val:.1f}%", delta=f"{a_delta:+.1f}%p")

    st.markdown("---")
    st.markdown("**🛡️ 안전 및 품질(APW) 현황**")
    tbm_df = load_tbm_data()
    tbm_count = len(tbm_df)
    
    start_accident_free = date(2026, 1, 1)
    today_date = date.today()
    calculated_days = (today_date - start_accident_free).days + 1
    
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.metric(label="현재 무재해 달성", value=f"{calculated_days}일", delta="목표: 365일")
    with s_col2:
        st.metric(label="누적 TBM 실시", value=f"{tbm_count}회", delta="지속 누적 중")
    with s_col3:
        st.metric(label="APW 진단 결과 (6/25)", value="3.43 Level", delta="목표 초과 달성 (T/G: 3.0)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📈 항목별 월별 트렌드 분석**")
    
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        fig1 = px.line(kpi_df, x="월", y=["가동율", "실가동율"], markers=True, title="가동율 및 실가동율 추이 (%)", color_discrete_sequence=['#1e3a8a', '#0d9488'], template="plotly_white")
        fig1.update_traces(mode="lines+markers+text", textposition="top center", texttemplate='%{y:.1f}')
        fig1.update_layout(xaxis_title="연월", yaxis_title="비율 (%)", legend_title_text='구분', margin=dict(t=40, b=10, l=10, r=10), xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

    with row1_c2:
        fig2 = px.bar(kpi_df, x="월", y="클레임", text="클레임", title="클레임 (#6,7) 발생 현황 (건)", color_discrete_sequence=['#e11d48'], template="plotly_white")
        fig2.update_traces(textposition='outside')
        fig2.update_layout(xaxis_title="연월", yaxis_title="발생 건수", margin=dict(t=40, b=10, l=10, r=10), xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        fig3 = px.bar(kpi_df, x="월", y="상차율", text="상차율", title="상차율 (CBM) 추이", color_discrete_sequence=['#d97706'], template="plotly_white")
        fig3.update_traces(textposition='outside')
        fig3.update_layout(xaxis_title="연월", yaxis_title="CBM", margin=dict(t=40, b=10, l=10, r=10), xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

    with row2_c2:
        fig4 = px.line(kpi_df, x="월", y=["정시출하율", "정시도착율"], markers=True, title="정시 출하율 및 도착율 추이 (%)", color_discrete_sequence=['#7c3aed', '#0284c7'], template="plotly_white")
        fig4.update_traces(mode="lines+markers+text", textposition="top center", texttemplate='%{y:.1f}')
        fig4.update_layout(xaxis_title="연월", yaxis_title="비율 (%)", legend_title_text='구분', margin=dict(t=40, b=10, l=10, r=10), yaxis=dict(range=[80, 105]), xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    with st.expander("⚙️ [관리자/직원용] KPI 실적 데이터 업데이트"):
        st.markdown("직원이 구글 스프레드시트에서 작성한 CSV 파일을 업로드하여 실적을 갱신할 수 있습니다.")
        tab_up, tab_link = st.tabs(["📂 파일 직접 업로드 (권장)", "🌐 구글 시트 연동 (사내망 차단 시 불가)"])
        
        with tab_up:
            kpi_file = st.file_uploader("최신 KPI 실적 파일(CSV) 업로드", type=["csv"], key="kpi_up")
            if kpi_file is not None:
                file_id = kpi_file.name + str(kpi_file.size)
                if "last_kpi_file" not in st.session_state or st.session_state["last_kpi_file"] != file_id:
                    with open(KPI_FILE, "wb") as f:
                        f.write(kpi_file.getbuffer())
                    if os.path.exists(CONFIG_FILE):
                        os.remove(CONFIG_FILE)
                    st.session_state["last_kpi_file"] = file_id
                st.success("새로운 KPI 실적 파일이 성공적으로 반영되었습니다!")
                
        with tab_link:
            saved_url = get_kpi_url()
            new_url = st.text_input("구글 시트 '웹에 게시(CSV)' 링크 붙여넣기", value=saved_url, key="kpi_link", placeholder="https://docs.google.com/spreadsheets/...")
            if st.button("연동 저장 및 적용", key="kpi_btn"):
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    f.write(new_url.strip())
                st.success("구글 시트 주소가 저장되었습니다! 화면이 새로고침됩니다.")
                st.rerun()

# --- [메뉴 2] 안전 교육 ---
elif menu == "안전 교육 (Safety Edu)":
    st.markdown("### 📺 월별 안전 보건 교육")
    st.markdown("---")
    
    edu_df = load_edu_data()
    month_list = edu_df['월'].astype(str).tolist()
    
    selected_month = st.selectbox("📅 시청할 교육 월(Monthly)을 선택하세요.", month_list)
    current_data = edu_df[edu_df['월'] == selected_month].iloc[0]
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader(f"📌 {selected_month} 안전보건교육 영상")
        st.video(current_data["유튜브_주소"])
        
    with col_b:
        st.subheader("📝 교육 이수 확인")
        form_url = current_data["구글폼_주소"]
        if pd.isna(form_url) or str(form_url).strip() == "":
            st.info("💡 본 교육은 현장 오프라인 서명부로 이수를 완료하는 교육입니다.")
        else:
            st.write("영상을 시청하신 후 하단 버튼을 통해 구글폼 서명을 완료해 주세요.")
            st.link_button("👉 교육 이수확인 바로가기", str(form_url))
            
    st.markdown("---")
    st.markdown("### 📂 교육일지 파일 업로드 및 보관함")
    st.caption("수기로 작성된 오프라인 서명부나 스캔본 파일을 업로드하여 안전하게 보관하세요.")
    
    upload_col, list_col = st.columns([1, 1])
    
    with upload_col:
        with st.form("upload_edu_log_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("새로운 일지 첨부 (PDF, 이미지, 엑셀, 한글 등)", type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls", "hwp", "docx"])
            submit_upload = st.form_submit_button("🚀 파일 업로드하기")
            
            if submit_upload and uploaded_file is not None:
                file_path = os.path.join(EDU_LOGS_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"'{uploaded_file.name}' 파일이 성공적으로 보관되었습니다!")
                st.rerun()
            elif submit_upload and uploaded_file is None:
                st.warning("업로드할 파일을 먼저 선택해 주세요.")

    with list_col:
        st.markdown("**저장된 교육일지 목록**")
        saved_files = os.listdir(EDU_LOGS_DIR)
        
        if saved_files:
            for file_name in saved_files:
                file_path = os.path.join(EDU_LOGS_DIR, file_name)
                
                f_col1, f_col2 = st.columns([4, 1])
                with f_col1:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    st.download_button(
                        label=f"📥 {file_name}",
                        data=file_bytes,
                        file_name=file_name,
                        use_container_width=True,
                        key=f"dl_{file_name}"
                    )
                with f_col2:
                    if st.button("🗑️ 삭제", key=f"del_{file_name}"):
                        try:
                            os.remove(file_path)
                            st.rerun()
                        except Exception as e:
                            st.error(f"파일 삭제에 실패했습니다: {e}")
        else:
            st.info("아직 보관된 교육일지 파일이 없습니다.")

# --- [메뉴 3] TBM 작업일지 ---
elif menu == "작업일지 (TBM Log)":
    st.markdown("### 👷‍♂️ TBM (작업 전 안전점검) Log")
    st.caption("현장 TBM 실시 이력 통합 조회 및 신규 등록 시스템")
    st.markdown("---")
    
    tbm_history_df = load_tbm_data()
    tbm_history_df = tbm_history_df.sort_values(by="실시일자", ascending=False).reset_index(drop=True)
    
    total_tbm = len(tbm_history_df)
    latest_date = tbm_history_df.iloc[0]['실시일자'] if total_tbm > 0 else "기록 없음"
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("총 TBM 실시 횟수", f"{total_tbm}회")
    with c2:
        st.metric("가장 최근 실시일", latest_date)
    with c3:
        st.metric("책임 점검 리더", "신종일 부장")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📑 TBM 누적 이력 목록**")
    st.dataframe(tbm_history_df, use_container_width=True, height=400)
    
    st.markdown("---")
    with st.expander("➕ 신규 TBM 일지 작성하기", expanded=False):
        with st.form("tbm_form", clear_on_submit=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                tbm_date = st.date_input("실시일자", value=date.today())
            with f_col2:
                tbm_type = st.selectbox("구분", ["주간 정기 TBM", "일일 TBM", "특별 안전 TBM"])
            with f_col3:
                tbm_leader = st.text_input("점검 리더", value="신종일 부장")
            with f_col4:
                tbm_confirmer = st.text_input("확인자", value="한진미 대리")
            
            t_topic = st.text_area("중점 점검 주제 및 공지 내용", placeholder="밴드에 게시한 TBM 공지 내용을 복사해 붙여넣으세요.", height=100)
            submit_btn = st.form_submit_button("💾 TBM 기록 등록하기")
            
            if submit_btn:
                if not t_topic.strip():
                    st.error("점검 주제 및 내용을 입력해 주세요.")
                else:
                    new_entry = {"실시일자": str(tbm_date), "구분": tbm_type, "중점 점검 주제": t_topic, "점검 리더": tbm_leader, "확인자": tbm_confirmer}
                    save_tbm_record(new_entry)
                    st.success("TBM 일지가 성공적으로 등록되었습니다!")
                    st.rerun()

# --- [메뉴 4] 운영 현황 (실적 관리) ---
elif menu == "운영 현황 (실적 관리)":
    st.markdown("### 📊 센터 운영 및 실적 현황")
    st.markdown("---")

    sales_df, is_live_sales, sales_error = load_sales_data()
    
    if is_live_sales:
        st.success("🟢 구글 시트와 정상 연동 중입니다!")
    else:
        if get_sales_url() != "":
            st.error(f"🔴 구글 시트 연동 에러: {sales_error}")
        else:
            pass 
    
    raw_month_list = sales_df['연월'].dropna().unique().tolist()
    valid_months = [m for m in raw_month_list if '-' in str(m) and len(str(m).split('-')) == 2 and str(m).split('-')[0].isdigit() and int(str(m).split('-')[0]) >= 2000]
    valid_months.sort(reverse=True)
    
    default_idx = 0
    for i, m in enumerate(valid_months):
        row = sales_df[sales_df['연월'] == m].iloc[0]
        if pd.notna(row['매출(만원)']) or pd.notna(row['O/B']) or pd.notna(row['I/B']) or pd.notna(row['BMPR']):
            default_idx = i
            break
    
    def format_korean_ym(x):
        try:
            y, m = str(x).split('-')
            return f"{y}년 {m}월"
        except:
            return x

    if not valid_months:
        valid_months = ["2025-01"]
        sales_df = pd.DataFrame([{"연월": "2025-01", "매출(만원)": None, "O/B": None, "I/B": None, "BMPR": None}])
        default_idx = 0

    selected_ym = st.selectbox(
        "📅 조회할 연월(Year-Month)을 선택하세요.", 
        valid_months,
        index=default_idx,
        format_func=format_korean_ym
    )
    
    curr = sales_df[sales_df['연월'] == selected_ym].iloc[0]
    
    prev_yoy = None
    try:
        yoy_year = str(int(selected_ym.split('-')[0]) - 1)
        yoy_ym = f"{yoy_year}-{selected_ym.split('-')[1]}"
        if yoy_ym in sales_df['연월'].values:
            prev_yoy = sales_df[sales_df['연월'] == yoy_ym].iloc[0]
    except:
        pass

    prev_mom = None
    try:
        curr_y, curr_m = int(selected_ym.split('-')[0]), int(selected_ym.split('-')[1])
        if curr_m == 1:
            mom_ym = f"{curr_y - 1}-12"
        else:
            mom_ym = f"{curr_y}-{curr_m - 1:02d}"
        if mom_ym in sales_df['연월'].values:
            prev_mom = sales_df[sales_df['연월'] == mom_ym].iloc[0]
    except:
        pass
    
    def get_safe_val(val, suffix=""):
        if pd.isna(val) or str(val).strip() == "":
            return "기록 없음"
        return f"{val:,.0f} {suffix}".strip()

    def get_dual_delta_val(col_name):
        c_val = curr[col_name]
        
        mom_str = "-"
        if prev_mom is not None and pd.notna(c_val) and pd.notna(prev_mom[col_name]) and str(c_val).strip() != "":
            mom_val = float(c_val - prev_mom[col_name])
            mom_str = f"{mom_val:+,.0f} (전월)"
            
        yoy_str = "-"
        if prev_yoy is not None and pd.notna(c_val) and pd.notna(prev_yoy[col_name]) and str(c_val).strip() != "":
            yoy_val = float(c_val - prev_yoy[col_name])
            yoy_str = f"{yoy_val:+,.0f} (전년)"
            
        if mom_str == "-" and yoy_str == "-":
            return None
            
        return f"{mom_str}  /  {yoy_str}"

    st.markdown(f"**📌 {format_korean_ym(selected_ym)} 실적 요약 (전월 및 전년 동월 대비)**")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="💰 총 매출", value=get_safe_val(curr['매출(만원)'], "만원"), delta=get_dual_delta_val('매출(만원)'))
    with c2:
        st.metric(label="📤 O/B 물동량 (CBM)", value=get_safe_val(curr['O/B']), delta=get_dual_delta_val('O/B'))
    with c3:
        st.metric(label="📥 I/B 물동량 (CBM)", value=get_safe_val(curr['I/B']), delta=get_dual_delta_val('I/B'))
    with c4:
        st.metric(label="🚘 BMPR 물동량 (QTY)", value=get_safe_val(curr['BMPR']), delta=get_dual_delta_val('BMPR'))

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("**📥 실적 데이터 관리 및 다운로드**")
    
    html_report = f"""
    <html lang="ko">
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; margin: 20px; }}
        h2 {{ color: #1e3a8a; text-align: center; margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th {{ background-color: #1e3a8a; color: #ffffff; padding: 12px 15px; text-align: center; font-size: 14px; border: 1px solid #cbd5e1; font-weight: bold; }}
        td {{ padding: 10px 15px; text-align: center; font-size: 13px; border: 1px solid #cbd5e1; color: #0f172a; }}
        tr:nth-child(even) {{ background-color: #f8fafc; }}
    </style>
    </head>
    <body>
        <h2>RKG 함안센터 종합 운영 실적 보고서</h2>
        {sales_df.dropna(how='all', subset=['매출(만원)', 'O/B', 'I/B', 'BMPR']).to_html(index=False, escape=False)}
    </body>
    </html>
    """
    
    st.download_button(
        label="📥 실적 다운로드",
        data=html_report.encode('utf-8-sig'),
        file_name="RKG_Haman_Center_Report.xls",
        mime="application/vnd.ms-excel",
        help="클릭하시면 현재까지의 실적 데이터를 엑셀에서 깔끔한 서식으로 다운로드합니다."
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"**📈 전체 매출 및 물동량 트렌드 분석**")
    
    sales_df['연월_표시'] = sales_df['연월'].apply(lambda x: f"{x.split('-')[0][2:]}년 {int(x.split('-')[1])}월" if '-' in str(x) else str(x))

    tab_rev, tab_vol = st.tabs(["💰 매출 트렌드", "📦 물동량 트렌드 (O/B, I/B & BMPR)"])
    
    with tab_rev:
        st.markdown("#### 🔹 전체 월별 매출 추이")
        valid_sales_df = sales_df.dropna(subset=['매출(만원)'])
        if not valid_sales_df.empty:
            fig_rev = px.bar(valid_sales_df, x="연월_표시", y="매출(만원)", text="매출(만원)", color_discrete_sequence=['#1e3b82'], template="plotly_white")
            fig_rev.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
            fig_rev.update_layout(xaxis_title="연월", yaxis_title="매출(만원)", xaxis_tickangle=-45, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig_rev, use_container_width=True)
        else:
            st.info("해당 데이터가 없습니다.")

    with tab_vol:
        st.markdown("#### 🔹 전체 [O/B & I/B 물동량] 추이")
        valid_v = sales_df.dropna(subset=['O/B', 'I/B'], how='all')
        if not valid_v.empty:
            fig_v = px.line(valid_v, x="연월_표시", y=["O/B", "I/B"], markers=True, color_discrete_sequence=['#1e3b82', '#0d9488'], template="plotly_white")
            fig_v.update_traces(mode="lines+markers+text", textposition="top center", texttemplate='%{y:,.0f}', connectgaps=False)
            fig_v.update_layout(xaxis_title="연월", yaxis_title="물동량 (CBM)", legend_title_text='구분', xaxis_tickangle=-45, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig_v, use_container_width=True)
        else:
            st.info("해당 데이터가 없습니다.")

        st.markdown("---")
        st.markdown("#### 🔹 전체 [범퍼 물동량 (BMPR)] 추이")
        valid_b = sales_df.dropna(subset=['BMPR'])
        if not valid_b.empty:
            fig_b = px.line(valid_b, x="연월_표시", y="BMPR", markers=True, color_discrete_sequence=['#d97706'], template="plotly_white")
            fig_b.update_traces(mode="lines+markers+text", textposition="top center", texttemplate='%{y:,.0f}', connectgaps=False)
            fig_b.update_layout(xaxis_title="연월", yaxis_title="BMPR 수치 (QTY)", xaxis_tickangle=-45, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig_b, use_container_width=True)
        else:
            st.info("해당 데이터가 없습니다.")
            
    st.markdown("---")
    with st.expander("⚙️ [관리자/직원용] 운영 현황 실적 데이터 업데이트"):
        st.markdown("직원이 구글 스프레드시트에서 작성한 CSV 파일을 업로드하여 실적을 갱신할 수 있습니다.")
        tab_up_s, tab_link_s = st.tabs(["📂 파일 직접 업로드 (권장)", "🌐 구글 시트 연동 (사내망 차단 시 불가)"])
        
        with tab_up_s:
            sales_file = st.file_uploader("최신 운영 실적 파일(CSV) 업로드", type=["csv"], key="sales_up")
            if sales_file is not None:
                file_id = sales_file.name + str(sales_file.size)
                if "last_sales_file" not in st.session_state or st.session_state["last_sales_file"] != file_id:
                    with open(SALES_FILE, "wb") as f:
                        f.write(sales_file.getbuffer())
                    if os.path.exists(SALES_CONFIG_FILE):
                        os.remove(SALES_CONFIG_FILE)
                    st.session_state["last_sales_file"] = file_id
                st.success("새로운 실적 파일이 성공적으로 반영되었습니다!")
                
        with tab_link_s:
            saved_sales_url = get_sales_url()
            new_sales_url = st.text_input("구글 시트 '웹에 게시(CSV)' 링크 붙여넣기", value=saved_sales_url, key="sales_link", placeholder="https://docs.google.com/spreadsheets/...")
            if st.button("연동 저장 및 적용", key="sales_btn"):
                with open(SALES_CONFIG_FILE, "w", encoding="utf-8") as f:
                    f.write(new_sales_url.strip())
                st.success("구글 시트 주소가 저장되었습니다! 화면이 새로고침됩니다.")
                st.rerun()