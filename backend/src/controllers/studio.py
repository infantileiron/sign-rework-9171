from src.config.database import connect
from src.models import audit, orders, plans
from src.utils.errors import Problem


def save_order(form, actor, code=None):
    with connect() as db:
        values = form.model_dump()
        values['hours'] = values['hours'] or 0.0
        if code:
            current = db.execute('SELECT hours FROM orders WHERE code = %s', (code,)).fetchone()
            if current and orders.settlement_lines(db, code) and values['hours'] != current['hours']:
                raise Problem(409, '该工单的工时由结算单分摊决定，请在「结算补录」中修订流水分摊')
            row = orders.edit_order(db, code, values)
            audit.record(db, actor, 'order.edit', code)
        else:
            row = orders.insert_order(db, values)
            audit.record(db, actor, 'order.create', row['code'])
        return row


def save_plan(form, actor):
    with connect() as db:
        plan = plans.insert_plan(db, form.model_dump(), actor)
        audit.record(db, actor, 'plan.create', plan['id'])
        return plan
