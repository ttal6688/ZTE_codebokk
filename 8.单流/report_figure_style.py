"""Version every current report image when the shared legend style changes."""
from pathlib import Path, PurePosixPath
import json,re
ROOT=Path(__file__).resolve().parent
STYLE=json.loads((ROOT/'report_figure_style.json').read_text(encoding='utf-8'))
VERSION=STYLE['image_version']

def version_legend_images(content):
    def replace(match):
        path=PurePosixPath(match.group(2))
        if path.parent.name==VERSION:return match.group(0)
        return match.group(1)+str(path.parent/VERSION/path.name)+match.group(3)
    return re.sub(r'(!\[[^\]]*\]\()([^\n)]+\.png)(\))',replace,content)
