from src.config.database import connect
from src.models import audit, orders, plans


def save_order(form, actor, code=None):
    with connect() as db:
        values = form.model_dump()
        values['hours'] = values['hours'] or 0.0
        if code:
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
