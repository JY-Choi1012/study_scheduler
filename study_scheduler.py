import streamlit as st
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
now = datetime.now(timezone(timedelta(hours=9)))

st.set_page_config(page_title='벼락치기 스케줄러', page_icon='📚', layout='centered')
import re


def quick_plan(topics_text, difficult_text, important_text, hours):
    """입력한 학습 가능 시간을 단원과 마무리 복습에 정확히 나눈다."""
    topics = list(dict.fromkeys(t.strip() for t in re.split(r"[,\n]", topics_text) if t.strip()))
    difficult = [x.strip().casefold() for x in re.split(r"[,\n]", difficult_text) if x.strip()]
    important = [x.strip().casefold() for x in re.split(r"[,\n]", important_text) if x.strip()]
    total = round(hours * 60)
    review = round(total * 0.1) if total >= 60 else 0
    budget = total - review
    def matches(topic, terms):
        name = topic.casefold()
        return any(term in name or name in term for term in terms)
    weights = [1 + int(matches(t, difficult)) + int(matches(t, important)) for t in topics]
    raw = [budget * w / sum(weights) for w in weights]
    minutes = [int(x) for x in raw]
    for idx in sorted(range(len(topics)), key=lambda i: (-(raw[i] - minutes[i]), i))[:budget - sum(minutes)]:
        minutes[idx] += 1
    rows = []
    for i in sorted(range(len(topics)), key=lambda i: (-weights[i], i)):
        reasons = []
        if matches(topics[i], difficult): reasons.append('어려운 내용')
        if matches(topics[i], important): reasons.append('강조한 내용')
        rows.append({'내용': topics[i], '분': minutes[i], '이유': ' · '.join(reasons) or '입력한 시험 범위'})
    if review:
        rows.append({'내용': '전체 핵심 복습', '분': review, '이유': '마지막으로 핵심 내용을 확인'})
    return rows


def minutes_label(n):
    return f"{n // 60}시간 {n % 60}분" if n >= 60 and n % 60 else (f"{n // 60}시간" if n >= 60 else f"{n}분")


st.title('📚 벼락치기 플래너')
st.caption('시험까지 남은 시간에 맞춰 공부 순서와 시간을 정해요.')
quick_tab, detail_tab, agent_tab = st.tabs(['⚡ 빠른 계획 만들기', '⚙️ 자세히 설정하기', '🧭 학습 실행·재계획'])
with quick_tab:
    st.subheader('⚡ 빠른 계획 만들기')
    st.write('과목과 시험 정보, 공부할 내용과 시간을 입력해 주세요.')
    st.caption('이름, 연락처 없이 사용할 수 있어요. 입력 내용은 새로고침하면 사라질 수 있어요.')
    with st.form('quick_plan_form'):
        quick_subject = st.text_input('무슨 시험을 준비하나요? *', placeholder='예: 일반물리')
        col_date, col_time = st.columns(2)
        with col_date:
            quick_date = st.date_input('시험 날짜 *', value=now.date(), min_value=now.date(), key='quick_date')
        with col_time:
            quick_time = st.time_input('시험 시간 *', value=time(9, 0), step=timedelta(minutes=10), key='quick_time')
        quick_topics = st.text_area('공부할 내용을 적어 주세요 *', placeholder='예: 전기장, 전위, 축전기', help='내용을 쉼표나 줄바꿈으로 구분해 주세요. 입력한 내용대로 계획을 만들어요.')
        quick_hours = st.number_input('시험 전까지 공부할 수 있는 총 시간 *', min_value=0.5, max_value=200.0, value=3.0, step=0.5, format='%.1f 시간')
        st.markdown('**조금 더 맞춤으로 만들기** · 선택 사항')
        quick_difficult = st.text_input('어려운 내용이 있나요?', placeholder='예: 전위')
        quick_important = st.text_input('교수님이 강조한 내용이 있나요?', placeholder='예: 전기장, 축전기')
        submit_quick = st.form_submit_button('⚡ 나만의 벼락치기 계획 만들기', type='primary')
    if submit_quick:
        current_quick = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
        exam_quick = datetime.combine(quick_date, quick_time)
        topics = [x.strip() for x in re.split(r"[,\n]", quick_topics) if x.strip()]
        if not quick_subject.strip() or not topics:
            st.error('과목명과 공부할 내용을 입력해 주세요.')
        elif exam_quick <= current_quick:
            st.error('시험 날짜와 시간을 현재보다 이후로 선택해 주세요.')
        elif len(set(topics)) > 30:
            st.error('공부할 내용은 최대 30개까지 입력해 주세요.')
        else:
            st.session_state['quick_result'] = {'subject': quick_subject.strip(), 'exam': exam_quick, 'hours': quick_hours, 'rows': quick_plan(quick_topics, quick_difficult, quick_important, quick_hours), 'remaining': (exam_quick-current_quick).total_seconds()/3600, 'generated': current_quick}
    if st.session_state.get('quick_result'):
        result_quick = st.session_state['quick_result']
        st.divider()
        st.subheader('📋 나의 벼락치기 계획')
        st.write(f"**{result_quick['subject']}** · 시험 {result_quick['exam']:%m월 %d일 %H:%M}")
        st.write(f"공부 가능 시간 **{result_quick['hours']:g}시간** · 계획 생성 시 시험까지 약 {result_quick['remaining']:.1f}시간")
        if result_quick['hours'] > result_quick['remaining']:
            st.warning('입력한 공부 시간이 시험까지 남은 전체 시간보다 길어요. 공부 가능 시간을 다시 확인해 주세요.')
        st.table([{'순서': str(i), '공부 내용': row['내용'], '추천 시간': minutes_label(row['분']), '추천 이유': row['이유']} for i, row in enumerate(result_quick['rows'], 1)])
        st.caption('어렵거나 강조한 내용을 공부할 내용과 같은 단어로 입력하면 더 많은 시간을 배정해요. 입력값을 바꾸면 버튼을 다시 눌러 주세요.')
        st.info('이 계획은 입력한 내용을 기준으로 시간을 나눈 간단한 추천이에요. 실제 시간대 배치와 더 자세한 설정은 「자세히 설정하기」에서 이용할 수 있어요.')
    st.caption('정확한 단원 이름을 모른다면 교재에서 단원 제목을 확인해 쉼표로 구분해 적어 주세요.')
