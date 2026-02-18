import mysql.connector
import datetime
from app.utility.config import DB_HOST, DB_USER, DB_PASS, DB_NAME

def get_db_conn():
    # Step 1: Connect without selecting DB
    root_conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        autocommit=True
    )

    cursor = root_conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    root_conn.close()

    # Step 2: Connect again but now use the DB
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=False
    )
def ensure_tables():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    conn.database = DB_NAME
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticket_id VARCHAR(128) UNIQUE,
        created_by VARCHAR(128),
        severity VARCHAR(64),
        issue_type VARCHAR(128),
        ticket TEXT,
        inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        classification VARCHAR(64),
        confidence FLOAT,
        reasoning TEXT,
        agent_name VARCHAR(64),
        status VARCHAR(32) DEFAULT 'new',
        processed_at DATETIME NULL
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    cursor.close()
    conn.close()

def upsert_alert(alert):
    conn = get_db_conn()
    cursor = conn.cursor()
    sql = """
    INSERT INTO alerts (ticket_id, ticket, created_by, severity)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      ticket = VALUES(ticket),
      created_by = VALUES(created_by),
      severity = VALUES(severity)
    """
    cursor.execute(sql, (
        alert["Ticket ID"],
        alert["Ticket"],
        alert["Created By"],
        alert["Severity"]
    ))
    conn.commit()
    cursor.close()
    conn.close()

# def fetch_unprocessed(limit=10):
#     conn = get_db_conn()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM alerts WHERE classification IS NULL LIMIT %s", (limit,))
#     rows = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     return rows

def fetch_alert_by_id(alert_id):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def update_alert_classification(id, issue_type,classification, confidence, reasoning, agent_name):
    conn = get_db_conn()
    cursor = conn.cursor()
    processed_at = datetime.datetime.utcnow().replace(microsecond=0).isoformat(sep=' ')
    sql = """
    UPDATE alerts
    SET issue_type=%s, classification=%s, confidence=%s, reasoning=%s, agent_name=%s,
    status='IN_PROGRESS', processed_at=%s
    WHERE id=%s
    """
    cursor.execute(sql, (
        issue_type,
        classification,
        confidence,
        reasoning,
        agent_name,
        processed_at,
        id
    ))
    conn.commit()
    cursor.close()
    conn.close()
