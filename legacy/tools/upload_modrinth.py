# -*- coding: utf-8 -*-
"""Neko Custom Discs —— Modrinth 批量替换 / 上传脚本

安全约定：
  * 令牌只从环境变量 MODRINTH_TOKEN 或 ~/.modrinth_token 读取，绝不写入本文件、绝不打印。
  * 默认 dry-run（只列计划，不发送任何写请求）；只有显式 --go 才真正写入。
  * --delete-old 为破坏性操作，必须与 --go 同时给出才生效。
  * 逐版本处理：删旧 -> 传新 -> 回读校验，第一个版本是探针，失败立即停止，避免扩大损失。
  * 脚本幂等：中途失败后直接重跑即可自愈（同版本号的旧条目会被再次删除重建）。

用法：
  python tools/upload_modrinth.py --slug <slug>                       # 预演
  python tools/upload_modrinth.py --slug <slug> --go                  # 只上传，不删旧
  python tools/upload_modrinth.py --slug <slug> --go --delete-old     # 删旧 + 上传
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

VERSIONS = [
    '1.20.1', '1.20.2', '1.20.3', '1.20.4', '1.20.5', '1.20.6',
    '1.21', '1.21.1', '1.21.2', '1.21.3', '1.21.4', '1.21.5', '1.21.6',
    '1.21.7', '1.21.8', '1.21.9', '1.21.10', '1.21.11',
]

# 已在 Modrinth 官方 API 核实的依赖项目 ID
DEFAULT_DEPS = [
    {'project_id': 'P7dR8mSH', 'dependency_type': 'required'},  # Fabric API
    {'project_id': '9s6osm5g', 'dependency_type': 'required'},   # Cloth Config API
    {'project_id': 'mOgUt4GM', 'dependency_type': 'optional'},    # Mod Menu
]

CHANGELOG = 'Neko Custom Discs 1.0.0 for Minecraft {mc}. 支持用本地 .ogg 音乐自定义唱片。'


def get_token():
    t = os.environ.get('MODRINTH_TOKEN', '').strip()
    if t:
        return t
    p = pathlib.Path.home() / '.modrinth_token'
    if p.is_file():
        return p.read_text(encoding='utf-8').strip()
    sys.exit('未找到 Modrinth 令牌：请设置环境变量 MODRINTH_TOKEN，或把令牌写入 %s' % p)


def request(method, path, token, payload=None, files=None):
    url = API + path
    headers = {
        'Authorization': token,
        'User-Agent': 'NekoStudio-CustomDiscs-Uploader/1.0',
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

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:600]
        raise RuntimeError('%s %s -> HTTP %s: %s' % (method, path, e.code, detail))


def hashes(data):
    return {'sha1': hashlib.sha1(data).hexdigest(),
            'sha512': hashlib.sha512(data).hexdigest()}


def clean_deps(deps):
    """旧条目里的依赖只保留创建版本需要的两个字段，避免 version_id 之类引起 400。"""
    out = []
    for d in deps or []:
        pid, dt = d.get('project_id'), d.get('dependency_type')
        if pid and dt:
            out.append({'project_id': pid, 'dependency_type': dt})
    return out or list(DEFAULT_DEPS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True, help='Modrinth 项目 slug 或 ID')
    ap.add_argument('--go', action='store_true', help='真正执行写操作（默认只预演）')
    ap.add_argument('--delete-old', action='store_true', help='删掉项目里已有的版本条目（破坏性）')
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
    print('现有版本条目：%d 个' % len(existing))

    by_vn = {}
    for x in existing:
        by_vn.setdefault(x.get('version_number'), []).append(x)
    planned = {'1.0.0-' + v for v in VERSIONS}
    extra = [x for x in existing if x.get('version_number') not in planned]

    print('\n版本        将删除的旧条目                     旧 name / 依赖 / 游戏版本')
    for v in VERSIONS:
        vn = '1.0.0-' + v
        olds = by_vn.get(vn, [])
        ref = olds[0] if olds else None
        ids = ','.join(x['id'] for x in olds) or '-'
        detail = ('%r / %d 个依赖 / %s' % (
            ref.get('name'), len(ref.get('dependencies') or []), ref.get('game_versions'))) if ref else '（无）'
        print('  %-9s  %-34s  %s' % (v, ids, detail))
    if extra:
        print('\n另有 %d 个不在计划内的旧条目，也会一并删除：' % len(extra))
        for x in extra:
            print('  - %s | %s' % (x['id'], x.get('version_number')))

    print('\n将上传 18 个新文件（沿用旧条目的 name / 依赖 / 类型，游戏版本统一修正为「只勾对应一个」）：')
    for v in VERSIONS:
        print('  %-9s -> customdiscs-1.0.0-%s.jar' % (v, v))

    if not args.go:
        print('\n[预演结束] 未发送任何写请求。确认后加 --go；要删旧版本再加 --delete-old。')
        return

    results = []
    probe_failed = False
    for idx, v in enumerate(VERSIONS, 1):
        vn = '1.0.0-' + v
        name = 'customdiscs-1.0.0-%s.jar' % v
        content = (LIBS / name).read_bytes()
        want = hashes(content)
        olds = by_vn.get(vn, [])
        ref = olds[0] if olds else None
        try:
            if args.delete_old:
                for x in olds:
                    request('DELETE', '/version/' + x['id'], token)

            payload = {
                'name': (ref or {}).get('name') or ('Neko Custom Discs ' + vn),
                'version_number': vn,
                'changelog': (ref or {}).get('changelog') or CHANGELOG.format(mc=v),
                'dependencies': clean_deps((ref or {}).get('dependencies')),
                'game_versions': [v],
                'version_type': (ref or {}).get('version_type') or 'release',
                'loaders': ['fabric'],
                'featured': bool((ref or {}).get('featured', False)),
                'status': (ref or {}).get('status') or 'listed',
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
                assert got['sha1'] == want['sha1'], 'sha1 不一致（上传的可能不是本地新文件）'
            elif 'sha512' in got:
                assert got['sha512'] == want['sha512'], 'sha512 不一致'

            results.append((v, 'OK', created['id']))
            print('[%2d/18] %-9s 完成：删 %d 条 / 传 1 条 / 回读校验 + 哈希一致  id=%s'
                  % (idx, v, len(olds) if args.delete_old else 0, created['id']))
        except Exception as e:
            msg = str(e)[:220]
            results.append((v, 'FAIL', msg))
            print('[%2d/18] %-9s 失败：%s' % (idx, v, msg))
            if idx == 1:
                probe_failed = True
                print('!! 第一个版本即失败，立即停止，避免扩大损失。')
                print('!! 常见原因：令牌缺少 VERSION_DELETE / VERSION_CREATE 权限。')
                print('!! 脚本可重复执行，修好后直接重跑即可自愈。')
                break

    if args.delete_old and not probe_failed:
        for x in extra:
            try:
                request('DELETE', '/version/' + x['id'], token)
                print('已清理计划外旧条目 %s' % x['id'])
            except Exception as e:
                print('清理 %s 失败：%s' % (x['id'], str(e)[:160]))

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
        if not any(f['filename'] == name for f in x.get('files', [])):
            bad.append('%s: 文件名不符' % v)
    ok = sum(1 for r in results if r[1] == 'OK')
    print('项目现有版本条目：%d 个；本轮成功：%d/18；异常：%d 条' % (len(final), ok, len(bad)))
    for b in bad:
        print('  ! ' + b)
    for v, st, info in results:
        if st == 'FAIL':
            print('  失败 %-9s %s' % (v, info))

    if ok == 18 and not bad:
        print('\n完成：18/18 个版本已替换，逐个回读校验通过，游戏版本均精确对应。')
    else:
        print('\n未全部完成，修好后重跑本脚本即可补齐（幂等）。')
        sys.exit(1)


if __name__ == '__main__':
    main()
