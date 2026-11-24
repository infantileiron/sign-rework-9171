from psycopg.errors import UniqueViolation

from src.utils.errors import Problem


def list_plans(db):
    return db.execute('SELECT * FROM plans ORDER BY id DESC').fetchall()


def get_plan(db, plan_id):
    plan = db.execute('SELECT * FROM plans WHERE id = %s', (plan_id,)).fetchone()
    if not plan:
        raise Problem(404, '特征方案不存在')
    return plan


def insert_plan(db, plan, actor):
    try:
        return db.execute('''INSERT INTO plans (name, alpha, features, created_by)
            VALUES (%(name)s, %(alpha)s, %(features)s, %(actor)s) RETURNING *''',
            {**plan, 'actor': actor}).fetchone()
    except UniqueViolation as exc:
        raise Problem(409, '版本名称已使用，请为新版本另起名称') from exc
