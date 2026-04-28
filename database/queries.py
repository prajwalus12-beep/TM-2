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
    if not supabase: return pd.DataFrame(columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link'])
    
    res = supabase.table('project').select('project_code, project_name, status, priority, lead_engineer, trello_link').order('project_code', desc=True).execute()
    data = res.data or []
    
    # Decrypt project names
    decrypted_res = [[r['project_code'], decrypt_data(r['project_name']), r['status'], r.get('priority'), r.get('lead_engineer'), r.get('trello_link')] for r in data]
    return pd.DataFrame(decrypted_res, columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link'])

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
        "Phase": phase_code,
        "project_status": project_status
    }
    
    try:
        supabase.table('timesheet').insert(data).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_timesheets(start_date=None, end_date=None, emp_id=None, project_code=None):
    """Fetch timesheet entries with optional filters using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    query = supabase.table('timesheet').select('id, emp_id, emp_name, project_code, project_name, date, hours, Phase, project_status')
    
    if start_date: query = query.gte('date', start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date)
    if end_date: query = query.lte('date', end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date)
    if emp_id: query = query.eq('emp_id', emp_id)
    if project_code: query = query.eq('project_code', project_code)
    
    res = query.order('date', desc=True).execute()
    data = res.data or []
    
    if not data: return pd.DataFrame()
    
    # Decrypt project names
    cols = ['id', 'emp_id', 'emp_name', 'project_code', 'project_name', 'date', 'hours', 'Phase', 'project_status']
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
            r['Phase'],
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
        "Phase": phase_code,
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
    """Replace any NaN/NaT values with None so they serialize as JSON null."""
    return {k: (None if pd.isna(v) else v) if not isinstance(v, str) else v
            for k, v in d.items()}

def import_projects(df):
    """Import projects using Supabase SDK. Updates existing projects by Job No."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        # Fetch existing project codes to determine new vs updated
        existing_res = supabase.table('project').select('project_code').execute()
        existing_codes = {r['project_code'] for r in (existing_res.data or [])}
        
        data = []
        updated_count = 0
        new_count = 0
        for _, row in df.iterrows():
            code = str(row.get('Job No') or row.get('Project Code') or '')
            record = {
                "project_code": code,
                "project_name": encrypt_data(str(row.get('Project', ''))),
                "status": row.get('Status', 'In progress'),
                "priority": row.get('Job Priority'),
                "lead_engineer": row.get('Lead engineer'),
                "trello_link": row.get('Trello')
            }
            data.append(_sanitize_dict(record))
            if code in existing_codes:
                updated_count += 1
            else:
                new_count += 1
        
        if data:
            supabase.table('project').upsert(data, on_conflict='project_code').execute()
        return True, f"Successfully imported {len(df)} projects ({new_count} new, {updated_count} updated)."
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

def get_project_reports():
    """Fetch all data from project_reports table."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    res = supabase.table('project_reports').select('*').order('project_code', desc=True).execute()
    data = res.data or []
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def import_project_updates(df):
    """Import project updates into project_reports using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        # Fetch existing records for comparison (only the fields we need to diff)
        existing_res = supabase.table('project_reports').select(
            'project_code, project_name, lead_engineer, priority, status, trello_link'
        ).execute()
        existing_map = {r['project_code']: r for r in (existing_res.data or [])}
        
        inserts = []
        updates = []
        resets = []   # records that match import — clear all *_updated flags
        for _, row in df.iterrows():
            code = str(row.get('Job No') or row.get('Project Code') or '')
            if not code or code.lower() == 'nan':
                continue
            
            # Build record with default flags set to False
            record = {
                "project_code": code,
                "project_name": str(row.get('Project', '')),
                "lead_engineer": str(row.get('Lead engineer', '')),
                "priority": str(row.get('Job Priority', '')),
                "status": str(row.get('Status', 'In progress')),
                "trello_link": str(row.get('Trello', '')) if pd.notna(row.get('Trello')) else None,
                "project_code_updated": False,
                "project_name_updated": False,
                "lead_engineer_updated": False,
                "priority_updated": False,
                "status_updated": False,
                "trello_link_updated": False,
                "start_date_updated": False,
                "end_date_updated": False,
                "phase_updated": False,
                "prototype_link_updated": False
            }
            clean_record = _sanitize_dict(record)
            
            if code in existing_map:
                # Compare with existing record to see if any field changed
                existing = existing_map[code]
                changes = []
                # Compare each relevant field
                if clean_record.get('project_name') != existing.get('project_name'):
                    changes.append('project_name')
                if clean_record.get('lead_engineer') != existing.get('lead_engineer'):
                    changes.append('lead_engineer')
                if clean_record.get('priority') != existing.get('priority'):
                    changes.append('priority')
                if clean_record.get('status') != existing.get('status'):
                    changes.append('status')
                if clean_record.get('trello_link') != existing.get('trello_link'):
                    changes.append('trello_link')
                if changes:
                    # Mark updated flags for changed columns only
                    for col in changes:
                        clean_record[f"{col}_updated"] = True
                    updates.append(clean_record)
                else:
                    # No field changes → import confirms data matches; clear any existing highlight flags
                    resets.append(code)
            else:
                # New record – set a default phase and mark as insert
                clean_record["phase"] = "Analysis"
                inserts.append(clean_record)
        if inserts:
            supabase.table('project_reports').insert(inserts).execute()
        if updates:
            for u in updates:
                supabase.table('project_reports').update(u).eq('project_code', u['project_code']).execute()
        if resets:
            # Clear all *_updated flags for records that exactly match the imported sheet
            # Use a single batched call instead of per-record loop to avoid socket exhaustion
            reset_payload = {
                "project_code_updated": False,
                "project_name_updated": False,
                "lead_engineer_updated": False,
                "priority_updated": False,
                "status_updated": False,
                "trello_link_updated": False,
                "start_date_updated": False,
                "end_date_updated": False,
                "phase_updated": False,
                "prototype_link_updated": False
            }
            supabase.table('project_reports').update(reset_payload).in_('project_code', resets).execute()
        return True, f"Successfully imported {len(inserts)} new, updated {len(updates)} changed, and cleared highlights for {len(resets)} matched project(s)."
    except Exception as e:
        return False, str(e)

def save_project_updates(edited_rows_dict, current_df):
    """Process st.data_editor changes and save to project_reports, updating flags."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        updated_records = []
        for row_idx, changes in edited_rows_dict.items():
            # Get original row using index
            orig_row = current_df.iloc[int(row_idx)]
            proj_code = orig_row['project_code']
            
            update_payload = {"project_code": proj_code}
            
            for col, new_val in changes.items():
                update_payload[col] = new_val
                # Set the updated flag to true if a corresponding column exists
                flag_col = f"{col}_updated"
                if flag_col in current_df.columns:
                    update_payload[flag_col] = True
            
            if len(update_payload) > 1: # More than just project_code
                updated_records.append(update_payload)
                
        for record in updated_records:
            supabase.table('project_reports').update(record).eq('project_code', record['project_code']).execute()
            
        return True, f"Successfully updated {len(updated_records)} projects."
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
