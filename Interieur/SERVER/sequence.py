from db import get_mysql_connection

def update_sequence_table():
    tables = ["users", "measurements", "admin_logs", "alert_config"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM sequence WHERE table_name = %s", (table,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute(
                    "UPDATE sequence SET total = %s, updated_at = NOW() WHERE table_name = %s",
                    (total, table)
                )
            else:
                cursor.execute(
                    "INSERT INTO sequence (table_name, total, updated_at) VALUES (%s, %s, NOW())",
                    (table, total)
                )
        conn.commit()

def get_sequence_totals():
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT table_name, total FROM sequence")
        return cursor.fetchall()