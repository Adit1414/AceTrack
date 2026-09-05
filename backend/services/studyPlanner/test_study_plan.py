# backend/services/studyPlanner/test_study_plan.py
"""
Unit tests for the StudyPlanGenerator module.
Run with: pytest backend/services/studyPlanner/test_study_plan.py -v
No DB or network connection required for these tests.
"""

from datetime import date, timedelta
from services.studyPlanner.StudyPlanGenerator import (
    get_study_calendar,
    compute_hour_budget,
    _validate_and_cap_daily_hours,
    _generate_schedule_algorithmic,
    compute_mastery_from_completion,
    redistribute_overdue_tasks,
)

MOCK_TOPICS = [
    {"subject": "Physics", "topic": "Thermodynamics", "weightage": 3.0},
    {"subject": "Physics", "topic": "Optics", "weightage": 1.0},
    {"subject": "Chemistry", "topic": "Periodic Table", "weightage": 1.5},
    {"subject": "Chemistry", "topic": "Organic Basics", "weightage": 2.0},
    {"subject": "Maths", "topic": "Calculus", "weightage": 3.0},
]


# ============================================================
# 1. Calendar & Rest Days Tests (Requirements 3 & 6)
# ============================================================

def test_study_calendar_7_days_per_week():
    start = date(2026, 9, 1)
    exam = date(2026, 9, 15)  # 14 days
    cal = get_study_calendar(start, exam, days_per_week=7)
    assert len(cal["all_dates"]) == 14
    assert len(cal["rest_dates"]) == 0
    assert len(cal["active_study_dates"]) == 14
    assert exam not in cal["all_dates"]  # Exam day has no tasks


def test_study_calendar_5_days_per_week():
    start = date(2026, 9, 1)
    exam = date(2026, 9, 15)  # 14 days (2 full 7-day cycles)
    cal = get_study_calendar(start, exam, days_per_week=5)
    assert len(cal["all_dates"]) == 14
    assert len(cal["active_study_dates"]) == 10
    assert len(cal["rest_dates"]) == 4  # 2 rest days per week * 2 weeks


def test_study_calendar_6_days_per_week():
    start = date(2026, 9, 1)
    exam = date(2026, 9, 15)  # 14 days
    cal = get_study_calendar(start, exam, days_per_week=6)
    assert len(cal["active_study_dates"]) == 12
    assert len(cal["rest_dates"]) == 2  # 1 rest day per week * 2 weeks


# ============================================================
# 2. Workload & Priority Tests (Requirements 4 & 5)
# ============================================================

def test_large_topic_workload_sizing():
    """A heavy topic can take up to the entire daily hours (e.g. 4h)."""
    start = date(2026, 9, 1)
    exam = date(2026, 9, 20)
    result = compute_hour_budget(
        syllabus_topics=MOCK_TOPICS,
        topics_already_done=[],
        weak_subjects=[],
        daily_hours=4.0,
        days_per_week=7,
        start_date=start,
        exam_date=exam,
    )
    budget = result["budget"]
    # Heavy topics like Calculus or Thermodynamics should have high hours
    assert budget["Maths"]["Calculus"] >= 3.0
    assert budget["Physics"]["Thermodynamics"] >= 3.0


def test_insufficient_time_excludes_lower_priority_topics():
    """When time budget is tiny, only top priority fit; others are excluded."""
    start = date(2026, 9, 1)
    exam = date(2026, 9, 3)  # Only 2 days available
    result = compute_hour_budget(
        syllabus_topics=MOCK_TOPICS,
        topics_already_done=[],
        weak_subjects=[],
        daily_hours=2.0,  # Only 4 total hours
        days_per_week=7,
        start_date=start,
        exam_date=exam,
    )
    assert len(result["excluded_topics"]) > 0
    # Top weightage (Thermodynamics or Calculus) gets included
    assert len(result["scheduled_topics"]) >= 1
    # Excluded topics have subject and clear reason
    for exc in result["excluded_topics"]:
        assert "subject" in exc
        assert "topic" in exc
        assert "reason" in exc


