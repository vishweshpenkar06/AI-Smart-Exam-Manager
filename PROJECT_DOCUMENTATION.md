# AI EXAM MANAGER — Project Documentation

## How to Start

```bash
cd "AI Smart Exam Manager"
python app.py
```
Then open **http://localhost:5000** in your browser.

## How to Stop
Press `Ctrl+C` in the terminal.

---

## Login Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | `AdminPro` | `admin@123` | Full system access, AI scheduling |
| Teacher | `Teacher` | `teacher@456` | View duties, mark attendance |
| Staff | `Staff` | `staff@789` | View staff duties, mark attendance |

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask 3 |
| Database | SQLite (persistent — `exam_manager.db`) |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login (session-based) |
| Frontend | HTML5 + Vanilla CSS + Vanilla JavaScript |
| Charts | Chart.js 4 (CDN) |
| Excel I/O | openpyxl |
| Icons | Font Awesome 6 (CDN) |
| Fonts | Google Fonts — Inter |

---

## Project File Structure

```
AI Smart Exam Manager/
├── app.py                    # Main Flask app (40+ routes)
├── models.py                 # SQLAlchemy database models (15 tables)
├── ai_engine.py              # AI scheduling & intelligence engine
├── excel_handler.py          # Excel import/export handler
├── requirements.txt          # Python dependencies
├── exam_manager.db           # SQLite database (auto-created on first run)
├── PROJECT_DOCUMENTATION.md  # This file
├── static/
│   ├── css/style.css         # Complete design system
│   ├── js/app.js             # SPA frontend (~1000 lines)
│   └── uploads/              # Uploaded Excel files
└── templates/
    ├── login.html            # Login page (3-role)
    ├── admin.html            # Admin SPA shell
    ├── teacher.html          # Teacher/Invigilator portal
    └── staff.html            # Non-teaching staff portal
```

---

## Database Models (15 Tables)

| Table | Purpose |
|-------|---------|
| `users` | Admin, Teacher, Staff login accounts |
| `invigilators` | Teacher/invigilator records with availability & fatigue tracking |
| `rooms` | Exam rooms with capacity, floor, availability |
| `subjects` | Course subjects with branch & student count |
| `students` | Students with roll number & social group_id |
| `exams` | Scheduled exam sessions |
| `seating_assignments` | Student-to-seat mapping per exam |
| `duty_assignments` | Invigilator duty roster with attendance |
| `inventory_items` | Non-teaching supplies stock |
| `restock_requests` | Supply restock approval workflow |
| `branches` | Academic department/branch records |
| `emergency_logs` | Emergency event audit trail |
| `audit_logs` | Full system activity history |
| `settings` | College profile & schedule configuration |
| `staff_duties` | Non-teaching staff duty assignments |

---

## AI Algorithms

### 1. CSP Timetable Generator
**File:** `ai_engine.py` → `AIExamScheduler`

**Algorithm:** Constraint Satisfaction Problem (CSP) with backtracking

**Constraints checked:**
- Room capacity ≥ subject student count
- No two exams in the same room at the same time  
- No same-branch exams in the same time slot
- Invigilator fatigue factor (max 2 consecutive sessions)

**Process:**
1. Sort subjects by student count (largest first — hardest to fit)
2. For each subject, iterate through date × time-slot × room combinations
3. If all constraints pass, assign and mark the slot as occupied
4. If no slot found, record a conflict

### 2. Social-Graph Isolation (Anti-Cheating)
**File:** `ai_engine.py` → `SocialGraphIsolation`

**Algorithm:** Group-aware seat distribution

**Logic:**
- Students with the same `group_id` (friends, project partners, batch-mates) are placed in **different rooms**
- Groups are distributed in round-robin fashion across rooms
- If a same-group student is already in a room, the algorithm places the next in a different room
- Falls back gracefully when there are more group members than rooms

**Impact:** Breaks the "buddy system" that enables planned cheating

### 3. Fatigue-Aware Duty Assignment
**File:** `ai_engine.py` → `_assign_invigilators()`

**Algorithm:** Greedy with fatigue factor

**Logic:**
- Sort candidates by: (duty_count, fatigue_score) ascending
- Skip invigilators who have done 2+ duties on the same day (consecutive heavy sessions)
- Assign the least-loaded available invigilator
- Update duty count after each assignment

### 4. Self-Healing Emergency Re-routing
**File:** `ai_engine.py` → `SelfHealingEngine`

**Algorithm:** Best-fit heuristic local search

**Room emergency:**
1. Find all exams in the unavailable room
2. Sort available rooms by capacity (smallest that fits first — best-fit)
3. Reassign each exam to the smallest fitting room
4. If no single room fits, split across multiple rooms (minimum displacement)
5. Update all database records atomically

**Invigilator absence:**
1. Find all duties of the absent invigilator
2. Sort available replacements by current duty load (least-loaded first)
3. Reassign each duty to the least-loaded available invigilator

### 5. Inventory Prediction
**File:** `ai_engine.py` → `InventoryPredictor`

**Algorithm:** Linear usage-rate projection

- Tracks `usage_rate` (units/week) on each item
- Predicts `days_until_low = (quantity - min_threshold) / daily_rate`
- Classifies urgency: critical (≤7 days), warning (≤14 days), info (≤30 days)
- Recommends restock quantity: `max(threshold × 2, rate × 30)`

### 6. Resource Health Check
**File:** `ai_engine.py` → `resource_health_check()`

