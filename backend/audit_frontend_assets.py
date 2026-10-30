import os
import glob
from html.parser import HTMLParser

class AssetChecker(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.broken = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        target = None
        if tag == 'link' and attr_dict.get('rel') == 'stylesheet':
            target = attr_dict.get('href')
        elif tag == 'script' and 'src' in attr_dict:
            target = attr_dict.get('src')
        elif tag == 'img' and 'src' in attr_dict:
            target = attr_dict.get('src')

        if target and not target.startswith(('http:', 'https:', '#', 'mailto:', 'data:')):
            clean = target.split('?')[0].split('#')[0]
            if clean and not os.path.exists(clean):
                self.broken.append((self.filename, tag, target))

broken_all = []
for h in glob.glob("*.html"):
    with open(h, 'r', encoding='utf-8') as f:
        parser = AssetChecker(h)
        parser.feed(f.read())
        broken_all.extend(parser.broken)

print(f"Total HTML files checked: {len(glob.glob('*.html'))}")
print(f"Total broken asset references: {len(broken_all)}")
for b in broken_all:
    print(f"  {b[0]} -> <{b[1]}> {b[2]}")
