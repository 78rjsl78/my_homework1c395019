import streamlit as st
from database import init_db, SessionLocal, User, DailyRecord, Goal
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Diet Mate", page_icon="🍏", layout="wide")

# --- Custom CSS (네이비 & 베이비블루 테마) ---
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {
        font-family: 'Pretendard', sans-serif;
        color: #AEE2FF !important; /* 베이비블루 */
    }
    .stApp {
        background-color: #0A1128 !important; /* 네이비 */
    }
    h1, h2, h3, h4, p, label, span, div[data-testid="stMetricValue"] {
        color: #AEE2FF !important;
    }
    /* 제목 위 빈 공간(기본 헤더) 및 기본 프레임 제거 */
    header {visibility: hidden !important;}
    .block-container {padding-top: 2rem !important;}
    
    /* 선택된 탭 등 일부 필요한 곳만 둥근 모서리 유지, 거추장스러운 전체 틀 제거 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
    }
    /* 일반 버튼 (체중 조절 등) */
    .stButton>button[kind="secondary"] {
        background-color: #1E3163 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        transition: 0.2s;
    }
    .stButton>button[kind="secondary"]:hover {
        background-color: #2A488E !important;
    }
    /* 메인 저장 버튼 (크게, 흰색 글씨) */
    .stButton>button[kind="primary"] {
        background-color: #007AFF !important;
        color: #FFFFFF !important;
        font-size: 20px !important;
        padding: 20px !important;
        border-radius: 12px;
        font-weight: 800;
    }
    /* 입력 필드 */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #0A1128 !important;
        border: 1px solid #AEE2FF !important;
        border-radius: 8px;
        color: #AEE2FF !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

init_db()

# 자동 로그인 설정
if 'user_id' not in st.session_state or st.session_state['user_id'] is None:
    db = SessionLocal()
    default_user = db.query(User).filter(User.username == "default").first()
    if not default_user:
        default_user = User(username="default", password_hash="", height=170.0, weight=70.0, gender="남성", age=25)
        db.add(default_user)
        db.commit()
    st.session_state['user_id'] = default_user.id
    db.close()

db = SessionLocal()
user = db.query(User).filter(User.id == st.session_state['user_id']).first()
goal = db.query(Goal).filter(Goal.user_id == user.id).first()

# --- 화면 상단: 앱 타이틀 ---
st.markdown("""
<div style='text-align: center; margin-top: -30px;'>
    <h1 style='font-size: 6.5rem; color: #AEE2FF; font-weight: 900; margin-bottom: 5px; border-bottom: none; line-height: 1.1;'>Diet-log</h1>
    <p style='font-size: 1.5rem; color: #AEE2FF; margin-top: 0px; margin-bottom: 20px;'>나를 위하는 시간</p>
</div>
""", unsafe_allow_html=True)

# 1. 전역 날짜 선택 및 네비게이션 UI (session_state 활용)
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

def prev_day():
    st.session_state.current_date -= timedelta(days=1)
def next_day():
    st.session_state.current_date += timedelta(days=1)
def update_date():
    st.session_state.current_date = st.session_state.date_picker

st.write("# 📅 달력")
date_col1, date_col2, date_col3 = st.columns([1, 2, 1])
with date_col1:
    st.button("◀ Yesterday", on_click=prev_day, use_container_width=True, key="btn_prev")
with date_col2:
    st.date_input("날짜", value=st.session_state.current_date, key="date_picker", on_change=update_date, label_visibility="collapsed")
with date_col3:
    st.button("Tomorrow ▶", on_click=next_day, use_container_width=True, key="btn_next")

sel_date_str = st.session_state.current_date.isoformat()

record = db.query(DailyRecord).filter(DailyRecord.user_id == user.id, DailyRecord.date == sel_date_str).first()

if not record:
    record = DailyRecord(user_id=user.id, date=sel_date_str, weight=user.weight, exercise_time=0, water=0.0)
    db.add(record)
    db.commit()

# --- 화면 상단: 대시보드 요약 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"체중 ({sel_date_str})", f"{record.weight:.1f} kg")
with col2:
    if goal:
        diff = record.weight - goal.target_weight
        st.metric("목표 체중", f"{goal.target_weight} kg", f"{-diff:.1f} kg (남은 감량)" if diff > 0 else "달성!", delta_color="normal" if diff > 0 else "off")
    else:
        st.metric("목표 체중", "미설정")
with col3:
    burned = (record.exercise_time or 0) * 5
    st.metric("소모 칼로리", f"{burned} kcal")
with col4:
    st.metric("물 섭취", f"{record.water:.1f} L")

# 4. 시각적인 동기부여 요소 (Progress Bars)
st.write("📈 **오늘의 달성률**")
pcol1, pcol2 = st.columns(2)
with pcol1:
    water_percent = min((record.water or 0.0) / 2.0, 1.0)
    st.progress(water_percent, text=f"💧 수분 목표 (2.0L 중 {record.water or 0.0:.1f}L 달성 - {int(water_percent*100)}%)")
with pcol2:
    cal_percent = min(burned / 300.0, 1.0)
    st.progress(cal_percent, text=f"🔥 소모 칼로리 목표 (300kcal 중 {burned}kcal 달성 - {int(cal_percent*100)}%)")

st.divider()

