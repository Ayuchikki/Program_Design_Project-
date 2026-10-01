# 911 Emergency Dispatch System

A command-line application that simulates a 911 dispatch center. A dispatcher logs an emergency, the system automatically assigns lead officers from the matching departments, an interactive radio feed simulates unit communication, and completed incidents are tracked in a case history. A built-in police records database supports quick background lookups.

Written in pure Python 3, with no external dependencies.

---

## Features

- **Multi-department call logging**: dispatch Police, Fire, and/or Paramedics (1 to 3 at once) for a single incident.
- **Automatic personnel calculation**: required personnel per department = `severity × 2`.
- **Smart lead-officer assignment**: picks an officer in the incident's sector with fewer than 3 active cases, preferring the lowest active workload and then the lowest completed count. Falls back to a city-wide search if the sector has no one available.
- **Interactive radio feed**: step through `Assigned → En Route → On Scene`, then mark the job complete (Y/N).
- **Priority queue**: Pending calls are sorted to the top by severity (highest first); Completed calls sink to the bottom.
- **Officer workload tracking**: each officer tracks active and completed case counts.
- **Police record search**: search by civilian name, last 4 digits of SSN, or prior-incident location code.
- **Past cases table**: formatted table of all completed incidents with assigned officers.
- **Input validation**: blank fields, bad department selections, invalid location codes, and out-of-range severity are all rejected with clear error messages.

---

## Project Structure

```
.
├── main.py        # CLI: menu, input prompts, and input validation
├── dispatch.py    # Core logic: data models, officer selection, queue, records, tables
└── README.md
```

| File | Responsibility |
|------|----------------|
| `main.py` | Presents the main menu, collects and validates user input, and calls into `dispatch.py`. |
| `dispatch.py` | Defines `Officer`, `PoliceRecord`, `EmergencyCall`, and `DispatchSystemState`, the location map, seed data, and all dispatch logic. |

---

## Getting Started

### Requirements

- Python 3.8 or newer

### Run

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python main.py
```

---

## Usage

### Main Menu

```
==================================================
    911 EMERGENCY DISPATCH SYSTEM - MAIN MENU
==================================================
1. Log Call & Start Radio Feed
2. Search Police Records
3. Officer Station (Complete Call)
4. View Past Cases Table
5. Exit Program
```

### 1. Log a call

You'll be prompted for:

1. **Caller name** and **emergency description** (cannot be blank)
2. **Departments**: comma-separated numbers, e.g. `1, 3`
   - `1` = Police, `2` = Fire, `3` = Paramedic
3. **Location code**: `L01` to `L10` (see table below)
4. **Severity**: integer from `1` (minor) to `5` (critical)

The system assigns a Call ID (`CALL-001`, `CALL-002`, ...), allocates officers, and starts the radio feed. Press **Enter** to advance the unit to *En Route* and then *On Scene*, then answer `Y` or `N` to *"Is the job complete?"*

- `Y` completes the call immediately.
- `N` leaves the call Pending. Close it later from option 3.

### 2. Search police records

Search by name, SSN last 4, or a location code found in a person's incident history.

Sample data included: `Jane Doe`, `John Smith`, `Ayush Kumar`, `4321`, `L04`.

### 3. Complete a call

Enter a Call ID such as `CALL-001`. A call can only be completed after its unit is **On Scene**.

### 4. View past cases

Displays a table of all completed incidents.

### 5. Exit

Quits the program.

---

## Location Codes

| Code | Landmark | Sector |
|------|----------|--------|
| L01 | Times Square | Manhattan |
| L02 | Washington Square Park | Lower East Side |
| L03 | Union Square | Lower East Side |
| L04 | Brooklyn Bridge | Brooklyn |
| L05 | Coney Island | Brooklyn |
| L06 | Central Park (Mall/Bethesda) | Upper West Side |
| L07 | Williamsburg | Brooklyn |
| L08 | SoHo | Lower East Side |
| L09 | Bryant Park | Manhattan |
| L10 | East Village | Lower East Side |

---

## How Dispatching Works

**Personnel required:**

```
personnel_per_dept = severity × 2        # severity 4 → 8 per department
```

**Lead officer selection** (per department):

1. Candidates in the incident's sector with `active_cases < 3`, ranked by fewest active cases, then fewest completed cases.
2. If none, the same rule applied city-wide.
3. If still none, a warning is printed and the call is not dispatched.

**Queue ordering** (`sort_queue`):

```
key = (Pending first, higher severity first, earlier call ID first)
```

**Call lifecycle:**

- Unit status: `Assigned → En Route → On Scene → Cleared`
- Call status: `Pending → Completed`

---

## Example Session

```
Select Option (1-5): 1
Caller Name: Jane Doe
Emergency Description: Robbery
Select Departments (comma separated, e.g., 1, 3): 1, 3
Enter Location Code (L01-L10): L01
Severity Level (1-5): 4

[SYSTEM] Call Logged: CALL-001
Location: Times Square (Manhattan)
Personnel Allocated: 8 per department

--- INTERACTIVE RADIO DIALOGUE FEED [CALL-001] ---
[RADIO] Dispatch to Lead Patrol Officer Maria Chen (P-101 - Manhattan): Proceed to Times Square.
Press [ENTER] to receive unit response...
[RADIO] Patrol Officer Maria Chen: 'Copy Dispatch. Heading to location.' [Status: EN ROUTE]
Press [ENTER] to confirm unit arrival on scene...
[RADIO] Patrol Officer Maria Chen: 'Reached location. Scene under control.' [Status: ON SCENE]

Is the job complete? (Y/N): Y
[SYSTEM] CALL-001 marked as COMPLETED and moved to past cases history.
```

---

## Roadmap

The current build covers the core dispatch loop. Features from the original PRD and design document that are planned but **not yet implemented**:

- [ ] Dynamic severity escalation for active calls (with personnel recalculation and lead-rank upgrade)
- [ ] Department-specific queue filtering
- [ ] Combined queue + officer telemetry view (menu option 4)
- [ ] Shift telemetry export to `shift_summary.txt` on exit
- [ ] Confirmation prompt when exiting with Severity 5 calls still pending
- [ ] Real priority waitlist with automatic re-dispatch after each completion (currently a warning only)
- [ ] Severity-based lead rank selection (e.g. Commander / Battalion Chief for severity 5)
- [ ] Full 60-officer registry across 10 sectors (currently 12 officers across 4 sectors)
- [ ] Active pending call counter on the main menu
- [ ] Expanded police record search (location incident history lookup by code)

---

## Contributing

Issues and pull requests are welcome. For larger changes, please open an issue first to discuss what you'd like to change.

