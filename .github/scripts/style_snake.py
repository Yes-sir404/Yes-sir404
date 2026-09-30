"""Frame Platane's animated SVG with a GitHub-style contribution calendar."""
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

def node(parent, tag, **attrs):
    return ET.SubElement(parent, f'{{{NS}}}{tag}', {k: str(v) for k, v in attrs.items()})

def decorate(path, today):
    source = ET.parse(path).getroot()
    cells = [e for e in source.iter() if 'c' in e.get('class', '').split()]
    xs = sorted({float(e.get('x')) for e in cells})
    ys = sorted({float(e.get('y')) for e in cells})
    if len(xs) < 2 or len(ys) != 7:
        raise ValueError('Unexpected contribution grid; refusing to publish a malformed chart')
    pitch = xs[1] - xs[0]
    scale = 15 / pitch
    dark = 'dark' in path.stem
    background, text, muted, border, empty = (
        ('#0d1117', '#f0f6fc', '#9198a1', '#3d444d', '#eff2f5') if dark else
        ('#ffffff', '#1f2328', '#59636e', '#d1d9e0', '#eff2f5')
    )
    greens = ['#aceebb', '#4ac26b', '#2da44e', '#116329']
    width, height = 60 + len(xs) * 15, 222
    root = ET.Element(f'{{{NS}}}svg', {'viewBox': f'0 0 {width} {height}', 'width': str(width), 'height': str(height), 'role': 'img', 'aria-labelledby': 'title'})
    node(root, 'title', id='title').text = 'GitHub contribution calendar with an animated snake'
    node(root, 'rect', width=width, height=height, fill=background)
    def label(x, y, value, size=12, color=muted):
        node(root, 'text', x=x, y=y, fill=color, **{'font-family': '-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif', 'font-size': size}).text = value
    label(1, 24, 'Contributions in the last year', 18, text)
    node(root, 'path', d=f'M0 43H{width}M0 221H{width}', stroke=border, fill='none')
    # Source grid coordinates and CSS keyframes remain intact, preserving animation.
    # Crop the generator's collection bar below the calendar, keeping the grid and snake.
    source.set('x', '37')
    source.set('y', '69')
    source.set('width', str(len(xs) * 15 + 8))
    source.set('height', '116')
    source.set('viewBox', f'{xs[0]-3/scale} {ys[0]-9/scale} {(len(xs)*15+8)/scale} {116/scale}')
    source.set('overflow', 'hidden')
    style = node(source, 'style')
    style.text = ':root{--cb:rgba(27,31,36,0.06)}.c{width:' + str(11/scale) + 'px;height:' + str(11/scale) + 'px;stroke-width:' + str(1/scale) + 'px;stroke:rgba(27,31,36,0.06)}'
    for cell in cells:
        cell.set('rx', str(2/scale))
        cell.set('ry', str(2/scale))
    root.append(source)
    for row, name in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        label(1, 87 + row * 15, name)
    last_sunday = today - timedelta(days=(today.weekday()+1) % 7)
    first_sunday = last_sunday - timedelta(weeks=len(xs)-1)
    previous_month = None
    for i in range(len(xs)):
        day = first_sunday + timedelta(weeks=i)
        if day.month != previous_month and i < len(xs)-1 and (i > 0 or day.day <= 14):
            label(40 + i*15, 66, day.strftime('%b'))
        previous_month = day.month
    label(12, 201, 'Learn how we count contributions')
    legend_x = width - 164
    label(legend_x, 201, 'Less')
    for i, color in enumerate([empty] + greens):
        node(root, 'rect', x=legend_x+34+i*15, y=190, width=11, height=11, rx=2, fill=color, stroke='rgba(27,31,36,0.06)')
    label(legend_x+113, 201, 'More')
    ET.ElementTree(root).write(path, encoding='unicode')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.files:
        decorate(path, datetime.now(timezone.utc).date())
