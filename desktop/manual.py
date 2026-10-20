import base64
from pathlib import Path
import markdown
from . import __version__
from .config import data_dir

ROOT = Path(__file__).resolve().parents[1]
STYLE = '''body{font:17px/1.65 system-ui,sans-serif;color:#203047;max-width:1040px;margin:32px auto;padding:0 24px;background:#fff}
h1,h2,h3{line-height:1.25;color:#12293d}h1{font-size:36px}h2{border-top:1px solid #d9e3ec;padding-top:25px;margin-top:35px}
a{color:#12644e}img{max-width:100%;height:auto;border-radius:8px;border:1px solid #cbd6e1}table{border-collapse:collapse;width:100%;font-size:15px}
td,th{border:1px solid #cbd6e1;padding:8px;text-align:left}th{background:#edf4f7}code{background:#edf2f6;padding:2px 5px;border-radius:3px}
pre{overflow:auto;padding:14px;background:#edf2f6}blockquote{border-left:4px solid #26a675;margin-left:0;padding:8px 18px;background:#f0faf6}
.toc{background:#f5f8fa;padding:14px 25px;border-radius:8px}li{margin:5px 0}@media print{body{font-size:11pt;margin:0;max-width:none}h2{break-before:auto}img{max-height:145mm;object-fit:contain}.toc{break-after:page}}'''

def render(destination=None):
    source = ROOT / 'docs/manual.md'
    text = source.read_text(encoding='utf8').replace('{{VERSION}}', __version__)
    for image in (ROOT / 'docs/manual-assets').glob('*.png'):
        data = base64.b64encode(image.read_bytes()).decode('ascii')
        text = text.replace('manual-assets/' + image.name, 'data:image/png;base64,' + data)
    body = markdown.markdown(text, extensions=['tables', 'toc', 'fenced_code'], extension_configs={'toc': {'toc_depth': '2-3'}})
    document = '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manual Guitar Lab '+__version__+'</title><style>'+STYLE+'</style><body>'+body+'</body></html>'
    path = Path(destination) if destination else data_dir() / 'Manual-GuitarLab.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding='utf8')
    return path
