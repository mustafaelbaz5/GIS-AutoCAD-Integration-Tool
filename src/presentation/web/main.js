/**
 * Main window state machine, per Iteration 4 Task D.
 *
 * Renders one of four states — empty / files_loaded / processing /
 * results — by swapping the nav Actions Bar and <main> content
 * wholesale. Each state's markup is transcribed verbatim from its
 * source Stitch export (resources/design/stitch_exports/) so the
 * exact button styling/disabled-state per screen is reproduced
 * exactly, not approximated. The Advanced Settings expanded panel has
 * no Stitch design yet (see resources/design/INVENTORY.md) — its
 * markup below is plain/utilitarian, clearly not a Stitch screen,
 * built only so the real MergeOptions/mapping-picker functionality
 * Task D requires has somewhere to live.
 */

const State = {
  screen: 'empty', // 'empty' | 'files_loaded' | 'processing' | 'results'
  base: null, // { path, name, rowCount } | null
  secondary: null, // { path, name, rowCount } | null
  outputDir: '', // fetched from Python at startup — see loadOutputDir()
  progress: { percent: 0, message: '' },
  stats: null,
  advancedSettingsOpen: false,
  mergeOptions: { includeLaghiRows: false, enableSpatialSort: true },
  availableSecondaryMappings: [],
  secondaryMappingPath: null,
  logEntries: [],
};

function canStart() {
  return Boolean(State.base && State.secondary && State.screen !== 'processing');
}

// ---- Actions Bar templates (one per screen state) --------------------------

function navActionsEmpty() {
  return `
    <button data-action="start" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-surface-container-highest text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">play_arrow</span>تشغيل
    </button>
    <button data-action="clear" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-transparent text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">delete</span>مسح
    </button>
    <button data-action="search" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-transparent text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">search</span>بحث
    </button>`;
}

function navActionsFilesLoaded() {
  const startEnabled = canStart();
  return `
    <button data-action="start" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md ${
      startEnabled
        ? 'bg-primary text-on-primary hover:bg-primary/90 active:scale-95 transition-all shadow-lg shadow-primary/20'
        : 'bg-surface-container-highest text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed'
    }" ${startEnabled ? '' : 'disabled'}>
      <span class="material-symbols-outlined text-[18px]">play_arrow</span>تشغيل
    </button>
    <button data-action="clear" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-surface-container-highest text-on-surface hover:bg-surface-variant active:scale-95 transition-all border border-outline-variant">
      <span class="material-symbols-outlined text-[18px]">delete</span>مسح
    </button>
    <button data-action="search" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-transparent text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">search</span>بحث
    </button>`;
}

function navActionsProcessing() {
  return `
    <button class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-primary/50 text-on-primary/70 cursor-not-allowed transition-all" disabled>
      <span class="material-symbols-outlined text-[18px] animate-spin">sync</span>جارِ المعالجة...
    </button>
    <button class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-surface-container-highest text-on-surface hover:bg-surface-variant active:scale-95 transition-all border border-outline-variant opacity-50 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">delete</span>مسح
    </button>
    <button class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-transparent text-on-surface-variant/50 border border-outline-variant/30 opacity-70 cursor-not-allowed" disabled>
      <span class="material-symbols-outlined text-[18px]">search</span>بحث
    </button>`;
}

function navActionsResults() {
  return `
    <button data-action="start" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-secondary-container text-on-secondary-container hover:bg-surface-container-highest active:scale-95 transition-all border border-outline-variant">
      <span class="material-symbols-outlined text-[18px]">play_arrow</span>تشغيل
    </button>
    <button data-action="clear" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-surface-container-highest text-on-surface hover:bg-surface-variant active:scale-95 transition-all border border-outline-variant">
      <span class="material-symbols-outlined text-[18px]">delete</span>مسح
    </button>
    <button data-action="search" class="flex items-center gap-xs px-md py-sm rounded font-label-md text-label-md bg-primary text-on-primary hover:bg-primary/90 active:scale-95 transition-all shadow-lg shadow-primary/20 relative">
      <span class="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-surface-container-low"></span>
      <span class="material-symbols-outlined text-[18px]">search</span>بحث
    </button>`;
}

