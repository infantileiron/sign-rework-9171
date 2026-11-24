import {roles} from '../constants/domain.js';
import {modules} from '../router/routes.js';
import {esc} from '../utils/format.js';

export function shell(user, page) {
  return `<div class="workspace">
    <aside class="sidebar"><a class="identity" href="#/orders"><i class="mark" aria-hidden="true">Ⅲ</i><span>桥语手语<small>制作工作台</small></span></a>
      <nav aria-label="业务模块">${modules.map(([key, label, icon]) => `<a href="#/${key}" ${key === page ? 'aria-current="page"' : ''}><span aria-hidden="true">${icon}</span>${label}</a>`).join('')}</nav>
      <div class="sidebar-foot"><span class="avatar">${esc(user.display_name[0])}</span><div>${esc(user.display_name)}<small>${roles[user.role]}</small></div><button id="logout" class="plain" type="button">退出</button></div>
    </aside>
    <main class="main"><div class="context"><span>制作运营 <i>/</i> 视频返工工时比选</span><span class="context-meta">工时单位 · 小时</span></div><div id="route" class="content"></div></main>
  </div>`;
}
