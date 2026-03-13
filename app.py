import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, time
import database as db

# Initialize Database
db.init_db()

st.set_page_config(page_title="Attendance Management", page_icon="📅", layout="wide")

# Advanced Custom CSS for a Premium, Modern UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Headers with Gradient Text */
    h1 {
        background: -webkit-linear-gradient(45deg, #4F46E5, #9333EA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    h2, h3 {
        color: #1E293B;
        font-weight: 600;
    }

    /* Premium Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2), 0 2px 4px -1px rgba(79, 70, 229, 0.1);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3), 0 4px 6px -2px rgba(79, 70, 229, 0.15);
        background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(226, 232, 240, 0.8);
    }
    
    /* Custom Alerts/Cards */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stAlert"]:has(p) {
        border-left: 4px solid #4F46E5;
    }

    /* Input Fields */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        transition: border-color 0.2s;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 1px #4F46E5 !important;
    }
    
    /* Selectboxes and Form Elements */
    .stSelectbox>div>div>div {
        border-radius: 8px;
    }
    
    /* Metrics / Quick Stats Cards Styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid #F1F5F9;
        text-align: center;
        transition: transform 0.2s;
        margin-bottom: 1rem;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-title {
        color: #64748B;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 2.5rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    
    /* Style Dataframes container */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Leave reason options
LEAVE_REASONS = [
    "",
    "Sick Leave",
    "Medical Appointment",
    "Family Emergency",
    "Personal Work",
    "Festival / Holiday",
    "Travel",
    "Maternity / Paternity",
    "Other",
]

# Pre-built time options every 15 min from 07:00 to 22:00
TIME_OPTIONS = [""] + [
    f"{h:02d}:{m:02d}"
    for h in range(7, 23)
    for m in (0, 15, 30, 45)
]

# Sidebar Navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("---")
page = st.sidebar.radio("Go to", ["Dashboard", "Add Attendance", "View History", "Monthly Reports", "Manage Employees"])

# Google Sheets Sync Section
st.sidebar.markdown("---")
st.sidebar.subheader("Google Sheets Sync")
sheet_url = st.sidebar.text_input("Sheet URL", value="https://docs.google.com/spreadsheets/d/1LipdBbx5WLkaQznhneHvkUZpGhrDETNrYlD0bWYPa-4/edit?gid=0#gid=0")
if st.sidebar.button("Sync Now"):
    with st.spinner("Syncing..."):
        success, msg = db.sync_google_sheets(sheet_url)
        if success:
            st.sidebar.success(msg)
            st.rerun()
        else:
            st.sidebar.error(msg)
st.sidebar.info("💡 Ensure the sheet has 'Anyone with the link can view' access.")

