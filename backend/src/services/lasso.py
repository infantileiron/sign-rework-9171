"""One fit takes training rows only. Population standardization and intercept are part of the fit."""
from math import copysign, sqrt
from statistics import mean, median


def soft(value, alpha):
    return copysign(abs(value) - alpha, value) if abs(value) > alpha else 0.0


def fit(rows, features, alpha):
    targets = [row['hours'] for row in rows]
    target_mean = mean(targets)
    residuals = [target - target_mean for target in targets]
    columns = []
    statistics = []
    n = len(rows)
    for feature in features:
        values = [row[feature] for row in rows]
        center = mean(values)
        spread = sqrt(sum((value - center) ** 2 for value in values) / n)
        columns.append([(value - center) / spread for value in values] if spread else [0.0] * n)
        statistics.append({'key': feature, 'mean': center, 'scale': spread,
                           'min': min(values), 'max': max(values)})

    coefficients = [0.0] * len(columns)
    for iteration in range(1, 5001):
        largest_update = 0.0
        for index, column in enumerate(columns):
            if not statistics[index]['scale']:
                continue
            previous = coefficients[index]
            score = sum(value * residual for value, residual in zip(column, residuals)) / n + previous
            updated = soft(score, alpha)
            delta = updated - previous
            coefficients[index] = updated
            if delta:
                residuals = [residual - delta * value for residual, value in zip(residuals, column)]
            largest_update = max(largest_update, abs(delta))
        if largest_update < 1e-9:
            break
    else:
        raise ValueError('Lasso 未在迭代上限内收敛，请提高 α 或减少共线特征')

    intercept = target_mean
    for summary, coefficient in zip(statistics, coefficients):
        raw = coefficient / summary['scale'] if summary['scale'] else 0.0
        summary.update(standard_coefficient=coefficient, hours_per_unit=raw)
        intercept -= raw * summary['mean']
    return {'intercept': intercept, 'target_mean': target_mean, 'median': median(targets),
            'features': statistics, 'iterations': iteration}


def estimate(model, row):
    raw = model['intercept'] + sum(item['hours_per_unit'] * row[item['key']] for item in model['features'])
    return max(0.0, raw)
