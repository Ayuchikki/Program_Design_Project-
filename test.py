"""
Pytest suite for the 911 Dispatch System.

Setup:
  1. Keep this file in the same folder as dispatch.py and main.py.
  2. pip install pytest
  3. Run:  pytest test.py -v
"""

import pytest

import dispatch
import main


# ---------------------------------------------------------------- helpers
@pytest.fixture
def state():
    return dispatch.initialize_system_data()


def feed(monkeypatch, answers):
    """Make input() return the given answers one by one."""
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def log(state, depts=("Police",), loc="L01", sev=3):
    return dispatch.log_emergency_call(state, "Ann", "Fire", list(depts), loc, sev)


# ---------------------------------------------------- calculate_personnel_count
@pytest.mark.parametrize("sev,expected", [(1, 2), (3, 6), (5, 10)])
def test_personnel_count(sev, expected):
    assert dispatch.calculate_personnel_count(sev) == expected


# ------------------------------------------------------- initialize_system_data
def test_initial_state(state):
    assert len(state.officer_registry) == 12
    assert len(state.police_database) == 3
    assert state.call_queue == []
    assert state.call_counter == 1
    assert all(o.active_cases == 0 for o in state.officer_registry.values())


# -------------------------------------------------------- select_lead_officer
def test_select_prefers_exact_sector(state):
    o = dispatch.select_lead_officer(state, "Police", "Brooklyn")
    assert o.officer_id == "P-103"


def test_select_sector_is_case_insensitive(state):
    o = dispatch.select_lead_officer(state, "Fire", "brooklyn")
    assert o.officer_id == "F-103"


def test_select_falls_back_to_other_sector_when_local_busy(state):
    state.officer_registry["P-103"].active_cases = 3
    o = dispatch.select_lead_officer(state, "Police", "Brooklyn")
    assert o is not None and o.officer_id != "P-103"
    assert o.department == "Police"


def test_select_returns_none_when_whole_dept_busy(state):
    for o in state.officer_registry.values():
        if o.department == "Fire":
            o.active_cases = 3
    assert dispatch.select_lead_officer(state, "Fire", "Manhattan") is None


def test_select_tiebreak_uses_completed_cases(state):
    # Two Brooklyn candidates would be needed; simulate via city-wide fallback
    state.officer_registry["P-103"].active_cases = 3  # remove local option
    state.officer_registry["P-101"].completed_cases = 5
    state.officer_registry["P-102"].completed_cases = 1
    state.officer_registry["P-104"].completed_cases = 9
    o = dispatch.select_lead_officer(state, "Police", "Brooklyn")
    assert o.officer_id == "P-102"  # same active_cases, fewest completed


def test_select_unknown_department_returns_none(state):
    assert dispatch.select_lead_officer(state, "Coast Guard", "Brooklyn") is None


# ------------------------------------------------------ log_emergency_call
def test_log_call_basic(state):
    call = log(state, ("Police",), "L04", 4)
    assert call.call_id == "CALL-001"
    assert call.landmark_name == "Brooklyn Bridge"
    assert call.personnel_per_dept == 8
    assert call.call_status == "Pending"
    assert call.unit_status == "Assigned"
    assert call.assigned_officers["Police"].location_sector == "Brooklyn"
    assert call.assigned_officers["Police"].active_cases == 1
    assert state.call_counter == 2
    assert call in state.call_queue


def test_log_call_multiple_departments(state):
    call = log(state, ("Police", "Fire", "Paramedic"))
    assert set(call.assigned_officers) == {"Police", "Fire", "Paramedic"}
    assert all(o.active_cases == 1 for o in call.assigned_officers.values())


def test_call_ids_increment(state):
    assert log(state).call_id == "CALL-001"
    assert log(state).call_id == "CALL-002"


def test_log_call_invalid_location_raises(state):
    with pytest.raises(KeyError):
        log(state, loc="L99")


def test_log_call_when_dept_full_returns_none_and_no_side_effects(state, capsys):
    for o in state.officer_registry.values():
        if o.department == "Fire":
            o.active_cases = 3
    before = {k: o.active_cases for k, o in state.officer_registry.items()}

    call = log(state, ("Police", "Fire"))

    assert call is None
    assert "WARNING" in capsys.readouterr().out
    assert state.call_counter == 1
    assert state.call_queue == []
    after = {k: o.active_cases for k, o in state.officer_registry.items()}
    assert before == after  # Police officer must NOT have been charged


