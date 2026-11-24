"""Ingest work logs and settlement sheets, then switch a component once aligned.

The comparison sample lives in ``orders.hours``. Settlement only rewrites it
when the connected component — orders linked by shared serials, directly or
indirectly — has every serial reconciled against the work-log ledger. Until
then those orders keep their previous sample, while unrelated orders are
untouched.
"""
from src.models import settlements
from src.services.reconcile import TOLERANCE, reconcile
from src.utils.errors import Problem


def snapshot(db):
    lines = [{'order': row['order_code'], 'serial': row['serial'], 'hours': row['hours']}
             for row in settlements.all_lines(db)]
    ledger = settlements.work_log_hours(db, {line['serial'] for line in lines})
    return reconcile(lines, ledger, settlements.committed_hours(db), settlements.order_hours(db))


def _switch_aligned(db, state):
    """Write changed, aligned components back; the caller's transaction is all-or-nothing.

    Components that are still waiting keep their old sample. A retry that
    produces the same hours changes nothing, so re-uploading is a no-op.
    """
    switched = []
    for component in state['components']:
        if component['state'] != 'aligned':
            continue
        pending = {code: state['orders'][code]['pending_hours'] for code in component['orders']}
        oversized = sorted(code for code, hours in pending.items() if not 0 <= hours <= 200)
        if oversized:
            raise Problem(422, f'工单分摊合计须在 0–200 h 之间：{"、".join(oversized)}')
        changed = [code for code, hours in pending.items()
                   if abs((state['orders'][code]['sample_hours'] or 0) - hours) > TOLERANCE]
        for code in changed:
            settlements.write_sample(db, code, pending[code])
        if changed:
            switched.append(sorted(component['orders']))
    return switched


def _settle(db):
    state = snapshot(db)
    switched = _switch_aligned(db, state)
    if switched:
        state = snapshot(db)  # reflect the new sample values in the response
    return {**state, 'switched': switched}


def ingest_ledger(db, entries):
    """Record work logs; retries replace by serial so hours never double count."""
    settlements.lock(db)
    for row in entries:
        settlements.upsert_work_log(db, row.serial, row.hours)
    return _settle(db)


def upload(db, form, actor):
    """Store one settlement sheet's allocations; the ledger is uploaded separately.

    A serial whose ledger entry has not arrived yet simply shows as *missing*
    until a 记工补传 records it, so a short sheet naturally blocks its group.
    Retrying the same sheet replaces that sheet's own rows by (order, serial),
    so shares never double count.
    """
    settlements.lock(db)
    codes = {row.order for row in form.allocations}
    missing = sorted(codes - settlements.known_orders(db, codes))
    if missing:
        raise Problem(422, f'结算单引用了未录入的工单：{"、".join(missing)}')

    sheet = settlements.upsert_sheet(db, form.sheet_no, actor)
    settlements.replace_sheet_lines(db, sheet['id'],
                                    [(row.order, row.serial, row.hours) for row in form.allocations])
    return {**_settle(db), 'sheet_no': sheet['sheet_no']}


def order_detail(db, code):
    sample = settlements.order_hours(db)
    if code not in sample:
        raise Problem(404, '工单不存在')
    detail = snapshot(db)['orders'].get(code)
    if detail:
        return detail
    return {
        'order': code, 'state': 'unsettled', 'serials': [], 'missing': [], 'unbalanced': [],
        'waiting_on': [], 'component_waiting': [], 'component': [code],
        'pending_hours': None, 'sample_hours': sample[code],
        'committed_hours': settlements.committed_hours(db).get(code),
    }
