"""Local-only thumbnail generator: python3 site/build/previews.py, then open its URL."""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, urlsplit
import build

PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Generate model thumbnails</title>
<h1>Model thumbnails</h1><button id="generate">Generate thumbnails</button><p role="status">Ready</p>
<canvas width="1100" height="770" style="width:770px;height:539px"></canvas>
<script type="module">
import { createModelView } from '/viewer.js';
document.querySelector('button').onclick = async event => {
  event.target.disabled = true;
  const status = document.querySelector('[role=status]');
  const canvas = document.querySelector('canvas');
  try {
    const items = await (await fetch('/_preview-items')).json();
    for (const [index, item] of items.entries()) {
      status.textContent = `${index + 1}/${items.length}: ${item.preview}`;
      const view = await createModelView(canvas, item.model, { width:1100, height:770, thumbnail:true });
      const png = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      const response = await fetch('/_preview-image/' + encodeURIComponent(item.preview), {method:'POST',body:png});
      view.dispose();
      if (!response.ok) throw new Error('Could not save ' + item.preview);
    }
    status.textContent = `Saved ${items.length} thumbnails.`;
  } catch (error) { status.textContent = error.message; }
  event.target.disabled = false;
};
</script></html>'''


def main():
    projects = json.loads((build.SITE / 'catalog.json').read_text())
    items = {view['preview']: '/' + quote(build.artifact(view['previewModel']))
             for project in projects for view in build.project_views(project)}
    for project in projects:
        for shoe in project.get('assemblyShoes', []):
            for mode in ('assembly', 'exploded'):
                preview = shoe[mode]
                items[preview['preview']] = '/' + quote(build.artifact(preview['model']))

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=build.OUT, **kwargs)

        def do_GET(self):
            route = urlsplit(self.path).path
            if route not in {'/_previews', '/_preview-items'}:
                return super().do_GET()
            data = PAGE.encode() if route == '/_previews' else json.dumps([
                dict(preview=preview, model=model) for preview, model in items.items()]).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html' if route == '/_previews' else 'application/json')
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            from urllib.parse import unquote
            name = unquote(self.path.removeprefix('/_preview-image/'))
            size = int(self.headers.get('Content-Length', 0))
            if (self.headers.get('Origin') != 'http://127.0.0.1:8775'
                    or name not in items or not 8 < size < 5_000_000):
                return self.send_error(400)
            data = self.rfile.read(size)
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):
                return self.send_error(400)
            (build.SITE / name).write_bytes(data)
            self.send_response(204)
            self.end_headers()

    print('Open http://127.0.0.1:8775/_previews', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8775), Handler).serve_forever()


if __name__ == '__main__':
    main()
