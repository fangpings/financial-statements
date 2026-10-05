#!/usr/bin/env python3
"""Verify generated Pages URLs resolve inside the build output (no network)."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / '.vitepress' / 'dist'
BASE = '/financial-statements/'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.urls.append(value)


def main():
    pages = sorted(DIST.rglob('*.html'))
    assert pages, 'Build the site first: npm run build'
    errors = []
    count = 0
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        origin = 'https://example.test' + BASE + page.relative_to(DIST).as_posix()
        for href in parser.urls:
            url = urlsplit(urljoin(origin, href))
            if url.scheme not in ('http', 'https') or url.netloc != 'example.test':
                continue
            path = unquote(url.path)
            if not path.startswith(BASE):
                errors.append(f'{page.name}: outside Pages base: {href}')
                continue
            target = DIST / path[len(BASE):]
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                errors.append(f'{page.name}: missing target: {href}')
            count += 1
    assert (DIST / 'index.html').is_file(), 'Missing homepage'
    assert len(list(DIST.glob('[0-9][0-9]-*.html'))) == 36, 'Missing chapters'
    assert len(list(DIST.glob('appendix-*.html'))) == 6, 'Missing appendices'
    assert (DIST / 'data/index.html').is_file(), 'Missing data guide'
    assert (DIST / 'reviews/index.html').is_file(), 'Missing reviews'
    assert not errors, '\n'.join(errors)
    print(f'PASS: {len(pages)} rendered pages; {count} local URLs resolve under {BASE}')


if __name__ == '__main__':
    main()
