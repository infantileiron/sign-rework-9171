import {session} from '../stores/session.js';
import {studio} from '../stores/studio.js';

export async function request(path, {method = 'GET', data, blob = false, signal} = {}) {
  const headers = {};
  if (session.get()) headers.Authorization = `Bearer ${session.get()}`;
  if (data) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {method, headers, body: data ? JSON.stringify(data) : undefined, signal});
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      session.clear();
      window.dispatchEvent(new Event('session-ended'));
    }
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.message ?? '请求失败，请确认服务可用后重试');
  }
  return blob ? response.blob() : response.json();
}

export const api = {
  login: data => request('/auth/login', {method:'POST', data}),
  me: () => request('/auth/me'),
  orders: () => request('/orders'),
  crews: () => request('/crews'),
  plans: () => request('/plans'),
  reports: () => request('/reports'),
  saveOrder: (data, code) => request(code ? `/orders/${encodeURIComponent(code)}` : '/orders', {method:code ? 'PUT' : 'POST', data}),
  savePlan: data => request('/plans', {method:'POST', data}),
  run: data => request('/reports', {method:'POST', data}),
  report: (id, signal) => request(`/reports/${id}`, {signal}),
  publish: id => request(`/reports/${id}/publish`, {method:'POST'}),
  estimate: (id, data) => request(`/reports/${id}/estimate`, {method:'POST', data}),
  export: id => request(`/reports/${id}/export`, {blob:true}),
};

export async function loadStudio() {
  [studio.orders, studio.crews, studio.plans, studio.reports] = await Promise.all([
    api.orders(), api.crews(), api.plans(), api.reports(),
  ]);
}
