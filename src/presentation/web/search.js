/**
 * Search window logic, per Iteration 4 Task E.
 *
 * No Stitch design exists for this window (see
 * resources/design/INVENTORY.md) — the markup this renders into
 * (search.html) is plain/utilitarian. All the real behavior described
 * in the brief lives here: live autocomplete, keyboard navigation,
 * multi-parcel sub-lists, a compass border layout with server-resolved
 * neighbor navigability, and clipboard copy.
 */

const State = {
  loaded: false,
  fileInfo: null, // { path, count }
  screen: 'empty', // 'empty' | 'idle' | 'sub_list' | 'detail'
  query: '',
  matches: [],
  highlightedIndex: -1,
  subListHoldingId: null,
  subListParcels: [],
  detail: null,
};

function setFileInfo(status) {
  const el = document.getElementById('file-info');
  if (status && status.loaded) {
    el.textContent = `${status.count} حيازة محمّلة`;
  } else {
    el.textContent = '';
  }
}

function showToast(text) {
  const toast = document.getElementById('toast');
  toast.textContent = text;
  toast.classList.add('visible');
  setTimeout(() => toast.classList.remove('visible'), 1500);
}

// ---- Screens ------------------------------------------------------------

function renderEmpty() {
  return `
    <div class="empty-state">
      <span class="material-symbols-outlined" style="font-size: 48px;">search_off</span>
      <p>لا يوجد ملف مُنتَج بعد. قم بتشغيل المعالجة أولاً أو افتح ملفاً موجوداً.</p>
    </div>`;
}

function renderIdle() {
  return `
    <div class="search-box">
      <input id="search-input" type="text" placeholder="ابحث باسم الحائز أو رقم الحيازة ..." autocomplete="off"/>
      <div id="dropdown" class="hidden"></div>
    </div>`;
}

function renderSubList() {
  const items = State.subListParcels
    .map(
      (p) => `
      <div class="sub-list-item" data-parcel-index="${p.parcel_index}">
        <span>رقم الأرض: ${p.land_number || '—'}</span>
        <span>${p.area_summary}</span>
      </div>`
    )
    .join('');
  return `
    ${renderIdle()}
    <div style="max-width:480px; margin: var(--space-lg) auto 0;">
      <button class="ghost" data-action="back-to-search">⬅ رجوع للبحث</button>
      <h3 style="margin: var(--space-md) 0;">اختر القطعة (${State.subListParcels.length} قطع تحت هذه الحيازة)</h3>
      ${items}
    </div>`;
}

function borderCell(label, border) {
  const navigable = border && border.is_navigable;
  const classes = `compass-cell${navigable ? ' navigable' : ''}`;
  const dataAttrs = navigable
    ? `data-action="navigate-neighbor" data-target="${border.target_holding_id}"`
    : '';
  return `<div class="${classes}" ${dataAttrs}><span class="label">${label}</span><span class="value">${(border && border.text) || '—'}</span></div>`;
}

function renderDetail() {
  const d = State.detail;
  const b = d.borders;
  return `
    ${renderIdle()}
    <div class="detail-wrapper">
      <button class="ghost" data-action="back-to-search" style="width:fit-content;">⬅ رجوع للنتائج</button>
      <div class="compass">
        <div class="compass-cell"></div>
        ${borderCell('⬆ البحري (شمال)', b.north)}
        <div class="compass-cell"></div>
        ${borderCell('⬅ الغربي', b.west)}
        <div class="compass-cell center">🌾<br/>${d.holding_id}</div>
        ${borderCell('الشرقي ➡', b.east)}
        <div class="compass-cell"></div>
        ${borderCell('⬇ القبلي (جنوب)', b.south)}
        <div class="compass-cell"></div>
      </div>
      <div class="info-card">
        <div><div class="field-label">الحائز</div><div class="field-value">${d.holder_name || '—'}</div></div>
        <div><div class="field-label">الرقم القومي</div><div class="field-value">${d.national_id || '—'}</div></div>
        <div><div class="field-label">الحوض</div><div class="field-value">${d.basin_name || '—'}</div></div>
        <div><div class="field-label">كود الحوض</div><div class="field-value">${d.basin_code || '—'}</div></div>
        <div><div class="field-label">المديرية</div><div class="field-value">${d.directorate || '—'}</div></div>
        <div><div class="field-label">الإدارة</div><div class="field-value">${d.administration || '—'}</div></div>
        <div><div class="field-label">رقم الأرض</div><div class="field-value">${d.land_number || '—'}</div></div>
        <div><div class="field-label">المساحة</div><div class="field-value">${d.feddan ?? 0} فدان، ${d.qirat ?? 0} قيراط، ${d.sahm ?? 0} سهم${d.total_sqm ? ' ≈ ' + d.total_sqm + ' م²' : ''}</div></div>
      </div>
      <div class="actions-row">
        <button class="primary" data-action="copy-detail">📋 نسخ البيانات</button>
      </div>
    </div>`;
}

