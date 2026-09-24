class Officer:

    def __init__(
        self,
        officer_id,
        name,
        department,
        location_sector,
        rank,
        active_cases=0,
        completed_cases=0,
    ):
        self.officer_id = officer_id
        self.name = name
        self.department = department
        self.location_sector = location_sector
        self.rank = rank
        self.active_cases = active_cases
        self.completed_cases = completed_cases


class PoliceRecord:

    def __init__(
        self,
        record_id,
        person_name,
        ssn_last4,
        warrants,
        citations,
        prior_incidents,
    ):
        self.record_id = record_id
        self.person_name = person_name
        self.ssn_last4 = ssn_last4
        self.warrants = warrants
        self.citations = citations
        self.prior_incidents = prior_incidents


class EmergencyCall:

    def __init__(
        self,
        call_id,
        caller_name,
        incident_description,
        departments,
        location_code,
        landmark_name,
        severity,
        personnel_per_dept,
        assigned_officers,
        unit_status="Assigned",
        call_status="Pending",
    ):
        self.call_id = call_id
        self.caller_name = caller_name
        self.incident_description = incident_description
        self.departments = departments
        self.location_code = location_code
        self.landmark_name = landmark_name
        self.severity = severity
        self.personnel_per_dept = personnel_per_dept
        self.assigned_officers = assigned_officers
        self.unit_status = unit_status
        self.call_status = call_status


LOCATION_MAP = {
    "L01": ("Times Square", "Manhattan"),
    "L02": ("Washington Square Park", "Lower East Side"),
    "L03": ("Union Square", "Lower East Side"),
    "L04": ("Brooklyn Bridge", "Brooklyn"),
    "L05": ("Coney Island", "Brooklyn"),
    "L06": ("Central Park (Mall/Bethesda)", "Upper West Side"),
    "L07": ("Williamsburg", "Brooklyn"),
    "L08": ("SoHo", "Lower East Side"),
    "L09": ("Bryant Park", "Manhattan"),
    "L10": ("East Village", "Lower East Side"),
}


class DispatchSystemState:

    def __init__(self):
        self.call_queue = []
        self.officer_registry = {}
        self.police_database = []
        self.call_counter = 1


def initialize_system_data():
    state = DispatchSystemState()

    raw_officers = [
        ("P-101", "Maria Chen", "Police", "Manhattan", "Patrol Officer"),
        ("P-102", "David Okafor", "Police", "Lower East Side", "Sergeant"),
        ("P-103", "Anna Martinez", "Police", "Brooklyn", "Lieutenant"),
        ("P-104", "James Wright", "Police", "Upper West Side", "Patrol Officer"),
        ("M-101", "Sarah Wilson", "Paramedic", "Manhattan", "EMT-Basic"),
        ("M-102", "Thomas Reed", "Paramedic", "Lower East Side", "Paramedic"),
        ("M-103", "Neha Patel", "Paramedic", "Brooklyn", "EMT-Basic"),
        ("M-104", "Chris Taylor", "Paramedic", "Upper West Side", "EMT-Paramedic"),
        ("F-101", "Tom Harris", "Fire", "Manhattan", "Firefighter"),
        ("F-102", "Ken Lee", "Fire", "Lower East Side", "Lieutenant"),
        ("F-103", "Elena Vasquez", "Fire", "Brooklyn", "Captain"),
        ("F-104", "Marcus Vance", "Fire", "Upper West Side", "Firefighter"),
    ]

    for oid, name, dept, sec, rank in raw_officers:
        state.officer_registry[oid] = Officer(oid, name, dept, sec, rank)

    state.police_database = [
        PoliceRecord(
            "REC-001",
            "Jane Doe",
            "4321",
            ["Active Theft Warrant"],
            ["Speeding 2024"],
            ["L01 - Grand Larceny Allegation"],
        ),
        PoliceRecord(
            "REC-002",
            "John Smith",
            "8765",
            [],
            ["Reckless Driving"],
            ["L04 - Traffic Collision"],
        ),
        PoliceRecord(
            "REC-003",
            "Ayush Kumar",
            "1122",
            ["Assault Warrant"],
            ["Disorderly Conduct"],
            ["L02 - Disturbance"],
        ),
    ]

    return state


def calculate_personnel_count(severity):
    return severity * 2


def select_lead_officer(state, dept, target_sector):
    exact_candidates = [
        o
        for o in state.officer_registry.values()
        if o.department == dept
        and o.location_sector.lower() == target_sector.lower()
        and o.active_cases < 3
    ]
    if exact_candidates:
        return sorted(
            exact_candidates, key=lambda x: (x.active_cases, x.completed_cases)
        )[0]

    city_candidates = [
        o
        for o in state.officer_registry.values()
        if o.department == dept and o.active_cases < 3
    ]
    if city_candidates:
        return sorted(
            city_candidates, key=lambda x: (x.active_cases, x.completed_cases)
        )[0]

    return None


def sort_queue(state):
    state.call_queue.sort(
        key=lambda call: (
            0 if call.call_status == "Pending" else 1,
            -call.severity,
            call.call_id,
        )
    )


