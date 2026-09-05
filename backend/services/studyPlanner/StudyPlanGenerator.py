# backend/services/studyPlanner/StudyPlanGenerator.py

import os
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

from services.studyPlanner.PromptsDict import STUDY_PLAN_SEQUENCING_PROMPT

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in backend/.env.")
    return OpenAI(api_key=api_key)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ============================================================
# 1. CALENDAR & STUDY/REST DAY COMPUTATION
# ============================================================

def get_study_calendar(
    start_date: date,
    exam_date: date,
    days_per_week: int = 7,
) -> Dict[str, Any]:
    """
    Computes active study days, rest days, and revision days between start_date and exam_date - 1.
    - 7 days/week = 0 rest days / week
    - 6 days/week = 1 rest day / week (every 7th day)
    - 5 days/week = 2 rest days / week (every 6th and 7th day)
    - etc.
    - Exam day itself has zero study tasks.
    """
    if exam_date <= start_date:
        raise ValueError("Target exam date must be in the future.")

    days_per_week = max(1, min(7, days_per_week))
    total_days = (exam_date - start_date).days

    all_dates: List[date] = [start_date + timedelta(days=i) for i in range(total_days)]
    active_study_dates: List[date] = []
    rest_dates: List[date] = []

    for i, d in enumerate(all_dates):
        # Determine day in the 7-day cycle (0 to 6)
        cycle_idx = i % 7
        if cycle_idx < days_per_week:
            active_study_dates.append(d)
        else:
            rest_dates.append(d)

    if not active_study_dates:
        active_study_dates = [start_date]

    # Calculate revision days at the tail end of active study dates
    total_active = len(active_study_dates)
    if total_active >= 14:
        num_revision_days = min(5, max(2, round(total_active * 0.15)))
    elif total_active >= 7:
        num_revision_days = 2
    elif total_active >= 3:
        num_revision_days = 1
    else:
        num_revision_days = 0

    if num_revision_days > 0 and len(active_study_dates) > num_revision_days:
        regular_study_dates = active_study_dates[:-num_revision_days]
        revision_dates = active_study_dates[-num_revision_days:]
    else:
        regular_study_dates = active_study_dates[:]
        revision_dates = []

    return {
        "all_dates": all_dates,
        "active_study_dates": active_study_dates,
        "rest_dates": rest_dates,
        "regular_study_dates": regular_study_dates,
        "revision_dates": revision_dates,
    }


# ============================================================
# 2. PURE COMPUTATION — Hour Budget, Priority & Workload
# ============================================================

