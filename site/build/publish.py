"""Validate the committed source, push main, and publish its static Pages branch."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import build


def git(*args, cwd=build.ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def publish():
    if git('branch', '--show-current') != 'main':
        raise SystemExit('Publish from main after committing the accepted changes.')
    build.build()
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'site/build', '-p', 'test_*.py'], cwd=build.ROOT, check=True)
    manifest = json.loads((build.OUT / 'publication.json').read_text())
    paths = manifest['files'] + [str(p.relative_to(build.ROOT)) for p in build.SITE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    tracked = set(git('ls-files').splitlines())
    missing = sorted(set(paths) - tracked)
    if missing:
        raise SystemExit('Commit these published inputs first:\n' + '\n'.join(missing))
    if git('diff', 'HEAD', '--name-only', '--', *paths):
        raise SystemExit('Commit changes to the site and project artifacts before publishing.')
    revision = git('rev-parse', 'HEAD')
    (build.OUT / 'build-info.json').write_text(json.dumps({'sourceRevision': revision}) + '\n')
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=build.ROOT, check=True)
    remote = git('remote', 'get-url', 'origin')
    exists = bool(git('ls-remote', '--heads', 'origin', 'gh-pages'))
    with tempfile.TemporaryDirectory(prefix='3d-library-pages-') as directory:
        checkout = Path(directory) / 'pages'
        if exists:
            subprocess.run(['git', 'clone', '--quiet', '--depth=1', '--single-branch', '--branch=gh-pages', remote, str(checkout)], check=True)
            for path in checkout.iterdir():
                if path.name != '.git':
                    shutil.rmtree(path) if path.is_dir() else path.unlink()
        else:
            checkout.mkdir()
            git('init', '--quiet', '-b', 'gh-pages', cwd=checkout)
            git('remote', 'add', 'origin', remote, cwd=checkout)
        for key in ('user.name', 'user.email'):
            git('config', key, git('config', key), cwd=checkout)
        shutil.copytree(build.OUT, checkout, dirs_exist_ok=True)
        git('add', '--all', cwd=checkout)
        if not git('diff', '--cached', '--name-only', cwd=checkout):
            print('Pages already matches the current source.')
            return
        git('commit', '--quiet', '-m', f'Publish model library from {revision[:8]}', cwd=checkout)
        subprocess.run(['git', 'push', 'origin', 'gh-pages'], cwd=checkout, check=True)
        print(f'Published source {revision} to gh-pages. Verify the Pages deployment before claiming it is live.')


if __name__ == '__main__':
    publish()
