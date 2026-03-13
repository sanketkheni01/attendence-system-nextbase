import sqlite3
import pandas as pd
import os
import requests
import io
from datetime import datetime

DB_PATH = 'attendance.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            team TEXT DEFAULT 'Unassigned'
        )
    ''')
    
    # Create Attendance Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            date DATE NOT NULL,
            in_time TEXT,
            out_time TEXT,
            type TEXT NOT NULL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (employee_name) REFERENCES employees(name)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_employee(name, team="Unassigned"):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO employees (name, team) VALUES (?, ?)', (name, team))
        conn.commit()
        conn.close()
        return True, "Employee added successfully!"
    except sqlite3.IntegrityError:
        return False, "Employee already exists!"
    except Exception as e:
        return False, str(e)

def get_all_employees():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT name FROM employees ORDER BY name ASC')
    employees = [row[0] for row in c.fetchall()]
    conn.close()
    return employees

def get_teams():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT DISTINCT team FROM employees ORDER BY team ASC')
    teams = [row[0] for row in c.fetchall()]
    conn.close()
    return teams

def get_employees_by_team(team):
    conn = get_connection()
    c = conn.cursor()
    if team == "All":
        c.execute('SELECT name FROM employees ORDER BY name ASC')
    else:
        c.execute('SELECT name FROM employees WHERE team = ? ORDER BY name ASC', (team,))
    employees = [row[0] for row in c.fetchall()]
    conn.close()
    return employees

def delete_employee(name):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM employees WHERE name = ?', (name,))
        conn.commit()
        conn.close()
        return True, "Employee deleted successfully!"
    except Exception as e:
        return False, str(e)

def add_attendance(employee_name, date, in_time, out_time, attendance_type, notes=""):
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Check if attendance already exists for this employee on this date
        c.execute('SELECT id, in_time, out_time, notes FROM attendance WHERE employee_name = ? AND date = ?', (employee_name, date))
        existing = c.fetchone()
        
        if existing:
            record_id, old_in, old_out, old_notes = existing
            
            # If the user leaves the time blank during update, keep the old time
            final_in = in_time if in_time else old_in
            final_out = out_time if out_time else old_out
            
            # If no new notes provided, keep old notes (or we could append, but replacing is usually better)
            final_notes = notes if notes else old_notes
            
            c.execute('''
                UPDATE attendance 
                SET in_time = ?, out_time = ?, type = ?, notes = ?
                WHERE id = ?
            ''', (final_in, final_out, attendance_type, final_notes, record_id))
            conn.commit()
            conn.close()
            return True, f"Attendance updated successfully for {employee_name} on {date}!"
            
        c.execute('''
            INSERT INTO attendance (employee_name, date, in_time, out_time, type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_name, date, in_time, out_time, attendance_type, notes))
        conn.commit()
        conn.close()
        return True, "Attendance marked successfully!"
    except Exception as e:
        return False, str(e)

def get_attendance_history(start_date=None, end_date=None, employee_name=None, team_name=None):
    conn = get_connection()
    
    query = '''
        SELECT a.*, e.team
        FROM attendance a
        LEFT JOIN employees e ON a.employee_name = e.name
        WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += ' AND a.date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND a.date <= ?'
        params.append(end_date)
    if employee_name and employee_name != "All":
        query += ' AND a.employee_name = ?'
        params.append(employee_name)
    if team_name and team_name != "All":
        query += ' AND e.team = ?'
        params.append(team_name)
        
    query += ' ORDER BY a.date DESC, a.employee_name ASC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_attendance_by_id(record_id, in_time, out_time, attendance_type, notes=""):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE attendance 
            SET in_time = ?, out_time = ?, type = ?, notes = ?
            WHERE id = ?
        ''', (in_time, out_time, attendance_type, notes, record_id))
        conn.commit()
        conn.close()
        return True, "Record updated successfully!"
    except Exception as e:
        return False, str(e)

def delete_attendance(record_id):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM attendance WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        return True, "Record deleted successfully!"
    except Exception as e:
        return False, str(e)

