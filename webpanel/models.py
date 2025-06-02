import psycopg2
from config import DB_URI

def get_db_connection():
    conn = psycopg2.connect(DB_URI)
    return conn

def get_all_tickets(search=None, status=None):
    conn = get_db_connection()
    cur = conn.cursor()
    # Включаем поле status_updated_at (позиция [10])
    query = """
        SELECT id, user_id, lang, city, department, message, ticket_number, created_at, status, reply, status_updated_at
        FROM tickets
    """
    params = []
    where_clauses = []

    if search:
        where_clauses.append(
            "(message ILIKE %s OR city ILIKE %s OR department ILIKE %s OR ticket_number ILIKE %s)"
        )
        search_param = f"%{search}%"
        params += [search_param, search_param, search_param, search_param]
    if status:
        where_clauses.append("status = %s")
        params.append(status)
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY id DESC"

    cur.execute(query, params)
    tickets = cur.fetchall()
    cur.close()
    conn.close()
    return tickets

def get_ticket_by_id(ticket_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, lang, city, department, message, ticket_number, created_at, status, reply, status_updated_at FROM tickets WHERE id = %s",
        (ticket_id,)
    )
    ticket = cur.fetchone()
    cur.close()
    conn.close()
    return ticket

def update_ticket_status(ticket_id, new_status):
    # Обновляем статус и дату обновления статуса!
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tickets SET status = %s, status_updated_at = NOW() WHERE id = %s",
        (new_status, ticket_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def add_ticket_reply(ticket_id, reply):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tickets SET reply = %s WHERE id = %s",
        (reply, ticket_id)
    )
    conn.commit()
    cur.close()
    conn.close()
