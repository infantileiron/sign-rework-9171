from psycopg.types.json import Jsonb

from src.constants.domain import Status
from src.utils.errors import Problem


SUMMARY = ('id, plan_id, plan_name, holdout, fingerprint, status, created_by, created_at, '
           'completed_at, published_by, published_at')


def create_report(db, snapshot, fingerprint, actor):
    return db.execute(f'''INSERT INTO reports (plan_id, plan_name, holdout, snapshot, fingerprint, created_by)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING {SUMMARY}''',
        (snapshot['plan']['id'], snapshot['plan']['name'], snapshot['holdout'], Jsonb(snapshot), fingerprint, actor)
    ).fetchone()


def list_reports(db, published_only):
    where = "WHERE status = 'published'" if published_only else ''
    return db.execute(f'SELECT {SUMMARY} FROM reports {where} ORDER BY id DESC').fetchall()


def get_report(db, report_id, published_only):
    row = db.execute(f'''SELECT {SUMMARY}, snapshot->'plan' AS plan, snapshot->>'method' AS method,
        jsonb_array_length(snapshot->'orders') AS sample_count, result, error FROM reports WHERE id = %s''',
        (report_id,)).fetchone()
    if not row or published_only and row['status'] != Status.PUBLISHED:
        raise Problem(404, '比选报告不存在')
    return row


def publish_report(db, report_id, actor):
    updated = db.execute(f'''UPDATE reports SET status = 'published', published_by = %s, published_at = now()
        WHERE id = %s AND status = 'succeeded' RETURNING {SUMMARY}''', (actor, report_id)).fetchone()
    if updated:
        return updated, True
    current = db.execute(f'SELECT {SUMMARY} FROM reports WHERE id = %s', (report_id,)).fetchone()
    if not current:
        raise Problem(404, '比选报告不存在')
    if current['status'] != Status.PUBLISHED:
        raise Problem(409, '计算成功后才可发布报告')
    return current, False


def take_job(db):
    return db.execute("SELECT id, snapshot, fingerprint FROM reports WHERE status = 'queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED").fetchone()


def finish_job(db, report_id, status, result, error):
    db.execute('UPDATE reports SET status=%s, result=%s, error=%s, completed_at=now() WHERE id=%s',
               (status.value, Jsonb(result) if result is not None else None, error, report_id))
