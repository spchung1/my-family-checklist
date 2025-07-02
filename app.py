import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import plotly.express as px

# --- Supabase 연결 ---
SUPABASE_URL = "https://vvwybayxvlzzefhfsczu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2d3liYXl4dmx6emVmaGZzY3p1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzNjAxNzIsImV4cCI6MjA2NjkzNjE3Mn0.43HOMrnUPInvaASdep_oi_2ybPCXts8TM_IAtRCrrdc"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase 연결에 실패했습니다: {e}")
    st.stop()

# --- 기본 정보 및 UI 설정 ---
st.set_page_config(layout="wide")
st.title("👨‍👩‍👦‍👦 우리 가족 성장 챌린지")

# --- 규칙 정의 ---
CHILDREN = ["정은용", "정윤용", "정원용"]
COMMON_ITEMS_DESC = {
    "item_1_checked": "거짓말 않기", "item_2_checked": "욕설 금지", "item_3_checked": "형제 폭력 금지",
    "item_4_checked": "학원 정시 출석", "item_5_checked": "숙제 완수", "item_6_checked": "타 스마트폰 사용 않기",
    "item_7_checked": "PC방 무단출입 금지", "item_8_checked": "물건 훔치지 않기", "item_9_checked": "정량 식사",
}
PERSONAL_ITEMS_DESC = {
    "정은용": {"item_10_checked": "서피스탭 규칙 사용", "item_11_checked": "한의원 무단 외출 않기"},
    "정윤용": {"item_10_checked": "방과 후 배회 않기", "item_11_checked": "부모님 말씀에 어깃장 놓지 않기"},
    "정원용": {"item_10_checked": "스마트폰 조르지 않기", "item_11_checked": "방과 후 무단 체류 없음"},
}
ALL_ITEMS_DESC = {**COMMON_ITEMS_DESC, **PERSONAL_ITEMS_DESC["정은용"], **PERSONAL_ITEMS_DESC["정윤용"], **PERSONAL_ITEMS_DESC["정원용"]}

# --- 대시보드 표시 함수 ---
def display_dashboard(child_name_filter=None):
    # ... (함수 상단 내용은 이전과 동일) ...
    if child_name_filter:
        st.header(f"나의 주간 성과 대시보드")
    else:
        st.header("주간 성과 대시보드")

    try:
        today = datetime.date.today()
        seven_days_ago = today - datetime.timedelta(days=7)
        response = supabase.table("daily_checks").select("*").gte("date", seven_days_ago).lte("date", today).execute()
        records = response.data

        if not records:
            st.info("최근 7일간의 기록이 없습니다.")
            return

        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        selected_option = None # selected_option 초기화
        if child_name_filter:
            df_filtered = df[df['child_name'] == child_name_filter]
        else:
            st.sidebar.header("대시보드 필터")
            filter_options = ["전체 보기"] + CHILDREN
            selected_option = st.sidebar.radio("아이 선택:", options=filter_options)
            if selected_option == "전체 보기":
                df_filtered = df
            else:
                df_filtered = df[df['child_name'] == selected_option]

        if df_filtered.empty:
            st.warning("선택된 기간에 해당 기록이 없습니다.")
            return
        
        total_earned = df_filtered['total_score'].sum()
        total_possible = len(df_filtered) * 110
        achievement_rate = (total_earned / total_possible) * 100 if total_possible > 0 else 0

        col1, col2 = st.columns(2)
        col1.metric("달성률", f"{achievement_rate:.1f} %")
        col2.metric("평균 점수 (110점 만점)", f"{df_filtered['total_score'].mean():.1f} 점")
        st.markdown("---")
        
        st.subheader("📊 일일 점수 변화")
        fig_daily_score = px.bar(df_filtered, x='date', y='total_score', color='child_name' if not child_name_filter else None,
                                 labels={'date': '날짜', 'total_score': '점수', 'child_name': '아이'},
                                 color_discrete_map={"정은용": "#636EFA", "정윤용": "#EF553B", "정원용": "#00CC96"})
        st.plotly_chart(fig_daily_score, use_container_width=True)

        st.subheader("👍 항목별 성공률")
        rule_columns = [col for col in df_filtered.columns if 'item_' in col]
        success_counts = df_filtered[rule_columns].sum()
        total_counts = len(df_filtered)
        rule_success_rate = (success_counts / total_counts * 100).dropna().sort_values(ascending=True)
        
        # --- ✨✨✨ 버그 수정된 부분 시작 ✨✨✨ ---
        # 현재 선택된 아이에 맞는 규칙 설명 목록을 동적으로 생성합니다.
        if selected_option and selected_option != "전체 보기":
            # 특정 아이가 선택된 경우
            current_mapping_dict = {**COMMON_ITEMS_DESC, **PERSONAL_ITEMS_DESC[selected_option]}
        else:
            # '전체 보기' 또는 아이 전용 뷰일 경우 (모든 규칙 포함)
            current_mapping_dict = ALL_ITEMS_DESC
        
        rule_success_rate.index = rule_success_rate.index.map(current_mapping_dict)
        # --- ✨✨✨ 버그 수정된 부분 끝 ✨✨✨ ---

        fig_rule_rate = px.bar(rule_success_rate, x=rule_success_rate.values, y=rule_success_rate.index,
                               orientation='h', labels={'x': '성공률 (%)', 'y': '규칙 항목'})
        fig_rule_rate.update_layout(xaxis_range=[0, 100])
        st.plotly_chart(fig_rule_rate, use_container_width=True)

    except Exception as e:
        st.error(f"대시보드를 불러오는 중 오류가 발생했습니다: {e}")

