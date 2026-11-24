import {features, models} from '../constants/domain.js';
import {crewName} from '../stores/studio.js';
import {esc, fixed, signed} from '../utils/format.js';

export function maeBars(metrics, scale) {
  return `<div class="mae-bars">${['lasso','baseline'].map(key => `<div><span>${models[key]}</span>
    <span class="bar-track" aria-hidden="true"><i class="bar ${key}" style="--length:${100 * metrics[key] / scale}%"></i></span><strong class="mono">${fixed(metrics[key],3)} h</strong></div>`).join('')}</div>`;
}

export function predictions(rows) {
  return `<div class="table-wrap"><table class="predictions"><thead><tr><th>工单号</th><th>实际 h</th><th>Lasso h</th><th>中位数 h</th></tr></thead><tbody>${rows.map(row => `<tr><td class="mono">${esc(row.code)}</td><td>${fixed(row.actual)}</td><td>${fixed(row.lasso)}</td><td>${fixed(row.baseline)}</td></tr>`).join('')}</tbody></table></div>`;
}

export function foldDetails(fold) {
  return `<details class="fold"><summary><span><b>${esc(crewName(fold.crew))}</b><small>${fold.test_samples} 条验证样本</small></span>
      <span class="mono">${fixed(fold.mae.lasso,3)} <i>/</i> ${fixed(fold.mae.baseline,3)} h</span></summary>
    <p class="subtle">训练组 ${fold.train_crews.map(crew => esc(crewName(crew))).join('、')} · ${fold.train_samples} 条</p>${coefficients(fold.fit)}${predictions(fold.predictions)}</details>`;
}

export function coefficients(fit) {
  return `<p class="subtle">训练目标均值 ${fixed(fit.target_mean,3)} h · 基线中位数 ${fixed(fit.median,3)} h · Lasso 截距 ${signed(fit.intercept)} h</p>
    <div class="table-wrap"><table class="coefficients"><thead><tr><th>接单特征</th><th>均值</th><th>总体标准差</th><th>标准化系数 h</th><th>原尺度 h / 单位</th></tr></thead><tbody>${fit.features.map(item => `<tr><td>${features[item.key]}${item.scale === 0 ? ' <small>常量列</small>' : ''}</td><td>${fixed(item.mean,3)}</td><td>${fixed(item.scale,3)}</td><td>${signed(item.standard_coefficient)}</td><td class="${item.hours_per_unit === 0 ? 'muted' : 'actual'}">${signed(item.hours_per_unit)}</td></tr>`).join('')}</tbody></table></div>`;
}
