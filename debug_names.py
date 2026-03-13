import sqlite3

def debug_counts():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM employees')
    emp_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM attendance WHERE date = "2026-03-11"')
    att_count = c.fetchone()[0]
    
    c.execute('SELECT DISTINCT employee_name FROM attendance WHERE date = "2026-03-11"')
    dist_att_names = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT name FROM employees')
    emp_names = [row[0] for row in c.fetchall()]
    
    print(f"Total Employees: {emp_count}")
    print(f"Total Attendance Records (2026-03-11): {att_count}")
    print(f"Distinct Names in Attendance (2026-03-11): {len(dist_att_names)}")
    
    print("\nNames in Attendance but not in Employees (Case Insensitive & Trim):")
    emp_names_clean = {n.strip().lower() for n in emp_names}
    mismatched = []
    for n in dist_att_names:
        if n.strip().lower() not in emp_names_clean:
            mismatched.append(n)
    print(mismatched)
    
    print("\nDuplicates in Attendance (2026-03-11):")
    from collections import Counter
    counts = Counter(dist_att_names)
    dupes = [name for name, count in counts.items() if count > 1]
    print(dupes)

    conn.close()

if __name__ == "__main__":
    debug_counts()
