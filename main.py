import dispatch


def handle_log_call(state):
    print("\n--- NEW EMERGENCY INTAKE ---")
    caller = input("Caller Name: ").strip()
    desc = input("Emergency Description: ").strip()

    if not caller or not desc:
        print("Error: Caller name and emergency description cannot be blank.")
        return

    print("\nDepartments: 1. Police | 2. Fire | 3. Paramedics")
    dept_in = input(
        "Select Departments (comma separated, e.g., 1, 3): "
    ).strip()

    if len(dept_in) > 1 and "," not in dept_in:
        print(
            "Error: Invalid formatting. Separate department numbers using commas (e.g., '1, 2')."
        )
        return

    dept_map = {"1": "Police", "2": "Fire", "3": "Paramedic"}
    selected_depts = []
    tokens = [t.strip() for t in dept_in.split(",") if t.strip()]

    for t in tokens:
        if t in dept_map:
            if dept_map[t] not in selected_depts:
                selected_depts.append(dept_map[t])
        else:
            print(
                "Error: Please use valid single department numbers (1, 2, or 3) separated by commas."
            )
            return

    if not selected_depts:
        print("Error: Please select at least one department.")
        return

    loc_lines = ["\nLocation Codes Directory:", "-" * 55]
    for code, (landmark, sector) in dispatch.LOCATION_MAP.items():
        loc_lines.append(f"  {code} : {landmark:<28} ({sector})")
    loc_lines.append("-" * 55)
    print("\n".join(loc_lines))

    loc_code = input("Enter Location Code (L01-L10): ").strip().upper()
    if loc_code not in dispatch.LOCATION_MAP:
        print("Error: Invalid location code. Select from L01 to L10.")
        return

    sev_in = input("Severity Level (1-5): ").strip()
    if not sev_in.isdigit() or not (1 <= int(sev_in) <= 5):
        print("Error: Severity must be an integer from 1 to 5.")
        return

    severity = int(sev_in)
    call = dispatch.log_emergency_call(
        state, caller, desc, selected_depts, loc_code, severity
    )

    if call:
        print(
            f"\n[SYSTEM] Call Logged: {call.call_id}\n"
            f"Location: {call.landmark_name} ({dispatch.LOCATION_MAP[loc_code][1]})\n"
            f"Personnel Allocated: {call.personnel_per_dept} per department"
        )

        is_completed = dispatch.run_radio_dialogue_feed(call)
        if is_completed:
            dispatch.complete_call(state, call.call_id)


def handle_search_records(state):
    q = input("\nEnter Search Query (Name, SSN last 4, or Location): ").strip()
    if q:
        dispatch.search_police_records(state, q)
    else:
        print("Error: Query cannot be empty.")


def handle_complete_call(state):
    cid = input("\nEnter Call ID to Complete (e.g., CALL-001): ").strip().upper()
    dispatch.complete_call(state, cid)


def display_menu():
    print(
        f"\n{'=' * 50}\n"
        f"    911 EMERGENCY DISPATCH SYSTEM - MAIN MENU   \n"
        f"{'=' * 50}\n"
        f"1. Log Call & Start Radio Feed\n"
        f"2. Search Police Records\n"
        f"3. Officer Station (Complete Call)\n"
        f"4. View Past Cases Table\n"
        f"5. Exit Program\n"
        f"{'-' * 50}"
    )


def process_menu_choice(choice, state):
    if choice == "1":
        handle_log_call(state)
    elif choice == "2":
        handle_search_records(state)
    elif choice == "3":
        handle_complete_call(state)
    elif choice == "4":
        dispatch.display_past_cases_table(state)
    elif choice == "5":
        print("Exiting Emergency Dispatch System. Goodbye.")
        return False
    else:
        print("Error: Invalid choice. Select 1, 2, 3, 4, or 5.")
    return True


def main():
    state = dispatch.initialize_system_data()
    running = True

    while running:
        display_menu()
        choice = input("Select Option (1-5): ").strip()
        running = process_menu_choice(choice, state)


if __name__ == "__main__":
    main()