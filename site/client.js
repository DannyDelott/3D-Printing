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
  const select = document.querySelector('#assembly-shoe');
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

  if (select) {
    function selectShoe() {
      const option = select.selectedOptions[0];
      viewer.dataset.model = option.dataset.model;
      poster.src = option.dataset.poster;
      poster.alt = `${option.textContent} on the sanding plane`;
      document.querySelector('#shoe-details').href = option.dataset.details;
      const url = new URL(location.href);
      url.searchParams.set('shoe', option.value);
      history.replaceState(null, '', url);
      for (const link of document.querySelectorAll('[data-assembly-link]')) {
        const target = new URL(link.href);
        target.searchParams.set('shoe', option.value);
        link.href = target;
      }
    }
    const selected = new URLSearchParams(location.search).get('shoe');
    if ([...select.options].some(option => option.value === selected)) select.value = selected;
    selectShoe();
    select.closest('.assembly-controls').hidden = false;
    select.addEventListener('change', () => { selectShoe(); loadModel(); });
  }
  retryButton.addEventListener('click', loadModel);
  loadModel();
}