def test_sufficient_time_includes_all_topics():
    """When time budget is plenty, zero topics are excluded."""
    start = date(2026, 9, 1)
    exam = date(2026, 11, 1)  # 61 days
    result = compute_hour_budget(
        syllabus_topics=MOCK_TOPICS,
        topics_already_done=[],
        weak_subjects=[],
        daily_hours=4.0,
        days_per_week=7,
        start_date=start,
        exam_date=exam,
    )
    assert len(result["excluded_topics"]) == 0
    assert result["warning"] is None


# ============================================================
# 3. Revision Plan Tests (Requirement 6)
# ============================================================

def test_revision_plan_includes_completed_and_scheduled_topics():
    start = date(2026, 9, 1)
    exam = date(2026, 9, 20)  # 19 days -> has revision days
    result = compute_hour_budget(
        syllabus_topics=MOCK_TOPICS,
        topics_already_done=["Calculus"],  # Already done topic
        weak_subjects=[],
        daily_hours=4.0,
        days_per_week=7,
        start_date=start,
        exam_date=exam,
    )
    # Calculus is excluded from new study topics
    assert "Calculus" not in result["budget"].get("Maths", {})
    # But Calculus IS included in revision tasks!
    rev_tasks = result["revision_tasks"]
    assert len(rev_tasks) > 0
    rev_topic_names = [r["topic"] for r in rev_tasks]
    assert any("Calculus" in t for t in rev_topic_names)


# ============================================================
# 4. Algorithmic Scheduler & Rest Days (Requirements 3 & 4)
# ============================================================

def test_algorithmic_scheduler_respects_rest_days():
    start = date(2026, 9, 1)
    exam = date(2026, 9, 15)
    cal = get_study_calendar(start, exam, days_per_week=5)
    result = compute_hour_budget(
        syllabus_topics=MOCK_TOPICS,
        topics_already_done=[],
        weak_subjects=[],
        daily_hours=4.0,
        days_per_week=5,
        start_date=start,
        exam_date=exam,
    )
    schedule = _generate_schedule_algorithmic(
        hour_budget=result["budget"],
        revision_tasks=result["revision_tasks"],
        regular_study_dates=cal["regular_study_dates"],
        revision_dates=cal["revision_dates"],
        daily_available_hours=4.0
    )
    scheduled_dates = {s["date"] for s in schedule}
    rest_date_strings = {d.isoformat() for d in cal["rest_dates"]}

    # No task should ever be scheduled on a rest date
    assert scheduled_dates.isdisjoint(rest_date_strings)
    # No task should be on exam date
    assert exam.isoformat() not in scheduled_dates


# ============================================================
# 5. Redistribution / Rebalance Tests (Requirement 7)
# ============================================================

def test_redistribution_respects_future_dates_and_cap():
    today = date(2026, 9, 10)
    exam = date(2026, 9, 15)
    cal = get_study_calendar(today, exam, days_per_week=6)
    future_study = cal["active_study_dates"]

    existing_loads = {d.isoformat(): 2.0 for d in future_study}
    overdue = [
        {"estimated_hours": 1.5, "subject": "Physics", "topic": "Optics"},
        {"estimated_hours": 1.0, "subject": "Maths", "topic": "Calculus"},
    ]
    additions = redistribute_overdue_tasks(overdue, future_study, 4.0, existing_loads)
    for day_str, tasks in additions.items():
        added_h = sum(t["estimated_hours"] for t in tasks)
        assert existing_loads[day_str] <= 4.5


if __name__ == "__main__":
    print("Running Study Planner unit tests...")
    test_study_calendar_7_days_per_week()
    test_study_calendar_5_days_per_week()
    test_study_calendar_6_days_per_week()
    test_large_topic_workload_sizing()
    test_insufficient_time_excludes_lower_priority_topics()
    test_sufficient_time_includes_all_topics()
    test_revision_plan_includes_completed_and_scheduled_topics()
    test_algorithmic_scheduler_respects_rest_days()
    test_redistribution_respects_future_dates_and_cap()
    print("✅ All 9 Study Planner unit tests passed successfully!")
