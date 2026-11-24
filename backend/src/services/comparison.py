"""Nested use of one fixed external crew and leave-one-crew-out development folds."""
from collections import Counter
from statistics import mean

from src.services.lasso import estimate, fit
from src.utils.errors import Problem


def validate_sample(rows, holdout):
    counts = Counter(row['crew'] for row in rows)
    if len(rows) > 600:
        raise Problem(422, '每份比选最多支持 600 条工单')
    if holdout not in counts or len(counts) < 3 or min(counts.values()) < 2:
        raise Problem(422, '须有至少 3 个有样本的摄制组，且参评各组至少有 2 条已结算工单')


def evaluate(training, testing, plan):
    model = fit(training, plan['features'], plan['alpha'])
    predictions = []
    for row in testing:
        baseline = model['median']
        lasso = estimate(model, row)
        predictions.append({'code': row['code'], 'actual': row['hours'], 'baseline': baseline, 'lasso': lasso})
    return {
        'crew': testing[0]['crew'], 'train_crews': sorted({row['crew'] for row in training}),
        'train_samples': len(training), 'test_samples': len(testing), 'fit': model,
        'mae': {name: mean(abs(row[name] - row['actual']) for row in predictions) for name in ('baseline', 'lasso')},
        'predictions': predictions,
    }


def compare(snapshot):
    rows, plan, holdout = (snapshot[key] for key in ('orders', 'plan', 'holdout'))
    validate_sample(rows, holdout)
    development = [row for row in rows if row['crew'] != holdout]
    external = [row for row in rows if row['crew'] == holdout]
    folds = []
    for crew in sorted({row['crew'] for row in development}):
        training = [row for row in development if row['crew'] != crew]
        validation = [row for row in development if row['crew'] == crew]
        folds.append(evaluate(training, validation, plan))
    macro = {name: mean(fold['mae'][name] for fold in folds) for name in ('baseline', 'lasso')}
    winner = 'lasso' if macro['lasso'] < macro['baseline'] - 1e-9 else 'baseline'
    return {'folds': folds, 'macro_mae': macro, 'winner': winner,
            'holdout': evaluate(development, external, plan)}


def predict(result, row):
    model = result['holdout']['fit']
    lasso = estimate(model, row)
    return {
        'hours': lasso if result['winner'] == 'lasso' else model['median'],
        'model': result['winner'], 'lasso': lasso, 'baseline': model['median'],
        'outside_range': [item['key'] for item in model['features'] if not item['min'] <= row[item['key']] <= item['max']],
    }
