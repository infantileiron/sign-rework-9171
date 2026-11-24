import {api, loadStudio} from './api/studio.js';
import {shell} from './components/shell.js';
import {login} from './pages/login.js';
import {ordersPage} from './pages/orders.js';
import {plansPage} from './pages/plans.js';
import {reportsPage} from './pages/reports.js';
import {runsPage} from './pages/runs.js';
import {activeRoute} from './router/routes.js';
import {session} from './stores/session.js';
import {studio} from './stores/studio.js';

const root = document.querySelector('#app');
let cleanup;

function reset(expired = false) {
  cleanup?.();
  cleanup = null;
  session.clear();
  studio.user = null;
  studio.orderFilter = '';
  login(root, render, expired);
}

async function render() {
  if (!studio.user) return;
  cleanup?.();
  cleanup = null;
  const [page, id] = activeRoute();
  root.innerHTML = shell(studio.user, page);
  window.scrollTo(0,0);
  root.querySelector('#logout').onclick = () => reset();
  const panel = root.querySelector('#route');
  if (page === 'orders') ordersPage(panel, render);
  if (page === 'plans') plansPage(panel, render);
  if (page === 'reports' && id) cleanup = reportsPage(panel, id, render);
  if (page === 'runs' || page === 'reports' && !id) {
    panel.textContent = '正在读取运行记录…';
    try {
      studio.reports = await api.reports();
      if (!panel.isConnected) return;
      if (page === 'runs') runsPage(panel);
      else reportsPage(panel);
    } catch (error) {
      if (!panel.isConnected) return;
      panel.textContent = error.message + ' ';
      const retry = Object.assign(document.createElement('button'), {textContent:'重试', className:'button'});
      retry.onclick = render;
      panel.append(retry);
    }
  }
}

window.addEventListener('hashchange', render);
window.addEventListener('session-ended', () => reset(true));
if (session.get()) {
  try {
    studio.user = await api.me();
    await loadStudio();
    render();
  } catch { reset(true); }
} else {
  login(root, render);
}
