const search = document.querySelector('#search');
if (search) {
  document.querySelector('#filters').hidden = false;
  const buttons = [...document.querySelectorAll('button[data-category]')];
  const rows = [...document.querySelectorAll('.project-row')];
  const params = new URLSearchParams(location.search);
  let category = params.get('category') || 'All projects';
  if (!buttons.some(button => button.dataset.category === category)) category = 'All projects';
  search.value = params.get('q') || '';

  function filter() {
    const query = search.value.trim().toLowerCase();
    let count = 0;
    for (const row of rows) {
      row.hidden = !(category === 'All projects' || row.dataset.category === category) || !row.dataset.search.includes(query);
      if (!row.hidden) count++;
    }
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.category === category));
    document.querySelector('#empty').hidden = count !== 0;
    const url = new URL(location.href);
    query ? url.searchParams.set('q', search.value) : url.searchParams.delete('q');
    category === 'All projects' ? url.searchParams.delete('category') : url.searchParams.set('category', category);
    history.replaceState(null, '', url);
  }
  search.addEventListener('input', filter);
  for (const button of buttons) button.addEventListener('click', () => { category = button.dataset.category; filter(); });
  document.querySelector('#clear-search').addEventListener('click', () => {
    search.value = '';
    category = 'All projects';
    filter();
    search.focus();
  });
  filter();
}

const viewer = document.querySelector('.viewer');
if (viewer) {
  const retryButton = document.querySelector('#retry-model');
  const canvas = document.querySelector('#model-viewer');
  const poster = document.querySelector('#model-poster');
  const shoes = document.querySelector('#assembly-shoes');
  const navigation = document.querySelector('.plane-navigation');
  const exploded = document.querySelector('#exploded-view');
  const status = document.querySelector('#viewer-status');
  const prints = [...document.querySelectorAll('[data-print]')];
  const printLabel = document.querySelector('#active-print-label');
  let displayedPrint = null;
  let viewPromise;
  let request = 0;

  async function loadModel() {
    const current = ++request;
    const model = viewer.dataset.model;
    const activePrint = prints.find(print => print.open)?.dataset.print || null;
    retryButton.hidden = true;
    canvas.hidden = true;
    poster.hidden = false;
    viewer.setAttribute('aria-busy', 'true');
    status.textContent = 'Loading the model…';
    try {
      const { mountViewer } = await import(new URL(viewer.dataset.viewer, document.baseURI).href);
      if (current !== request) return;
      viewPromise ??= mountViewer(canvas, model).catch(error => {
        viewPromise = null;
        throw error;
      });
      const view = await viewPromise;
      if (current !== request) return;
      // Keep dimensions available while refitting. aria-busy hides the canvas
      // until the new geometry is ready, while the poster remains visible.
      canvas.hidden = false;
      if (current !== 1 || view.loadedUrl !== model) await view.setModel(model, { refit: displayedPrint !== activePrint });
      if (current !== request) return;
      displayedPrint = activePrint;
      canvas.hidden = false;
      poster.hidden = true;
      for (const button of document.querySelectorAll('.viewer-controls button:not(#retry-model)')) button.hidden = false;
      status.textContent = '';
    } catch (error) {
      if (current !== request) return;
      canvas.hidden = true;
      poster.hidden = false;
      status.textContent = '3D preview unavailable. The image and downloads are still available.';
      retryButton.hidden = false;
      console.warn(error);
    } finally {
      if (current === request) viewer.setAttribute('aria-busy', 'false');
    }
  }

  if (navigation) {
    const params = new URLSearchParams(location.search);
    const kind = navigation.dataset.part;
    const defaultShoe = navigation.dataset.defaultShoe;
    const ids = [...navigation.querySelectorAll('[data-shoe-panel]')].map(panel => panel.dataset.shoePanel);
    // Component URLs identify their own profile; shared parts retain the query's selection.
    let selected = ['shoe', 'coupon', 'plate'].includes(kind) ? defaultShoe : params.get('shoe');
    if (!ids.includes(selected)) selected = defaultShoe;
    if (exploded && params.has('view')) exploded.checked = params.get('view') === 'exploded';

    const initialPrint = prints.find(print => print.dataset.print === params.get('print'));
    if (initialPrint) {
      initialPrint.open = true;
      if (ids.includes(initialPrint.dataset.print)) selected = initialPrint.dataset.print;
    }

    function selectShoe() {
      const option = shoes?.querySelector(`input[value="${selected}"]`);
      if (option) option.checked = true;
      for (const panel of document.querySelectorAll('[data-shoe-panel]')) {
        panel.hidden = panel.dataset.shoePanel !== selected;
      }
      if (kind === 'assembly') {
        const mode = exploded.checked ? 'exploded' : 'assembled';
        const active = prints.find(print => print.open);
        viewer.dataset.model = active?.dataset.model || option.dataset[mode + 'Model'];
        poster.src = active?.dataset.poster || option.dataset[mode + 'Poster'];
        poster.alt = active ? active.dataset.label : `${option.dataset.label} on the sanding plane, ${mode}`;
        printLabel.hidden = !active;
        printLabel.textContent = active ? active.dataset.label : '';
        document.querySelector('.assembly-description').hidden = !!active;
      }
      const url = new URL(location.href);
      url.searchParams.set('shoe', selected);
      if (exploded) url.searchParams.set('view', exploded.checked ? 'exploded' : 'assembled');
      const active = prints.find(print => print.open);
      if (active) url.searchParams.set('print', active.dataset.print);
      else url.searchParams.delete('print');
      history.replaceState(null, '', url);
      for (const link of navigation.querySelectorAll('[data-part="assembly"]')) {
        const target = new URL(link.href);
        if (exploded?.checked) target.searchParams.set('view', 'exploded');
        else target.searchParams.delete('view');
        link.href = target;
      }
    }
    selectShoe();
    if (shoes) {
      shoes.closest('.assembly-controls').hidden = false;
      shoes.addEventListener('change', () => {
        const option = shoes.querySelector('input:checked');
        if (kind !== 'assembly') {
          location.assign(option.dataset.destination);
          return;
        }
        selected = option.value;
        for (const print of prints) print.open = false;
        selectShoe();
        loadModel();
      });
    }
    exploded?.addEventListener('change', () => {
      for (const print of prints) print.open = false;
      selectShoe();
      loadModel();
    });
    for (const print of prints) print.addEventListener('toggle', () => {
      if (print.open) {
        for (const other of prints) if (other !== print) other.open = false;
        if (ids.includes(print.dataset.print)) selected = print.dataset.print;
      }
      selectShoe();
      if (viewer.dataset.model !== canvas.dataset.model) loadModel();
    });
  }
  retryButton.addEventListener('click', loadModel);
  loadModel();
}
