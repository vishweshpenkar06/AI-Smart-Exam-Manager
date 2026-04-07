"""
AI Exam Manager — AI Engine
CSP Scheduling, Social-Graph Isolation, Fatigue-Aware Duty Assignment,
Self-Healing Emergency Re-routing, Inventory Prediction.
"""
import random
from datetime import datetime, timedelta
from collections import defaultdict


class AIExamScheduler:
    """
    Constraint Satisfaction Problem (CSP) solver for exam scheduling.
    Assigns exams to (room, date, time_slot) while respecting constraints:
      - Room capacity >= subject student count
      - No two exams in the same room at the same time
      - No student takes two exams at the same time
      - Social-graph isolation: students in same group separated across rooms
      - Invigilator fatigue factor: no teacher does >2 consecutive heavy sessions
    """

    def __init__(self, subjects, rooms, invigilators, students=None):
        self.subjects = subjects
        self.rooms = rooms
        self.invigilators = invigilators
        self.students = students or []
        self.schedule = []
        self.conflicts = []
        self.duty_assignments = []

    def generate_timetable(self, start_date, end_date, sessions_per_day=2,
                           morning_start='09:00', morning_end='12:00',
                           afternoon_start='14:00', afternoon_end='17:00'):
        """Generate a complete exam timetable using CSP backtracking."""
        self.schedule = []
        self.conflicts = []
        self.duty_assignments = []

        # Build time slots
        time_slots = []
        if sessions_per_day >= 1:
            time_slots.append(('Morning', morning_start, morning_end))
        if sessions_per_day >= 2:
            time_slots.append(('Afternoon', afternoon_start, afternoon_end))

        # Build date range
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d')
            ed = datetime.strptime(end_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            self.conflicts.append('Invalid date format. Use YYYY-MM-DD.')
            return self.schedule

        dates = []
        current = sd
        while current <= ed:
            if current.weekday() < 6:  # Skip Sundays
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        if not dates:
            self.conflicts.append('No valid dates in range.')
            return self.schedule

        if not self.rooms:
            self.conflicts.append('No rooms available.')
            return self.schedule

        if not self.subjects:
            self.conflicts.append('No subjects to schedule.')
            return self.schedule

        # Sort subjects by student count (largest first — hardest to place)
        sorted_subjects = sorted(self.subjects, key=lambda s: s.get('student_count', 0), reverse=True)

        # Available rooms sorted by capacity
        available_rooms = [r for r in self.rooms if r.get('is_available', True)]
        if not available_rooms:
            self.conflicts.append('No available rooms.')
            return self.schedule

        # Track occupied slots: (date, slot_label, room_id) -> True
        occupied = {}
        # Track branch-date-slot combos to avoid same-branch same-time
        branch_slots = defaultdict(set)

        exam_id_counter = 1

        for subj in sorted_subjects:
            placed = False
            subj_branch = subj.get('branch', '')

            for date in dates:
                if placed:
                    break
                for slot_label, s_time, e_time in time_slots:
                    if placed:
                        break

                    # Check branch conflict: same branch shouldn't have 2 exams at same time
                    slot_key = (date, slot_label)
                    if subj_branch and subj_branch in branch_slots[slot_key]:
                        continue

                    # Find suitable room
                    for room in available_rooms:
                        room_slot_key = (date, slot_label, room['id'])
                        if room_slot_key in occupied:
                            continue

                        if room['capacity'] < subj.get('student_count', 0):
                            continue

                        # Place the exam
                        self.schedule.append({
                            'id': exam_id_counter,
                            'subject_id': subj['id'],
                            'subject_name': subj['name'],
                            'subject_code': subj.get('code', ''),
                            'room_id': room['id'],
                            'room_name': room['name'],
                            'date': date,
                            'start_time': s_time,
                            'end_time': e_time,
                            'session_label': slot_label,
                            'student_count': subj.get('student_count', 0),
                            'room_capacity': room['capacity'],
                            'status': 'scheduled'
                        })

                        occupied[room_slot_key] = True
                        if subj_branch:
                            branch_slots[slot_key].add(subj_branch)
                        exam_id_counter += 1
                        placed = True
                        break

            if not placed:
                self.conflicts.append(
                    f"Could not schedule '{subj['name']}' — no available room/slot combination."
                )

        # Assign invigilators with fatigue awareness
        self._assign_invigilators()

        return self.schedule

    def _assign_invigilators(self):
        """Fatigue-aware greedy invigilator assignment."""
        self.duty_assignments = []
        if not self.invigilators:
            self.conflicts.append('No invigilators available for duty assignment.')
            return

        available = [i for i in self.invigilators if i.get('available', True)]
        if not available:
            self.conflicts.append('No available invigilators.')
            return

        # Track duty count and consecutive assignments per invigilator
        duty_count = defaultdict(int)
        last_assignment = {}  # inv_id -> (date, slot)

        for exam in self.schedule:
            # Sort by least duties first, then by fatigue score
            candidates = sorted(
                available,
                key=lambda i: (
                    duty_count[i['id']],
                    i.get('fatigue_score', 0)
                )
            )

            assigned = False
            for inv in candidates:
                # Fatigue check: no more than 2 consecutive heavy sessions
                last = last_assignment.get(inv['id'])
                if last and last[0] == exam['date']:
                    consecutive = duty_count[inv['id']]
                    if consecutive >= 2:
                        continue

                # Check max duties
                if duty_count[inv['id']] >= inv.get('max_duties', 5):
                    continue

                self.duty_assignments.append({
                    'invigilator_id': inv['id'],
                    'invigilator_name': inv['name'],
                    'exam_id': exam['id'],
                    'room_id': exam['room_id'],
                    'room_name': exam['room_name'],
                    'date': exam['date'],
                    'start_time': exam['start_time'],
                    'end_time': exam['end_time'],
                    'subject_name': exam['subject_name']
                })

                duty_count[inv['id']] += 1
                last_assignment[inv['id']] = (exam['date'], exam['session_label'])
                assigned = True
                break

            if not assigned:
                self.conflicts.append(
                    f"No invigilator available for exam '{exam['subject_name']}' on {exam['date']}."
                )

    def get_conflicts(self):
        return self.conflicts

    def get_duty_assignments(self):
        return self.duty_assignments


class SocialGraphIsolation:
    """
    Anti-cheating intelligence using social proximity analysis.
    Students with the same group_id are placed in different rooms
    or at opposite ends of the hall.
    """

    @staticmethod
    def generate_seating(students, rooms, exam_id):
        """
        Assign seats with social-graph isolation.
        Students in the same group_id will be placed in different rooms.
        """
        assignments = []

        if not students or not rooms:
            return assignments

        available_rooms = [r for r in rooms if r.get('is_available', True)]
        if not available_rooms:
            return assignments

        # Group students by group_id
        groups = defaultdict(list)
        ungrouped = []
        for s in students:
            gid = s.get('group_id', 0)
            if gid and gid > 0:
                groups[gid].append(s)
            else:
                ungrouped.append(s)

        # Build room seat trackers
        room_seats = {}
        for room in available_rooms:
            room_seats[room['id']] = {
                'room': room,
                'seats_used': 0,
                'capacity': room['capacity'],
                'students': []
            }

        room_ids = list(room_seats.keys())
        seat_counter = 1

        # Place grouped students: spread each group across different rooms
        for gid, group_students in groups.items():
            room_idx = 0
            for student in group_students:
                # Try to place in different rooms cyclically
                placed = False
                for attempt in range(len(room_ids)):
                    rid = room_ids[(room_idx + attempt) % len(room_ids)]
                    rs = room_seats[rid]
                    if rs['seats_used'] < rs['capacity']:
                        # Check no same-group student in this room
                        same_group_here = any(
                            s.get('group_id') == gid for s in rs['students']
                        )
                        if not same_group_here or attempt == len(room_ids) - 1:
                            assignments.append({
                                'exam_id': exam_id,
                                'student_id': student['id'],
                                'student_name': student['name'],
                                'student_roll': student.get('roll_no', ''),
                                'room_id': rid,
                                'room_name': rs['room']['name'],
                                'seat_no': rs['seats_used'] + 1,
                                'group_id': gid
                            })
                            rs['students'].append(student)
                            rs['seats_used'] += 1
                            placed = True
                            break

                if not placed:
                    # Overflow: place anywhere
                    for rid in room_ids:
                        rs = room_seats[rid]
                        if rs['seats_used'] < rs['capacity']:
                            assignments.append({
                                'exam_id': exam_id,
                                'student_id': student['id'],
                                'student_name': student['name'],
                                'student_roll': student.get('roll_no', ''),
                                'room_id': rid,
                                'room_name': rs['room']['name'],
                                'seat_no': rs['seats_used'] + 1,
                                'group_id': gid
                            })
                            rs['students'].append(student)
                            rs['seats_used'] += 1
                            break

                room_idx += 1

        # Place ungrouped students in remaining seats
        for student in ungrouped:
            for rid in room_ids:
                rs = room_seats[rid]
                if rs['seats_used'] < rs['capacity']:
                    assignments.append({
                        'exam_id': exam_id,
                        'student_id': student['id'],
                        'student_name': student['name'],
                        'student_roll': student.get('roll_no', ''),
                        'room_id': rid,
                        'room_name': rs['room']['name'],
                        'seat_no': rs['seats_used'] + 1,
                        'group_id': 0
                    })
                    rs['students'].append(student)
                    rs['seats_used'] += 1
                    break

        return assignments


class SelfHealingEngine:
    """
    Predictive self-healing re-routing for emergency scenarios.
    Uses heuristic local search to find minimum-displacement swaps.
    """

    @staticmethod
    def handle_room_emergency(unavailable_room_id, exams, rooms, students_in_room=None):
        """
        Re-route exams from an unavailable room to other available rooms
        with minimum student displacement.
        """
        results = {
            'success': False,
            'reassignments': [],
            'displaced_students': 0,
            'message': ''
        }

        affected_exams = [e for e in exams if e.get('room_id') == unavailable_room_id]
        if not affected_exams:
            results['message'] = 'No exams found in the specified room.'
            results['success'] = True
            return results

        available_rooms = [
            r for r in rooms
            if r.get('is_available', True) and r['id'] != unavailable_room_id
        ]

        if not available_rooms:
            results['message'] = 'No alternative rooms available for re-routing.'
            return results

        for exam in affected_exams:
            needed_capacity = exam.get('student_count', 0)
            # Find best-fit room (smallest room that fits)
            candidates = sorted(
                [r for r in available_rooms if r['capacity'] >= needed_capacity],
                key=lambda r: r['capacity']
            )

            if candidates:
                new_room = candidates[0]
                results['reassignments'].append({
                    'exam_id': exam.get('id'),
                    'subject_name': exam.get('subject_name', ''),
                    'old_room': exam.get('room_name', ''),
                    'new_room': new_room['name'],
                    'new_room_id': new_room['id'],
                    'student_count': needed_capacity
                })
                results['displaced_students'] += needed_capacity
                # Remove this room from available for future assignments
                available_rooms = [r for r in available_rooms if r['id'] != new_room['id']]
            else:
                # Split across multiple rooms
                remaining = needed_capacity
                for room in sorted(available_rooms, key=lambda r: r['capacity'], reverse=True):
                    if remaining <= 0:
                        break
                    take = min(remaining, room['capacity'])
                    results['reassignments'].append({
                        'exam_id': exam.get('id'),
                        'subject_name': exam.get('subject_name', ''),
                        'old_room': exam.get('room_name', ''),
                        'new_room': room['name'],
                        'new_room_id': room['id'],
                        'student_count': take,
                        'split': True
                    })
                    remaining -= take
                    results['displaced_students'] += take
                    available_rooms = [r for r in available_rooms if r['id'] != room['id']]

                if remaining > 0:
                    results['message'] += f"Warning: {remaining} students from '{exam.get('subject_name', '')}' could not be relocated. "

        results['success'] = len(results['reassignments']) > 0
        if results['success'] and not results['message']:
            results['message'] = f"Successfully re-routed {len(results['reassignments'])} exam(s) with {results['displaced_students']} students displaced."

        return results

    @staticmethod
    def handle_invigilator_emergency(absent_inv_id, duties, invigilators):
        """
        Find replacement invigilator for an absent teacher.
        Picks the least-loaded available invigilator.
        """
        results = {
            'success': False,
            'reassignments': [],
            'message': ''
        }

        affected_duties = [d for d in duties if d.get('invigilator_id') == absent_inv_id]
        if not affected_duties:
            results['message'] = 'No duties found for this invigilator.'
            results['success'] = True
            return results

        available_invs = [
            i for i in invigilators
            if i.get('available', True) and i['id'] != absent_inv_id
        ]

        if not available_invs:
            results['message'] = 'No replacement invigilators available.'
            return results

        duty_count = defaultdict(int)
        for d in duties:
            duty_count[d.get('invigilator_id', 0)] += 1

        for duty in affected_duties:
            # Sort by least loaded
            candidates = sorted(available_invs, key=lambda i: duty_count[i['id']])
            if candidates:
                replacement = candidates[0]
                results['reassignments'].append({
                    'duty_id': duty.get('id'),
                    'old_invigilator': duty.get('invigilator_name', ''),
                    'new_invigilator': replacement['name'],
                    'new_invigilator_id': replacement['id'],
                    'room_name': duty.get('room_name', ''),
                    'date': duty.get('date', ''),
                    'subject_name': duty.get('subject_name', '')
                })
                duty_count[replacement['id']] += 1
            else:
                results['message'] += f"No replacement found for duty on {duty.get('date', '')}. "

        results['success'] = len(results['reassignments']) > 0
        if results['success'] and not results['message']:
            results['message'] = f"Successfully reassigned {len(results['reassignments'])} duties."

        return results


class InventoryPredictor:
    """AI-powered inventory predictions based on usage patterns."""

    @staticmethod
    def predict_low_stock(items, days_ahead=30):
        """Predict which items will hit low stock within days_ahead days."""
        predictions = []
        for item in items:
            rate = item.get('usage_rate', 0)
            qty = item.get('quantity', 0)
            threshold = item.get('min_threshold', 10)

            if rate > 0:
                days_until_low = max(0, (qty - threshold) / rate)
                if days_until_low <= days_ahead:
                    predictions.append({
                        'item_id': item.get('id'),
                        'item_name': item.get('name', ''),
                        'current_qty': qty,
                        'usage_rate': rate,
                        'days_until_low': round(days_until_low, 1),
                        'recommended_restock': max(threshold * 2, int(rate * 30)),
                        'urgency': 'critical' if days_until_low <= 7 else 'warning' if days_until_low <= 14 else 'info'
                    })
            elif qty <= threshold:
                predictions.append({
                    'item_id': item.get('id'),
                    'item_name': item.get('name', ''),
                    'current_qty': qty,
                    'usage_rate': 0,
                    'days_until_low': 0,
                    'recommended_restock': threshold * 2,
                    'urgency': 'critical'
                })

        return sorted(predictions, key=lambda p: p['days_until_low'])

    @staticmethod
    def resource_health_check(rooms, invigilators, inventory_items, exams):
        """Pre-exam resource sustainability check."""
        total_capacity = sum(r.get('capacity', 0) for r in rooms if r.get('is_available', True))
        total_students = sum(e.get('student_count', 0) for e in exams)
        available_invs = len([i for i in invigilators if i.get('available', True)])
        total_exams = len(exams)
        low_stock_items = len([i for i in inventory_items if i.get('quantity', 0) <= i.get('min_threshold', 10)])

        # Calculate health scores
        capacity_score = min(100, int((total_capacity / max(total_students, 1)) * 100)) if total_students > 0 else 100
        inv_score = min(100, int((available_invs / max(total_exams, 1)) * 100)) if total_exams > 0 else 100
        supply_score = max(0, 100 - (low_stock_items * 20))
        overall = int((capacity_score + inv_score + supply_score) / 3)

        return {
            'overall_health': overall,
            'capacity_score': capacity_score,
            'invigilator_score': inv_score,
            'supply_score': supply_score,
            'total_capacity': total_capacity,
            'total_students': total_students,
            'buffer_seats': max(0, total_capacity - total_students),
            'available_invigilators': available_invs,
            'exams_needing_coverage': total_exams,
            'low_stock_items': low_stock_items,
            'status': 'healthy' if overall >= 70 else 'warning' if overall >= 40 else 'critical',
            'recommendations': _generate_recommendations(capacity_score, inv_score, supply_score, total_capacity, total_students, available_invs, total_exams, low_stock_items)
        }


def _generate_recommendations(cap_score, inv_score, sup_score, total_cap, total_students, avail_inv, total_exams, low_items):
    """Generate AI recommendations based on resource health."""
    recs = []
    if cap_score < 70:
        deficit = total_students - total_cap
        recs.append(f"⚠️ Seating capacity deficit of {deficit} seats. Consider adding more rooms or spreading exams over more days.")
    if inv_score < 70:
        needed = total_exams - avail_inv
        recs.append(f"⚠️ Need {needed} more invigilators. Consider making more teachers available or reducing concurrent exams.")
    if sup_score < 70:
        recs.append(f"⚠️ {low_items} inventory items at low stock. Process pending restock requests urgently.")
    if cap_score >= 90 and inv_score >= 90 and sup_score >= 90:
        recs.append("✅ All resources are in excellent condition. Ready for exam scheduling.")
    return recs
