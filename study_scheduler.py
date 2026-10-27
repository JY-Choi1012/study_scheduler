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
if 'fixed_events' not in st.session_state:
    st.session_state.fixed_events = []

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
            prerequisite_options = [u['name'] for u in subject['units']]
            prerequisites = st.multiselect('먼저 공부해야 할 선수 단원', prerequisite_options, help='이미 추가한 같은 과목의 단원을 선택해요. 없다면 비워 두세요.')
            unit_hours = st.number_input('예상 학습량 (시간)', min_value=0.5, value=1.0, step=0.5, help='이 단원을 공부하는 데 필요할 것으로 예상되는 시간이에요.')
            add_unit = st.form_submit_button('단원 추가')
            if add_unit:
                if not unit_name.strip():
                    st.error('단원명을 입력해 주세요.')
                elif any(u['name'] == unit_name.strip() for u in subject['units']):
                    st.error('같은 과목 안에서 단원 이름은 다르게 입력해 주세요.')
                else:
                    subject['units'].append({'name': unit_name.strip(), 'understanding': understanding, 'importance': importance, 'hours': unit_hours, 'prerequisites': prerequisites})
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
                if unit.get('prerequisites'):
                    st.caption(f"{unit['name']}의 선수 단원: {', '.join(unit['prerequisites'])}")
                if st.button(f"🗑️ {unit['name']} 삭제", key=f'delete_{sid}_{index}'):
                    removed = subject['units'].pop(index)['name']
                    for other in subject['units']:
                        other['prerequisites'] = [x for x in other.get('prerequisites', []) if x != removed]
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

st.divider()
st.subheader('4️⃣ 고정 일정과 공부 가능 시간')
st.write('수업, 알바, 수면처럼 매주 반복되는 시간을 추가해 주세요.')
weekdays = ['월', '화', '수', '목', '금', '토', '일']
with st.form('fixed_event', clear_on_submit=True):
    event_name = st.text_input('일정 이름 *', placeholder='예: 수면, 수업, 알바')
    event_days = st.multiselect('반복 요일 *', weekdays, default=weekdays)
    c1, c2 = st.columns(2)
    with c1:
        event_start = st.time_input('시작 시간', value=time(23, 0), step=timedelta(minutes=10))
    with c2:
        event_end = st.time_input('종료 시간', value=time(7, 0), step=timedelta(minutes=10))
    st.caption('종료 시간이 시작 시간보다 이르면 다음 날 종료되는 일정으로 계산해요.')
    if st.form_submit_button('고정 일정 추가'):
        if not event_name.strip() or not event_days:
            st.error('일정 이름과 반복 요일을 입력해 주세요.')
        elif event_start == event_end:
            st.error('시작 시간과 종료 시간을 다르게 입력해 주세요.')
        else:
            st.session_state.fixed_events.append({'name': event_name.strip(), 'days': event_days, 'start': event_start, 'end': event_end})
            st.rerun()

for i, event in enumerate(st.session_state.fixed_events):
    c1, c2 = st.columns([4, 1])
    with c1:
        suffix = ' (다음 날 종료)' if event['end'] < event['start'] else ''
        st.write(f"**{event['name']}** · {', '.join(event['days'])} · {event['start']:%H:%M}~{event['end']:%H:%M}{suffix}")
    with c2:
        if st.button('삭제', key=f'event_delete_{i}'):
            st.session_state.fixed_events.pop(i)
            st.rerun()


def available_seconds(start, end, events):
    """고정 일정들의 합집합을 제외한다. start/end는 한국 시간의 naive datetime."""
    intervals = []
    day = start.date() - timedelta(days=1)
    while day <= end.date():
        for event in events:
            if weekdays[day.weekday()] not in event['days']:
                continue
            a = datetime.combine(day, event['start'])
            b = datetime.combine(day, event['end'])
            if b <= a:
                b += timedelta(days=1)
            a, b = max(a, start), min(b, end)
            if a < b:
                intervals.append((a, b))
        day += timedelta(days=1)
    intervals.sort()
    merged = []
    for a, b in intervals:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return max(0.0, (end - start).total_seconds() - sum((b - a).total_seconds() for a, b in merged))


