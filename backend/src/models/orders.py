from psycopg.errors import ForeignKeyViolation, UniqueViolation

from src.utils.errors import Problem


def list_orders(db):
    return db.execute('SELECT * FROM orders ORDER BY code').fetchall()


def list_crews(db):
    return db.execute('''SELECT crews.*, count(orders.code) AS samples FROM crews
                         LEFT JOIN orders ON orders.crew = crews.code GROUP BY crews.code ORDER BY crews.code''').fetchall()


def insert_order(db, order):
    try:
        return db.execute('''INSERT INTO orders (code, title, crew, minutes, shots, switches, hours)
            VALUES (%(code)s, %(title)s, %(crew)s, %(minutes)s, %(shots)s, %(switches)s, %(hours)s)
            RETURNING *''', order).fetchone()
    except UniqueViolation as exc:
        raise Problem(409, '工单编号已存在') from exc
    except ForeignKeyViolation as exc:
        raise Problem(422, '请选择摄制组名册中的组别') from exc


def edit_order(db, code, details):
    try:
        row = db.execute('''UPDATE orders SET title = %(title)s, crew = %(crew)s, minutes = %(minutes)s,
            shots = %(shots)s, switches = %(switches)s, hours = %(hours)s
            WHERE code = %(code)s RETURNING *''', {**details, 'code': code}).fetchone()
    except ForeignKeyViolation as exc:
        raise Problem(422, '请选择摄制组名册中的组别') from exc
    if not row:
        raise Problem(404, '工单不存在')
    return row
