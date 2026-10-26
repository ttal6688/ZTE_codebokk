"""Replace only the four percentage figures in existing MD/DOCX reports."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/feedback_percentage_20261026'
VERSION = 'legend_manual_v4'
OLD_VERSION = 'legend_best_v3'
NAME = '反馈开销占比_AP数.png'
REPORTS = {
    'single': 'UPA单流400位置正式实验报告',
    'dual': 'UPA单极化双流400位置完整实验报告',
}


def update():
    records = []
    for stream, title in REPORTS.items():
        md = ROOT / 'docs' / (title + '.md')
        content = md.read_text(encoding='utf-8')
        replacements = {}
        for branch in ('CPU', 'UE'):
            base = f'../results/{OUT.name}/figures/{stream}/{branch}/'
            old = base + OLD_VERSION + '/' + NAME
            new = base + VERSION + '/' + NAME
            assert content.count(old) == 1, f'Expected one old image reference: {old}'
            content = content.replace(old, new)
            old_bytes = (md.parent / old).read_bytes()
            new_bytes = (md.parent / new).read_bytes()
            replacements[sha256(old_bytes).hexdigest()] = new_bytes

        # Preserve all XML, formatting and unrelated media; replace two PNG parts.
        docx = md.with_suffix('.docx')
        temporary = docx.with_suffix('.legend.tmp')
        replaced = 0
        with ZipFile(docx) as source, ZipFile(temporary, 'w') as target:
            target.comment = source.comment
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename.startswith('word/media/'):
                    replacement = replacements.get(sha256(payload).hexdigest())
                    if replacement is not None:
                        payload = replacement
                        replaced += 1
                target.writestr(info, payload)
        assert replaced == 2, f'Expected exactly two percentage images in {docx.name}'
        temporary.replace(docx)
        md.write_text(content, encoding='utf-8')
        records.append({'report': title, 'updated_percentage_images': replaced})

    archive = OUT / '反馈开销百分比四图_PPT用_手动避让版.zip'
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as target:
        for stream, label in [('single', '单流'), ('dual', '双流')]:
            for branch in ('CPU', 'UE'):
                png = OUT / 'figures' / stream / branch / VERSION / NAME
                target.write(png, f'{label}_{branch}_反馈开销百分比.png')
        target.write(OUT / 'README.md', '计算口径与图例更新说明.md')

    manifest = json.loads((OUT / 'source_SHA256.json').read_text(encoding='utf-8'))
    paths = [entry['path'] for entry in manifest['files']]
    paths = list(dict.fromkeys(paths + [Path(__file__).name, 'report_figure_style.py']))
    manifest['files'] = [dict(path=path, sha256_LF=sha256(
        (ROOT / path).read_text(encoding='utf-8').replace('\r\n', '\n').encode('utf-8')
    ).hexdigest()) for path in paths]
    (OUT / 'source_SHA256.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    audit = dict(figure_version=VERSION, reports=records,
                 only_percentage_figure_media_replaced=True,
                 simulation_rerun=False, Word_inspected=False)
    (OUT / 'manual_legend_update.json').write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Updated four MD image references, four Word image parts and PPT image archive.')


if __name__ == '__main__':
    update()