def priority_order(subjects, current):
    """점수 우선순위와 선수 관계를 함께 반영한 위상 정렬."""
    rows = []
    for subject in subjects:
        exam_at = datetime.combine(subject['date'], subject['time'])
        remaining = (exam_at - current).total_seconds() / 3600
        if remaining <= 0:
            continue
        urgency = 3 if remaining <= 24 else 2 if remaining <= 72 else 1
        for unit in subject['units']:
            score = urgency * 3 + {'높음': 3, '보통': 2, '낮음': 1}[unit['importance']] * 2 + {'낮음': 3, '보통': 2, '높음': 1}[unit['understanding']] * 2
            rows.append({'key': (subject['id'], unit['name']), 'subject': subject, 'unit': unit, 'score': score, 'exam': exam_at, 'remaining': remaining})
    ordered, done = [], set()
    while len(ordered) < len(rows):
        ready = [r for r in rows if r['key'] not in done and all((r['subject']['id'], p) in done for p in r['unit'].get('prerequisites', []))]
        if not ready:
            return ordered, False
        best = min(ready, key=lambda r: (-r['score'], r['exam'], r['subject']['name'], r['unit']['name']))
        ordered.append(best)
        done.add(best['key'])
    return ordered, True

current = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
future_subjects = [s for s in st.session_state.subjects if datetime.combine(s['date'], s['time']) > current]
if future_subjects:
    last_exam = max(datetime.combine(s['date'], s['time']) for s in future_subjects)
    if last_exam > current + timedelta(days=60):
        st.warning('마지막 시험이 60일보다 멀리 있어요. 기간 계산을 위해 시험일을 60일 이내로 입력해 주세요.')
    else:
        st.caption('현재 시각부터 마지막 시험 시작까지를 계산해요. 식사·이동·휴식 등도 고정 일정에 넣어 주세요.')
        available = available_seconds(current, last_exam, st.session_state.fixed_events) / 3600
        st.metric('전체 공부 가능 시간', f'{available:.1f}시간')
        per_subject = []
        for s in sorted(future_subjects, key=lambda x: (x['date'], x['time'])):
            exam_at = datetime.combine(s['date'], s['time'])
            free = available_seconds(current, exam_at, st.session_state.fixed_events) / 3600
            per_subject.append({'과목': s['name'], '시험 전까지 비어 있는 시간': f'{free:.1f}시간'})
        st.table(per_subject)
        st.caption('과목별 시간은 같은 빈 시간을 함께 포함해요. 과목마다 따로 확보된 시간이 아니므로 서로 더하지 마세요.')
        needed = sum(u['hours'] for s in future_subjects for u in s['units'])
        st.write(f'등록한 단원의 예상 학습량 합계: **{needed:g}시간**')
        if needed > available:
            st.warning(f'전체 빈 시간보다 예상 학습량이 {needed - available:.1f}시간 많아요.')
        for s in future_subjects:
            exam_at = datetime.combine(s['date'], s['time'])
            due_needed = sum(u['hours'] for other in future_subjects if datetime.combine(other['date'], other['time']) <= exam_at for u in other['units'])
            due_free = available_seconds(current, exam_at, st.session_state.fixed_events) / 3600
            if due_needed > due_free:
                st.warning(f"{s['name']} 시험 시점까지 필요한 학습량이 빈 시간보다 {due_needed - due_free:.1f}시간 많아요.")
else:
    st.caption('앞으로 예정된 시험을 등록하면 공부 가능 시간이 계산돼요.')

st.divider()
st.subheader('5️⃣ 학습 우선순위 제안')
st.caption('시험이 가까울수록, 중요도가 높을수록, 이해도가 낮을수록 높은 점수예요. 선수 단원은 해당 단원보다 먼저 배치해요.')
ranked, valid = priority_order(st.session_state.subjects, current)
if not valid:
    st.error('선수 단원 관계를 확인해 주세요. 서로 먼저 공부해야 하는 관계는 만들 수 없어요.')
if ranked:
    for rank, item in enumerate(ranked, 1):
        u, s = item['unit'], item['subject']
        deps = ', '.join(u.get('prerequisites', [])) or '없음'
        st.write(f"**{rank}. {s['name']} · {u['name']}** — {item['score']}점")
        st.caption(f"시험까지 약 {item['remaining']:.1f}시간 · 중요도 {u['importance']} · 이해도 {u['understanding']} · 선수 단원 {deps} · 예상 {u['hours']:g}시간")
    st.caption('점수 기준: 시험까지 24시간 이내 9점, 72시간 이내 6점, 그 외 3점 + 중요도 2~6점 + 이해도(낮을수록) 2~6점. 선수 관계에 따라 점수보다 순서가 앞설 수 있어요.')
else:
    st.caption('과목과 단원을 추가하면 추천 순서가 나타나요.')
st.info('이 순서는 입력값을 바탕으로 한 규칙 기반 추천이에요. 자동 시간표와 AI 분석은 아직 연결되지 않았어요.')