// ---- Main content templates -------------------------------------------------

function dropZoneEmpty(slot, icon, title) {
  return `
    <div id="dropzone-${slot}" data-slot="${slot}" class="drop-zone bg-[#1e293b] elevation-card rounded-xl p-lg flex flex-col items-center justify-center min-h-[300px] cursor-pointer relative overflow-hidden group">
      <div class="absolute inset-sm border-dashed-custom rounded-lg pointer-events-none group-hover:border-primary/50 transition-colors"></div>
      <span class="material-symbols-outlined text-6xl text-on-surface-variant mb-md group-hover:text-primary transition-colors" style="font-variation-settings: 'wght' 200;">${icon}</span>
      <h3 class="font-headline-lg text-headline-lg text-on-surface mb-sm">${title}</h3>
      <p class="font-body-md text-body-md text-on-surface-variant text-center">اسحب الملف هنا أو انقر للتصفح</p>
      <div class="mt-lg">
        <button data-select-file="${slot}" class="bg-surface-container-high hover:bg-surface-variant text-on-surface font-label-md text-label-md px-lg py-sm rounded-full border border-outline-variant transition-colors flex items-center gap-sm">
          <span class="material-symbols-outlined text-sm">upload</span>اختيار ملف
        </button>
      </div>
    </div>`;
}

function dropZoneLoaded(slot, fileInfo, opts) {
  const disabledAttrs = opts && opts.disabled ? 'opacity-40 pointer-events-none' : '';
  return `
    <div id="dropzone-${slot}" data-slot="${slot}" class="drop-zone bg-[#1e293b] elevation-card rounded-xl p-lg flex flex-col items-center justify-center min-h-[300px] cursor-pointer relative overflow-hidden group ${disabledAttrs}">
      <div class="absolute top-2 left-2 z-20">
        <button data-action="remove-file" data-slot="${slot}" class="p-1 hover:bg-surface-variant rounded-full text-on-surface-variant transition-colors">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>
      <div class="flex flex-col items-center gap-md">
        <div class="relative">
          <span class="material-symbols-outlined text-6xl text-primary">table_chart</span>
          <div class="absolute -bottom-1 -right-1 bg-green-500 rounded-full p-0.5 border-2 border-[#1e293b]">
            <span class="material-symbols-outlined text-white text-[14px] font-bold">check</span>
          </div>
        </div>
        <div class="text-center">
          <h3 class="font-headline-md text-headline-md text-on-surface">${fileInfo.name}</h3>
          <p class="font-body-sm text-body-sm text-on-surface-variant">${fileInfo.rowCount != null ? fileInfo.rowCount + ' صف' : ''}</p>
        </div>
      </div>
    </div>`;
}

function outputPathRow() {
  return `
    <div class="bg-[#1e293b] elevation-card rounded-lg p-md flex flex-row-reverse justify-between items-center w-full">
      <div class="flex items-center gap-sm">
        <span class="material-symbols-outlined text-on-surface-variant">folder</span>
        <span class="font-body-md text-body-md text-on-surface-variant">مكان الحفظ:</span>
        <code id="output-path" class="font-mono text-sm bg-surface-container-lowest px-sm py-1 rounded text-primary-fixed-dim" dir="ltr">${State.outputDir}</code>
      </div>
      <button data-action="change-output" class="font-label-md text-label-md text-primary border border-[#334155] hover:bg-surface-container-high px-md py-sm rounded transition-colors flex items-center gap-xs">
        تغيير<span class="material-symbols-outlined text-[16px]">edit</span>
      </button>
    </div>`;
}

