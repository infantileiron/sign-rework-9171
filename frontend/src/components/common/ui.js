import {statuses} from '../../constants/domain.js';
import {esc} from '../../utils/format.js';

export const empty = message => `<p class="empty">${esc(message)}</p>`;
export const status = value => `<span class="status ${esc(value)}">${esc(statuses[value])}</span>`;
export const heading = (section, title, description, action = '') => `<header class="page-head">
  <div><p class="eyebrow">${section}</p><h1>${title}</h1><p class="description">${description}</p></div>${action}</header>`;
export const panelTitle = (title, detail = '') => `<div class="panel-head"><h2>${title}</h2>${detail}</div>`;
export const stat = (label, value, unit = '') => `<div class="stat"><span>${label}</span><strong>${value}</strong><small>${unit}</small></div>`;
export const numeric = (label, name, {min, max, step = 1, value = ''}) => `<label>${label}<input name="${name}" type="number" required min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
export const intakeFields = (row = {}) => [
  numeric('成片分钟', 'minutes', {min:0.01, max:180, step:'any', value:row.minutes}),
  numeric('镜头数', 'shots', {min:1, max:1000, value:row.shots}),
  numeric('背景切换次数', 'switches', {min:0, max:999, value:row.switches}),
].join('');
export const intakeValues = data => Object.fromEntries(['minutes','shots','switches'].map(key => [key, Number(data.get(key))]));