def test_capacity_limit_is_twelve_police_calls(state):
    # 4 police officers x 3 active cases each = 12 calls, 13th must fail
    for _ in range(12):
        assert log(state, ("Police",)) is not None
    assert log(state, ("Police",)) is None


# ---------------------------------------------------------------- sort_queue
def test_sort_queue_pending_before_completed_then_severity(state):
    c1 = log(state, ("Police",), sev=2)
    c2 = log(state, ("Fire",), sev=5)
    c3 = log(state, ("Paramedic",), sev=4)
    c2.call_status = "Completed"
    dispatch.sort_queue(state)
    assert [c.call_id for c in state.call_queue] == [
        c3.call_id, c1.call_id, c2.call_id,
    ]


def test_sort_queue_same_severity_orders_by_call_id(state):
    a = log(state, ("Police",), sev=3)
    b = log(state, ("Fire",), sev=3)
    dispatch.sort_queue(state)
    assert [c.call_id for c in state.call_queue] == [a.call_id, b.call_id]


# ------------------------------------------------------------- complete_call
def test_complete_call_unknown_id(state, capsys):
    assert dispatch.complete_call(state, "CALL-999") is False
    assert "not found" in capsys.readouterr().out


def test_complete_call_requires_on_scene(state, capsys):
    call = log(state)
    assert dispatch.complete_call(state, call.call_id) is False
    assert call.call_status == "Pending"
    assert "arrival" in capsys.readouterr().out


def test_complete_call_success_updates_officers(state):
    call = log(state, ("Police", "Fire"))
    call.unit_status = "On Scene"
    officers = list(call.assigned_officers.values())

    assert dispatch.complete_call(state, call.call_id) is True
    assert call.call_status == "Completed"
    assert call.unit_status == "Cleared"
    for o in officers:
        assert o.active_cases == 0
        assert o.completed_cases == 1


def test_complete_call_twice_fails(state):
    call = log(state)
    call.unit_status = "On Scene"
    assert dispatch.complete_call(state, call.call_id) is True
    assert dispatch.complete_call(state, call.call_id) is False
    # counters must not be double-counted
    o = call.assigned_officers["Police"]
    assert o.completed_cases == 1 and o.active_cases == 0


def test_completed_officer_becomes_available_again(state):
    for o in state.officer_registry.values():
        if o.department == "Fire":
            o.active_cases = 3
    state.officer_registry["F-101"].active_cases = 2
    call = log(state, ("Fire",))
    assert call is not None  # F-101 took the last slot


# -------------------------------------------------- run_radio_dialogue_feed
def test_radio_feed_yes(state, monkeypatch):
    call = log(state)
    feed(monkeypatch, ["", "", "y"])
    assert dispatch.run_radio_dialogue_feed(call) is True
    assert call.unit_status == "On Scene"


def test_radio_feed_no(state, monkeypatch):
    call = log(state)
    feed(monkeypatch, ["", "", "N"])
    assert dispatch.run_radio_dialogue_feed(call) is False
    assert call.unit_status == "On Scene"


def test_radio_feed_reprompts_on_invalid(state, monkeypatch, capsys):
    call = log(state)
    feed(monkeypatch, ["", "", "maybe", "", "Y"])
    assert dispatch.run_radio_dialogue_feed(call) is True
    assert "Enter 'Y'" in capsys.readouterr().out


# ----------------------------------------------------- search_police_records
@pytest.mark.parametrize(
    "query,expected",
    [
        ("jane", "REC-001"),            # name, case-insensitive
        ("8765", "REC-002"),            # SSN last 4
        ("L02", "REC-003"),             # prior incident code
        ("traffic collision", "REC-002"),
    ],
)
def test_search_finds_record(state, capsys, query, expected):
    dispatch.search_police_records(state, query)
    assert expected in capsys.readouterr().out


def test_search_no_match(state, capsys):
    dispatch.search_police_records(state, "zzzz")
    assert "No matching" in capsys.readouterr().out


def test_search_shows_none_for_empty_warrants(state, capsys):
    dispatch.search_police_records(state, "John Smith")
    assert "Warrants:  None" in capsys.readouterr().out