function advancedSettingsToggle() {
  return `
    <button data-action="toggle-advanced" class="flex items-center gap-xs text-on-surface-variant hover:text-on-surface transition-colors w-fit font-label-md text-label-md">
      <span class="material-symbols-outlined text-[18px]">settings</span>الإعدادات المتقدمة
      <span class="material-symbols-outlined text-[18px]">${State.advancedSettingsOpen ? 'expand_less' : 'expand_more'}</span>
    </button>
    ${State.advancedSettingsOpen ? advancedSettingsPanel() : ''}`;
}

function advancedSettingsPanel() {
  // No Stitch design exists for this panel yet (see
  // resources/design/INVENTORY.md) — plain/utilitarian styling using
  // the shared tokens, not a reproduction of a received screen.
  const mappingOptions = State.availableSecondaryMappings
    .map(
      (m) =>
        `<option value="${m.path}" ${m.path === State.secondaryMappingPath ? 'selected' : ''}>${m.name}</option>`
    )
    .join('');
  return `
    <div class="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg p-md flex flex-col gap-md text-body-sm">
      <label class="flex items-center justify-between gap-md">
        <span class="text-on-surface-variant">تعيين الملف الخارجي</span>
        <select data-action="secondary-mapping" class="bg-surface-container-lowest border border-outline-variant rounded px-sm py-1 text-on-surface">${mappingOptions}</select>
      </label>
      <label class="flex items-center justify-between gap-md">
        <span class="text-on-surface-variant">تضمين الصفوف الملغاة (لاغى)</span>
        <input type="checkbox" data-action="include-laghi" ${State.mergeOptions.includeLaghiRows ? 'checked' : ''}/>
      </label>
      <label class="flex items-center justify-between gap-md">
        <span class="text-on-surface-variant">تفعيل الترتيب المكاني</span>
        <input type="checkbox" data-action="enable-spatial-sort" ${State.mergeOptions.enableSpatialSort ? 'checked' : ''}/>
      </label>
    </div>`;
}

function mainContentEmpty() {
  return `
    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-lg rtl">
      ${dropZoneEmpty('secondary', 'description', 'الملف الخارجي')}
      ${dropZoneEmpty('base', 'folder_open', 'ملف المنظومة')}
    </div>
    <div class="w-full max-w-5xl flex flex-col gap-md">
      ${outputPathRow()}
      ${advancedSettingsToggle()}
    </div>`;
}

function mainContentFilesLoaded() {
  return `
    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-lg rtl">
      ${State.secondary ? dropZoneLoaded('secondary', State.secondary) : dropZoneEmpty('secondary', 'description', 'الملف الخارجي')}
      ${State.base ? dropZoneLoaded('base', State.base) : dropZoneEmpty('base', 'folder_open', 'ملف المنظومة')}
    </div>
    <div class="w-full max-w-5xl flex flex-col gap-md">
      ${outputPathRow()}
      ${advancedSettingsToggle()}
    </div>`;
}

function mainContentProcessing() {
  return `
    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-lg rtl">
      ${dropZoneLoaded('secondary', State.secondary, { disabled: true })}
      ${dropZoneLoaded('base', State.base, { disabled: true })}
    </div>
    <div class="w-full max-w-5xl flex flex-col gap-md">
      ${outputPathRow()}
      <div class="bg-[#1e293b] elevation-card rounded-lg p-md flex flex-col gap-sm w-full border-t-2 border-primary/30">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-sm">
            <span class="material-symbols-outlined text-primary animate-pulse">hourglass_empty</span>
            <span class="font-body-sm text-body-sm text-on-surface">${State.progress.message}</span>
          </div>
          <div class="flex items-center gap-md">
            <span class="font-mono text-sm text-primary">${State.progress.percent}%</span>
            <button data-action="cancel" class="text-error hover:bg-error/10 px-sm py-1 rounded transition-colors font-label-sm text-label-sm flex items-center gap-xs">
              <span class="material-symbols-outlined text-[14px]">close</span>إلغاء
            </button>
          </div>
        </div>
        <div class="w-full bg-surface-container-lowest h-2 rounded-full overflow-hidden">
          <div class="bg-primary h-full transition-all duration-500 ease-out" style="width: ${State.progress.percent}%"></div>
        </div>
      </div>
      ${advancedSettingsToggle()}
    </div>`;
}