def compute_hour_budget(
    syllabus_topics: List[Dict],   # List of {"subject": str, "topic": str, "weightage": float}
    topics_already_done: List[str],
    weak_subjects: List[str],
    daily_hours: float,
    days_remaining: Optional[int] = None,
    days_per_week: int = 7,
    start_date: Optional[date] = None,
    exam_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Computes workload and hour allocation:
    - Excludes topics already done.
    - Slices remaining capacity based on daily hours and active non-revision study days.
    - Fits high-weightage topics first. Lower-priority topics that don't fit are marked in excluded_topics.
    - Prepares revision tasks for revision days (topics_already_done + newly scheduled topics).
    """
    if start_date is None:
        start_date = date.today()
    if exam_date is None:
        if days_remaining is None or days_remaining <= 0:
            raise ValueError("Target exam date must be in the future.")
        exam_date = start_date + timedelta(days=days_remaining)

    cal = get_study_calendar(start_date, exam_date, days_per_week)
    regular_study_dates = cal["regular_study_dates"]
    revision_dates = cal["revision_dates"]

    total_regular_hours = len(regular_study_dates) * daily_hours

    # 1. Filter out topics already completed
    done_set = set()
    cleaned_done_topics = []
    for t in (topics_already_done or []):
        t_clean = t.strip()
        done_set.add(t_clean)
        done_set.add(t_clean.split('\n')[0].strip())
        cleaned_done_topics.append(t_clean)

    remaining_syllabus = []
    for item in syllabus_topics:
        t_full = item["topic"].strip()
        t_first = t_full.split('\n')[0].strip()
        if t_full not in done_set and t_first not in done_set:
            remaining_syllabus.append(item)

    if not remaining_syllabus and not cleaned_done_topics:
        raise ValueError("No syllabus topics available for planning.")

    # 2. Group by subject & sort by weightage (highest first)
    by_subject: Dict[str, List[Dict]] = {}
    for item in remaining_syllabus:
        subj = item["subject"]
        if subj not in by_subject:
            by_subject[subj] = []
        by_subject[subj].append(item)

    for subj in by_subject:
        by_subject[subj].sort(key=lambda x: float(x.get("weightage", 1.0)), reverse=True)

    # 3. Interleave topics across subjects
    interleaved = []
    subjs = list(by_subject.keys())
    indices = {s: 0 for s in subjs}

    while any(indices[s] < len(by_subject[s]) for s in subjs):
        for s in subjs:
            if indices[s] < len(by_subject[s]):
                interleaved.append(by_subject[s][indices[s]])
                indices[s] += 1

    # 4. Workload calculation & allocation within total_regular_hours
    hour_budget: Dict[str, Dict[str, float]] = {s: {} for s in subjs}
    excluded_topics: List[Dict[str, str]] = []
    scheduled_topics: List[Dict[str, Any]] = []
    remaining_hours = total_regular_hours

    for item in interleaved:
        subj = item["subject"]
        topic = item["topic"]
        weight = float(item.get("weightage", 1.0))

        # Dynamic sizing: large/heavy topics (e.g. weight >= 2.0) take 3h to full day; small topics 1.5h
        base_h = max(1.5, min(daily_hours, (weight / 0.03) * 2.5 if weight < 0.5 else weight * 1.5))
        req_hours = round(base_h * 2) / 2
        if req_hours > daily_hours:
            req_hours = daily_hours
        if subj in weak_subjects:
            req_hours = min(daily_hours, round((req_hours * 1.2) * 2) / 2)

        if remaining_hours >= req_hours or (remaining_hours >= 1.0 and len(scheduled_topics) == 0):
            alloc_hours = min(req_hours, remaining_hours) if remaining_hours < req_hours else req_hours
            hour_budget[subj][topic] = alloc_hours
            scheduled_topics.append({"subject": subj, "topic": topic, "weightage": weight, "hours": alloc_hours})
            remaining_hours -= alloc_hours
        else:
            excluded_topics.append({
                "subject": subj,
                "topic": topic,
                "reason": f"Excluded due to limited study time ({total_regular_hours:.1f}h available before revision). Lower priority/weightage."
            })

    # Clean empty subjects
    hour_budget = {s: t_dict for s, t_dict in hour_budget.items() if t_dict}

    # 5. Revision Plan Tasks
    # Revision pool = pre-completed topics + newly scheduled topics
    revision_pool: List[Dict[str, Any]] = []
    seen_revision = set()

    for s_item in scheduled_topics:
        key = (s_item["subject"], s_item["topic"])
        if key not in seen_revision:
            seen_revision.add(key)
            revision_pool.append(s_item)

    for item in syllabus_topics:
        t_full = item["topic"].strip()
        t_first = t_full.split('\n')[0].strip()
        if (t_full in done_set or t_first in done_set) and (item["subject"], item["topic"]) not in seen_revision:
            seen_revision.add((item["subject"], item["topic"]))
            revision_pool.append({
                "subject": item["subject"],
                "topic": item["topic"],
                "weightage": float(item.get("weightage", 1.0)),
                "hours": 1.5
            })

    # Sort revision topics by weightage descending
    revision_pool.sort(key=lambda x: float(x.get("weightage", 1.0)), reverse=True)

    revision_tasks: List[Dict[str, Any]] = []
    if revision_dates and revision_pool:
        total_rev_hours = len(revision_dates) * daily_hours
        rev_remaining = total_rev_hours
        for r_item in revision_pool:
            if rev_remaining < 1.0:
                break
            rev_h = min(2.0, max(1.0, daily_hours / 2.0))
            rev_h = round(rev_h * 2) / 2
            if rev_remaining >= rev_h:
                revision_tasks.append({
                    "subject": r_item["subject"],
                    "topic": f"Revision: {r_item['topic']}",
                    "hours": rev_h,
                    "priority": 1
                })
                rev_remaining -= rev_h

    warning_msg = None
    if excluded_topics:
        warning_msg = (
            f"{len(excluded_topics)} lower-priority topics were excluded due to limited time budget. "
            "Consider increasing daily study hours or study days per week."
        )

    return {
        "budget": hour_budget,
        "scheduled_topics": scheduled_topics,
        "excluded_topics": excluded_topics,
        "revision_tasks": revision_tasks,
        "calendar": cal,
        "warning": warning_msg
    }


# ============================================================
# 3. PROMPT BUILDING FOR LLM SEQUENCER
# ============================================================

def build_llm_sequencing_prompt(
    hour_budget_dict: Dict[str, Dict[str, float]],
    revision_tasks: List[Dict[str, Any]],
    allowed_study_dates: List[date],
    revision_dates: List[date],
    start_date: date,
    target_exam_date: date,
    daily_available_hours: float,
) -> str:
    """Formats hour budget, revision tasks, and allowed study dates into the LLM prompt."""
    budget_list = []
    for subj, topics in hour_budget_dict.items():
        for topic, hours in topics.items():
            budget_list.append({
                "subject": subj,
                "topic": topic,
                "hours": hours,
                "priority": 3
            })
    for rev in revision_tasks:
        budget_list.append(rev)

    allowed_dates_str = [d.isoformat() for d in allowed_study_dates]
    revision_dates_str = [d.isoformat() for d in revision_dates]

    return STUDY_PLAN_SEQUENCING_PROMPT.format(
        daily_available_hours=daily_available_hours,
        hour_budget_json=json.dumps(budget_list, indent=2),
        allowed_dates_json=json.dumps(allowed_dates_str),
        revision_dates_json=json.dumps(revision_dates_str),
        start_date=start_date.isoformat(),
        exam_date=target_exam_date.isoformat(),
    )


# ============================================================
# 4. ALGORITHMIC SEQUENCER (Pure Deterministic Fallback)
# ============================================================

def _generate_schedule_algorithmic(
    hour_budget: Dict[str, Dict[str, float]],
    revision_tasks: List[Dict[str, Any]],
    regular_study_dates: List[date],
    revision_dates: List[date],
    daily_available_hours: float,
) -> List[Dict]:
    """
    Sequences study schedule deterministically:
    - Normal tasks are mapped only onto regular_study_dates.
    - Sizing: Large topics fill a full day; small topics share days within daily_available_hours.
    - Revision tasks are mapped only onto revision_dates.
    - Rest days and exam day remain completely empty (no tasks).
    """
    by_subj = {subj: list(topics.items()) for subj, topics in hour_budget.items()}
    subjs = list(by_subj.keys())
    indices = {s: 0 for s in subjs}

    flat_regular_tasks = []
    while any(indices[s] < len(by_subj[s]) for s in subjs):
        for s in subjs:
            if indices[s] < len(by_subj[s]):
                topic, hours = by_subj[s][indices[s]]
                flat_regular_tasks.append({
                    "subject": s,
                    "topic": topic,
                    "hours": float(hours),
                    "priority": 3
                })
                indices[s] += 1

    days_schedule: List[Dict] = []

    # 1. Schedule regular tasks onto regular_study_dates
    reg_date_idx = 0
    curr_day_tasks = []
    curr_day_hours = 0.0

    for task in flat_regular_tasks:
        rem_hours = task["hours"]
        while rem_hours > 0 and reg_date_idx < len(regular_study_dates):
            current_date = regular_study_dates[reg_date_idx]
            avail = max(0.0, daily_available_hours - curr_day_hours)
            if avail <= 0.25:
                if curr_day_tasks:
                    days_schedule.append({
                        "date": current_date.isoformat(),
                        "tasks": curr_day_tasks
                    })
                reg_date_idx += 1
                curr_day_tasks = []
                curr_day_hours = 0.0
                if reg_date_idx >= len(regular_study_dates):
                    break
                avail = daily_available_hours

            chunk = min(rem_hours, avail)
            curr_day_tasks.append({
                "subject": task["subject"],
                "topic": task["topic"],
                "hours": round(chunk, 2),
                "priority": task.get("priority", 3)
            })
            curr_day_hours += chunk
            rem_hours -= chunk

    if curr_day_tasks and reg_date_idx < len(regular_study_dates):
        days_schedule.append({
            "date": regular_study_dates[reg_date_idx].isoformat(),
            "tasks": curr_day_tasks
        })

    # 2. Schedule revision tasks onto revision_dates
    rev_date_idx = 0
    curr_rev_tasks = []
    curr_rev_hours = 0.0

    for rev_task in revision_tasks:
        rem_hours = rev_task["hours"]
        while rem_hours > 0 and rev_date_idx < len(revision_dates):
            current_date = revision_dates[rev_date_idx]
            avail = max(0.0, daily_available_hours - curr_rev_hours)
            if avail <= 0.25:
                if curr_rev_tasks:
                    days_schedule.append({
                        "date": current_date.isoformat(),
                        "tasks": curr_rev_tasks
                    })
                rev_date_idx += 1
                curr_rev_tasks = []
                curr_rev_hours = 0.0
                if rev_date_idx >= len(revision_dates):
                    break
                avail = daily_available_hours

            chunk = min(rem_hours, avail)
            curr_rev_tasks.append({
                "subject": rev_task["subject"],
                "topic": rev_task["topic"],
                "hours": round(chunk, 2),
                "priority": 1
            })
            curr_rev_hours += chunk
            rem_hours -= chunk

    if curr_rev_tasks and rev_date_idx < len(revision_dates):
        days_schedule.append({
            "date": revision_dates[rev_date_idx].isoformat(),
            "tasks": curr_rev_tasks
        })

    # Sort days chronologically
    days_schedule.sort(key=lambda d: d["date"])
    return days_schedule


# ============================================================
# 5. LLM CALL + SCHEDULE GENERATION
# ============================================================

def _call_openai_and_parse(prompt: str, strict: bool = False) -> List[Dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a JSON-only output API. You NEVER include markdown fences, "
                "explanations, or any text outside the JSON object."
                + (" Return ONLY valid JSON. Nothing else." if strict else "")
            ),
        },
        {"role": "user", "content": prompt},
    ]

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if "days" not in parsed:
            raise ValueError("Missing 'days' key in LLM response")
        return parsed["days"]
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to parse LLM JSON output: {e}\nRaw output: {raw[:500]}")


def _generate_schedule_from_llm(
    hour_budget: Dict[str, Dict[str, float]],
    revision_tasks: List[Dict[str, Any]],
    regular_study_dates: List[date],
    revision_dates: List[date],
    start_date: date,
    target_exam_date: date,
    daily_available_hours: float,
) -> List[Dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _generate_schedule_algorithmic(
            hour_budget=hour_budget,
            revision_tasks=revision_tasks,
            regular_study_dates=regular_study_dates,
            revision_dates=revision_dates,
            daily_available_hours=daily_available_hours
        )

    allowed_study_dates = regular_study_dates + revision_dates
    prompt = build_llm_sequencing_prompt(
        hour_budget_dict=hour_budget,
        revision_tasks=revision_tasks,
        allowed_study_dates=allowed_study_dates,
        revision_dates=revision_dates,
        start_date=start_date,
        target_exam_date=target_exam_date,
        daily_available_hours=daily_available_hours
    )

    try:
        return _call_openai_and_parse(prompt, strict=False)
    except Exception as e:
        print(f"[WARNING] LLM study plan sequencing failed ({e}). Using algorithmic sequencer.")
        return _generate_schedule_algorithmic(
            hour_budget=hour_budget,
            revision_tasks=revision_tasks,
            regular_study_dates=regular_study_dates,
            revision_dates=revision_dates,
            daily_available_hours=daily_available_hours
        )


# ============================================================
# 6. POST-GENERATION VALIDATION
# ============================================================

def _validate_and_cap_daily_hours(
    days: List[Dict],
    daily_available_hours: float,
    allowed_dates: Optional[List[date]] = None
) -> List[Dict]:
    """
    Ensures:
    1. No day exceeds daily_available_hours.
    2. Only valid allowed dates contain tasks (if allowed_dates is provided).
    """
    allowed_date_strings = {d.isoformat() for d in allowed_dates} if allowed_dates else None

    validated = []
    overflow_tasks = []

    for day_entry in days:
        d_str = day_entry.get("date")
        if allowed_date_strings and d_str not in allowed_date_strings:
            # Shift tasks into overflow rather than discarding
            overflow_tasks.extend(day_entry.get("tasks", []))
            continue

        tasks = overflow_tasks + day_entry.get("tasks", [])
        overflow_tasks = []
        day_total = 0.0
        accepted = []

        for task in tasks:
            task_hours = float(task.get("hours", 0))
            if day_total + task_hours <= daily_available_hours + 0.01:
                accepted.append(task)
                day_total += task_hours
            else:
                overflow_tasks.append(task)

        if accepted:
            validated.append({"date": d_str, "tasks": accepted})

    if overflow_tasks and validated:
        for task in overflow_tasks:
            validated[-1]["tasks"].append(task)

    return validated


# ============================================================
# 7. ADAPTIVE REBALANCE (Redistribute overdue tasks)
# ============================================================

def redistribute_overdue_tasks(
    overdue_tasks: List[Dict],
    future_study_dates: List[date],
    daily_available_hours: float,
    existing_day_loads: Dict[str, float],
) -> Dict[str, List[Dict]]:
    """
    Redistributes overdue tasks across future available study dates (excluding rest days/exam day).
    Respects daily hour limits.
    """
    additions: Dict[str, List[Dict]] = {d.isoformat(): [] for d in future_study_dates}

    if not future_study_dates:
        return additions

    for task in overdue_tasks:
        # Find study day with lowest load
        best_day = min(
            future_study_dates,
            key=lambda d: existing_day_loads.get(d.isoformat(), 0.0),
        )
        best_day_str = best_day.isoformat()
        current_load = existing_day_loads.get(best_day_str, 0.0)
        task_hours = float(task.get("estimated_hours", 1.0))

        if current_load + task_hours <= daily_available_hours:
            additions[best_day_str].append(task)
            existing_day_loads[best_day_str] = current_load + task_hours
        else:
            # If all days are near full, still place in best_day so task is not lost
            additions[best_day_str].append(task)
            existing_day_loads[best_day_str] = current_load + task_hours

    return additions


def compute_mastery_from_completion(done: int, total: int) -> str:
    if total == 0:
        return "moderate"
    ratio = done / total
    if ratio >= 0.7:
        return "strong"
    elif ratio >= 0.4:
        return "moderate"
    else:
        return "weak"
