"""Version current report figures and replace their embedded Word images only."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import json
import os
import re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/report_legend_best_20261026'
STYLE = json.loads((ROOT / 'report_figure_style.json').read_text(encoding='utf-8'))
REPORTS = ['UPA单流400位置正式实验报告', 'UPA单极化双流400位置完整实验报告']
IMAGE = re.compile(r'!\[[^\]]*\]\(([^)]+\.png)\)')


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    OUT.mkdir(exist_ok=True)
    figures = {}
    reports = []
    for title in REPORTS:
        md = ROOT / 'docs' / (title + '.md')
        references = []
        for old in IMAGE.findall(md.read_text(encoding='utf-8')):
            source = (md.parent / old).resolve()
            assert source.is_relative_to(ROOT) and source.with_suffix('.fig').is_file()
            parent = source.parent
            if re.fullmatch(r'legend_(?:font\d+|best)_v\d+', parent.name):
                parent = parent.parent
            if parent.name == 'compact_legend_v2':
                parent = parent.parent
            target = parent / STYLE['image_version'] / source.name
            assert source != target, 'This migration has already been applied.'
            figures[source.as_posix()] = dict(
                source=source.relative_to(ROOT).as_posix(),
                target=target.relative_to(ROOT).as_posix())
            references.append(dict(old=old, new=Path(os.path.relpath(target, md.parent)).as_posix()))
        reports.append(dict(title=title, references=references))
    write_json(OUT / 'figure_manifest.json', dict(style=STYLE, reports=reports,
               unique_figures=len(figures), figures=list(figures.values())))
    print(f'Prepared {len(figures)} figures and {sum(len(r["references"]) for r in reports)} report references.')


def integrate():
    manifest = json.loads((OUT / 'figure_manifest.json').read_text(encoding='utf-8'))
    updates = []
    for report in manifest['reports']:
        md = ROOT / 'docs' / (report['title'] + '.md')
        content = md.read_text(encoding='utf-8')
        replacements = {}
        for ref in report['references']:
            old = (md.parent / ref['old']).resolve()
            new = (md.parent / ref['new']).resolve()
            old_hash = sha256(old.read_bytes()).hexdigest()
            replacements.setdefault(old_hash, new.read_bytes())
            content = content.replace('](' + ref['old'] + ')', '](' + ref['new'] + ')')
        # Preserve every XML part, layout and all unrelated media.
        docx = md.with_suffix('.docx')
        temporary = docx.with_suffix('.best.tmp')
        replaced = 0
        with ZipFile(docx) as source, ZipFile(temporary, 'w') as target:
            target.comment = source.comment
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename.startswith('word/media/'):
                    payload = replacements.get(sha256(data).hexdigest())
                    if payload is not None:
                        data = payload
                        replaced += 1
                target.writestr(info, data)
        assert replaced > 0
        temporary.replace(docx)
        md.write_text(content, encoding='utf-8')
        updates.append(dict(report=report['title'], image_references=len(report['references']),
                            replaced_embedded_image_parts=replaced))
    percentage = ROOT / 'results/feedback_percentage_20261026'
    with ZipFile(percentage / '反馈开销百分比四图_PPT用_best自动图例版.zip', 'w', compression=ZIP_DEFLATED) as archive:
        for stream, label in [('single', '单流'), ('dual', '双流')]:
            for branch in ('CPU', 'UE'):
                png = percentage / 'figures' / stream / branch / STYLE['image_version'] / '反馈开销占比_AP数.png'
                archive.write(png, f'{label}_{branch}_反馈开销百分比.png')
        archive.write(percentage / 'README.md', '计算口径与图例更新说明.md')
    write_json(OUT / 'report_update.json', dict(reports=updates, Word_inspected=False,
               document_XML_preserved=True, simulation_rerun=False))
    sources = ['report_figure_style.json', 'save_report_figure.m', 'report_figure_style.py',
               'plot_feedback_percentage.m', 'build_snr_revision_reports.py',
               'update_report_best.py', 'update_report_best_figures.m']
    write_json(OUT / 'source_SHA256.json', dict(files=[dict(path=p, sha256_LF=sha256(
        (ROOT / p).read_text(encoding='utf-8').encode('utf-8')).hexdigest()) for p in sources]))
    print('Updated both MD reports, embedded Word image parts and four-figure PPT archive; Word not inspected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'integrate'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else integrate()