function statCard(label, value, colorClass) {
  return `<div class="bg-surface-container-low border border-outline-variant/30 p-md rounded-lg flex flex-col gap-xs"><span class="text-on-surface-variant text-label-sm">${label}</span><span class="text-headline-md ${colorClass || 'text-on-surface'}">${value}</span></div>`;
}

function mainContentResults() {
  const stats = State.stats;
  const topBasins = stats.top_basins
    .map(([name, count]) => `<span class="text-body-md text-on-surface">${name} (${count})</span>`)
    .join('');
  return `
    <div class="w-full max-w-5xl bg-green-500/10 border border-green-500/30 rounded-lg p-md flex flex-row-reverse justify-between items-center">
      <div class="flex items-center gap-md">
        <div class="bg-green-500 rounded-full p-1 flex items-center justify-center"><span class="material-symbols-outlined text-white text-[20px] font-bold">check</span></div>
        <span class="font-headline-md text-on-surface">تم دمج ${stats.total_merged} حيازة بنجاح</span>
      </div>
      <button data-action="new-file" class="font-label-md text-label-md text-primary hover:text-primary/80 transition-colors flex items-center gap-xs">معالجة ملف جديد<span class="material-symbols-outlined text-[18px]">add</span></button>
    </div>
    <div class="w-full max-w-5xl grid grid-cols-2 md:grid-cols-5 gap-md rtl">
      ${statCard('إجمالي الحيازات المدمجة', stats.total_merged)}
      ${statCard('بيانات كاملة', stats.complete_rows, 'text-green-500')}
      ${statCard('بيانات ناقصة', stats.incomplete_rows, 'text-tertiary')}
      ${statCard('مع رقم قومي', stats.with_national_id)}
      ${statCard('بدون رقم قومي', stats.without_national_id)}
      ${statCard('صفوف «لاغى» مستبعدة', stats.excluded_laghi_count, 'text-on-surface-variant')}
      ${statCard('إجمالي المساحة', stats.total_feddan.toLocaleString('en-US', { maximumFractionDigits: 1 }) + ' فدان')}
      ${statCard('عدد الأحواض', stats.distinct_basin_count)}
      ${statCard('قطع لم يُحدَّد ترتيبها', stats.unplaced_count, 'text-tertiary')}
      ${statCard('زمن المعالجة', stats.elapsed_seconds.toFixed(1) + ' ثانية', 'text-primary')}
      <div class="col-span-2 md:col-span-5 bg-surface-container-low border border-outline-variant/30 p-md rounded-lg flex flex-row-reverse justify-between items-center">
        <span class="text-on-surface-variant text-label-sm">أكبر 3 أحواض:</span>
        <div class="flex gap-lg">${topBasins}</div>
      </div>
    </div>
    <div class="w-full max-w-5xl flex flex-col gap-md">
      <div class="bg-[#1e293b] elevation-card rounded-lg p-md flex flex-row-reverse justify-between items-center w-full">
        <div class="flex items-center gap-sm">
          <span class="material-symbols-outlined text-on-surface-variant">folder</span>
          <span class="font-body-md text-body-md text-on-surface-variant">مكان الحفظ:</span>
          <code class="font-mono text-sm bg-surface-container-lowest px-sm py-1 rounded text-primary-fixed-dim" dir="ltr">${State.outputDir}</code>
        </div>
        <div class="flex gap-sm">
          <button data-action="open-file" class="font-label-md text-label-md text-on-primary bg-primary hover:bg-primary/90 px-md py-sm rounded transition-colors flex items-center gap-xs"><span class="material-symbols-outlined text-[18px]">description</span>فتح الملف</button>
          <button data-action="open-folder" class="font-label-md text-label-md text-on-surface border border-outline-variant hover:bg-surface-container-high px-md py-sm rounded transition-colors flex items-center gap-xs"><span class="material-symbols-outlined text-[18px]">folder_open</span>فتح المجلد</button>
          <button data-action="clear-results" class="font-label-md text-label-md text-on-surface-variant/70 hover:text-error transition-colors flex items-center gap-xs px-sm">مسح النتائج<span class="material-symbols-outlined text-[18px]">delete_sweep</span></button>
        </div>
      </div>
      ${advancedSettingsToggle()}
    </div>`;
}