with detail_tab:
    st.subheader('⚙️ 자세히 설정하기')
    st.caption('빠른 계획과 별도로 과목, 단원, 고정 일정을 등록해요.')
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

    st.divider()
    st.subheader('6️⃣ 자동 학습 시간표')
    st.write('등록한 고정 일정과 시험 일시를 고려해 공부할 단원을 배치해요.')
    st.caption('30분 단위로 배치하며, 현재 시각 다음의 정각 또는 30분부터 시작해요. 식사·이동·휴식과 시험 시간도 필요하면 고정 일정에 추가해 주세요.')


    def make_schedule(subjects, events, current, days):
        """30분 단위로 일정 합집합을 피하고 시험 마감 및 선수 관계를 지킨다."""
        from math import ceil

        start = current.replace(second=0, microsecond=0)
        start += timedelta(minutes=(-start.minute) % 30)
        if start < current:
            start += timedelta(minutes=30)
        stop = current + timedelta(days=days)
        tasks = []
        for subject in subjects:
            exam_at = datetime.combine(subject['date'], subject['time'])
            if exam_at <= current:
                continue
            for unit in subject['units']:
                tasks.append({'key': (subject['id'], unit['name']), 'subject': subject,
                              'unit': unit, 'exam': exam_at,
                              'remaining': round(float(unit['hours']) * 60)})
        schedule = []
        cursor = start
        while cursor + timedelta(minutes=30) <= stop:
            slot_end = cursor + timedelta(minutes=30)
            if available_seconds(cursor, slot_end, events) < 30 * 60:
                cursor = slot_end
                continue
            done = {t['key'] for t in tasks if t['remaining'] <= 0}
            ready = [t for t in tasks if t['remaining'] > 0 and slot_end <= t['exam']
                     and all((t['subject']['id'], dep) in done for dep in t['unit'].get('prerequisites', []))]
            if ready:
                def order_key(t):
                    hours_left = (t['exam'] - cursor).total_seconds() / 3600
                    urgency = 3 if hours_left <= 24 else 2 if hours_left <= 72 else 1
                    score = urgency * 3 + {'높음': 3, '보통': 2, '낮음': 1}[t['unit']['importance']] * 2 + {'낮음': 3, '보통': 2, '높음': 1}[t['unit']['understanding']] * 2
                    return (-score, t['exam'], t['subject']['name'], t['unit']['name'])
                task = min(ready, key=order_key)
                task['remaining'] -= 30
                if schedule and schedule[-1]['key'] == task['key'] and schedule[-1]['end'] == cursor and schedule[-1]['start'].date() == cursor.date():
                    schedule[-1]['end'] = slot_end
                else:
                    schedule.append({'key': task['key'], 'subject': task['subject']['name'], 'unit': task['unit']['name'], 'start': cursor, 'end': slot_end})
            cursor = slot_end
        remaining = [t for t in tasks if t['remaining'] > 0]
        return schedule, remaining, start, stop

    if 'generated_schedule' not in st.session_state:
        st.session_state.generated_schedule = None
    period = st.number_input('시간표를 만들 기간 (일)', min_value=1, max_value=60, value=7, step=1, help='현재 시각부터 선택한 일수까지 만들어요. 시험이 먼저 있으면 해당 단원은 시험 전에만 배치해요.')
    if st.button('📅 자동 시간표 만들기', type='primary'):
        if not any(s['units'] for s in future_subjects):
            st.warning('아직 예정된 시험의 단원이 없어요. 과목과 단원을 먼저 등록해 주세요.')
        elif not st.session_state.fixed_events:
            st.warning('고정 일정이 없어요. 수면·식사·이동 등도 일정에 넣은 뒤 시간표를 만들어 주세요.')
        else:
            st.session_state.generated_schedule = make_schedule(st.session_state.subjects, st.session_state.fixed_events, datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None), int(period))
            st.rerun()

    result = st.session_state.generated_schedule
    if result is not None:
        blocks, unscheduled, start, stop = result
        st.caption(f'생성 범위: {start:%Y-%m-%d %H:%M}부터 {stop:%Y-%m-%d %H:%M}까지 · 한국 시간')
        st.warning('과목이나 단원, 고정 일정을 바꿨다면 「자동 시간표 만들기」를 다시 눌러 주세요.')
        if blocks:
            st.table([{'날짜': b['start'].strftime('%Y-%m-%d'), '시간': f"{b['start']:%H:%M}~{b['end']:%H:%M}", '과목': b['subject'], '단원': b['unit'], '학습 시간': f"{(b['end']-b['start']).total_seconds()/3600:g}시간"} for b in blocks])
            st.success(f"총 {sum((b['end'] - b['start']).total_seconds() for b in blocks)/3600:g}시간을 배치했어요.")
        else:
            st.warning('선택한 기간에 배치할 수 있는 30분짜리 시간이 없어요. 고정 일정과 기간을 확인해 주세요.')
        if unscheduled:
            st.warning('아래 학습량은 선택한 기간 또는 해당 시험 전까지 배치하지 못했어요.')
            st.table([{'과목': t['subject']['name'], '단원': t['unit']['name'], '남은 학습량': f"{t['remaining']/60:g}시간", '시험 일시': t['exam'].strftime('%Y-%m-%d %H:%M')} for t in unscheduled])
            st.caption('기간을 늘리거나 고정 일정, 예상 학습량, 선수 단원 관계를 확인해 주세요.')
        elif blocks:
            st.success('예정된 시험의 등록 단원을 모두 배치했어요!')

