import database as db
from datetime import datetime, timedelta

raw_data = """11 Mar 2026				
AI teem		Himansu	9:43	7:02
		yash	9:47	7:34
		Nirav	9:29	7:22
		Dhruvit	9:37	6:58
		krishi	9:18	6:36
		jaimil	8:45	6:56
		Vinit	9:13	6:41
full stack		darshil		
		dixit	9:00	8:22
		harsh	9:11	7:05
		harshil	9:37	6:58
		niraj	9:20	6:39
		ankita	9:05	6:14
		krish	9:20	7:02
		prince	9:32	7:02
		sujal		
ui/ux		devarsh	9:03	6:38
		bansi chapani	9:05	6:55
seo		Chiragbhai	9:09	6:43
		bansi chavda	9:24	6:55
		jay	9:08	6:41
		om		
		rohan	9:09	6:44
app dev		vishva	9:13	6:37
marketing		sahil	9:32	6:58
		dhruvik	9:29	6:48"""

def parse_time(t, is_out=False):
    t = t.strip()
    if not t: return ""
    try:
        parts = t.split(":")
        if len(parts) != 2: return t
        h, m = int(parts[0]), int(parts[1])
        if is_out and 1 <= h < 12:
            h += 12
        return f"{h:02d}:{m:02d}"
    except Exception:
        return t

def get_auto_notes(in_time_str, out_time_str):
    auto_notes = []
    expected_out_mins = 18 * 60 + 30 # Default 6:30 PM
    
    if in_time_str:
        try:
            h, m = map(int, in_time_str.split(":"))
            in_mins = h * 60 + m
            if in_mins > 9 * 60 + 30:
                auto_notes.append("Arrived Late")
            expected_out_mins = in_mins + 9 * 60 + 30
        except: pass
        
    if out_time_str:
        try:
            h, m = map(int, out_time_str.split(":"))
            if h * 60 + m < expected_out_mins:
                auto_notes.append("Left Early")
        except: pass
        
    return " | ".join(auto_notes)

current_date_str = "2026-03-11"

# The parsing logic needs to be careful with the tabs/spaces in raw_data
for line in raw_data.split('\n'):
    if not line.strip() or line.startswith('11 Mar'): continue
    
    # Split by tabs and filter out empty strings
    parts = [p.strip() for p in line.split('\t') if p.strip()]
    
    if not parts: continue
    
    # Check if first part is a team name
    teams = ["ai teem", "full stack", "ui/ux", "seo", "app dev", "marketing"]
    if parts[0].lower() in teams:
        name = parts[1]
        raw_in = parts[2] if len(parts) > 2 else ""
        raw_out = parts[3] if len(parts) > 3 else ""
    else:
        name = parts[0]
        raw_in = parts[1] if len(parts) > 1 else ""
        raw_out = parts[2] if len(parts) > 2 else ""
    
    in_time = parse_time(raw_in, False)
    out_time = parse_time(raw_out, True)

    if not in_time and not out_time:
        att_type = "Work From Home"
        notes = ""
    else:
        att_type = "Present"
        notes = get_auto_notes(in_time, out_time)
        
    print(f"Adding: {name}, {current_date_str}, {in_time}, {out_time}, {att_type}, {notes}")
    
    success, msg = db.add_attendance(name, current_date_str, in_time, out_time, att_type, notes)
    if not success:
        print(f"Failed to add {name}: {msg}")
            
print("Done!")