# --- URL 파라미터를 읽어 뷰(View) 결정 ---
view_mode = st.query_params.get("view")

if view_mode in CHILDREN:
    # 아이들용 전용 뷰
    display_dashboard(child_name_filter=view_mode)
else:
    # 아버님용 뷰
    tab1, tab2 = st.tabs(["📊 대시보드", "📝 기록 관리"])
    with tab1:
        display_dashboard()
    with tab2:
        # 기록 관리 탭 내용 (이전과 동일)
        st.header("기록 입력 및 관리")
        with st.expander("오늘의 기록 입력하기 ✏️", expanded=True):
            selected_child_form = st.selectbox("기록할 아이", CHILDREN, key="form_child_select")
            with st.form(key=f"check_form_{selected_child_form}", clear_on_submit=True):
                st.write(f"--- **{selected_child_form}**의 체크리스트 ---")
                selected_date = st.date_input("기록할 날짜", datetime.date.today())
                checked_status = {}
                child_items = {**COMMON_ITEMS_DESC, **PERSONAL_ITEMS_DESC[selected_child_form]}
                for key, text in child_items.items():
                    checked_status[key] = st.checkbox(text)
                submitted = st.form_submit_button("저장하기")
                if submitted:
                    score = sum(10 for checked in checked_status.values() if checked)
                    data_to_insert = {"date": str(selected_date), "child_name": selected_child_form, "total_score": score, **checked_status}
                    try:
                        response = supabase.table("daily_checks").select("id").eq("date", str(selected_date)).eq("child_name", selected_child_form).execute()
                        if response.data:
                             st.warning(f"⚠️ {selected_date} {selected_child_form}의 기록은 이미 존재합니다.")
                        else:
                            supabase.table("daily_checks").insert(data_to_insert).execute()
                            st.success(f"🎉 {selected_date} {selected_child_form}의 기록({score}점)이 성공적으로 저장되었습니다!")
                    except Exception as e:
                        st.error(f"데이터 저장 중 오류가 발생했습니다: {e}")
        st.markdown("---")
        st.subheader("기록 수정 또는 삭제")
        try:
            response = supabase.table("daily_checks").select("*").order("date", desc=True).limit(50).execute()
            records_manage = response.data
            if records_manage:
                record_options = {r['id']: f"{r['date']} - {r['child_name']} ({r['total_score']}점)" for r in records_manage}
                selected_id_to_manage = st.selectbox("관리할 기록을 선택하세요.", options=list(record_options.keys()), format_func=lambda x: record_options[x])
                if selected_id_to_manage:
                    record_to_edit = next((r for r in records_manage if r['id'] == selected_id_to_manage), None)
                    with st.form(f"edit_form_{selected_id_to_manage}"):
                        st.write(f"**{record_to_edit['date']} / {record_to_edit['child_name']}** 기록 수정")
                        edit_checked_status = {}
                        items_to_edit = {**COMMON_ITEMS_DESC, **PERSONAL_ITEMS_DESC[record_to_edit['child_name']]}
                        for key, text in items_to_edit.items():
                            edit_checked_status[key] = st.checkbox(text, value=record_to_edit.get(key, False), key=f"edit_{record_to_edit['id']}_{key}")
                        col1, col2, _ = st.columns([1, 1, 4])
                        update_button = col1.form_submit_button("수정하기")
                        delete_button = col2.form_submit_button("삭제하기")
                        if update_button:
                            new_score = sum(10 for checked in edit_checked_status.values() if checked)
                            data_to_update = {"total_score": new_score, **edit_checked_status}
                            supabase.table("daily_checks").update(data_to_update).eq("id", selected_id_to_manage).execute()
                            st.success("기록이 성공적으로 수정되었습니다!"); st.rerun()
                        if delete_button:
                            supabase.table("daily_checks").delete().eq("id", selected_id_to_manage).execute()
                            st.success("기록이 성공적으로 삭제되었습니다!"); st.rerun()
        except Exception as e:
            st.error(f"기록 관리 섹션을 불러오는 중 오류 발생: {e}")