if page == "Dashboard":
    st.title("Welcome to Attendance Management System 📅")
    st.markdown("Use the sidebar to navigate through the application.")
    
    st.markdown("---")
    st.subheader("Quick Stats")
    employees = db.get_all_employees()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Employees Registered</div>
        <div class="metric-value">{len(employees)}</div>
    </div>
    """, unsafe_allow_html=True)
    
elif page == "Manage Employees":
    st.title("Manage Employees")
    
    with st.form("add_employee_form"):
        new_emp_name = st.text_input("Employee Name", placeholder="e.g. John Doe")
        exist_teams = db.get_teams()
        # Allows user to type a new team or select an existing one
        new_emp_team = st.text_input("Team Name", placeholder="e.g. AI, Full Stack (or leave blank for Unassigned)")
        submit_btn = st.form_submit_button("Add Employee")
        
        if submit_btn:
            if new_emp_name.strip():
                final_team = new_emp_team.strip() if new_emp_team.strip() else "Unassigned"
                success, msg = db.add_employee(new_emp_name.strip(), final_team)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Please enter a valid name.")
                
    st.markdown("---")
    st.subheader("Current Employees")
    teams = db.get_teams()
    has_emps = False
    
    for t in teams:
        emps_in_team = db.get_employees_by_team(t)
        if emps_in_team:
            has_emps = True
            st.markdown(f"**Team: {t}**")
            for emp in emps_in_team:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"- {emp}")
                with col2:
                    if st.button("Delete", key=f"del_{emp}"):
                        success, msg = db.delete_employee(emp)
                        if success:
                            st.success(f"Deleted {emp}")
                            st.rerun()
                        else:
                            st.error(msg)
            st.markdown("---")
            
    if not has_emps:
        st.info("No employees added yet.")

elif page == "Add Attendance":
    st.title("Add Daily Attendance")

    top_col1, top_col2 = st.columns([2, 2])
    with top_col1:
        att_date = st.date_input("Date", date.today())
    with top_col2:
        teams = ["All"] + db.get_teams()
        selected_team = st.selectbox("Filter by Team", teams)

    employees = db.get_employees_by_team(selected_team)

    if not employees:
        st.warning("No employees found for the selected team.")
    else:
        # Pre-fill with any existing records for this date
        existing_df = db.get_attendance_history(
            start_date=str(att_date),
            end_date=str(att_date),
            team_name=selected_team
        )
        existing = {}
        if not existing_df.empty:
            for _, r in existing_df.iterrows():
                existing[r['employee_name']] = r

        ATT_TYPES = ["Full Day", "Half Day", "Work From Home", "Custom Leave"]

        # Map DB stored values → display labels
        DB_TO_UI = {
            "Present": "Full Day",
            "Half Day Leave": "Half Day",
            "Work From Home": "Work From Home",
            "Leave": "Custom Leave",
        }
        # Map display labels → DB stored values
        UI_TO_DB = {v: k for k, v in DB_TO_UI.items()}

        rows = []
        # Get team for each employee to group/sort
        conn = db.get_connection()
        c = conn.cursor()
        if selected_team == "All":
            c.execute('SELECT name, team FROM employees ORDER BY team ASC, name ASC')
        else:
            c.execute('SELECT name, team FROM employees WHERE team = ? ORDER BY name ASC', (selected_team,))
        ordered_emps = c.fetchall()
        conn.close()

        for emp_name, emp_team in ordered_emps:
            if emp_name in existing:
                r = existing[emp_name]
                ui_type = DB_TO_UI.get(r['type'], "Full Day")
                # If Custom Leave, show reason in Leave Reason column; Notes keeps the rest
                raw_notes = r['notes'] if r['notes'] else ""
                # Restore dropdown selection; if stored value not in list, default to "Other"
                stored_reason = raw_notes if ui_type == "Custom Leave" else ""
                leave_reason = stored_reason if stored_reason in LEAVE_REASONS else ("Other" if stored_reason else "")
                plain_notes  = "" if ui_type == "Custom Leave" else raw_notes
                rows.append({
                    "Team": emp_team,
                    "Employee": emp_name,
                    "Leave Type": ui_type,
                    "Leave Reason": leave_reason,
                    "In Time (HH:MM)": r['in_time'] if r['in_time'] else "",
                    "Out Time (HH:MM)": r['out_time'] if r['out_time'] else "",
                    "Notes": plain_notes,
                })
            else:
                rows.append({
                    "Team": emp_team,
                    "Employee": emp_name,
                    "Leave Type": "Full Day",
                    "Leave Reason": "",
                    "In Time (HH:MM)": "",
                    "Out Time (HH:MM)": "",
                    "Notes": "",
                })

        init_df = pd.DataFrame(rows)

        already = len(existing)
        st.caption(
            f"📋 **{att_date.strftime('%A, %B %d %Y')}** — {len(employees)} employee(s) shown. "
            + (f"✅ {already} existing record(s) pre-filled." if already else "No records yet for this date.")
        )

        st.caption("💡 Select **Custom Leave** in Leave Type and fill in the **Leave Reason** column with the reason.")

        edited_df = st.data_editor(
            init_df,
            column_config={
                "Team": st.column_config.TextColumn("Team", disabled=True, width="small"),
                "Employee": st.column_config.TextColumn("Employee", disabled=True, width="medium"),
                "Leave Type": st.column_config.SelectboxColumn(
                    "Leave Type",
                    options=ATT_TYPES,
                    required=True,
                    width="medium",
                ),
                "Leave Reason": st.column_config.SelectboxColumn(
                    "Leave Reason",
                    options=LEAVE_REASONS,
                    help="Required when Leave Type is 'Custom Leave'",
                    width="medium",
                ),
                "In Time (HH:MM)": st.column_config.TextColumn(
                    "In Time",
                    help="e.g. 9:30 or 18:00",
                    width="small",
                ),
                "Out Time (HH:MM)": st.column_config.TextColumn(
                    "Out Time",
                    help="e.g. 6:30 or 18:30",
                    width="small",
                ),
                "Notes": st.column_config.TextColumn("Notes", width="large"),
            },
            column_order=["Team", "Employee", "Leave Type", "Leave Reason", "In Time (HH:MM)", "Out Time (HH:MM)", "Notes"],

            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="bulk_attendance_editor",
        )

        if st.button("✅ Submit All Attendance", type="primary"):
            def parse_and_adjust(t_str, is_out):
                if not t_str or not str(t_str).strip():
                    return ""
                t_str = str(t_str).strip().lower()
                
                # Handle formats like "9:30 AM", "6:30 PM"
                if "am" in t_str or "pm" in t_str:
                    try:
                        clean_t = t_str.replace("am", "").replace("pm", "").strip()
                        if ":" in clean_t:
                            h, m = map(int, clean_t.split(":"))
                        else:
                            h, m = int(clean_t), 0
                        
                        if "pm" in t_str and h < 12:
                            h += 12
                        elif "am" in t_str and h == 12:
                            h = 0
                        return f"{h:02d}:{m:02d}"
                    except:
                        pass

                try:
                    if ":" in t_str:
                        h, m = map(int, t_str.split(":"))
                    else:
                        # Handle "930" -> 09:30 or "9" -> 09:00
                        if len(t_str) >= 3:
                            h = int(t_str[:-2])
                            m = int(t_str[-2:])
                        else:
                            h = int(t_str)
                            m = 0
                    
                    # Intelligent AM/PM adjustment:
                    # If it's an out-time and h is between 1 and 6, assume PM (13:00-18:00)
                    if is_out and 1 <= h <= 11:
                        h += 12
                    # If it's an in-time and h is 1-6, assume PM (13:00-18:00) for late shifts
                    elif not is_out and 1 <= h <= 6:
                        h += 12
                        
                    return f"{h:02d}:{m:02d}"
                except Exception:
                    return t_str

            success_count, error_msgs = 0, []

            for _, row in edited_df.iterrows():
                emp        = row["Employee"]
                ui_type    = row["Leave Type"]
                att_type   = UI_TO_DB.get(ui_type, "Present")
                leave_reason = str(row["Leave Reason"]).strip() if row["Leave Reason"] else ""
                in_t_str   = parse_and_adjust(row["In Time (HH:MM)"], False)
                out_t_str  = parse_and_adjust(row["Out Time (HH:MM)"], True)
                plain_notes = str(row["Notes"]).strip() if row["Notes"] else ""

                # Validate: Custom Leave needs a reason
                if ui_type == "Custom Leave" and not leave_reason:
                    error_msgs.append(f"**{emp}**: Custom Leave selected but no reason provided.")
                    continue

                # Build combined notes: leave reason first, then plain notes, then auto-flags
                notes_parts = []
                if leave_reason:
                    notes_parts.append(leave_reason)
                if plain_notes:
                    notes_parts.append(plain_notes)
                notes = " | ".join(notes_parts)

                # Auto late / early-leave detection
                auto_notes = []
                expected_out_mins = 18 * 60 + 30  # default 6:30 PM
                if in_t_str:
                    try:
                        h, m = map(int, in_t_str.split(":"))
                        in_mins = h * 60 + m
                        if in_mins > 9 * 60 + 30:
                            auto_notes.append("Arrived Late")
                        expected_out_mins = in_mins + 9 * 60 + 30
                    except Exception:
                        pass
                if out_t_str:
                    try:
                        h, m = map(int, out_t_str.split(":"))
                        if h * 60 + m < expected_out_mins:
                            auto_notes.append("Left Early")
                    except Exception:
                        pass
                if auto_notes:
                    auto_str = ", ".join(auto_notes)
                    notes = (notes + " | " + auto_str) if notes else auto_str

                ok, msg = db.add_attendance(emp, str(att_date), in_t_str, out_t_str, att_type, notes)
                if ok:
                    success_count += 1
                else:
                    error_msgs.append(f"**{emp}**: {msg}")

            if success_count:
                st.success(f"✅ Saved {success_count} record(s) for {att_date}!")
            for em in error_msgs:
                st.error(em)

elif page == "View History":
    st.title("Attendance History")
    
    # Force a refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    teams = ["All"] + db.get_teams()
    
    with st.expander("Filter Records", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_d = st.date_input("Start Date", value=None)
        with col2:
            end_d = st.date_input("End Date", value=None)
        with col3:
            search_team = st.selectbox("Search by Team", teams)
        with col4:
            emps = ["All"] + db.get_employees_by_team(search_team)
            search_emp = st.selectbox("Search by Employee", emps)
        
    df = db.get_attendance_history(
        start_date=str(start_d) if start_d else None,
        end_date=str(end_d) if end_d else None,
        employee_name=search_emp,
        team_name=search_team
    )
    
    if not df.empty:
        # Create a custom display dataframe to combine in-time and out-time
        display_df = df.copy()
        
        def to_12h(time_str):
            if not time_str or time_str == 'N/A' or pd.isna(time_str):
                return 'N/A'
            try:
                t = datetime.strptime(time_str, "%H:%M")
                return t.strftime("%I:%M %p")
            except:
                return str(time_str)
                
        def calc_total_hours(in_str, out_str):
            if not in_str or not out_str or in_str == 'N/A' or out_str == 'N/A' or pd.isna(in_str) or pd.isna(out_str):
                return 'N/A'
            try:
                fmt = "%H:%M"
                t_in = datetime.strptime(in_str, fmt)
                t_out = datetime.strptime(out_str, fmt)
                
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

                h = int(total_mins // 60)
                m = int(total_mins % 60)
                return f"{h:02d}:{m:02d}"
            except:
                return 'N/A'

        display_df['Total Hours'] = display_df.apply(lambda row: calc_total_hours(row['in_time'], row['out_time']), axis=1)
        
        in_t = display_df['in_time'].replace('', 'N/A').apply(to_12h)
        out_t = display_df['out_time'].replace('', 'N/A').apply(to_12h)
        display_df['Timings (In - Out)'] = in_t + " to " + out_t
        
        # Select and rename columns for a cleaner UI
        if 'notes' in display_df.columns:
            if 'team' in display_df.columns:
                display_df = display_df[['employee_name', 'team', 'date', 'Timings (In - Out)', 'Total Hours', 'type', 'notes']]
                display_df.columns = ['Employee Name', 'Team', 'Date', 'Timings (In - Out)', 'Total Hours', 'Attendance Type', 'Notes']
            else:
                display_df = display_df[['employee_name', 'date', 'Timings (In - Out)', 'Total Hours', 'type', 'notes']]
                display_df.columns = ['Employee Name', 'Date', 'Timings (In - Out)', 'Total Hours', 'Attendance Type', 'Notes']
        else:
            if 'team' in display_df.columns:
                display_df = display_df[['employee_name', 'team', 'date', 'Timings (In - Out)', 'Total Hours', 'type']]
                display_df.columns = ['Employee Name', 'Team', 'Date', 'Timings (In - Out)', 'Total Hours', 'Attendance Type']
            else:
                display_df = display_df[['employee_name', 'date', 'Timings (In - Out)', 'Total Hours', 'type']]
                display_df.columns = ['Employee Name', 'Date', 'Timings (In - Out)', 'Total Hours', 'Attendance Type']
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("Manage Records")
        
        # Create a user-friendly dropdown for edit/deletion
        manage_options = df['id'].astype(str) + " - " + df['employee_name'] + " (" + df['date'].astype(str) + ")"
        selected_record = st.selectbox("Select Record to Edit/Delete", [""] + manage_options.tolist())
        
        if selected_record:
            record_id = int(selected_record.split(" - ")[0])
            record_row = df[df['id'] == record_id].iloc[0]
            
            with st.expander("✏️ Edit Record", expanded=False):
                with st.form(key=f"edit_form_{record_id}"):
                    att_types = ["Present", "Half Day Leave", "Work From Home", "Leave"]
                    idx = att_types.index(record_row['type']) if record_row['type'] in att_types else 0
                    new_type = st.selectbox("Attendance Type", att_types, index=idx)
                    
                    try:
                        curr_in = datetime.strptime(record_row['in_time'], "%H:%M").time() if record_row['in_time'] else None
                    except:
                        curr_in = None
                    try:
                        curr_out = datetime.strptime(record_row['out_time'], "%H:%M").time() if record_row['out_time'] else None
                    except:
                        curr_out = None
                        
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        new_in = st.time_input("Office In Time", value=curr_in)
                    with e_col2:
                        new_out = st.time_input("Office Out Time", value=curr_out)
                        
                    new_notes = st.text_input("Notes", value=record_row.get('notes', ''))
                    
                    if st.form_submit_button("Save Changes"):
                        def auto_adjust(t, is_out):
                            if not t: return t
                            h, m = t.hour, t.minute
                            if is_out and 1 <= h <= 11:
                                return time(h + 12, m)
                            if not is_out and 1 <= h <= 6:
                                return time(h + 12, m)
                            return t
                            
                        new_in = auto_adjust(new_in, False)
                        new_out = auto_adjust(new_out, True)

                        in_t_str = new_in.strftime("%H:%M") if new_in else ""
                        out_t_str = new_out.strftime("%H:%M") if new_out else ""
                        
                        auto_notes = []
                        expected_out = time(18, 30) # Default to 6:30 PM
                        if new_in:
                            if new_in.hour > 9 or (new_in.hour == 9 and new_in.minute > 30):
                                auto_notes.append("Arrived Late")
                                
                            in_dt = datetime.combine(date.today(), new_in)
                            expected_out = (in_dt + timedelta(hours=9, minutes=30)).time()
                            
                        if new_out:
                            if new_out < expected_out:
                                auto_notes.append("Left Early")
                                
                        final_notes = new_notes.strip()
                        if auto_notes:
                            auto_str = ", ".join(auto_notes)
                            # Only add them if not actively typed in manually by user previously
                            if "Arrived Late" not in final_notes and "Arrived Late" in auto_str:
                                final_notes = final_notes + (" | " if final_notes else "") + "Arrived Late"
                            if "Left Early" not in final_notes and "Left Early" in auto_str:
                                final_notes = final_notes + (" | " if final_notes else "") + "Left Early"
                                
                        success, msg = db.update_attendance_by_id(record_id, in_t_str, out_t_str, new_type, final_notes)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                            
            if st.button("🗑️ Delete Record"):
                success, msg = db.delete_attendance(record_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("No records found for the selected criteria.")

elif page == "Monthly Reports":
    st.title("Generate Monthly Reports")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)
    with col2:
        current_year = date.today().year
        year = st.selectbox("Year", range(current_year - 2, current_year + 3), index=2)
    with col3:
        teams = ["All"] + db.get_teams()
        report_team = st.selectbox("Filter by Team", teams)
        
    st.markdown("---")
    df_report = db.get_monthly_report(month, year, report_team)
    
    if not df_report.empty:
        st.subheader(f"Report for {month:02d}/{year}")
        
        # Format columns
        if 'team' in df_report.columns:
            df_report = df_report.rename(columns={'employee_name': 'Employee Name', 'team': 'Team'})
        else:
            df_report = df_report.rename(columns={'employee_name': 'Employee Name'})
            
        # --- Sorting Logic ---
        sort_options = list(df_report.columns)
        
        scol1, scol2 = st.columns(2)
        with scol1:
            sort_by = st.selectbox("Sort Data By", sort_options, index=0)
        with scol2:
            sort_order = st.radio("Sorting Order", ["Ascending", "Descending"], horizontal=True)
            
        is_ascending = (sort_order == "Ascending")
        
        # Helper to allow sorting the 'Total Worked Hours' properly (it's a string HH:MM)
        if sort_by == 'Total Worked Hours':
            # Convert "HH:MM" temporarily to an integer representing total minutes for accurate sorting
            def time_to_mins(t_str):
                if not isinstance(t_str, str) or ":" not in t_str: return 0
                try:
                    h, m = map(int, t_str.split(":"))
                    return h * 60 + m
                except: return 0
            
            temp_col = df_report[sort_by].apply(time_to_mins)
            df_report = df_report.iloc[temp_col.argsort()]
            if not is_ascending:
                df_report = df_report.iloc[::-1]
        else:
            df_report = df_report.sort_values(by=sort_by, ascending=is_ascending)
        # ---------------------
            
        st.dataframe(df_report, use_container_width=True, hide_index=True)
        
        csv = df_report.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"attendance_report_{month}_{year}.csv",
            mime="text/csv",
        )
    else:
        st.warning("No attendance data found for this month.")
