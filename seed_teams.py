import sqlite3

DB_PATH = 'attendance.db'

def run():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Add team column to employees if it doesn't exist
    try:
        c.execute("ALTER TABLE employees ADD COLUMN team TEXT DEFAULT 'Unassigned'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    teams_data = {
        "AI": ["Himansu", "yash", "Nirav", "Dhruvit", "krishi", "jaimil", "Vinit"],
        "Full Stack": ["darshil", "dixit", "harsh", "harshil", "niraj", "ankita", "krish", "prince", "sujal"],
        "UI/UX": ["devarsh", "bansi chapani"],
        "SEO": ["Chiragbhai", "bansi chavda", "jay", "om", "rohan"],
        "App Dev": ["vishva", "meet"],
        "Marketing": ["sahil", "dhruvik"]
    }
    
    # First, let's optional clear existing test employees to clean up if we want
    # c.execute("DELETE FROM employees")

    for team, members in teams_data.items():
        for emp in members:
            # Check if emp exists
            c.execute("SELECT id FROM employees WHERE name=?", (emp,))
            if c.fetchone():
                c.execute("UPDATE employees SET team=? WHERE name=?", (team, emp))
            else:
                c.execute("INSERT INTO employees (name, team) VALUES (?, ?)", (emp, team))

    # Optional: Delete the "John Doe" testing user if it exists
    c.execute("DELETE FROM employees WHERE name='John Doe'")

    conn.commit()
    conn.close()
    print("Database seeded with teams and employees!")

if __name__ == "__main__":
    run()
