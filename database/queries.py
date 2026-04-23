import pandas as pd
from database.connection import get_supabase_client
from services.auth_service import hash_password, encrypt_data, decrypt_data

print(f"DEBUG: Loading queries.py from {__file__}")

def get_all_employees(exclude_admin=False):
    """Fetch all employees using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['employee_id', 'employee_name', 'slack_id'])
    
    query = supabase.table('employee').select('employee_id, employee_name, slack_id')
    if exclude_admin:
        query = query.neq('employee_id', 'admin')
    
    res = query.order('employee_name').execute()
    data = res.data or []
    return pd.DataFrame(data, columns=['employee_id', 'employee_name', 'slack_id'])

def get_all_projects():
    """Fetch all projects using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link', 'start_date', 'end_date', 'phase', 'prototype_link'])
    
    res = supabase.table('project').select('project_code, project_name, status, priority, lead_engineer, trello_link, start_date, end_date, phase, prototype_link').order('project_code', desc=True).execute()
    data = res.data or []
    
    # Decrypt project names
    decrypted_res = [[r['project_code'], decrypt_data(r['project_name']), r['status'], r.get('priority'), r.get('lead_engineer'), r.get('trello_link'), r.get('start_date'), r.get('end_date'), r.get('phase'), r.get('prototype_link')] for r in data]
    return pd.DataFrame(decrypted_res, columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link', 'start_date', 'end_date', 'phase', 'prototype_link'])

def get_user_by_username(username):
    """Fetch user details using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return None
    
    res = supabase.table('users').select('id, employee_id, username, password, failed_attempts, locked_until').eq('username', username).execute()
    data = res.data
    if data:
        u = data[0]
        return (u['id'], u['employee_id'], u['username'], u['password'], u['failed_attempts'], u['locked_until'])
    return None

def update_user_lockout(username, failed_attempts, locked_until=None):
    """Update failed login attempts and lockout timestamp using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('users').update({
            'failed_attempts': failed_attempts, 
            'locked_until': locked_until.isoformat() if locked_until else None
        }).eq('username', username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_all_users():
    """Fetch all users with their details using Supabase SDK join-like approach."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['id', 'username', 'employee_name', 'slack_id', 'password'])
    
    # Supabase allows embedding related tables if relationships are defined in DB
    res = supabase.table('users').select('id, username, password, employee:employee(employee_name, slack_id)').order('username').execute()
    data = res.data or []
    
    rows = []
    for r in data:
        emp = r.get('employee') or {}
        rows.append([
            r['id'],
            r['username'],
            emp.get('employee_name'),
            emp.get('slack_id'),
            r['password']
        ])
    
    return pd.DataFrame(rows, columns=['id', 'username', 'employee_name', 'slack_id', 'password'])

def get_employee_by_id(emp_id):
    """Fetch single employee details using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return None
    
    res = supabase.table('employee').select('*').eq('employee_id', emp_id).execute()
    return res.data[0] if res.data else None

def add_timesheet_entry(emp_id, emp_name, project_code, project_name, date, hours, phase, project_status="Not started"):
    """Insert a new timesheet entry using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5", "Support": "6"}
    phase_code = phase_map.get(phase, phase)
    
    data = {
        "emp_id": emp_id,
        "emp_name": emp_name,
        "project_code": project_code,
        "project_name": encrypt_data(project_name),
        "date": date.isoformat() if hasattr(date, 'isoformat') else date,
        "hours": float(hours),
        "phase": phase_code,
        "project_status": project_status
    }
    
    try:
        supabase.table('timesheet').insert(data).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def normalize_code(c):
    if c is None: return ""
    s = str(c).strip()
    if s.endswith('.0'): s = s[:-2]
    return s

def get_timesheets(start_date=None, end_date=None, emp_id=None, project_code=None):
    """Fetch timesheet entries with optional filters using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    query = supabase.table('timesheet').select('id, emp_id, emp_name, project_code, project_name, date, hours, phase, project_status')
    
    if start_date: query = query.gte('date', start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date)
    if end_date: query = query.lte('date', end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date)
    if emp_id: query = query.eq('emp_id', emp_id)
    if project_code: query = query.eq('project_code', project_code)
    
    res = query.order('date', desc=True).execute()
    data = res.data or []
    
    if not data: return pd.DataFrame()
    
    # Decrypt project names
    cols = ['id', 'emp_id', 'emp_name', 'project_code', 'project_name', 'date', 'hours', 'phase', 'project_status']
    rows = []
    for r in data:
        rows.append([
            r['id'],
            r['emp_id'],
            r['emp_name'],
            r['project_code'],
            decrypt_data(r['project_name']),
            r['date'],
            r['hours'],
            r['phase'],
            r['project_status']
        ])
    
    return pd.DataFrame(rows, columns=cols)

def delete_timesheet_entry(entry_id):
    """Delete a timesheet entry using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('timesheet').delete().eq('id', entry_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def update_timesheet_entry(entry_id, emp_id, emp_name, project_code, project_name, date, hours, phase, project_status):
    """Update a timesheet entry using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5", "Support": "6"}
    phase_code = phase_map.get(phase, phase)
    
    data = {
        "emp_id": emp_id,
        "emp_name": emp_name,
        "project_code": project_code,
        "project_name": encrypt_data(project_name),
        "date": date.isoformat() if hasattr(date, 'isoformat') else date,
        "hours": float(hours),
        "phase": phase_code,
        "project_status": project_status
    }
    
    try:
        supabase.table('timesheet').update(data).eq('id', entry_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def update_user_password(username, hashed_password):
    """Update a user's password using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def verify_user_password(username, password):
    """Verify if the provided password matches the one in DB using Supabase SDK."""
    from services.auth_service import verify_password
    user = get_user_by_username(username)
    if user:
        # user tuple order: (id, employee_id, username, password, failed_attempts, locked_until)
        return verify_password(password, user[3])
    return False

def assign_project(emp_id, project_code):
    """Assign a project to an employee using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('project_employee').upsert({'employee_id': emp_id, 'project_code': project_code}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def revoke_project(emp_id, project_code):
    """Remove a project assignment using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('project_employee').delete().match({'employee_id': emp_id, 'project_code': project_code}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_projects_by_employee(emp_id):
    """Fetch projects assigned to a specific employee using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    # Get project codes joined with project details
    res = supabase.table('project_employee').select('project!inner(project_code, project_name, status)').eq('employee_id', emp_id).execute()
    data = res.data or []
    
    rows = []
    for r in data:
        p = r.get('project') or {}
        rows.append([
            p['project_code'],
            decrypt_data(p['project_name']),
            p['status']
        ])
    
    return pd.DataFrame(rows, columns=['project_code', 'project_name', 'status'])

def get_all_assignments():
    """Fetch all project assignments using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    res = supabase.table('project_employee').select('employee_id, employee:employee(employee_name), project_code, project:project(project_name)').execute()
    data = res.data or []
    
    rows = []
    for r in data:
        emp = r.get('employee') or {}
        proj = r.get('project') or {}
        rows.append([
            r['employee_id'],
            emp.get('employee_name'),
            r['project_code'],
            decrypt_data(proj.get('project_name', ''))
        ])
    
    return pd.DataFrame(rows, columns=['employee_id', 'employee_name', 'project_code', 'project_name'])

def check_assignment(emp_id, project_code):
    """Check if an employee is assigned to a project using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False
    
    res = supabase.table('project_employee').select('1').match({'employee_id': emp_id, 'project_code': project_code}).execute()
    return len(res.data) > 0

def _sanitize_dict(d):
    """Replace any NaN/NaT values with None, and convert dates to string."""
    sanitized = {}
    for k, v in d.items():
        if isinstance(v, str):
            sanitized[k] = v
        elif pd.isna(v):
            sanitized[k] = None
        elif hasattr(v, 'isoformat'):
            sanitized[k] = v.isoformat()
        else:
            sanitized[k] = v
    return sanitized

def import_projects(df):
    """Import projects using Supabase SDK. Updates existing projects by Job No."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        # Fetch existing projects to compare data
        existing_res = supabase.table('project').select('*').execute()
        existing_data = {r['project_code']: r for r in (existing_res.data or [])}
        
        data_to_upsert = []
        codes_to_clear = []
        updated_count = 0
        new_count = 0
        
        for _, row in df.iterrows():
            # Support both human-readable and internal column names
            raw_code = row.get('Job No') or row.get('Project Code') or row.get('project_code')
            code = normalize_code(raw_code)
            
            if not code: continue
            
            # Helper to normalize any value for comparison
            def _norm_val(v):
                if v is None or pd.isna(v): return ""
                s = str(v).strip()
                if s.endswith('.0'): s = s[:-2]
                return s

            proj_name = str(row.get('Project') or row.get('project_name') or '')
            status = row.get('Status') or row.get('status') or 'In progress'
            priority = _norm_val(row.get('Job Priority') or row.get('priority'))
            lead = row.get('Lead engineer') or row.get('lead_engineer')
            trello = row.get('Trello') or row.get('trello_link')
            start = row.get('Date Start') or row.get('start_date')
            end = row.get('Date Finish') or row.get('end_date')
            proto = row.get('Prototype') or row.get('prototype_link')
            phase = row.get('Phase') or row.get('phase')

            record = {
                "project_code": code,
                "project_name": encrypt_data(proj_name),
                "status": status,
                "priority": priority,
                "lead_engineer": lead,
                "trello_link": trello,
                "start_date": start,
                "end_date": end,
                "prototype_link": proto,
                "phase": phase
            }
            
            sanitized_record = _sanitize_dict(record)
            data_to_upsert.append(sanitized_record)
            
            if code in existing_data:
                updated_count += 1
                existing = existing_data[code]
                
                match = True
                fields_to_check = [
                    ('project_name', decrypt_data(existing.get('project_name')), proj_name),
                    ('status', existing.get('status'), status),
                    ('priority', existing.get('priority'), priority),
                    ('lead_engineer', existing.get('lead_engineer'), lead),
                    ('trello_link', existing.get('trello_link'), trello),
                    ('start_date', existing.get('start_date'), start),
                    ('end_date', existing.get('end_date'), end),
                    ('prototype_link', existing.get('prototype_link'), proto),
                    ('phase', existing.get('phase'), phase)
                ]
                
                for field_key, db_val, incoming_val in fields_to_check:
                    # Deep normalization for comparison
                    def _deep_norm(v):
                        if v is None or pd.isna(v): return ""
                        if isinstance(v, (datetime.date, datetime.datetime)):
                            return v.strftime('%Y-%m-%d')
                        s = str(v).strip()
                        if s.endswith('.0'): s = s[:-2]
                        # Handle potential full timestamps in strings (e.g. 2024-04-23T00:00:00)
                        if len(s) >= 10 and s[4] == '-' and s[7] == '-':
                            s = s[:10]
                        return s
                    
                    db_str = _deep_norm(db_val)
                    in_str = _deep_norm(incoming_val)
                    
                    if db_str != in_str:
                        # Log the mismatch to console for debugging
                        print(f"DEBUG: Import Mismatch for Project {code} | Field: {field_key} | DB: '{db_str}' | File: '{in_str}'")
                        match = False
                        break
                
                if match:
                    codes_to_clear.append(code)
            else:
                new_count += 1
        
        if data_to_upsert:
            supabase.table('project').upsert(data_to_upsert, on_conflict='project_code').execute()
            
            if codes_to_clear:
                supabase.table('project_reports').delete().in_('project_code', codes_to_clear).execute()

        return True, f"Successfully imported {len(df)} projects ({new_count} new, {updated_count} updated). {len(codes_to_clear)} matching reports cleared."
    except Exception as e:
        return False, str(e)

def import_employees(df):
    """Import employees and create users using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        from services.auth_service import FIXED_PASSWORD
        emp_data = []
        user_data = []
        
        for _, row in df.iterrows():
            emp_id = str(row.get('a__Serial', ''))
            emp_name = row.get('Name', '')
            slack_id = row.get('Slack ID', '')
            if not emp_id or not emp_name: continue
            
            emp_data.append(_sanitize_dict({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "slack_id": slack_id
            }))
            
            username = " ".join(emp_name.strip().lower().split())
            enc_pwd = encrypt_data(FIXED_PASSWORD)
            user_data.append(_sanitize_dict({
                "employee_id": emp_id,
                "username": username,
                "password": enc_pwd
            }))
            
        if emp_data:
            supabase.table('employee').upsert(emp_data).execute()
        if user_data:
            supabase.table('users').upsert(user_data, on_conflict='employee_id').execute()
            
        return True, f"Successfully imported {len(df)} employees."
    except Exception as e:
        return False, str(e)

def import_assignments(df):
    """Import assignments using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        data = []
        for _, row in df.iterrows():
            emp_code = str(row.get('Projects_Resources::a_EmployeeID', ''))
            proj_code = str(row.get('Projects_Resources::a_ProjectID', ''))
            if emp_code and proj_code:
                data.append(_sanitize_dict({
                    "employee_id": emp_code,
                    "project_code": proj_code
                }))
        
        if data:
            supabase.table('project_employee').upsert(data).execute()
        return True, f"Successfully imported {len(df)} assignments."
    except Exception as e:
        return False, str(e)

def init_db():
    """Initialize system admin if missing using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        from services.auth_service import FIXED_PASSWORD
        enc_pwd = encrypt_data(FIXED_PASSWORD)
        
        # 1. UPSERT admin employee
        supabase.table('employee').upsert({
            "employee_id": "admin", 
            "employee_name": "System Administrator"
        }).execute()
        
        # 2. UPSERT admin user
        supabase.table('users').upsert({
            "employee_id": "admin", 
            "username": "admin", 
            "password": enc_pwd
        }, on_conflict='username').execute()
        
        return True, "Database references initialized (System Admin created)"
    except Exception as e:
        return False, str(e)

def save_project_update(project_code, updates):
    """Save updates to both 'project' and 'project_reports' tables."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        # 1. Update the main 'project' table
        db_updates = {}
        for k, v in updates.items():
            if k == 'project_name':
                db_updates[k] = encrypt_data(str(v))
            else:
                db_updates[k] = v
        
        if db_updates:
            # _sanitize_dict handles NaNs/Dates
            clean_updates = _sanitize_dict(db_updates)
            supabase.table('project').update(clean_updates).eq('project_code', project_code).execute()
        
        # 2. Insert into 'project_reports'
        report_data = {"project_code": project_code}
        for k, v in updates.items():
            # In project_reports, we might store project_name encrypted or not. 
            # To stay consistent with project table, we encrypt.
            val = v
            if k == 'project_name':
                val = encrypt_data(str(v))
            
            report_data[k] = val
            report_data[f"{k}_updated"] = True
            
        if len(report_data) > 1:
            clean_report = _sanitize_dict(report_data)
            supabase.table('project_reports').insert(clean_report).execute()
        
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_reported_updates():
    """Get a mapping of project codes to the set of columns that have been updated in project_reports."""
    supabase = get_supabase_client()
    if not supabase: return {}
    try:
        res = supabase.table('project_reports').select('*').execute()
        updates = {}
        for r in (res.data or []):
            c = normalize_code(r['project_code'])
            
            if c not in updates:
                updates[c] = set()
            
            # Check all columns ending in _updated
            for col, val in r.items():
                if col.endswith('_updated') and val is True:
                    original_col = col.replace('_updated', '')
                    updates[c].add(original_col)
        return updates
    except Exception:
        return {}
