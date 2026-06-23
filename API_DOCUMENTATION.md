# AI Smart Exam Manager — API Documentation

This document outlines the JSON API endpoints available in the application. Most endpoints are protected by session-based authentication (`@login_required`).

## Base URL
`/api`

---

## 1. Authentication

- **POST /login**
  - Payload: `{"username": "AdminPro", "password": "..."}`
  - Rate limited to 5 attempts per minute.

---

## 2. Dashboard Stats

- **GET /api/stats**
  - Returns comprehensive metrics, chart data, and resource health.

---

## 3. Resources

### Invigilators
- **GET /api/invigilators** — List all
- **POST /api/invigilators** — Create
  - Payload: `{"name": "...", "email": "...", "phone": "...", "department": "..."}`
- **PUT /api/invigilators/<id>** — Update
- **DELETE /api/invigilators/<id>** — Delete
- **POST /api/invigilators/<id>/toggle** — Toggle availability status

### Rooms
- **GET /api/rooms** — List all
- **POST /api/rooms** — Create
  - Payload: `{"name": "...", "capacity": 30, "room_type": "Classroom"}`
- **PUT /api/rooms/<id>** — Update
- **DELETE /api/rooms/<id>** — Delete

### Subjects
- **GET /api/subjects** — List all
- **POST /api/subjects** — Create
- **PUT /api/subjects/<id>** — Update
- **DELETE /api/subjects/<id>** — Delete

### Students
- **GET /api/students?branch=CS** — List all (optional filter)
- **POST /api/students** — Create
- **PUT /api/students/<id>** — Update
- **DELETE /api/students/<id>** — Delete

---

## 4. Exams & Scheduling

- **POST /api/exams/generate** (AI Engine)
  - Payload: `{"start_date": "...", "end_date": "...", "sessions_per_day": 2, "subject_ids": [1, 2]}`
- **GET /api/exams?page=1&per_page=20** — List generated exams
- **DELETE /api/exams/<id>** — Delete specific exam
- **POST /api/exams/clear** — Delete all exams, seating, and duties

### Seating & Duties
- **GET /api/seating?exam_id=1&room_id=2** — List seating assignments
- **GET /api/duties?date=...&invigilator_id=...** — List duty assignments
- **POST /api/duties/<id>/attend** — Mark attendance for duty

---

## 5. Inventory & Restock

- **GET /api/inventory** — List inventory
- **POST /api/inventory** — Create item
- **PUT /api/inventory/<id>** — Update logic
- **POST /api/inventory/<id>/adjust** — Manually add/subtract from stock
- **GET /api/inventory/predict** — Run AI predictor on low stock
- **GET /api/restocks** — List restock requests
- **POST /api/restocks** — Create request
- **POST /api/restocks/<id>/approve** — Approve request (updates inventory)
- **POST /api/restocks/<id>/reject** — Reject request

---

## 6. Self-Healing System (Emergency)

- **POST /api/emergency/room**
  - Payload: `{"room_id": 1, "reason": "Water leak"}`
  - Triggers AI to re-route exams to new rooms.
- **POST /api/emergency/invigilator**
  - Payload: `{"invigilator_id": 2, "reason": "Sick leave"}`
  - Triggers AI to substitute duties with standby invigilators.
- **GET /api/emergency/logs** — List emergency event logs.

---

## 7. Administrative

- **POST /admin/backup** — Create a SQLite backup file
- **GET /admin/backups** — List all backups
- **POST /admin/restore/<backup_name>** — Restore DB from backup file
- **GET /api/audit** — List system action logs
- **GET /health** — Application liveness check
