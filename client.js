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
  let viewPromise;
  let request = 0;

  async function loadModel() {
    const current = ++request;
    const model = viewer.dataset.model;
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
      if (current !== 1 || view.loadedUrl !== model) await view.setModel(model);
      if (current !== request) return;
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

    function selectShoe() {
      const option = shoes?.querySelector(`input[value="${selected}"]`);
      if (option) option.checked = true;
      for (const panel of document.querySelectorAll('[data-shoe-panel]')) {
        panel.hidden = panel.dataset.shoePanel !== selected;
      }
      if (kind === 'assembly') {
        const mode = exploded.checked ? 'exploded' : 'assembled';
        viewer.dataset.model = option.dataset[mode + 'Model'];
        poster.src = option.dataset[mode + 'Poster'];
        poster.alt = `${option.dataset.label} on the sanding plane, ${mode}`;
      }
      const url = new URL(location.href);
      url.searchParams.set('shoe', selected);
      if (exploded) url.searchParams.set('view', exploded.checked ? 'exploded' : 'assembled');
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
        selectShoe();
        loadModel();
      });
    }
    exploded?.addEventListener('change', () => { selectShoe(); loadModel(); });
  }
  retryButton.addEventListener('click', loadModel);
  loadModel();
}