// ---- Render ------------------------------------------------------------------

function render() {
  const nav = document.getElementById('nav-actions');
  const main = document.getElementById('main-content');

  const navTemplates = {
    empty: navActionsEmpty,
    files_loaded: navActionsFilesLoaded,
    processing: navActionsProcessing,
    results: navActionsResults,
  };
  const mainTemplates = {
    empty: mainContentEmpty,
    files_loaded: mainContentFilesLoaded,
    processing: mainContentProcessing,
    results: mainContentResults,
  };

  nav.innerHTML = navTemplates[State.screen]();
  main.innerHTML = mainTemplates[State.screen]();
  wireDropZones();
}

function appendLog(text) {
  State.logEntries.push(text);
  const content = document.getElementById('log-panel-content');
  if (content) {
    const line = document.createElement('div');
    line.textContent = text;
    content.appendChild(line);
    const panel = document.getElementById('log-panel');
    panel.scrollTop = panel.scrollHeight;
  }
}

function wireLogToggle() {
  const button = document.getElementById('btn-log-toggle');
  const panel = document.getElementById('log-panel');
  button.addEventListener('click', () => {
    panel.classList.toggle('hidden');
  });

  const copyButton = document.getElementById('btn-copy-log');
  copyButton.addEventListener('click', async () => {
    await navigator.clipboard.writeText(State.logEntries.join('\n'));
    const original = copyButton.innerHTML;
    copyButton.innerHTML = '<span class="material-symbols-outlined text-[14px]">check</span>تم النسخ';
    setTimeout(() => {
      copyButton.innerHTML = original;
    }, 1200);
  });
}

// ---- Event handling (delegation) ---------------------------------------------

async function onSelectFile(slot) {
  const result = await Bridge.call('select_file', slot);
  if (!result.ok) {
    appendLog(result.error);
    return;
  }
  if (result.value.cancelled) {
    return;
  }
  if (result.value.error) {
    appendLog(result.value.error);
    return;
  }
  applySelectedFile(slot, result.value);
}

function applySelectedFile(slot, fileInfo) {
  const entry = { path: fileInfo.path, name: fileInfo.name, rowCount: fileInfo.row_count };
  if (slot === 'base') {
    State.base = entry;
  } else {
    State.secondary = entry;
  }
  if (State.screen === 'empty' || State.screen === 'files_loaded') {
    State.screen = 'files_loaded';
  }
  render();
}

function wireDropZones() {
  document.querySelectorAll('[data-select-file]').forEach((button) => {
    button.addEventListener('click', () => onSelectFile(button.dataset.selectFile));
  });
  document.querySelectorAll('.drop-zone[data-slot]').forEach((zone) => {
    zone.addEventListener('dragover', (event) => event.preventDefault());
    zone.addEventListener('drop', async (event) => {
      event.preventDefault();
      const slot = zone.dataset.slot;
      const files = event.dataTransfer.files;
      if (!files || files.length === 0) {
        return;
      }
      // pywebview exposes the real filesystem path via file.path; the
      // browser File object alone doesn't carry one.
      const filePath = files[0].path || files[0].name;
      const result = await Bridge.call('handle_dropped_file', slot, filePath);
      if (!result.ok) {
        appendLog(result.error);
        return;
      }
      if (!result.value.valid) {
        appendLog(result.value.error);
        return;
      }
      applySelectedFile(slot, result.value);
    });
  });
}