def get_monthly_report(month, year, team_name="All"):
    conn = get_connection()
    
    month_str = f"{int(month):02d}"
    year_str = str(year)
    date_pattern = f"{year_str}-{month_str}-%"
    
    query = '''
        SELECT a.employee_name, e.team, a.type, a.in_time, a.out_time
        FROM attendance a
        LEFT JOIN employees e ON a.employee_name = e.name
        WHERE a.date LIKE ? 
    '''
    params = [date_pattern]
    
    if team_name != "All":
        query += " AND e.team = ?"
        params.append(team_name)
        
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
        
    # Calculate duration for each row in hours
    def calc_duration(row):
        in_t = row.get('in_time')
        out_t = row.get('out_time')
        if in_t and out_t and in_t != 'N/A' and out_t != 'N/A':
            try:
                fmt = "%H:%M"
                t_in = datetime.strptime(in_t, fmt)
                t_out = datetime.strptime(out_t, fmt)
                
                in_mins = t_in.hour * 60 + t_in.minute
                out_mins = t_out.hour * 60 + t_out.minute
                
                if out_mins < in_mins:
                    out_mins += 24 * 60
                    
                total_mins = out_mins - in_mins
                
                # Lunch break deduction (13:00 to 14:00)
                lunch_start = 13 * 60
                lunch_end = 14 * 60
                
                overlap_start = max(in_mins, lunch_start)
                overlap_end = min(out_mins, lunch_end)
                
                if overlap_start < overlap_end:
                    total_mins -= (overlap_end - overlap_start)

                return total_mins / 60.0
            except:
                return 0.0
        return 0.0
        
    df['hours_worked'] = df.apply(calc_duration, axis=1)
    
    # Calculate counts per type
    counts_df = df.groupby(['employee_name', 'team', 'type']).size().reset_index(name='count')
    pivot_df = counts_df.pivot(index=['employee_name', 'team'], columns='type', values='count').fillna(0)
    
    # Ensure all required columns exist
    required_columns = ['Present', 'Half Day Leave', 'Work From Home', 'Leave']
    for col in required_columns:
        if col not in pivot_df.columns:
            pivot_df[col] = 0
            
    # Reset index to make employee_name a regular column
    pivot_df = pivot_df.reset_index()
    
    # Calculate Total Days tracked
    pivot_df['Total Days Tracked'] = pivot_df[required_columns].sum(axis=1)
    
    # Calculate Total Hours Worked
    hours_df = df.groupby(['employee_name', 'team'])['hours_worked'].sum().reset_index()
    
    def format_hours(h):
        hours = int(h)
        mins = int(round((h - hours) * 60))
        if mins == 60:
            hours += 1
            mins = 0
        return f"{hours:02d}:{mins:02d}"
        
    hours_df['Total Worked Hours'] = hours_df['hours_worked'].apply(format_hours)
    
    # Merge hours into pivot_df
    final_df = pd.merge(pivot_df, hours_df[['employee_name', 'team', 'Total Worked Hours']], on=['employee_name', 'team'], how='left')
    
    return final_df

def sync_google_sheets(sheet_url):
    """
    Fetches data from a public Google Sheet (via CSV export) and updates attendance.
    """
    csv_url = sheet_url.replace('/edit?gid=', '/export?format=csv&gid=')
    if '/export?' not in csv_url:
        csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # We'll use a local helper to parse the CSV lines to handle the specific format
        lines = response.text.splitlines()
        if not lines:
            return False, "The sheet is empty."

        current_date_str = None
        success_count = 0
        
        # Simple parsing logic based on the user's example
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if not any(parts): continue
            
            # Look for a date in the first column (e.g., "11 Mar 2026")
            if "202" in parts[0] and any(m in parts[0] for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                try:
                    # Clean the date string
                    raw_date = parts[0].replace("\t", " ").strip()
                    dt = datetime.strptime(raw_date, "%d %b %Y")
                    current_date_str = dt.strftime("%Y-%m-%d")
                    continue
                except:
                    pass
            
            if not current_date_str: continue

            # Sub-rows start with empty columns or team name
            # Format: Team, Empty, Name, In, Out
            # OR Empty, Empty, Name, In, Out
            
            name, in_t, out_t = None, None, None
            
            # Logic to find name and times in the row
            # Usually: parts[2] is name, parts[3] is in, parts[4] is out
            if len(parts) >= 3 and parts[2]:
                name = parts[2]
                in_t = parts[3] if len(parts) > 3 else ""
                out_t = parts[4] if len(parts) > 4 else ""
            elif len(parts) >= 2 and parts[1]: # Sometimes name is in parts[1]
                name = parts[1]
                in_t = parts[2] if len(parts) > 2 else ""
                out_t = parts[3] if len(parts) > 3 else ""
            
            if name:
                # Use a simple parser for times (like in app.py)
                def clean_time(t, is_out):
                    if not t: return ""
                    t = t.replace(" ", "").lower()
                    try:
                        if ":" in t:
                            h, m = map(int, t.split(":"))
                        else:
                            h, m = int(t), 0
                        
                        if is_out and 1 <= h <= 11: h += 12
                        elif not is_out and 1 <= h <= 6: h += 12
                        return f"{h:02d}:{m:02d}"
                    except: return t

                in_time = clean_time(in_t, False)
                out_time = clean_time(out_t, True)
                
                # Determine attendance type
                att_type = "Present" if in_time or out_time else "Work From Home"
                
                # Update DB
                ok, _ = add_attendance(name, current_date_str, in_time, out_time, att_type, "Synced from Google Sheets")
                if ok: success_count += 1
        
        return True, f"Sync complete! Processed {success_count} records for {current_date_str}."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403, 404]:
            return False, "Unable to access the sheet. Make sure the sheet URL is correct and the sharing settings are set to 'Anyone with the link can view'."
        return False, f"Sync failed with server error ({e.response.status_code})."
    except Exception as e:
        return False, f"Sync failed: {str(e)}"