# 학습 실행 기능은 AI 없이 계산되는 독립적인 시연용 흐름입니다.
def agent_decompose(units, exam_at, now_at):
    activities = [('개념 학습', 0.4), ('문제 풀이', 0.4), ('복습', 0.2)]
    tasks = []
    for unit in units:
        total = int(unit['minutes'])
        parts = [int(total * ratio) for _, ratio in activities]
        parts[-1] += total - sum(parts)
        previous = None
        urgency = 3 if (exam_at - now_at).total_seconds() <= 86400 else 2 if (exam_at - now_at).total_seconds() <= 259200 else 1
        score = 2 * len(unit['evidence']) + 2 * (5 - unit['understanding']) + 3 * urgency
        for (kind, _), mins in zip(activities, parts):
            if mins == 0:
                continue
            tid = str(uuid4())
            tasks.append({'id': tid, 'unit': unit['name'], 'subject': unit['subject'], 'type': kind,
                          'title': f"{unit['name']} · {kind}", 'estimated': mins, 'remaining': mins,
                          'score': score, 'evidence': list(unit['evidence']),
                          'understanding': unit['understanding'], 'prereq': [previous] if previous else [],
                          'status': '대기', 'actual': 0, 'exam': exam_at})
            previous = tid
    return tasks


def triage_plan(tasks, available):
    """완료 과제와 선수 관계를 지키며 정해진 분량 안에 부분 배정한다."""
    planned, remaining_budget = [], max(0, int(available))
    done = {t['id'] for t in tasks if t['status'] == '완료'}
    pending = [t for t in tasks if t['status'] != '완료' and t['remaining'] > 0]
    included = set(done)
    while pending:
        ready = [t for t in pending if all(p in included for p in t['prereq'])]
        if not ready:
            break
        task = min(ready, key=lambda t: (t['exam'], -t['score'], t['title']))
        allocated = min(task['remaining'], remaining_budget)
        remaining_budget -= allocated
        planned.append({'id': task['id'], 'allocated': allocated, 'missing': task['remaining'] - allocated})
        pending.remove(task)
        if allocated == task['remaining']:
            included.add(task['id'])
    for task in pending:
        planned.append({'id': task['id'], 'allocated': 0, 'missing': task['remaining']})
    return planned


