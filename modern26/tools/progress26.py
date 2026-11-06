# -*- coding: utf-8 -*-
"""26.x 构建进度页（只读项目内状态文件，避开 Git Bash 与 Windows Python 的临时目录差异）。"""
import pathlib, datetime, html, sys, zipfile, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBS = ROOT / 'build' / 'libs'
STATUS = ROOT / '.build26-status'
OUT = ROOT / '26构建进度.html'
VERSIONS = ['26.1', '26.2', '26.3']


def read(p):
    try:
        return p.read_text(encoding='utf-8')
    except Exception:
        return ''


def check_jar(v):
    """真实读取 jar 内容校验，避免「文件名对但内部元数据错」被当成成功。"""
    p = LIBS / ('customdiscs-1.0.0-%s.jar' % v)
    try:
        with zipfile.ZipFile(p) as z:
            if z.testzip() is not None:
                return False, 'CRC 异常'
            cls = sum(1 for n in z.namelist() if n.endswith('.class'))
            m = json.loads(z.read('fabric.mod.json').decode('utf-8'))
        if cls != 11:
            return False, 'class 数异常'
        if m.get('version') != '1.0.0-' + v or m.get('depends', {}).get('minecraft') != '=' + v:
            return False, '元数据版本不符'
        if m.get('authors') != ['小红蛋']:
            return False, '署名不符'
        return True, '已出包 · 校验通过'
    except Exception as e:
        return False, '校验异常：%s' % str(e)[:30]


def state():
    t = read(STATUS)
    st = {}
    for v in VERSIONS:
        if (LIBS / ('customdiscs-1.0.0-%s.jar' % v)).exists():
            ok, label = check_jar(v)
            st[v] = ('ok' if ok else 'fail', label)
            continue
        last_start = t.rfind('########## %s 开始' % v)
        last_exit = t.rfind('%s EXIT=' % v)
        if last_start >= 0 and last_start > last_exit:
            st[v] = ('run', '构建中')
        elif last_exit >= 0:
            st[v] = ('fail', '上次失败，待补跑')
        else:
            st[v] = ('wait', '排队中')
    return st


def render():
    st = state()
    done = sum(1 for v in VERSIONS if st[v][0] == 'ok')
    pct = int(done * 100 / len(VERSIONS))
    colors = {'ok': '#1a7f37', 'run': '#9a6700', 'wait': '#57606a', 'fail': '#cf222e'}
    cards = []
    for v in VERSIONS:
        s, label = st[v]
        jar = LIBS / ('customdiscs-1.0.0-%s.jar' % v)
        size = ('%d B' % jar.stat().st_size) if jar.exists() else '—'
        cards.append('<div class="card"><span class="dot" style="background:%s"></span>'
                     '<b>Minecraft %s</b><span class="st">%s</span>'
                     '<span class="sz">%s</span></div>' % (colors[s], v, label, size))
    jars = sorted(LIBS.glob('customdiscs-1.0.0-26*.jar'))
    items = ''.join('<li>%s — %d B</li>' % (p.name, p.stat().st_size) for p in jars) or '<li>暂无</li>'
    t = read(STATUS)
    last = [l for l in t.splitlines() if l.strip()][-1:] or ['准备中']
    stage = ('26.x 全部出齐，3/3 CRC / class / 元数据 / 署名校验通过'
             if done == 3 else html.escape(last[0]))
    tpl = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="10"><title>Neko Custom Discs 26.x 构建进度</title>
<style>body{background:#f6f8fa;color:#1f2328;font:14px/1.7 -apple-system,"Microsoft YaHei",sans-serif;margin:0;padding:32px}
.wrap{max-width:760px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:12px;padding:28px 32px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:26px 0 10px;color:#57606a}
.sum{color:#57606a;margin:0 0 18px}.sum b{color:#1f2328}
.bar{height:10px;background:#d8dee4;border-radius:6px;overflow:hidden;margin:10px 0 22px}
.bar i{display:block;height:100%;background:#2da44e;width:__PCT__%}
.grid{display:grid;gap:10px}.card{display:flex;align-items:center;gap:12px;border:1px solid #d0d7de;border-radius:8px;padding:10px 14px}
.dot{width:10px;height:10px;border-radius:50%}.st{margin-left:auto;color:#57606a}.sz{width:90px;text-align:right;color:#8c959f}
ul{padding-left:20px}li{margin:3px 0}.tip{margin-top:22px;padding:12px 14px;background:#ddf4ff;border-radius:8px;color:#0969da}
.foot{margin-top:14px;color:#8c959f;font-size:12px}</style></head><body><div class="wrap">
<h1>Neko Custom Discs · Minecraft 26.x 构建进度</h1>
<p class="sum">已出包 <b>__DONE__ / 3</b>（__PCT__%）· 当前阶段：__STAGE__</p>
<div class="bar"><i></i></div><div class="grid">__CARDS__</div>
<h2>产物清单</h2><ul>__JARS__</ul>
<div class="tip">三个版本已一次性交付：<b>CustomDiscs-1.0.0-26.x-3-versions.zip</b> + 26.x上传清单.csv + 26.x发布说明.md，<b>不分批上传</b>。页面每 10 秒自动刷新。</div>
<div class="foot">更新于 __TIME__ · 免重映射构建链：Loom 1.20.0-alpha.19 / Gradle 9.8.2 / JDK 25</div>
</div></body></html>"""
    return (tpl.replace('__PCT__', str(pct)).replace('__DONE__', str(done))
            .replace('__STAGE__', stage).replace('__CARDS__', ''.join(cards))
            .replace('__JARS__', items)
            .replace('__TIME__', datetime.datetime.now().strftime('%H:%M:%S')))


if __name__ == '__main__':
    OUT.write_text(render(), encoding='utf-8')
    if '--once' not in sys.argv:
        print('已生成', OUT)