function render() {
  const main = document.getElementById('main-content');
  const screens = { empty: renderEmpty, idle: renderIdle, sub_list: renderSubList, detail: renderDetail };
  main.innerHTML = screens[State.screen]();
  wireSearchInput();
}

// ---- Search input + autocomplete ----------------------------------------

function wireSearchInput() {
  const input = document.getElementById('search-input');
  if (!input) {
    return;
  }
  input.value = State.query;
  input.addEventListener('input', async (event) => {
    State.query = event.target.value;
    if (!State.query.trim()) {
      State.matches = [];
      renderDropdown();
      return;
    }
    const result = await Bridge.call('search_holdings', State.query);
    if (result.ok) {
      State.matches = result.value;
      State.highlightedIndex = -1;
      renderDropdown();
    }
  });
  input.addEventListener('keydown', onSearchKeydown);
  input.focus();
}

function renderDropdown() {
  const dropdown = document.getElementById('dropdown');
  if (!dropdown) {
    return;
  }
  if (State.matches.length === 0) {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
    return;
  }
  dropdown.classList.remove('hidden');
  dropdown.innerHTML = State.matches
    .map((m, index) => {
      const highlighted = index === State.highlightedIndex ? ' highlighted' : '';
      const suffix = m.parcel_count > 1 ? ` (${m.parcel_count} قطع)` : '';
      return `<div class="dropdown-item${highlighted}" data-index="${index}">
        <span class="name">${m.holder_name || '—'}${suffix}</span>
        <span class="id">#${m.holding_id}</span>
      </div>`;
    })
    .join('');
  dropdown.querySelectorAll('.dropdown-item').forEach((el) => {
    el.addEventListener('click', () => selectMatch(State.matches[Number(el.dataset.index)]));
  });
}

function onSearchKeydown(event) {
  if (State.matches.length === 0) {
    return;
  }
  if (event.key === 'ArrowDown') {
    event.preventDefault();
    State.highlightedIndex = Math.min(State.highlightedIndex + 1, State.matches.length - 1);
    renderDropdown();
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    State.highlightedIndex = Math.max(State.highlightedIndex - 1, 0);
    renderDropdown();
  } else if (event.key === 'Enter') {
    event.preventDefault();
    if (State.highlightedIndex >= 0) {
      selectMatch(State.matches[State.highlightedIndex]);
    }
  } else if (event.key === 'Escape') {
    State.matches = [];
    renderDropdown();
  }
}

async function selectMatch(match) {
  if (match.parcel_count > 1) {
    const result = await Bridge.call('get_parcels_for_holding', match.holding_id);
    if (result.ok) {
      State.subListHoldingId = match.holding_id;
      State.subListParcels = result.value;
      State.screen = 'sub_list';
      render();
    }
    return;
  }
  await openDetail(match.holding_id, 0);
}

async function openDetail(holdingId, parcelIndex) {
  const result = await Bridge.call('get_holding_detail', holdingId, parcelIndex);
  if (!result.ok || result.value.error) {
    return;
  }
  State.detail = result.value;
  State.screen = 'detail';
  render();
}

// ---- Event delegation -----------------------------------------------------

document.addEventListener('click', async (event) => {
  const subListItem = event.target.closest('.sub-list-item');
  if (subListItem) {
    await openDetail(State.subListHoldingId, Number(subListItem.dataset.parcelIndex));
    return;
  }

  const actionEl = event.target.closest('[data-action]');
  if (!actionEl) {
    return;
  }
  const action = actionEl.dataset.action;
  if (action === 'back-to-search') {
    State.screen = 'idle';
    State.detail = null;
    render();
  } else if (action === 'navigate-neighbor') {
    await openDetail(actionEl.dataset.target, 0);
  } else if (action === 'copy-detail') {
    await navigator.clipboard.writeText(State.detail.formatted_text);
    showToast('تم النسخ');
  }
});

function applyLoadStatus(status) {
  State.loaded = Boolean(status.loaded);
  State.fileInfo = status.loaded ? { path: status.path, count: status.count } : null;
  State.screen = State.loaded ? 'idle' : 'empty';
  State.query = '';
  State.matches = [];
  State.detail = null;
  setFileInfo(status);
  render();
}

// Called by main.py's open_search_window() after preloading a newer
// output into an already-open window (see main.py), so the window
// reflects the new file without a full reload.
function refreshAfterExternalReload() {
  Bridge.call('get_initial_status').then((result) => {
    if (result.ok) {
      applyLoadStatus(result.value);
    }
  });
}
window.refreshAfterExternalReload = refreshAfterExternalReload;

document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btn-open-file').addEventListener('click', async () => {
    const result = await Bridge.call('open_different_file');
    if (result.ok && result.value.loaded) {
      applyLoadStatus(result.value);
    } else if (result.ok && result.value.error) {
      showToast(result.value.error);
    }
  });

  const result = await Bridge.call('get_initial_status');
  if (result.ok) {
    applyLoadStatus(result.value);
  } else {
    render();
  }
});
