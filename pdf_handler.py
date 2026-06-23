"""
AI Exam Manager — PDF Export Handler
Generates professional PDF documents for timetables and attendance.
"""
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

class ExamPDF(FPDF):
    def header(self):
        # Logo or Icon
        from models import Setting
        settings = {s.key: s.value for s in Setting.query.all()}
        college = settings.get('college_name', 'AI SMART EXAM MANAGER')
        code = settings.get('college_code', '')

        self.set_fill_color(27, 42, 74) # Dark blue header
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, college.upper(), ln=True, align='C')
        
        self.set_font('helvetica', 'B', 12)
        title = getattr(self, 'report_title', 'Examination Report')
        self.cell(0, 5, title, ln=True, align='C')
        self.ln(13)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='C')

def export_exams_pdf(data):
    """
    Export exam list to PDF.
    data: list of dicts with exam info
    """
    pdf = ExamPDF()
    pdf.report_title = 'Official Examination Timetable'
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Table Header
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(59, 130, 246)
    
    col_widths = [50, 30, 30, 40, 40]
    headers = ['Subject', 'Room', 'Date', 'Time', 'Session']
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, border=1, align='C', fill=True)
    pdf.ln()
    
    # Data Rows
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(31, 41, 55)
    
    fill = False
    for item in data:
        pdf.set_fill_color(249, 250, 251)
        pdf.cell(col_widths[0], 10, str(item.get('subject_name', '')), border=1, fill=fill)
        pdf.cell(col_widths[1], 10, str(item.get('room_name', '')), border=1, align='C', fill=fill)
        pdf.cell(col_widths[2], 10, str(item.get('date', '')), border=1, align='C', fill=fill)
        pdf.cell(col_widths[3], 10, f"{item.get('start_time', '')} - {item.get('end_time', '')}", border=1, align='C', fill=fill)
        pdf.cell(col_widths[4], 10, str(item.get('session_label', '')), border=1, align='C', fill=fill)
        pdf.ln()
        fill = not fill
        
    output = BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    return output

def export_attendance_pdf(data, title):
    """
    Export attendance sheet to PDF.
    """
    pdf = ExamPDF()
    pdf.report_title = title
    pdf.add_page()
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(27, 42, 74)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_fill_color(27, 42, 74)
    pdf.set_text_color(255, 255, 255)
    
    col_widths = [45, 45, 30, 30, 20, 20]
    headers = ['Name', 'Duty/Room', 'Date', 'Time', 'Attnd', 'Time In']
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align='C', fill=True)
    pdf.ln()
    
    # Data
    pdf.set_font('helvetica', '', 8)
    pdf.set_text_color(0, 0, 0)
    
    fill = False
    for item in data:
        pdf.set_fill_color(245, 247, 250)
        name = item.get('name', item.get('staff_name', item.get('invigilator_name', '')))
        duty = item.get('room_name', item.get('duty_description', item.get('location', '')))
        
        pdf.cell(col_widths[0], 8, str(name)[:25], border=1, fill=fill)
        pdf.cell(col_widths[1], 8, str(duty)[:25], border=1, fill=fill)
        pdf.cell(col_widths[2], 8, str(item.get('date', '')), border=1, align='C', fill=fill)
        pdf.cell(col_widths[3], 8, f"{item.get('start_time', '')}-{item.get('end_time', '')}", border=1, align='C', fill=fill)
        pdf.cell(col_widths[4], 8, 'Yes' if item.get('attended') else 'No', border=1, align='C', fill=fill)
        pdf.cell(col_widths[5], 8, str(item.get('check_in_time', '')), border=1, align='C', fill=fill)
        pdf.ln()
        fill = not fill
        
    output = BytesIO()
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    output.write(pdf_bytes)
    output.seek(0)
    return output
