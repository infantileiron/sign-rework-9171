"""Work-log ledger and per-order settlement allocations."""
LOCK_KEY = 5210


def lock(db):
    """Serialise settlement writes so one component switches in a single transaction."""
    db.execute('SELECT pg_advisory_xact_lock(%s)', (LOCK_KEY,))


def work_log_hours(db, serials):
    if not serials:
        return {}
    rows = db.execute('SELECT serial, hours FROM work_logs WHERE serial = ANY(%s)', (list(serials),)).fetchall()
    return {row['serial']: row['hours'] for row in rows}


def upsert_work_log(db, serial, hours):
    db.execute('''INSERT INTO work_logs (serial, hours) VALUES (%s, %s)
        ON CONFLICT (serial) DO UPDATE
        SET hours = excluded.hours,
            received_at = CASE WHEN work_logs.hours IS DISTINCT FROM excluded.hours
                THEN now() ELSE work_logs.received_at END''', (serial, hours))


def upsert_sheet(db, sheet_no, actor):
    return db.execute('''INSERT INTO settlement_sheets (sheet_no, uploaded_by) VALUES (%s, %s)
        ON CONFLICT (sheet_no) DO UPDATE SET last_uploaded_at = now() RETURNING *''',
        (sheet_no, actor)).fetchone()


def replace_sheet_lines(db, sheet_id, lines):
    """Make this sheet's stored allocations match the upload exactly.

    Only this sheet's rows are deleted; another sheet that also mentions the
    same (order, serial) keeps its own row. A retried upload therefore neither
    duplicates nor removes a share recorded by a different sheet.
    """
    db.execute('DELETE FROM settlement_lines WHERE sheet_id = %s', (sheet_id,))
    with db.cursor() as cursor:
        cursor.executemany('''INSERT INTO settlement_lines (sheet_id, order_code, serial, hours)
            VALUES (%s, %s, %s, %s)''',
            [(sheet_id, order_code, serial, hours) for order_code, serial, hours in lines])


def all_lines(db):
    """Effective allocations: the latest upload wins for each (order, serial).

    Sheets remember ``last_uploaded_at``, so re-sending a sheet deterministically
    takes over the pairs it mentions while leaving rows only other sheets carry.
    """
    return db.execute('''
        SELECT DISTINCT ON (l.order_code, l.serial)
               l.order_code, l.serial, l.hours
        FROM settlement_lines l JOIN settlement_sheets s ON s.id = l.sheet_id
        ORDER BY l.order_code, l.serial, s.last_uploaded_at DESC, s.id DESC''').fetchall()


def known_orders(db, codes):
    if not codes:
        return set()
    rows = db.execute('SELECT code FROM orders WHERE code = ANY(%s)', (list(codes),)).fetchall()
    return {row['code'] for row in rows}


def order_hours(db):
    """The comparison sample: every read and write of the sample goes through orders.hours."""
    return {row['code']: row['hours'] for row in db.execute('SELECT code, hours FROM orders').fetchall()}


def committed_hours(db):
    return {row['order_code']: row['committed_hours']
            for row in db.execute('SELECT order_code, committed_hours FROM order_settlements').fetchall()}


def write_sample(db, code, hours):
    """Switch one order onto the reconciled hours, recorded in the caller's transaction."""
    db.execute('UPDATE orders SET hours = %s WHERE code = %s', (hours, code))
    db.execute('''INSERT INTO order_settlements (order_code, committed_hours) VALUES (%s, %s)
        ON CONFLICT (order_code) DO UPDATE
        SET committed_hours = excluded.committed_hours,
            switched_at = CASE WHEN order_settlements.committed_hours IS DISTINCT FROM excluded.committed_hours
                THEN now() ELSE order_settlements.switched_at END''', (code, hours))
