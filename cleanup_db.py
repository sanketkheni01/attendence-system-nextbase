import sqlite3

def cleanup_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    print("Cleaning up duplicates...")
    # Keep only the latest record for each employee/date
    c.execute('''
        DELETE FROM attendance
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM attendance
            GROUP BY employee_name, date
        )
    ''')
    conn.commit()
    
    # Try to add unique constraint if possible (Sqlite doesn't support ALTER TABLE for this easily)
    # We'll just rely on the application logic for now, or recreate the table if needed.
    
    print(f"Cleanup complete. Total records: {c.execute('SELECT COUNT(*) FROM attendance').fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    cleanup_db()