async function onStart() {
  if (!canStart()) {
    return;
  }
  State.screen = 'processing';
  State.progress = { percent: 0, message: 'بدء المعالجة...' };
  render();
  const result = await Bridge.call(
    'start_processing',
    State.base.path,
    State.secondary.path,
    State.secondaryMappingPath,
    State.outputDir,
    State.mergeOptions.includeLaghiRows,
    State.mergeOptions.enableSpatialSort
  );
  if (!result.ok) {
    appendLog(result.error);
    State.screen = 'files_loaded';
    render();
  }
}

async function onClear() {
  await Bridge.call('clear_files');
  State.base = null;
  State.secondary = null;
  State.screen = 'empty';
  State.stats = null;
  render();
}

function onRemoveFile(slot) {
  if (slot === 'base') {
    State.base = null;
  } else {
    State.secondary = null;
  }
  State.screen = State.base || State.secondary ? 'files_loaded' : 'empty';
  render();
}

async function onChangeOutput() {
  const result = await Bridge.call('choose_output_folder');
  if (result.ok && result.value) {
    State.outputDir = result.value;
    render();
  }
}

async function onOpenFolder() {
  await Bridge.call('open_output_folder');
}

async function onOpenFile() {
  await Bridge.call('open_output_file');
}

function onToggleAdvanced() {
  State.advancedSettingsOpen = !State.advancedSettingsOpen;
  render();
}

async function onCancel() {
  await Bridge.call('cancel_processing');
}

function onNewFile() {
  State.screen = 'empty';
  State.base = null;
  State.secondary = null;
  State.stats = null;
  render();
}

function onClearResults() {
  State.screen = 'empty';
  State.base = null;
  State.secondary = null;
  State.stats = null;
  render();
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) {
    return;
  }
  const action = button.dataset.action;
  const handlers = {
    start: onStart,
    clear: onClear,
    search: () => Bridge.call('open_search_window'),
    'remove-file': () => onRemoveFile(button.dataset.slot),
    'change-output': onChangeOutput,
    'open-folder': onOpenFolder,
    'open-file': onOpenFile,
    'toggle-advanced': onToggleAdvanced,
    cancel: onCancel,
    'new-file': onNewFile,
    'clear-results': onClearResults,
  };
  const handler = handlers[action];
  if (handler) {
    handler();
  }
});

document.addEventListener('change', (event) => {
  const el = event.target.closest('[data-action]');
  if (!el) {
    return;
  }
  if (el.dataset.action === 'include-laghi') {
    State.mergeOptions.includeLaghiRows = el.checked;
  } else if (el.dataset.action === 'enable-spatial-sort') {
    State.mergeOptions.enableSpatialSort = el.checked;
  } else if (el.dataset.action === 'secondary-mapping') {
    State.secondaryMappingPath = el.value;
  }
});

function onProgressUpdate(payload) {
  State.progress = { percent: payload.percent, message: payload.message };
  if (State.screen === 'processing') {
    render();
  }
}

function onMergeComplete(stats) {
  State.stats = stats;
  State.screen = 'results';
  render();
}

function onMergeFailed(message) {
  appendLog(message);
  State.screen = 'files_loaded';
  render();
}

function onLogMessage(payload) {
  appendLog(`[${payload.level}] ${payload.message}`);
}

async function loadAvailableMappings() {
  const result = await Bridge.call('list_secondary_mappings');
  if (result.ok) {
    State.availableSecondaryMappings = result.value;
    if (!State.secondaryMappingPath && result.value.length > 0) {
      const defaultEntry = result.value.find((m) => m.is_default) || result.value[0];
      State.secondaryMappingPath = defaultEntry.path;
    }
  }
}

async function loadOutputDir() {
  const result = await Bridge.call('get_output_dir');
  if (result.ok && result.value) {
    State.outputDir = result.value;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  Bridge.onPush('onProgressUpdate', onProgressUpdate);
  Bridge.onPush('onMergeComplete', onMergeComplete);
  Bridge.onPush('onMergeFailed', onMergeFailed);
  Bridge.onPush('onLogMessage', onLogMessage);
  wireLogToggle();
  await Promise.all([loadAvailableMappings(), loadOutputDir()]);
  render();
});
