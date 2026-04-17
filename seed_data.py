"""
AI Exam Manager — Sample Data Seeder
Seeds all workable sections with realistic sample data for
Import/Export demonstrations.
"""
from datetime import datetime, timedelta


def seed_all(db, models):
    """
    Seed every section with sample data if the tables are empty.
    `models` is a dict with model class references.
    Returns a summary dict of how many records were inserted per section.
    """
    summary = {}

    # ── 1. Branches ───────────────────────────────────────────────
    Branch = models['Branch']
    if Branch.query.count() == 0:
        branches = [
            Branch(name='Computer Science', code='CS', color='#4A90D9', student_count=120),
            Branch(name='Electronics & Communication', code='EC', color='#E74C3C', student_count=90),
            Branch(name='Mechanical Engineering', code='ME', color='#2ECC71', student_count=100),
            Branch(name='Civil Engineering', code='CE', color='#F39C12', student_count=80),
            Branch(name='Information Technology', code='IT', color='#9B59B6', student_count=110),
            Branch(name='Electrical Engineering', code='EE', color='#1ABC9C', student_count=75),
        ]
        for b in branches:
            db.session.add(b)
        db.session.commit()
        summary['branches'] = len(branches)

    # ── 2. Invigilators ───────────────────────────────────────────
    Invigilator = models['Invigilator']
    if Invigilator.query.count() == 0:
        invigilators = [
            Invigilator(name='Dr. Rajesh Kumar', email='rajesh.kumar@aismartcollege.edu',
                        phone='9876543001', department='Computer Science',
                        available=True, max_duties=5, group_id=1),
            Invigilator(name='Prof. Anita Sharma', email='anita.sharma@aismartcollege.edu',
                        phone='9876543002', department='Mathematics',
                        available=True, max_duties=4, group_id=2),
            Invigilator(name='Dr. Vikram Patel', email='vikram.patel@aismartcollege.edu',
                        phone='9876543003', department='Electronics & Communication',
                        available=True, max_duties=5, group_id=1),
            Invigilator(name='Prof. Meena Iyer', email='meena.iyer@aismartcollege.edu',
                        phone='9876543004', department='Mechanical Engineering',
                        available=True, max_duties=6, group_id=3),
            Invigilator(name='Dr. Suresh Reddy', email='suresh.reddy@aismartcollege.edu',
                        phone='9876543005', department='Civil Engineering',
                        available=True, max_duties=4, group_id=2),
            Invigilator(name='Prof. Deepa Nair', email='deepa.nair@aismartcollege.edu',
                        phone='9876543006', department='Information Technology',
                        available=True, max_duties=5, group_id=1),
            Invigilator(name='Dr. Ramesh Gupta', email='ramesh.gupta@aismartcollege.edu',
                        phone='9876543007', department='Computer Science',
                        available=True, max_duties=5, group_id=3),
            Invigilator(name='Prof. Kavitha Menon', email='kavitha.menon@aismartcollege.edu',
                        phone='9876543008', department='Physics',
                        available=False, max_duties=3, group_id=2),
            Invigilator(name='Dr. Anil Verma', email='anil.verma@aismartcollege.edu',
                        phone='9876543009', department='Electrical Engineering',
                        available=True, max_duties=4, group_id=1),
            Invigilator(name='Prof. Sunita Das', email='sunita.das@aismartcollege.edu',
                        phone='9876543010', department='Chemistry',
                        available=True, max_duties=5, group_id=3),
        ]
        for inv in invigilators:
            db.session.add(inv)
        db.session.commit()
        summary['invigilators'] = len(invigilators)

    # ── 3. Rooms ──────────────────────────────────────────────────
    Room = models['Room']
    if Room.query.count() == 0:
        rooms = [
            Room(name='Room 101', capacity=40, floor='1st Floor', room_type='Classroom',
                 is_available=True, equipment='Projector, AC, Whiteboard', buffer_seats=5),
            Room(name='Room 102', capacity=40, floor='1st Floor', room_type='Classroom',
                 is_available=True, equipment='Projector, AC', buffer_seats=5),
            Room(name='Room 201', capacity=35, floor='2nd Floor', room_type='Classroom',
                 is_available=True, equipment='Blackboard, Fan', buffer_seats=4),
            Room(name='Room 202', capacity=35, floor='2nd Floor', room_type='Classroom',
                 is_available=True, equipment='Projector, AC', buffer_seats=4),
            Room(name='Hall A', capacity=120, floor='Ground Floor', room_type='Exam Hall',
                 is_available=True, equipment='CCTV, AC, PA System, Projector', buffer_seats=10),
            Room(name='Hall B', capacity=100, floor='Ground Floor', room_type='Exam Hall',
                 is_available=True, equipment='CCTV, AC, PA System', buffer_seats=8),
            Room(name='Lab 301', capacity=30, floor='3rd Floor', room_type='Computer Lab',
                 is_available=True, equipment='30 Computers, AC, Projector', buffer_seats=3),
            Room(name='Lab 302', capacity=30, floor='3rd Floor', room_type='Computer Lab',
                 is_available=True, equipment='30 Computers, AC', buffer_seats=3),
            Room(name='Seminar Hall', capacity=80, floor='2nd Floor', room_type='Seminar Room',
                 is_available=True, equipment='Projector, AC, PA System, Video Conf', buffer_seats=6),
            Room(name='Room 303', capacity=45, floor='3rd Floor', room_type='Classroom',
                 is_available=False, equipment='Under Renovation', buffer_seats=5),
        ]
        for r in rooms:
            db.session.add(r)
        db.session.commit()
        summary['rooms'] = len(rooms)

    # ── 4. Subjects ───────────────────────────────────────────────
    Subject = models['Subject']
    if Subject.query.count() == 0:
        subjects = [
            Subject(name='Data Structures & Algorithms', code='CS301', branch='Computer Science', student_count=60, color='#4A90D9'),
            Subject(name='Database Management Systems', code='CS302', branch='Computer Science', student_count=58, color='#3498DB'),
            Subject(name='Operating Systems', code='CS303', branch='Computer Science', student_count=55, color='#2980B9'),
            Subject(name='Computer Networks', code='CS304', branch='Computer Science', student_count=60, color='#1F618D'),
            Subject(name='Digital Signal Processing', code='EC301', branch='Electronics & Communication', student_count=45, color='#E74C3C'),
            Subject(name='VLSI Design', code='EC302', branch='Electronics & Communication', student_count=42, color='#C0392B'),
            Subject(name='Microprocessors & Controllers', code='EC303', branch='Electronics & Communication', student_count=48, color='#E67E22'),
            Subject(name='Thermodynamics', code='ME301', branch='Mechanical Engineering', student_count=50, color='#2ECC71'),
            Subject(name='Fluid Mechanics', code='ME302', branch='Mechanical Engineering', student_count=48, color='#27AE60'),
            Subject(name='Machine Design', code='ME303', branch='Mechanical Engineering', student_count=52, color='#1E8449'),
            Subject(name='Structural Analysis', code='CE301', branch='Civil Engineering', student_count=40, color='#F39C12'),
            Subject(name='Geotechnical Engineering', code='CE302', branch='Civil Engineering', student_count=38, color='#D68910'),
            Subject(name='Web Technologies', code='IT301', branch='Information Technology', student_count=55, color='#9B59B6'),
            Subject(name='Cloud Computing', code='IT302', branch='Information Technology', student_count=52, color='#8E44AD'),
            Subject(name='Power Systems', code='EE301', branch='Electrical Engineering', student_count=40, color='#1ABC9C'),
            Subject(name='Engineering Mathematics-III', code='MA301', branch='Computer Science', student_count=120, color='#34495E'),
        ]
        for s in subjects:
            db.session.add(s)
        db.session.commit()
        summary['subjects'] = len(subjects)

    # ── 5. Students ───────────────────────────────────────────────
    Student = models['Student']
    if Student.query.count() == 0:
        # Generate students for each branch
        student_data = [
            # Computer Science students
            ('Aarav Mehta',       'CS2024001', 'Computer Science', 1, 'aarav.mehta@student.aismartcollege.edu',       '9800000001'),
            ('Bhavya Sharma',    'CS2024002', 'Computer Science', 1, 'bhavya.sharma@student.aismartcollege.edu',    '9800000002'),
            ('Charvi Patel',     'CS2024003', 'Computer Science', 1, 'charvi.patel@student.aismartcollege.edu',     '9800000003'),
            ('Dhruv Joshi',      'CS2024004', 'Computer Science', 2, 'dhruv.joshi@student.aismartcollege.edu',      '9800000004'),
            ('Eshaan Kapoor',    'CS2024005', 'Computer Science', 2, 'eshaan.kapoor@student.aismartcollege.edu',    '9800000005'),
            ('Fatima Khan',      'CS2024006', 'Computer Science', 2, 'fatima.khan@student.aismartcollege.edu',      '9800000006'),
            ('Gauri Deshmukh',   'CS2024007', 'Computer Science', 3, 'gauri.deshmukh@student.aismartcollege.edu',   '9800000007'),
            ('Harsh Agarwal',    'CS2024008', 'Computer Science', 3, 'harsh.agarwal@student.aismartcollege.edu',    '9800000008'),
            ('Ishita Reddy',     'CS2024009', 'Computer Science', 3, 'ishita.reddy@student.aismartcollege.edu',     '9800000009'),
            ('Jayesh Trivedi',   'CS2024010', 'Computer Science', 1, 'jayesh.trivedi@student.aismartcollege.edu',   '9800000010'),
            # Electronics students
            ('Kavya Nair',       'EC2024001', 'Electronics & Communication', 1, 'kavya.nair@student.aismartcollege.edu',       '9800000011'),
            ('Lakshay Verma',    'EC2024002', 'Electronics & Communication', 1, 'lakshay.verma@student.aismartcollege.edu',    '9800000012'),
            ('Manya Iyer',       'EC2024003', 'Electronics & Communication', 2, 'manya.iyer@student.aismartcollege.edu',       '9800000013'),
            ('Nakul Sinha',      'EC2024004', 'Electronics & Communication', 2, 'nakul.sinha@student.aismartcollege.edu',      '9800000014'),
            ('Ojas Kulkarni',    'EC2024005', 'Electronics & Communication', 3, 'ojas.kulkarni@student.aismartcollege.edu',    '9800000015'),
            # Mechanical students
            ('Priya Choudhury',  'ME2024001', 'Mechanical Engineering', 1, 'priya.choudhury@student.aismartcollege.edu',  '9800000016'),
            ('Qasim Ahmed',      'ME2024002', 'Mechanical Engineering', 1, 'qasim.ahmed@student.aismartcollege.edu',      '9800000017'),
            ('Rithika Menon',    'ME2024003', 'Mechanical Engineering', 2, 'rithika.menon@student.aismartcollege.edu',    '9800000018'),
            ('Siddharth Rao',    'ME2024004', 'Mechanical Engineering', 2, 'siddharth.rao@student.aismartcollege.edu',    '9800000019'),
            ('Tanvi Bhatt',      'ME2024005', 'Mechanical Engineering', 3, 'tanvi.bhatt@student.aismartcollege.edu',      '9800000020'),
            # Civil students
            ('Utkarsh Pandey',   'CE2024001', 'Civil Engineering', 1, 'utkarsh.pandey@student.aismartcollege.edu',   '9800000021'),
            ('Vedika Saxena',    'CE2024002', 'Civil Engineering', 1, 'vedika.saxena@student.aismartcollege.edu',    '9800000022'),
            ('Waqar Ali',        'CE2024003', 'Civil Engineering', 2, 'waqar.ali@student.aismartcollege.edu',        '9800000023'),
            ('Ximena Gomes',     'CE2024004', 'Civil Engineering', 2, 'ximena.gomes@student.aismartcollege.edu',     '9800000024'),
            # IT students
            ('Yash Malhotra',    'IT2024001', 'Information Technology', 1, 'yash.malhotra@student.aismartcollege.edu',    '9800000025'),
            ('Zara Sheikh',      'IT2024002', 'Information Technology', 1, 'zara.sheikh@student.aismartcollege.edu',      '9800000026'),
            ('Aditya Tiwari',    'IT2024003', 'Information Technology', 2, 'aditya.tiwari@student.aismartcollege.edu',    '9800000027'),
            ('Brinda Nambiar',   'IT2024004', 'Information Technology', 2, 'brinda.nambiar@student.aismartcollege.edu',   '9800000028'),
            # Electrical students
            ('Chirag Mishra',    'EE2024001', 'Electrical Engineering', 1, 'chirag.mishra@student.aismartcollege.edu',    '9800000029'),
            ('Divya Prasad',     'EE2024002', 'Electrical Engineering', 1, 'divya.prasad@student.aismartcollege.edu',     '9800000030'),
        ]
        students = []
        for name, roll, branch, gid, email, phone in student_data:
            s = Student(name=name, roll_no=roll, branch=branch,
                        group_id=gid, email=email, phone=phone)
            db.session.add(s)
            students.append(s)
        db.session.commit()
        summary['students'] = len(students)

    # ── 6. Inventory Items ────────────────────────────────────────
    InventoryItem = models['InventoryItem']
    if InventoryItem.query.count() == 0:
        inventory = [
            InventoryItem(name='A4 Paper Ream (500 sheets)', category='Stationery', quantity=200, min_threshold=50, unit='reams', usage_rate=5.0),
            InventoryItem(name='Blue Ballpoint Pens', category='Stationery', quantity=500, min_threshold=100, unit='pcs', usage_rate=15.0),
            InventoryItem(name='Black Ballpoint Pens', category='Stationery', quantity=350, min_threshold=80, unit='pcs', usage_rate=10.0),
            InventoryItem(name='Answer Booklets (32 pages)', category='Exam Materials', quantity=1500, min_threshold=300, unit='booklets', usage_rate=50.0),
            InventoryItem(name='Answer Booklets (16 pages)', category='Exam Materials', quantity=800, min_threshold=200, unit='booklets', usage_rate=30.0),
            InventoryItem(name='Graph Sheets', category='Exam Materials', quantity=400, min_threshold=100, unit='sheets', usage_rate=8.0),
            InventoryItem(name='Drawing Sheets (A3)', category='Exam Materials', quantity=300, min_threshold=80, unit='sheets', usage_rate=5.0),
            InventoryItem(name='Staplers', category='Equipment', quantity=25, min_threshold=5, unit='pcs', usage_rate=0.2),
            InventoryItem(name='Stapler Pins (Box)', category='Equipment', quantity=60, min_threshold=15, unit='boxes', usage_rate=2.0),
            InventoryItem(name='Paper Clips (Box)', category='Equipment', quantity=40, min_threshold=10, unit='boxes', usage_rate=1.5),
            InventoryItem(name='Rubber Bands (Pack)', category='Equipment', quantity=30, min_threshold=8, unit='packs', usage_rate=1.0),
            InventoryItem(name='Correction Fluid', category='Stationery', quantity=15, min_threshold=5, unit='bottles', usage_rate=0.5),
            InventoryItem(name='Envelopes (Large)', category='Packaging', quantity=500, min_threshold=100, unit='pcs', usage_rate=20.0),
            InventoryItem(name='Envelopes (Small)', category='Packaging', quantity=300, min_threshold=80, unit='pcs', usage_rate=12.0),
            InventoryItem(name='Sealing Wax Sticks', category='Packaging', quantity=45, min_threshold=10, unit='sticks', usage_rate=1.5),
            InventoryItem(name='String/Thread Rolls', category='Packaging', quantity=20, min_threshold=5, unit='rolls', usage_rate=0.8),
            InventoryItem(name='Attendance Registers', category='Records', quantity=50, min_threshold=10, unit='pcs', usage_rate=0.5),
            InventoryItem(name='Carbon Paper Sheets', category='Stationery', quantity=8, min_threshold=20, unit='sheets', usage_rate=3.0),
            InventoryItem(name='Whiteboard Markers', category='Classroom', quantity=80, min_threshold=20, unit='pcs', usage_rate=4.0),
            InventoryItem(name='Chalk Boxes', category='Classroom', quantity=35, min_threshold=10, unit='boxes', usage_rate=2.5),
        ]
        for item in inventory:
            db.session.add(item)
        db.session.commit()
        summary['inventory'] = len(inventory)

    # ── 7. Staff Duties ───────────────────────────────────────────
    StaffDuty = models['StaffDuty']
    if StaffDuty.query.count() == 0:
        # Use dates a couple of weeks from now
        base_date = datetime(2026, 4, 20)
        staff_duties = [
            StaffDuty(staff_name='Rajesh Kumar', duty_description='Hall Arrangement & Seating Setup',
                      location='Hall A', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='07:30', end_time='09:00'),
            StaffDuty(staff_name='Priya Sharma', duty_description='Stationery Distribution to Rooms',
                      location='Staff Room', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='09:30'),
            StaffDuty(staff_name='Amit Patel', duty_description='Student Entry & ID Verification',
                      location='Main Gate', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='09:30'),
            StaffDuty(staff_name='Sunita Devi', duty_description='Answer Sheet Collection & Packing',
                      location='Hall A', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='12:00', end_time='13:30'),
            StaffDuty(staff_name='Manoj Singh', duty_description='Water & Refreshment Arrangement',
                      location='Canteen Area', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='08:30', end_time='12:30'),
            StaffDuty(staff_name='Rajesh Kumar', duty_description='Hall Arrangement for Afternoon Session',
                      location='Hall B', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='13:00', end_time='14:00'),
            StaffDuty(staff_name='Pooja Gupta', duty_description='First Aid & Medical Standby',
                      location='Medical Room', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='17:00'),
            StaffDuty(staff_name='Ravi Shankar', duty_description='CCTV Monitoring & Security',
                      location='Control Room', date=(base_date).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='17:00'),
            StaffDuty(staff_name='Neha Kapoor', duty_description='Student Guidance & Help Desk',
                      location='Lobby', date=(base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='09:30'),
            StaffDuty(staff_name='Amit Patel', duty_description='Emergency Coordination',
                      location='Admin Office', date=(base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='17:00'),
            StaffDuty(staff_name='Priya Sharma', duty_description='Answer Sheet Counting & Sealing',
                      location='Strong Room', date=(base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                      start_time='12:30', end_time='14:00'),
            StaffDuty(staff_name='Sunita Devi', duty_description='Stationery Distribution to Rooms',
                      location='Staff Room', date=(base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                      start_time='08:00', end_time='09:00'),
        ]
        for d in staff_duties:
            db.session.add(d)
        db.session.commit()
        summary['staff_duties'] = len(staff_duties)

    # ── 8. Exams (pre-scheduled sample) ───────────────────────────
    Exam = models['Exam']
    if Exam.query.count() == 0:
        # Get subject & room IDs
        all_subjects = Subject.query.all()
        all_rooms = Room.query.filter_by(is_available=True).all()

        if all_subjects and all_rooms:
            base_date = datetime(2026, 4, 20)
            exams_def = []
            day = 0
            subj_idx = 0
            room_idx = 0

            for subj in all_subjects[:8]:  # Schedule first 8 subjects
                room = all_rooms[room_idx % len(all_rooms)]
                session_morning = (subj_idx % 2 == 0)

                exam = Exam(
                    subject_id=subj.id,
                    room_id=room.id,
                    date=(base_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    start_time='09:00' if session_morning else '14:00',
                    end_time='12:00' if session_morning else '17:00',
                    status='scheduled',
                    session_label='Morning' if session_morning else 'Afternoon'
                )
                db.session.add(exam)
                exams_def.append(exam)

                subj_idx += 1
                room_idx += 1
                if subj_idx % 2 == 0:
                    day += 1

            db.session.commit()
            summary['exams'] = len(exams_def)

    return summary
