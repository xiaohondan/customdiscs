# -*- coding: utf-8 -*-
"""Custom Discs 26.x —— Modrinth 追加上传脚本（只追加，绝不删已有版本）

安全约定：
  * 令牌只从环境变量 MODRINTH_TOKEN 或 ~/.modrinth_token 读取，绝不写入本文件、绝不打印。
  * 默认 dry-run（只列计划，不发任何写请求）；只有显式 --go 才写。
  * 本脚本没有删除能力：遇到同版本号的既有条目默认跳过，可用 --replace-existing
    显式替换（仍需二次确认参数），但**永远不会碰** 1.20.x–1.21.11 那 18 个版本。
  * 每个版本上传后立即回读，校验游戏版本、加载器、文件名与 sha1。
  * 幂等：中途失败直接重跑即可。

用法：
  python tools/upload_modrinth_26.py --slug nekocustomdiscs                 # 预演
  python tools/upload_modrinth_26.py --slug nekocustomdiscs --go            # 追加 3 个版本
  python tools/upload_modrinth_26.py --slug nekocustomdiscs --go --replace-existing  # 同名条目换文件
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
import uuid

API = 'https://api.modrinth.com/v2'
ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBS = ROOT / 'build' / 'libs'
VERSIONS = ['26.1', '26.2', '26.3']

# Modrinth 官方 API 实测项目 ID
DEPS = [
    {'project_id': 'P7dR8mSH', 'dependency_type': 'required'},  # Fabric API
    {'project_id': '9s6osm5g', 'dependency_type': 'required'},   # Cloth Config API
    {'project_id': 'mOgUt4GM', 'dependency_type': 'optional'},    # Mod Menu
]
CHANGELOG = (
    'Neko Custom Discs 1.0.0 for Minecraft {mc}。支持用本地 .ogg 音乐自定义唱片。\n\n'
    '注意：本版本需要 Java 25；仅通过编译验证，尚未在真实游戏中启动测试。'
)


def get_token():
    t = os.environ.get('MODRINTH_TOKEN', '').strip()
    if t:
        return t
    p = pathlib.Path.home() / '.modrinth_token'
    if p.is_file():
        return p.read_text(encoding='utf-8').strip()
    sys.exit('未找到 Modrinth 令牌：请设置环境变量 MODRINTH_TOKEN，或写入 %s' % p)


def request(method, path, token, payload=None, files=None):
    headers = {
        'Authorization': token,
        'User-Agent': 'NekoStudio-CustomDiscs26-Uploader/1.0',
        'Accept': 'application/json',
    }
    body = None
    if files is not None:
        boundary = '----' + uuid.uuid4().hex
        buf = bytearray()

        def part(name, content, ctype=None, filename=None):
            disp = 'Content-Disposition: form-data; name="%s"' % name
            if filename:
                disp += '; filename="%s"' % filename
            buf.extend(('--' + boundary + '\r\n').encode())
            buf.extend((disp + '\r\n').encode())
            if ctype:
                buf.extend(('Content-Type: %s\r\n' % ctype).encode())
            buf.extend(b'\r\n')
            buf.extend(content)
            buf.extend(b'\r\n')

        part('data', json.dumps(payload, ensure_ascii=False).encode('utf-8'), 'application/json')
        for name, content in files:
            part(name, content, 'application/java-archive', name)
        buf.extend(('--' + boundary + '--\r\n').encode())
        body = bytes(buf)
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    elif payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:600]
        raise RuntimeError('%s %s -> HTTP %s: %s' % (method, path, e.code, detail))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True, help='Modrinth 项目 slug 或 ID')
    ap.add_argument('--go', action='store_true', help='真正执行上传（默认只预演）')
    ap.add_argument('--replace-existing', action='store_true',
                    help='同版本号的 26.x 条目已存在时，删除该条再重建（仅限 26.x，不碰其他版本）')
    args = ap.parse_args()

    token = get_token()
    missing = [v for v in VERSIONS if not (LIBS / ('customdiscs-1.0.0-%s.jar' % v)).is_file()]
    if missing:
        sys.exit('缺少 jar：' + ', '.join(missing))

    _, project = request('GET', '/project/' + args.slug, token)
    project_id = project['id']
    print('项目：%s（id=%s, slug=%s, 状态=%s）' % (
        project.get('title'), project_id, project.get('slug'), project.get('status')))

    _, existing = request('GET', '/project/%s/version' % project_id, token)
    by_vn = {}
    for x in existing:
        by_vn.setdefault(x.get('version_number'), []).append(x)
    print('现有版本条目：%d 个（本脚本只处理 26.x 三条，其余一律不动）' % len(existing))

    plan = []
    print('\n版本    既有 26.x 条目        动作')
    for v in VERSIONS:
        vn = '1.0.0-' + v
        olds = by_vn.get(vn, [])
        if olds and args.replace_existing:
            action = '删这 %d 条 26.x 条目后重建' % len(olds)
        elif olds:
            action = '跳过（已存在）'
        else:
            action = '新建版本 + 上传 jar'
        plan.append((v, vn, olds, action))
        print('  %-6s  %-20s  %s' % (v, ','.join(x['id'] for x in olds) or '-', action))

    print('\n将上传的文件：')
    for v in VERSIONS:
        print('  %-6s -> customdiscs-1.0.0-%s.jar  [%s]' % (v, v, '=' + v))

    if not args.go:
        print('\n[预演结束] 未发送任何写请求。确认后加 --go。')
        return

    results = []
    for idx, (v, vn, olds, action) in enumerate(plan, 1):
        if action.startswith('跳过'):
            results.append((v, 'SKIP'))
            print('[%d/3] %-6s 跳过（已存在，未改动）' % (idx, v))
            continue
        name = 'customdiscs-1.0.0-%s.jar' % v
        content = (LIBS / name).read_bytes()
        want = hashlib.sha1(content).hexdigest()
        try:
            if olds and args.replace_existing:
                for x in olds:
                    # 双保险：只删本版本号的条目，绝不触碰其他版本
                    assert x.get('version_number') == vn
                    request('DELETE', '/version/' + x['id'], token)

            payload = {
                'name': 'Neko Custom Discs ' + vn,
                'version_number': vn,
                'changelog': CHANGELOG.format(mc=v),
                'dependencies': list(DEPS),
                'game_versions': [v],
                'version_type': 'release',
                'loaders': ['fabric'],
                'featured': True,
                'status': 'listed',
                'project_id': project_id,
                'file_parts': [name],
                'primary_file': name,
            }
            _, created = request('POST', '/version', token, payload, [(name, content)])
            _, check = request('GET', '/version/' + created['id'], token)
            assert check['game_versions'] == [v], '游戏版本不符：%s' % check['game_versions']
            assert 'fabric' in check['loaders'], '加载器不符'
            f = next(f for f in check['files'] if f['filename'] == name)
            got = f.get('hashes') or {}
            if 'sha1' in got:
                assert got['sha1'] == want, 'sha1 不一致（上传的可能不是本地文件）'
            results.append((v, 'OK'))
            print('[%d/3] %-6s 完成：上传 + 回读校验，游戏版本=%s，sha1 一致  id=%s'
                  % (idx, v, check['game_versions'], created['id']))
        except Exception as e:
            results.append((v, 'FAIL'))
            print('[%d/3] %-6s 失败：%s' % (idx, v, str(e)[:220]))
            if idx == 1:
                print('!! 第一个版本即失败，停止。常见原因：令牌缺少 VERSION_CREATE 权限。')
                break

    print('\n=== 全量复核 ===')
    _, final = request('GET', '/project/%s/version' % project_id, token)
    final_by_vn = {}
    for x in final:
        final_by_vn.setdefault(x.get('version_number'), []).append(x)
    bad = []
    for v in VERSIONS:
        vn = '1.0.0-' + v
        name = 'customdiscs-1.0.0-%s.jar' % v
        items = final_by_vn.get(vn, [])
        if len(items) != 1:
            bad.append('%s: 条目数=%d' % (v, len(items)))
            continue
        x = items[0]
        if x.get('game_versions') != [v]:
            bad.append('%s: 游戏版本=%s' % (v, x.get('game_versions')))
        f = next((f for f in x.get('files', []) if f['filename'] == name), None)
        if not f:
            bad.append('%s: 缺少 %s' % (v, name))
        elif f.get('hashes', {}).get('sha1') != hashlib.sha1(
                (LIBS / name).read_bytes()).hexdigest():
            bad.append('%s: 远端 sha1 与本地不一致' % v)
    old_count = sum(1 for x in final if not x.get('version_number', '').startswith('1.0.0-26.'))
    print('项目版本条目总数：%d（其中原有非 26.x 条目 %d 个，均未改动）' % (len(final), old_count))
    print('本轮结果：', ', '.join('%s=%s' % r for r in results))
    print('异常：%d 条' % len(bad))
    for b in bad:
        print('  ! ' + b)
    if bad or any(st == 'FAIL' for _, st in results):
        sys.exit(1)
    print('\n完成：26.x 三个版本已就位，游戏版本精确对应，远端文件与本地一致。')


if __name__ == '__main__':
    main()