def log_emergency_call(state, caller, desc, depts, loc_code, severity):
    landmark, sector = LOCATION_MAP[loc_code]
    personnel = calculate_personnel_count(severity)
    assigned_officers = {}

    for dept in depts:
        officer = select_lead_officer(state, dept, sector)
        if not officer:
            print(
                f"\n[WARNING] All personnel in {dept} occupied. Call placed on waitlist."
            )
            return None
        assigned_officers[dept] = officer

    call_id = f"CALL-{str(state.call_counter).zfill(3)}"
    state.call_counter += 1

    call = EmergencyCall(
        call_id,
        caller,
        desc,
        depts,
        loc_code,
        landmark,
        severity,
        personnel,
        assigned_officers,
    )

    for officer in assigned_officers.values():
        officer.active_cases += 1

    state.call_queue.append(call)
    sort_queue(state)
    return call


def run_radio_dialogue_feed(call):
    first_dept = call.departments[0]
    lead = call.assigned_officers[first_dept]

    print(
        f"\n{'=' * 60}\n"
        f"--- INTERACTIVE RADIO DIALOGUE FEED [{call.call_id}] ---\n"
        f"{'=' * 60}\n"
        f"[RADIO] Dispatch to Lead {lead.rank} {lead.name} ({lead.officer_id} - {lead.location_sector}): Proceed to {call.landmark_name}."
    )

    input("Press [ENTER] to receive unit response...")
    call.unit_status = "En Route"
    print(
        f"[RADIO] {lead.rank} {lead.name}: 'Copy Dispatch. Heading to location.' [Status: EN ROUTE]"
    )

    input("Press [ENTER] to confirm unit arrival on scene...")
    call.unit_status = "On Scene"
    print(
        f"[RADIO] {lead.rank} {lead.name}: 'Reached location. Scene under control.' [Status: ON SCENE]"
    )

    while True:
        complete_input = input("\nIs the job complete? (Y/N): ").strip().upper()
        if complete_input in ["Y", "N"]:
            return complete_input == "Y"
        print("Error: Enter 'Y' for Yes or 'N' for No.")


def complete_call(state, call_id):
    target_call = None
    for call in state.call_queue:
        if call.call_id == call_id:
            target_call = call
            break

    if not target_call or target_call.call_status == "Completed":
        print("Error: Active pending Call ID not found.")
        return False

    if target_call.unit_status != "On Scene":
        print(
            "Error: Cannot complete call. Unit has not confirmed arrival on scene."
        )
        return False

    target_call.call_status = "Completed"
    target_call.unit_status = "Cleared"

    for officer in target_call.assigned_officers.values():
        officer.active_cases = max(0, officer.active_cases - 1)
        officer.completed_cases += 1

    sort_queue(state)
    print(
        f"\n[SYSTEM] {call_id} marked as COMPLETED and moved to past cases history."
    )
    return True


def search_police_records(state, query):
    query_str = query.strip().lower()
    results = [
        r
        for r in state.police_database
        if query_str in r.person_name.lower()
        or query_str in r.ssn_last4
        or any(query_str in inc.lower() for inc in r.prior_incidents)
    ]

    print(
        f"\n{'=' * 75}\n"
        f"--- POLICE DATABASE SEARCH RESULTS FOR: '{query}' ---\n"
        f"{'=' * 75}"
    )

    if not results:
        print(
            "[RECORD SYSTEM] No matching criminal or civil records found for query."
        )
    else:
        for r in results:
            warrants = ", ".join(r.warrants) if r.warrants else "None"
            citations = ", ".join(r.citations) if r.citations else "None"
            incidents = ", ".join(r.prior_incidents)
            print(
                f"Record ID: {r.record_id} | Name: {r.person_name} | SSN (Last 4): {r.ssn_last4}\n"
                f"Warrants:  {warrants}\n"
                f"Citations: {citations}\n"
                f"History:   {incidents}\n"
                f"{'-' * 75}"
            )


def display_past_cases_table(state):
    completed_calls = [
        c for c in state.call_queue if c.call_status == "Completed"
    ]

    table_header = (
        f"\n{'=' * 120}\n"
        f"{'PAST CASES HISTORY TABLE (COMPLETED INCIDENTS)':^120}\n"
        f"{'=' * 120}\n"
        f"{'Call ID':<9} | {'Caller Name':<15} | {'Description':<20} | {'Location':<25} | {'Sev':<4} | {'Departments':<14} | {'Assigned Officers'}\n"
        f"{'-' * 120}"
    )
    print(table_header)

    if not completed_calls:
        print(
            "  [INFO] No completed past cases currently in system records.\n"
            + "=" * 120
            + "\n"
        )
    else:
        for call in completed_calls:
            depts_str = ", ".join(call.departments)
            officers_str = ", ".join(
                [
                    f"{o.officer_id} ({o.name} - {o.location_sector})"
                    for o in call.assigned_officers.values()
                ]
            )
            loc_str = f"{call.location_code}: {call.landmark_name[:18]}"

            print(
                f"{call.call_id:<9} | {call.caller_name[:15]:<15} | {call.incident_description[:20]:<20} | {loc_str:<25} | {call.severity:<4} | {depts_str[:14]:<14} | {officers_str}"
            )
        print("=" * 120 + "\n")