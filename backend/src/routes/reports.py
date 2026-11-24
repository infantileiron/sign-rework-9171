from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from src.config.database import connect
from src.constants.domain import Role
from src.controllers.auth import allow, current_user
from src.models import audit, reports
from src.schemas.inputs import Intake, RunInput
from src.services.comparison import predict
from src.services.reports import enqueue, require_result, rows_csv


router = APIRouter(prefix='/api/reports')
ReportID = Annotated[int, Path(gt=0, le=9223372036854775807)]


@router.get('')
def index(user=Depends(current_user)):
    with connect() as db:
        return reports.list_reports(db, user['role'] == Role.VIEWER)


@router.post('', status_code=202)
def start(form: RunInput, user=Depends(allow(Role.ANALYST))):
    with connect() as db:
        return enqueue(db, form.plan_id, form.holdout, user['email'])


@router.get('/{report_id}')
def detail(report_id: ReportID, user=Depends(current_user)):
    with connect() as db:
        return reports.get_report(db, report_id, user['role'] == Role.VIEWER)


@router.post('/{report_id}/publish')
def publish(report_id: ReportID, user=Depends(allow(Role.OWNER))):
    with connect() as db:
        report, changed = reports.publish_report(db, report_id, user['email'])
        if changed:
            audit.record(db, user['email'], 'report.publish', report_id)
        return report


@router.post('/{report_id}/estimate')
def estimate(report_id: ReportID, form: Intake, user=Depends(current_user)):
    report = detail(report_id, user)
    return predict(require_result(report), form.model_dump())


@router.get('/{report_id}/export')
def export(report_id: ReportID, user=Depends(current_user)):
    content = rows_csv(detail(report_id, user))
    return Response(content, media_type='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="sign-rework-{report_id}.csv"'})