def test_search_by_borough_name_finds_nothing(state, capsys):
    # The CLI prompt says "Location", but records only store L-codes.
    dispatch.search_police_records(state, "Manhattan")
    assert "No matching" in capsys.readouterr().out


# ------------------------------------------------- display_past_cases_table
def test_past_cases_empty(state, capsys):
    dispatch.display_past_cases_table(state)
    assert "No completed past cases" in capsys.readouterr().out


def test_past_cases_lists_only_completed(state, capsys):
    done = log(state, ("Police",))
    pending = log(state, ("Fire",))
    done.unit_status = "On Scene"
    dispatch.complete_call(state, done.call_id)
    capsys.readouterr()

    dispatch.display_past_cases_table(state)
    out = capsys.readouterr().out
    assert done.call_id in out
    assert pending.call_id not in out


# ============================================================ CLI (main file)
def test_menu_exit_returns_false(state):
    assert main.process_menu_choice("5", state) is False


@pytest.mark.parametrize("choice", ["", "0", "6", "abc", "1.0"])
def test_menu_invalid_choice_keeps_running(state, capsys, choice):
    assert main.process_menu_choice(choice, state) is True
    assert "Invalid choice" in capsys.readouterr().out


def test_cli_log_call_happy_path(state, monkeypatch):
    # name, desc, depts, location, severity, ENTER, ENTER, complete?
    feed(monkeypatch, ["Ann", "Kitchen fire", "1, 2", "l01", "3", "", "", "Y"])
    main.handle_log_call(state)
    assert len(state.call_queue) == 1
    assert state.call_queue[0].call_status == "Completed"
    assert state.call_queue[0].departments == ["Police", "Fire"]


def test_cli_log_call_job_not_complete_stays_pending(state, monkeypatch):
    feed(monkeypatch, ["Ann", "Crash", "1", "L04", "2", "", "", "N"])
    main.handle_log_call(state)
    call = state.call_queue[0]
    assert call.call_status == "Pending"
    assert call.unit_status == "On Scene"


@pytest.mark.parametrize(
    "answers,msg",
    [
        (["", "desc"], "cannot be blank"),
        (["Ann", ""], "cannot be blank"),
        (["Ann", "d", "12"], "Invalid formatting"),          # missing comma
        (["Ann", "d", "1,9"], "valid single department"),
        (["Ann", "d", "x"], "valid single department"),
        (["Ann", "d", ""], "at least one department"),
        (["Ann", "d", "1", "L99"], "Invalid location"),
        (["Ann", "d", "1", "L01", "0"], "Severity must be"),
        (["Ann", "d", "1", "L01", "6"], "Severity must be"),
        (["Ann", "d", "1", "L01", "abc"], "Severity must be"),
        (["Ann", "d", "1", "L01", "-2"], "Severity must be"),
    ],
)
def test_cli_log_call_validation(state, monkeypatch, capsys, answers, msg):
    feed(monkeypatch, answers)
    main.handle_log_call(state)
    assert msg in capsys.readouterr().out
    assert state.call_queue == []


def test_cli_duplicate_departments_deduped(state, monkeypatch):
    feed(monkeypatch, ["Ann", "d", "1, 1, 2", "L01", "3", "", "", "N"])
    main.handle_log_call(state)
    assert state.call_queue[0].departments == ["Police", "Fire"]


def test_cli_search_empty_query(state, monkeypatch, capsys):
    feed(monkeypatch, ["   "])
    main.handle_search_records(state)
    assert "cannot be empty" in capsys.readouterr().out


def test_cli_search_valid_query(state, monkeypatch, capsys):
    feed(monkeypatch, ["Ayush"])
    main.handle_search_records(state)
    assert "REC-003" in capsys.readouterr().out


def test_cli_complete_call_lowercase_id(state, monkeypatch):
    call = log(state)
    call.unit_status = "On Scene"
    feed(monkeypatch, [call.call_id.lower()])
    main.handle_complete_call(state)
    assert call.call_status == "Completed"


def test_cli_full_session_via_main(monkeypatch, capsys):
    feed(monkeypatch, ["4", "2", "Jane", "5"])
    main.main()
    out = capsys.readouterr().out
    assert "No completed past cases" in out
    assert "REC-001" in out
    assert "Goodbye" in out

    #python -m pytest test.py -v