def correction_factor(logs, subject):
    records = [x['actual'] / x['estimated'] for x in logs if x['subject'] == subject and x['estimated'] > 0 and x['status'] in ('완료', '이해 부족')]
    if not records:
        return 1.0
    weight = len(records) / (len(records) + 1)
    return max(0.7, min(1.8, (1 - weight) + weight * sum(records) / len(records)))

with agent_tab:
    st.header('🧭 학습 실행과 재계획')
    st.caption('AI 연결 전 규칙 기반 시연 버전이에요. 아래 입력은 다른 탭과 별도로 관리돼요.')
    if 'agent_units' not in st.session_state:
        st.session_state.agent_units = []
    if 'agent_logs' not in st.session_state:
        st.session_state.agent_logs = []
    if 'agent_tasks' not in st.session_state:
        st.session_state.agent_tasks = []
    if 'agent_proposal' not in st.session_state:
        st.session_state.agent_proposal = None
    if 'agent_plan' not in st.session_state:
        st.session_state.agent_plan = []
    if 'agent_capacity' not in st.session_state:
        st.session_state.agent_capacity = 0
    if 'agent_exam' not in st.session_state:
        st.session_state.agent_exam = None
    st.markdown('#### 1. 시험과 단원 등록')
    st.caption('하나의 과목을 먼저 등록해 시연할 수 있어요. 단원은 여러 개 추가할 수 있어요.')
    with st.form('agent_unit_form', clear_on_submit=False):
        subject_in = st.text_input('과목명', key='agent_subject_input', placeholder='예: 일반물리')
        ca, cb = st.columns(2)
        with ca:
            exam_date_in = st.date_input('시험 날짜', min_value=now.date(), value=now.date() + timedelta(days=3), key='agent_date_input')
        with cb:
            exam_time_in = st.time_input('시험 시간', value=time(9), key='agent_time_input')
        unit_in = st.text_input('단원명', placeholder='예: 전기장')
        understanding_in = st.selectbox('현재 이해도', [1, 2, 3, 4], format_func=lambda x: {1:'1 · 처음 봄',2:'2 · 개념은 들어봄',3:'3 · 설명할 수 있음',4:'4 · 문제를 풀 수 있음'}[x])
        evidence_in = st.multiselect('중요도 근거 (해당되는 것만)', ['배점 높음', '교수 강조', '기출 빈출'])
        estimate_in = st.number_input('이 단원에 필요한 예상 시간 (분)', min_value=30, max_value=3000, value=120, step=30, help='직접 바꿀 수 있어요. 개념·문제·복습 시간의 합계예요.')
        if st.form_submit_button('단원 추가'):
            exam_dt = datetime.combine(exam_date_in, exam_time_in)
            current_agent = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
            if not subject_in.strip() or not unit_in.strip():
                st.error('과목명과 단원명을 입력해 주세요.')
            elif exam_dt <= current_agent:
                st.error('시험 일시는 현재보다 이후여야 해요.')
            elif st.session_state.agent_units and (subject_in.strip() != st.session_state.agent_units[0]['subject'] or exam_dt != st.session_state.agent_exam):
                st.error('이 시연 화면은 한 과목과 한 시험만 지원해요. 같은 시험 정보를 입력해 주세요.')
            elif any(u['name'] == unit_in.strip() for u in st.session_state.agent_units):
                st.error('단원명은 중복할 수 없어요.')
            else:
                st.session_state.agent_exam = exam_dt
                st.session_state.agent_units.append({'subject': subject_in.strip(), 'name': unit_in.strip(), 'understanding': understanding_in, 'evidence': evidence_in, 'minutes': estimate_in})
                st.rerun()
    if st.session_state.agent_units:
        st.table([{'단원':u['name'], '이해도':u['understanding'], '근거': ', '.join(u['evidence']) or '입력 없음', '예상 시간':minutes_label(u['minutes'])} for u in st.session_state.agent_units])
    st.markdown('#### 2. 공부 가능 시간과 계획')
    st.caption('수업·알바·수면·식사·휴식 시간을 뺀 뒤 실제로 공부할 수 있는 총 시간을 입력해 주세요.')
    capacity_h = st.number_input('공부 가능 시간 (시간)', min_value=0.5, max_value=200.0, value=8.0, step=0.5, key='agent_capacity_input')
    if st.button('과제 나누고 계획 만들기', key='agent_create', type='primary'):
        current_agent = datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)
        if not st.session_state.agent_units:
            st.error('단원을 먼저 추가해 주세요.')
        elif st.session_state.agent_exam <= current_agent:
            st.error('시험 시간이 지났어요. 시험 정보를 확인해 주세요.')
        elif capacity_h * 60 > (st.session_state.agent_exam - current_agent).total_seconds()/60:
            st.error('공부 가능 시간이 시험까지 남은 전체 시간보다 많아요. 다시 확인해 주세요.')
        else:
            st.session_state.agent_tasks = agent_decompose(st.session_state.agent_units, st.session_state.agent_exam, current_agent)
            st.session_state.agent_capacity = int(capacity_h * 60)
            st.session_state.agent_logs = []
            st.session_state.agent_plan = triage_plan(st.session_state.agent_tasks, st.session_state.agent_capacity)
            st.session_state.agent_proposal = None
            st.rerun()
    if st.session_state.agent_tasks:
        tasks = st.session_state.agent_tasks
        task_by_id = {t['id']: t for t in tasks}
        plan = st.session_state.agent_plan
        needed = sum(t['remaining'] for t in tasks if t['status'] != '완료')
        spent = sum(log['actual'] for log in st.session_state.agent_logs)
        available_left = max(0, st.session_state.agent_capacity - spent)
        short = max(0, needed - available_left)
        st.markdown('#### 3. 오늘 할 일과 시간 부족 확인')
        st.write(f'필요 **{minutes_label(needed)}** / 남은 가용 **{minutes_label(available_left)}** / 부족 **{minutes_label(short)}**')
        if short:
            st.warning('시간이 부족해요. 배정된 과제를 먼저 확인하고, 제외된 학습량을 살펴보세요.')
        st.progress(min(1.0, available_left / needed) if needed else 1.0, text='필요한 시간 대비 남은 가용 시간')
        table = []
        for item in plan:
            t = task_by_id.get(item['id'])
            if not t or t['status'] == '완료': continue
            category = '필수' if item['allocated'] == t['remaining'] and t['score'] >= 12 else ('권장' if item['allocated'] else '선택')
            table.append({'과제': t['title'], '분류':category, '배정':minutes_label(item['allocated']), '미배정':minutes_label(item['missing']), '근거': ', '.join(t['evidence']) or '사용자 입력 기준', '점수':t['score']})
        if table: st.table(table)
        st.caption('필수·권장·선택은 현재 입력과 배정 결과에 따른 시연용 분류이며, 실제 시험 출제를 보장하지 않아요.')
        st.caption('점수: 중요도 근거 1개당 2점 + (5−이해도)×2점 + 시험 임박도 3~9점. 시험이 빠른 과목을 먼저 고려해요.')
        st.markdown('#### 4. 학습 기록')
        actionable = [t for t in tasks if t['status'] != '완료' and t['remaining'] > 0 and all(task_by_id[p]['status']=='완료' for p in t['prereq'] if p in task_by_id)]
        if actionable:
            with st.form('agent_log_form'):
                chosen = st.selectbox('기록할 과제', [t['id'] for t in actionable], format_func=lambda x: task_by_id[x]['title'])
                outcome = st.selectbox('학습 결과', ['완료', '일부 완료', '미완료', '이해 부족'])
                actual = st.number_input('실제 공부한 시간 (분)', min_value=0, max_value=1440, value=30, step=5)
                left_minutes = st.number_input('일부 완료 또는 미완료일 때 남은 분량 (분)', min_value=0, max_value=3000, value=30, step=5)
                if st.form_submit_button('학습 기록 저장'):
                    t = task_by_id[chosen]
                    if outcome in ('일부 완료','미완료') and left_minutes <= 0:
                        st.error('남은 분량을 0보다 크게 입력해 주세요.')
                    else:
                        st.session_state.agent_logs.append({'subject':t['subject'],'task':t['title'],'estimated':t['remaining'],'actual':actual,'status':outcome})
                        t['actual'] += actual
                        if outcome in ('완료','이해 부족'):
                            t['status']='완료'; t['remaining']=0
                            if outcome == '이해 부족':
                                extra = dict(t)
                                extra.update({'id':str(uuid4()), 'title':t['unit']+' · 이해 보충', 'type':'복습', 'estimated':20, 'remaining':20, 'actual':0, 'status':'대기', 'prereq':[t['id']]})
                                tasks.append(extra)
                        else:
                            t['remaining'] = left_minutes
                        st.session_state.agent_proposal = None
                        st.rerun()
        else:
            st.success('현재 남아 있는 과제가 없어요.')
        if st.session_state.agent_logs:
            st.caption('학습 기록 후에는 아래에서 재계획 제안을 만들고 수락해야 배정표가 갱신돼요.')
            with st.expander('학습 기록과 과목별 시간 보정 보기'):
                st.table([{'과제':x['task'], '결과':x['status'], '기존 예상':minutes_label(x['estimated']), '실제':minutes_label(x['actual'])} for x in st.session_state.agent_logs])
                factor = correction_factor(st.session_state.agent_logs, tasks[0]['subject'])
                st.write(f"{tasks[0]['subject']} 시간 보정계수: **{factor:.2f}배**")
                st.caption('완료 기록 평균을 기존 추정과 섞어 0.7~1.8배로 제한해요. 보정은 재계획 제안 때 아직 시작하지 않은 과제에 적용돼요.')
        st.markdown('#### 5. 재계획 제안')
        st.caption('기록을 반영해 남은 학습량을 다시 계산해요. 실제 기록은 유지되며 제안을 수락해야 계획이 바뀌어요.')
        if st.button('재계획 제안 만들기'):
            import copy
            revised = copy.deepcopy(tasks)
            factor = correction_factor(st.session_state.agent_logs, tasks[0]['subject'])
            for t in revised:
                if t['status'] != '완료' and t['actual'] == 0 and not t['title'].endswith('이해 보충'):
                    t['remaining'] = max(1, round(t['estimated'] * factor))
            suggestion = triage_plan(revised, available_left)
            old = {i['id']:i['allocated'] for i in plan}
            changes = []
            for item in suggestion:
                task = next(t for t in revised if t['id']==item['id'])
                prev = old.get(item['id'], 0)
                if item['id'] not in old:
                    changes.append(f"추가: {task['title']} · 이해 부족 기록에 따른 보충 과제")
                elif prev != item['allocated']:
                    changes.append(f"변경: {task['title']} · {minutes_label(prev)} → {minutes_label(item['allocated'])} (남은 시간·보정계수 반영)")
            st.session_state.agent_proposal = {'tasks':revised, 'plan':suggestion, 'changes':changes, 'factor':factor}
        proposal = st.session_state.agent_proposal
        if proposal:
            st.write('**제안된 변경 사항**')
            for change in proposal['changes']: st.write('• ' + change)
            if not proposal['changes']: st.write('배정 시간의 변화가 없어요.')
            one, two = st.columns(2)
            with one:
                if st.button('제안 수락'):
                    st.session_state.agent_tasks = proposal['tasks']
                    st.session_state.agent_plan = proposal['plan']
                    st.session_state.agent_proposal = None
                    st.rerun()
            with two:
                if st.button('제안 거절'):
                    st.session_state.agent_proposal = None
                    st.rerun()
        if st.button('이 실행 계획 초기화'):
            for key in ('agent_units','agent_tasks','agent_logs','agent_plan'):
                st.session_state[key] = []
            st.session_state.agent_proposal = None
            st.session_state.agent_exam = None
            st.rerun()
    st.info('현재는 총 가용 시간 기준의 실행 계획이에요. 달력 드래그, 타이머, 날짜별 배치·전후 블록 비교, 영구 저장과 AI 분석은 아직 이 화면에 연결되지 않았어요. 새로고침하면 기록이 사라질 수 있어요.')
