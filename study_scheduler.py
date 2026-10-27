import streamlit as st
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
now = datetime.now(timezone(timedelta(hours=9)))

st.set_page_config(page_title='벼락치기 스케줄러', page_icon='📚', layout='centered')
st.title('📚 벼락치기 스케줄러')
st.caption('1단계 · 시험과 학습 정보를 입력해요')
st.info('과목을 먼저 등록한 뒤, 과목마다 시험 범위에 해당하는 단원을 추가해 주세요.')

if 'subjects' not in st.session_state:
    st.session_state.subjects = []

if st.button('시연용 예시 불러오기'):
    st.session_state.subjects.append({
        'id': str(uuid4()), 'name': '일반물리',
        'date': now.date() + timedelta(days=2), 'time': time(10, 0),
        'scope': '15~17장: 전기장, 전위, 축전기', 'hours': 4.0,
        'units': [
            {'name': '전기장', 'understanding': '낮음', 'importance': '높음', 'hours': 2.0},
            {'name': '전위', 'understanding': '보통', 'importance': '높음', 'hours': 2.0},
            {'name': '축전기', 'understanding': '높음', 'importance': '보통', 'hours': 1.0},
        ],
    })
    st.rerun()

st.subheader('1️⃣ 과목과 시험 정보')
with st.form('add_subject', clear_on_submit=True):
    name = st.text_input('과목명 *', placeholder='예: 일반물리')
    left, right = st.columns(2)
    with left:
        exam_date = st.date_input('시험 날짜 *', value=now.date(), min_value=now.date())
    with right:
        exam_time = st.time_input('시험 시간 *', value=time(9, 0), step=timedelta(minutes=10))
    scope = st.text_area('전체 학습 범위 *', placeholder='예: 15~17장, 강의자료 1~6주차')
    available = st.number_input('이 과목에 공부할 수 있는 총 시간 (시간)', min_value=0.0, value=0.0, step=0.5, help='아직 정하지 않았다면 0으로 두어도 돼요.')
    submitted = st.form_submit_button('과목 추가', type='primary')
    if submitted:
        if not name.strip() or not scope.strip():
            st.error('과목명과 전체 학습 범위를 입력해 주세요.')
        elif datetime.combine(exam_date, exam_time) <= now.replace(tzinfo=None):
            st.error('시험 일시는 현재보다 이후로 선택해 주세요.')
        else:
            st.session_state.subjects.append({'id': str(uuid4()), 'name': name.strip(), 'date': exam_date, 'time': exam_time, 'scope': scope.strip(), 'hours': available, 'units': []})
            st.rerun()

st.subheader('2️⃣ 단원별 학습 정보')
if not st.session_state.subjects:
    st.caption('먼저 위에서 과목을 추가해 주세요.')

for subject in st.session_state.subjects:
    sid = subject['id']
    with st.expander(f"📖 {subject['name']} · {subject['date']:%Y-%m-%d} {subject['time']:%H:%M}", expanded=True):
        st.write(f"**학습 범위:** {subject['scope']}")
        st.write(f"**공부 가능한 시간:** {subject['hours']:g}시간")
        with st.form(f'unit_{sid}', clear_on_submit=True):
            unit_name = st.text_input('단원명 *', placeholder='예: 전기장')
            a, b = st.columns(2)
            with a:
                understanding = st.selectbox('이해도', ['낮음', '보통', '높음'], help='해당 단원을 현재 얼마나 이해하고 있는지 선택해요.')
            with b:
                importance = st.selectbox('중요도', ['높음', '보통', '낮음'], help='시험에서 얼마나 중요한 단원인지 선택해요.')
            unit_hours = st.number_input('예상 학습량 (시간)', min_value=0.5, value=1.0, step=0.5, help='이 단원을 공부하는 데 필요할 것으로 예상되는 시간이에요.')
            add_unit = st.form_submit_button('단원 추가')
            if add_unit:
                if not unit_name.strip():
                    st.error('단원명을 입력해 주세요.')
                else:
                    subject['units'].append({'name': unit_name.strip(), 'understanding': understanding, 'importance': importance, 'hours': unit_hours})
                    st.rerun()
        if subject['units']:
            st.table([{'단원': u['name'], '이해도': u['understanding'], '중요도': u['importance'], '예상 학습량 (시간)': u['hours']} for u in subject['units']])
            total = sum(u['hours'] for u in subject['units'])
            st.write(f'**예상 학습량 합계: {total:g}시간**')
            if subject['hours'] > 0:
                if total > subject['hours']:
                    st.warning(f"공부 가능한 시간보다 {total - subject['hours']:g}시간이 더 필요해요.")
                else:
                    st.success('예상 학습량이 공부 가능한 시간 안에 들어와요.')
            for index, unit in enumerate(subject['units']):
                if st.button(f"🗑️ {unit['name']} 삭제", key=f'delete_{sid}_{index}'):
                    subject['units'].pop(index)
                    st.rerun()
        else:
            st.caption('아직 추가한 단원이 없어요.')
        if st.button('이 과목 삭제', key=f'delete_subject_{sid}'):
            st.session_state.subjects = [s for s in st.session_state.subjects if s['id'] != sid]
            st.rerun()

if st.session_state.subjects:
    st.subheader('3️⃣ 입력 현황')
    st.write(f"등록한 과목: {len(st.session_state.subjects)}개 · 등록한 단원: {sum(len(s['units']) for s in st.session_state.subjects)}개")
    st.info('현재는 정보 입력과 확인 단계예요. 자동 시간표 생성과 AI 기능은 아직 연결되지 않았어요.')
st.caption('입력 내용은 현재 브라우저 세션에만 보관돼요. 새로고침하거나 연결이 끊기면 사라질 수 있어요.')