# --- 메인 레이아웃: 좌측(기록/입력), 우측(통계) ---
left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.subheader(f"✏️ 기록하기 ({sel_date_str})")
    
    # 3. 입력칸 정리 (Tabs)
    tab_diet, tab_body = st.tabs(["🥗 식단 기록", "🏃 신체 & 활동"])
    
    with tab_diet:
        st.write("**식단 기록 (사진 AI 분석)**")
        uploaded_file = st.file_uploader("음식 사진을 업로드하면 AI가 분석합니다 📸", type=["png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            with st.spinner("🤖 AI가 이미지를 분석 중입니다..."):
                import time
                time.sleep(1.5) # 시뮬레이션 지연
                st.success("✅ AI 분석 결과: 구운 닭가슴살과 현미밥 (약 420 kcal)")
                if not record.breakfast:
                    record.breakfast = "구운 닭가슴살과 현미밥 (420kcal)"
                
        record.breakfast = st.text_input("아침", value=record.breakfast or "")
        record.lunch = st.text_input("점심", value=record.lunch or "")
        record.dinner = st.text_input("저녁", value=record.dinner or "")
        
    with tab_body:
        st.write("**체중 조절 (간편 버튼)**")
        w_col1, w_col2, w_col3, w_col4 = st.columns(4)
        if w_col1.button("-1.0kg"): 
            record.weight -= 1.0; db.commit(); st.rerun()
        if w_col2.button("-0.5kg"): 
            record.weight -= 0.5; db.commit(); st.rerun()
        if w_col3.button("+0.5kg"): 
            record.weight += 0.5; db.commit(); st.rerun()
        if w_col4.button("+1.0kg"): 
            record.weight += 1.0; db.commit(); st.rerun()
            
        record.weight = st.number_input("직접 입력 (kg)", value=float(record.weight), step=0.1)
    
        st.write("**운동 및 수분**")
        record.exercise_time = st.number_input("운동 시간 (분)", value=int(record.exercise_time or 0), step=10)
        record.water = st.number_input("물 섭취 (L)", value=float(record.water or 0.0), step=0.1)
        
        st.write("**목표 체중 설정**")
        new_target = st.number_input("목표 체중 (kg)", value=float(goal.target_weight if goal else user.weight), step=0.1)
        
    st.write("") # 간격
    if st.button("전체 저장 및 업데이트", type="primary", use_container_width=True):
        user.weight = record.weight
        if not goal:
            goal = Goal(user_id=user.id, target_weight=new_target, target_date=sel_date_str)
            db.add(goal)
        else:
            goal.target_weight = new_target
        db.commit()
        st.success("저장되었습니다.")
        st.rerun()

with right_col:
    st.subheader("⌚ 스마트 워치 연동")
    if st.button(" Apple Watch 데이터 가져오기"):
        st.success("애플워치(HealthKit) 연동 시뮬레이션: 선택된 날짜의 활동 데이터가 성공적으로 동기화되었습니다!")
        
    st.divider()

    st.subheader("나의 통계 및 변화")
    records = db.query(DailyRecord).filter(DailyRecord.user_id == user.id).order_by(DailyRecord.date).all()
    
    if len(records) > 0:
        df = pd.DataFrame([{"날짜": r.date, "체중": r.weight, "운동시간": r.exercise_time} for r in records])
        
        tab_w, tab_e = st.tabs(["체중 변화 그래프", "운동량 변화 그래프"])
        with tab_w:
            fig_w = px.line(df, x="날짜", y="체중", markers=True)
            fig_w.update_layout(plot_bgcolor='#0A1128', paper_bgcolor='#0A1128', font=dict(color='#AEE2FF'))
            fig_w.update_traces(line_color="#AEE2FF", marker=dict(size=8))
            st.plotly_chart(fig_w, use_container_width=True)
        with tab_e:
            fig_e = px.bar(df, x="날짜", y="운동시간")
            fig_e.update_layout(plot_bgcolor='#0A1128', paper_bgcolor='#0A1128', font=dict(color='#AEE2FF'))
            fig_e.update_traces(marker_color="#89CFF0")
            st.plotly_chart(fig_e, use_container_width=True)
            
        st.subheader("최근 식단 일지")
        st.dataframe(
            df_meals := pd.DataFrame([{
                "날짜": r.date, 
                "아침": r.breakfast, 
                "점심": r.lunch, 
                "저녁": r.dinner
            } for r in records[-5:]]),
            use_container_width=True, hide_index=True
        )
        
        st.subheader("🤖 AI 맞춤 피드백")
        feedback = []
        if record.water < 2.0:
            feedback.append("💧 **수분 보충 필요**: 대사가 느려지지 않도록 하루 2L 이상의 물을 섭취해 주세요.")
        else:
            feedback.append("💧 **수분 충분**: 훌륭합니다! 붓기 제거와 대사 촉진에 좋은 습관입니다.")
            
        if (record.exercise_time or 0) < 30:
            feedback.append("🏃 **운동량 부족**: 오늘은 가벼운 스쿼트나 30분 걷기로 근성장을 자극해 보는 건 어떨까요?")
        else:
            feedback.append("🏃 **운동 목표 달성**: 좋은 페이스입니다! 현재 운동 패턴을 꾸준히 유지하세요.")
            
        if not record.breakfast and not record.lunch and not record.dinner:
            feedback.append("🥗 **식단 코칭**: 정확한 분석을 위해 식단을 기록해 주세요. (추천: 닭가슴살, 고구마, 야채 샐러드)")
        else:
            feedback.append("🥗 **식단 코칭**: 정제 탄수화물을 줄이고 단백질 비중을 높이면 포만감이 오래 유지됩니다.")
            
        for f in feedback:
            st.info(f)

    else:
        st.info("데이터가 충분하지 않습니다.")

db.close()