Calculates three scores (0–100):
- **Capacity Score:** `(total_room_capacity / total_students) × 100`
- **Invigilator Score:** `(available_invs / total_exams) × 100`
- **Supply Score:** `100 - (low_stock_items × 20)`
- **Overall Health:** Average of all three scores

Generates AI recommendations based on score thresholds.

---

## Block Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI EXAM MANAGER                          │
├─────────────────────────────────────────────────────────────────┤
│  LOGIN LAYER                                                     │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────┐           │
│  │  Admin   │  │   Teacher   │  │  Non-Teaching    │           │
│  │ AdminPro │  │   Teacher   │  │  Staff / Staff   │           │
│  └────┬─────┘  └──────┬──────┘  └────────┬─────────┘           │
│       │               │                   │                      │
├───────▼───────────────▼───────────────────▼─────────────────────┤
│  FLASK APPLICATION LAYER (app.py)                               │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Auth Routes │ CRUD APIs │ AI APIs │ Import/Export APIs │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │                                       │
│        ┌─────────────────┼─────────────────┐                    │
│        ▼                 ▼                  ▼                    │
│  ┌───────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │ AI Engine │   │Excel Handler │   │  SQLite DB   │           │
│  │ ai_engine │   │excel_handler │   │  models.py   │           │
│  │           │   │              │   │  15 Tables   │           │
│  │ • CSP     │   │ • Import     │   │              │           │
│  │ • SocialG │   │ • Export     │   │ Persistent   │           │
│  │ • Fatigue │   │ • Templates  │   │ across       │           │
│  │ • Healing │   │ • Attendance │   │ restarts     │           │
│  │ • Predict │   │              │   │              │           │
│  └───────────┘   └──────────────┘   └──────────────┘           │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  FRONTEND (SPA)                                                  │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌───────────────┐   │
│  │Dashboard │  │Invig.   │  │Rooms     │  │Subjects       │   │
│  │+Charts   │  │+Toggle  │  │+Capacity │  │+Colors        │   │
│  └──────────┘  └─────────┘  └──────────┘  └───────────────┘   │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌───────────────┐   │
│  │AI Gener. │  │Sessions │  │Seating   │  │Duty List      │   │
│  │4-Step    │  │CRUD     │  │Grid View │  │Attendance     │   │
│  │Wizard    │  │         │  │          │  │               │   │
│  └──────────┘  └─────────┘  └──────────┘  └───────────────┘   │
│  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌───────────────┐   │
│  │Inventory │  │Restock  │  │Emergency │  │Audit Log      │   │
│  │+AI Pred. │  │Approve/ │  │Self-Heal │  │+Filter        │   │
│  │          │  │Reject   │  │AI Reroute│  │               │   │
│  └──────────┘  └─────────┘  └──────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Excel Import/Export Guide

### Importing Data
1. Click **Import** button in any section
2. Download the Excel template by clicking "Download template"
3. Fill in your data following the template format
4. Upload: drag-drop or click "Browse"
5. Click **Import** — data is saved automatically

### Supported Import Sections
| Section | Required Columns |
|---------|-----------------|
| Invigilators | Name, Email, Phone, Department, Available, Max Duties, Group ID |
| Rooms | Name, Capacity, Floor, Room Type, Available, Equipment, Buffer Seats |
| Subjects | Name, Code, Branch, Student Count, Color |
| Students | Name, Roll No, Branch, Group ID, Email, Phone |
| Inventory | Name, Category, Quantity, Min Threshold, Unit |
| Branches | Name, Code, Color, Student Count |
| Staff Duties | Staff Name, Duty Description, Location, Date, Start Time, End Time |

### Exporting Data
1. Click **Export** button in any section or go to Admin → Duty List / Staff Duties
2. An `.xlsx` file downloads automatically with current data

### Attendance Sheets
- **Teacher Attendance:** Admin → Duty List → "Attendance Sheet" button
- **Staff Attendance:** Admin → Staff Duties → "Attendance" button
- Both portals (Teacher/Staff) also have a direct download link

---

## API Reference (Selected Endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | JSON login (returns redirect URL) |
| GET | `/api/stats` | Dashboard statistics + charts data |
| GET/POST | `/api/invigilators` | List / Create invigilators |
| POST | `/api/exams/generate` | AI exam timetable generation |
| POST | `/api/emergency/room` | Trigger room emergency + AI reroute |
| POST | `/api/emergency/invigilator` | Handle invigilator absence |
| GET | `/api/inventory/predict` | AI low-stock predictions |
| POST | `/api/ai/suggest` | AI suggestions for any section |
| GET | `/api/export/<section>` | Download section data as Excel |
| POST | `/api/import/<section>` | Upload Excel to import records |
| GET | `/api/template/<section>` | Download blank Excel template |
| GET | `/api/export/attendance/<role>` | Download attendance sheet |

---

## Data Persistence

All data is stored in **SQLite** (`exam_manager.db` in the project root).

- Data **persists across restarts** — the database file is kept on disk
- No additional database server needed
- Back up `exam_manager.db` to preserve your data

---

## Troubleshooting

**App won't start:**
```bash
pip install -r requirements.txt
python app.py
```

**Can't login:**  
Make sure the database initialized (run `python app.py` once to create it).

**Import fails:**  
Check that your Excel file uses the exact column headers from the template. Download the template first.

**AI Generator shows conflicts:**  
Add more rooms or extend the date range. The system will tell you exactly which exams couldn't be placed.
