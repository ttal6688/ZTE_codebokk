"""Version every current report image when the shared legend style changes."""
from pathlib import Path, PurePosixPath
import json,re
ROOT=Path(__file__).resolve().parent
STYLE=json.loads((ROOT/'report_figure_style.json').read_text(encoding='utf-8'))
VERSION=STYLE['image_version']

def version_legend_images(content):
    def replace(match):
        path=PurePosixPath(match.group(2))
        version=STYLE.get('feedback_percentage_image_version',VERSION) if 'feedback_percentage_20261026' in path.parts else VERSION
        if path.parent.name==version:return match.group(0)
        parent=path.parent.parent if re.fullmatch(r'legend_(?:font\d+|best|manual)_v\d+',path.parent.name) else path.parent
        return match.group(1)+str(parent/version/path.name)+match.group(3)
    return re.sub(r'(!\[[^\]]*\]\()([^\n)]+\.png)(\))',replace,content)
