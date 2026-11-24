from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from src.config.database import connect
from src.constants.domain import Role
from src.controllers.auth import allow, current_user, login
from src.controllers.studio import save_plan, save_order
from src.models import audit, orders, plans
from src.schemas.inputs import LoginInput, OrderDetails, OrderInput, PlanInput, SettlementInput, WorkLogBatch
from src.services import settlement


router = APIRouter(prefix='/api')
analyst = allow(Role.ANALYST)


@router.post('/auth/login')
def sign_in(form: LoginInput, request: Request):
    return login(request, form.email, form.password)


@router.get('/auth/me')
def me(user=Depends(current_user)):
    return user


@router.get('/crews', dependencies=[Depends(current_user)])
def crews():
    with connect() as db:
        return orders.list_crews(db)


@router.get('/orders', dependencies=[Depends(current_user)])
def order_list():
    with connect() as db:
        return orders.list_orders(db)


@router.post('/orders', status_code=201)
def order_create(form: OrderInput, user=Depends(analyst)):
    return save_order(form, user['email'])


@router.put('/orders/{code}')
def order_update(code: Annotated[str, Path(pattern=r'^[A-Z][A-Z0-9-]{2,19}$')], form: OrderDetails,
                 user=Depends(analyst)):
    return save_order(form, user['email'], code)


@router.get('/orders/{code}/settlement')
def order_settlement(code: Annotated[str, Path(pattern=r'^[A-Z][A-Z0-9-]{2,19}$')],
                     user=Depends(current_user)):
    with connect() as db:
        return settlement.order_detail(db, code)


@router.get('/settlements')
def settlement_overview(user=Depends(current_user)):
    with connect() as db:
        return settlement.snapshot(db)


@router.post('/settlements/work-logs', status_code=201)
def work_log_upload(form: WorkLogBatch, user=Depends(analyst)):
    with connect() as db:
        state = settlement.ingest_ledger(db, form.entries)
        audit.record(db, user['email'], 'settlement.ledger', len(form.entries))
        return state


@router.post('/settlements', status_code=201)
def settlement_upload(form: SettlementInput, user=Depends(analyst)):
    with connect() as db:
        state = settlement.upload(db, form, user['email'])
        audit.record(db, user['email'], 'settlement.upload', form.sheet_no)
        return state


@router.get('/plans', dependencies=[Depends(current_user)])
def plan_list():
    with connect() as db:
        return plans.list_plans(db)


@router.post('/plans', status_code=201)
def plan_create(form: PlanInput, user=Depends(analyst)):
    return save_plan(form, user['email'])
