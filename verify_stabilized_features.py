import os
import io
import pandas as pd
from app import app, db, Invigilator, User
from flask_login import login_user

def verify_features():
    print("--- Starting Deep Feature Verification ---")
    
    with app.app_context():
        # Setup Test Client
        client = app.test_client()
        
        # 1. Mock Login (bypass CSRF for test client or get token)
        admin = User.query.filter_by(username='AdminPro').first()
        if not admin:
            # Seed if missing
            admin = User(username='AdminPro', role='admin', email='admin@test.com')
            admin.set_password('admin@123')
            db.session.add(admin)
            db.session.commit()
            
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        # 2. Test Export Route (GET)
        print("[TEST] GET /api/export/invigilators ...")
        res = client.get('/api/export/invigilators')
        if res.status_code == 200 and 'spreadsheetml' in res.mimetype:
            print("  [OK] EXPORT SUCCESS: Spreadsheet stream received.")
        else:
            print(f"  [ERROR] EXPORT FAILED: {res.status_code} {res.mimetype}")

        # 3. Test Template Route (GET)
        print("[TEST] GET /api/template/exams ...")
        res = client.get('/api/template/exams')
        if res.status_code == 200:
            print("  [OK] TEMPLATE SUCCESS: Template download verified.")
        else:
            print(f"  [ERROR] TEMPLATE FAILED: {res.status_code}")

        # 4. Test Import Route (POST)
        print("[TEST] POST /api/import/invigilators ...")
        test_file_path = os.path.join(os.getcwd(), 'test_import_script.xlsx')
        df = pd.DataFrame([['Dr. Scripted', 'script@test.com', '123', 'CS', 'Yes', 5, 0]], 
                          columns=['Name', 'Email', 'Phone', 'Department', 'Available', 'Max Duties', 'Group ID'])
        df.to_excel(test_file_path, index=False)
            
        with open(test_file_path, 'rb') as f:
            data = {'file': (f, 'test_import_script.xlsx')}
            # Note: CSRF is disabled for test_client by default
            res = client.post('/api/import/invigilators', data=data, content_type='multipart/form-data')
            
        if res.status_code == 200:
            print("  [OK] IMPORT SUCCESS: Server accepted and processed Excel file.")
            # Verify in DB
            inv = Invigilator.query.filter_by(name='Dr. Scripted').first()
            if inv:
                print(f"  [OK] DB SYNC SUCCESS: '{inv.name}' found in database.")
                db.session.delete(inv)
                db.session.commit()
            else:
                print("  [ERROR] DB SYNC FAILED: Record count did not increase.")
        else:
            print(f"  [ERROR] IMPORT FAILED: {res.status_code} - {res.get_json() if res.is_json else res.data}")

    print("--- Verification Completed ---")

if __name__ == "__main__":
    verify_features()
