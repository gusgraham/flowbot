"""
Migration script to make ml_classification and ml_confidence nullable
Run from backend directory: python migrate_classification.py
"""
import sqlite3
import os

DB_PATH = "flowbot.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dailyclassification'")
        if not cursor.fetchone():
            print("dailyclassification table doesn't exist yet - no migration needed")
            return
        
        # Get existing data
        cursor.execute("SELECT * FROM dailyclassification")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} existing classification records")
        
        # Get column info
        cursor.execute("PRAGMA table_info(dailyclassification)")
        columns = cursor.fetchall()
        col_names = [c[1] for c in columns]
        print(f"Existing columns: {col_names}")
        
        # Rename old table
        cursor.execute("ALTER TABLE dailyclassification RENAME TO dailyclassification_old")
        
        # Create new table with nullable ml_classification and ml_confidence
        cursor.execute("""
            CREATE TABLE dailyclassification (
                id INTEGER PRIMARY KEY,
                date DATETIME NOT NULL,
                ml_classification VARCHAR,
                ml_confidence FLOAT,
                manual_classification VARCHAR,
                override_reason VARCHAR,
                override_by VARCHAR,
                override_at DATETIME,
                interim_review_id INTEGER NOT NULL,
                FOREIGN KEY (interim_review_id) REFERENCES interimreview(id)
            )
        """)
        
        # Copy data back
        if rows:
            placeholders = ", ".join(["?" for _ in col_names])
            cursor.execute(f"INSERT INTO dailyclassification ({', '.join(col_names)}) VALUES ({placeholders})", rows[0])
            for row in rows[1:]:
                cursor.execute(f"INSERT INTO dailyclassification ({', '.join(col_names)}) VALUES ({placeholders})", row)
        
        # Drop old table
        cursor.execute("DROP TABLE dailyclassification_old")
        
        conn.commit()
        print("Migration completed successfully!")
        print("ml_classification and ml_confidence are now nullable")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
