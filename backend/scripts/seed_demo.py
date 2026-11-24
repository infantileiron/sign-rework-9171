import hashlib
import json

from src.config.database import connect
from src.utils.security import password_hash


ACCOUNTS = [('owner@bridge.test', '林桥', 'owner'), ('analyst@bridge.test', '周岚', 'analyst'),
            ('viewer@bridge.test', '许禾', 'viewer')]
TITLES = ['办事导引', '图书借阅', '就诊签到', '观展须知', '课堂签到', '防汛提示', '场馆换乘', '社区议事']
TOPICS = ['政务服务', '公共图书馆', '社区门诊', '城市展厅', '社区课堂', '轮渡服务']
NOISE = [-0.2, 0.3, 0.0, -0.1, 0.1, -0.3, 0.2, 0.0]


def demo_order(group, index):
    minutes = round(1.5 + 1.1 * index + 0.14 * group, 2)
    shots = 8 + 3 * ((index * 3 + group) % 8) + group
    switches = (index + group * 2) % 4
    shift = 1.55 if group == 6 else 0.10 * (group - 3)
    hours = round(0.5 + 0.45 * minutes + 0.14 * shots + shift + NOISE[index], 2)
    return (f'QY-{group:02d}{index + 1:02d}', f'{TOPICS[group - 1]}｜{TITLES[index]}',
            f'G{group:02d}', minutes, shots, switches, hours)


def demo_settlements(db):
    """Seed a shared-serial example that exercises alignment and waiting.

    QY-0601 and QY-0602 share one work-log entry that has arrived; the two
    shares add up to the ledger amount, so the pair aligns. QY-0603 shares a
    second entry whose ledger row is deliberately absent, so QY-0603 keeps its
    old sample and demonstrates the "没到流水" state until 记工补传 arrives.
    Every other seeded order gets a single-serial allocation equal to its
    recorded hours.
    """
    orders = {row['code']: row['hours'] for row in db.execute('SELECT code, hours FROM orders').fetchall()}
    sheets = {}
    for group in range(1, 7):
        sheet_no = f'JS-{group:02d}'
        sheet = db.execute('''INSERT INTO settlement_sheets (sheet_no, uploaded_by) VALUES (%s, %s)
            ON CONFLICT (sheet_no) DO NOTHING RETURNING id''', (sheet_no, 'analyst@bridge.test')).fetchone()
        sheets[group] = sheet['id'] if sheet else db.execute(
            'SELECT id FROM settlement_sheets WHERE sheet_no = %s', (sheet_no,)).fetchone()['id']

    ledger, lines = [], []
    shared = ['QY-0601', 'QY-0602']
    if all(code in orders for code in shared):
        serial = 'JS-06-SHARE'
        ledger.append((serial, round(sum(orders[code] for code in shared), 2)))
        lines += [(sheets[6], code, serial, orders[code]) for code in shared]
        waiting = 'QY-0603'
        if waiting in orders:
            lines.append((sheets[6], waiting, 'JS-06-PENDING', orders[waiting]))
    for code, hours in orders.items():
        if code in shared or code == 'QY-0603':
            continue
        group = int(code[3:5])
        ledger.append((f'{code}-L1', hours))
        lines.append((sheets[group], code, f'{code}-L1', hours))

    with db.cursor() as cursor:
        cursor.executemany('''INSERT INTO work_logs (serial, hours) VALUES (%s, %s)
            ON CONFLICT (serial) DO NOTHING''', ledger)
        cursor.executemany('''INSERT INTO settlement_lines (sheet_id, order_code, serial, hours)
            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING''', lines)


def seed():
    with connect() as db:
        for email, name, role in ACCOUNTS:
            if not db.execute('SELECT 1 FROM accounts WHERE email=%s', (email,)).fetchone():
                db.execute('INSERT INTO accounts VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                           (email, name, password_hash('Qiaoyu2026!'), role))
        with db.cursor() as cursor:
            cursor.executemany('''INSERT INTO orders (code, title, crew, minutes, shots, switches, hours)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING''',
                [demo_order(group, index) for group in range(1, 7) for index in range(8)])
        db.execute('''INSERT INTO plans (name, alpha, features, created_by)
            VALUES ('接单三项 · v1', 0.10, ARRAY['minutes','shots','switches'], %s),
                   ('时长与镜头 · v2', 0.20, ARRAY['minutes','shots'], %s)
            ON CONFLICT (name) DO NOTHING''', ('analyst@bridge.test', 'analyst@bridge.test'))
        demo_settlements(db)
        # Stable natural keys and user-editable values make repeat runs directly comparable.
        sets = {table: db.execute(f'SELECT {columns} FROM {table} ORDER BY {order_key}').fetchall()
                for table, columns, order_key in (
                    ('accounts', 'email, role', 'email'), ('orders', '*', 'code'), ('crews', '*', 'code'),
                    ('plans', 'name, alpha, features', 'name'),
                )}
    content = json.dumps(sets, sort_keys=True, ensure_ascii=False).encode()
    return {'rows': {table: len(rows) for table, rows in sets.items()}, 'keys_and_content_sha256': hashlib.sha256(content).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(seed(), sort_keys=True))
