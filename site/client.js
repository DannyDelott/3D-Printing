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

const loadButton = document.querySelector('#load-model');
if (loadButton) {
  loadButton.hidden = false;
  loadButton.addEventListener('click', async () => {
    const status = document.querySelector('#viewer-status');
    loadButton.disabled = true;
    status.textContent = 'Loading the model…';
    try {
      const { mountViewer } = await import('./viewer.js');
      await mountViewer(document.querySelector('#model-viewer'), document.querySelector('.viewer').dataset.model);
      document.querySelector('#model-poster').hidden = true;
      for (const button of document.querySelectorAll('.viewer-controls button')) button.hidden = false;
      loadButton.hidden = true;
      status.textContent = 'Drag or use arrow keys to orbit · scroll to zoom';
    } catch (error) {
      document.querySelector('#model-viewer').hidden = true;
      status.textContent = '3D preview unavailable. The image and downloads are still available.';
      loadButton.disabled = false;
      loadButton.textContent = 'Retry 3D preview';
      console.warn(error);
    }
  });
}
