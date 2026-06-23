# 🎓 AI Smart Exam Manager

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Data--Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **Intelligent, autonomous, and resilient examination administration for modern institutions.**

AI Smart Exam Manager is a premium, enterprise-grade institution management system designed to solve the NP-hard problem of examination scheduling. By leveraging advanced Constraint Satisfaction Algorithms, Social Graph Theory, and Heuristic Search, it eliminates administrative manual labor while maximizing academic integrity and staff wellbeing.

---

## ✨ Core Intelligence Modules

### 🧠 1. CSP Timetable Generator
Automates the creation of complex exam schedules using a **Constraint Satisfaction Problem (CSP)** approach with backtracking. 
- **Physical Constraints:** Ensures subject student counts Never exceed room capacities.
- **Temporal Constraints:** No overlapping exams for the same branch or in the same room.
- **Optimization:** Sorts subjects by complexity (student count) to guarantee the most efficient fit.

### 🛡️ 2. Social-Graph Isolation (Anti-Cheating)
A proactive academic integrity engine. Unlike reactive measures, this module uses **Social Graph Theory** to identify student cohorts (friends/lab partners) and systematically disperses them across different examination rooms using round-robin distribution.

### ⚖️ 3. Fatigue-Aware Duty Roster
Prioritizes faculty wellbeing. Implementing a **Greedy Load-Balancing Algorithm**, it tracks teacher duty counts and fatigue scores, ensuring no invigilator is assigned back-to-back heavy sessions or exceeds predefined work limits.

### 🚑 4. Self-Healing Emergency Engine
Real-time resilience. When an "Unavailability Event" (room closure or teacher absence) is triggered, the **Heuristic Local Search** engine performs an immediate sub-second re-calculation to re-route students and duties to the best-fit alternatives without human intervention.

### 📊 5. Predictive Inventory Management
Uses **Linear Usage Projection** to track exam supplies (answer sheets, stationery). It classifies stock urgency and calculates mathematically optimal restock quantities based on institutional usage rates.

---

## 🛠️ Technical Ecosystem

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.11+ / Flask 3.0 |
| **Persistence** | SQLite / Flask-SQLAlchemy (ORM) |
| **Security** | Session-based Auth / Flask-Login |
| **Data I/O** | openpyxl / Pandas (Excel Intermediaries) |
| **Frontend** | Vanilla JS (SPA Architecture) / HTML5 / CSS3 |
| **Visuals** | Chart.js 4 / Font Awesome 6 / Inter Font |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Pip (Python Package Index)

### Installation
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ai-smart-exam-manager.git
   cd ai-smart-exam-manager
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize & Run**
   ```bash
   python app.py
   ```

4. **Access the Portal**
   Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🔐 Access Credentials

The system initializes with three specialized roles:

| Role | Username | Password | Access |
| :--- | :--- | :--- | :--- |
| **Administrator** | `AdminPro` | `admin@123` | Full system control & AI scheduling |
| **Teacher** | `Teacher` | `teacher@456` | Duty view & Attendance marking |
| **Staff** | `Staff` | `staff@789` | Inventory & Non-teaching duties |

---

## 📂 Project Architecture

```text
AI Smart Exam Manager/
├── app.py              # Main Entry Point & API Controller
├── ai_engine.py        # Logic: CSP, Heuristics, & Social Graphs
├── models.py           # Data: SQLAlchemy Database Schemas
├── excel_handler.py    # I/O: Templated Data Import/Export
├── static/             # Assets: Design System & SPA Logic
│   ├── css/style.css   # Premium Glassmorphic UI Tokens
│   └── js/app.js       # Frontend State Management
├── templates/          # Views: Role-based SPA shells
└── tests/              # Quality: API & Logic Unit Tests
```

---

## 📸 Design Aesthetics
Built with a **Premium spatial-UI design system**, the application features:
- **Glassmorphism**: Elegant, semi-transparent dashboard components.
- **Dynamic Bento Grids**: Responsive information architecture.
- **Micro-animations**: Subtle feedback for every user interaction.
- **Persistent State**: Fluid navigation without page refreshes (SPA).

---

## 🤝 Contributing
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---
Developed with ❤️ by the AI Smart Exam Manager Team.
