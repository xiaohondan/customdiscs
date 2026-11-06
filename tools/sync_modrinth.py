# -*- coding: utf-8 -*-
"""按 release-manifest.json 把 dist/ 里的 jar 幂等同步到 Modrinth。

设计原则：
  * 清单是唯一事实来源，脚本**绝不删除清单以外的版本条目**。
  * 默认只预演（不发任何写请求）；--go 才真正写入。
  * 版本已存在且主文件 sha1 与本地一致 -> 跳过（因此重复运行不会产生重复版本）。
  * 版本存在但文件变了 -> 仅当显式给 --replace-mismatch 才删旧重建（需 VERSION_DELETE 权限）。
  * 令牌只从环境变量 MODRINTH_TOKEN 读取，不写文件、不打印、不进日志。

用法：
  python tools/sync_modrinth.py --check-only                  # 只做本地一致性校验，不联网
  python tools/sync_modrinth.py                              # 联网预演：列出将创建/替换/跳过的版本
  python tools/sync_modrinth.py --go                         # 只补缺失版本，不替换已有
  python tools/sync_modrinth.py --go --replace-mismatch      # 补缺失 + 替换文件已变的版本（CI 用）
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
import zipfile

API = 'https://api.modrinth.com/v2'
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'release-manifest.json'


def load_manifest():
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert m.get('project_id'), '清单缺少 project_id'
    assert len(m.get('versions', [])) > 0, '清单里没有版本'
    return m


def local_check(manifest):
    """离线校验：jar 存在、sha1 与清单一致、jar 内元数据与清单一致。"""
    errors = []
    for it in manifest['versions']:
        p = ROOT / it['file']
        if not p.is_file():
            errors.append('%s：文件不存在' % it['file'])
            continue
        data = p.read_bytes()
        if hashlib.sha1(data).hexdigest() != it.get('sha1'):
            errors.append('%s：sha1 与清单不符（改了 jar 必须同步更新 release-manifest.json）' % it['file'])
        try:
            with zipfile.ZipFile(p) as z:
                if z.testzip() is not None:
                    errors.append('%s：压缩包 CRC 异常' % it['file'])
                meta = json.loads(z.read('fabric.mod.json').decode('utf-8'))
            if meta.get('version') != it['version_number']:
                errors.append('%s：jar 内 version=%s，清单=%s' % (
                    it['file'], meta.get('version'), it['version_number']))
            if meta.get('depends', {}).get('minecraft') != '=' + it['mc']:
                errors.append('%s：jar 内 minecraft 声明与清单不符' % it['file'])
            if it['game_versions'] != [it['mc']]:
                errors.append('%s：game_versions 必须只含对应一个版本' % it['file'])
        except Exception as e:
            errors.append('%s：无法读取 fabric.mod.json（%s）' % (it['file'], e))
    return errors


def token():
    t = os.environ.get('MODRINTH_TOKEN', '').strip()
    if not t:
        sys.exit('缺少 MODRINTH_TOKEN：CI 中请配置为仓库 Actions Secret；本地可设环境变量。')
    return t


def request(method, path, tok, payload=None, files=None):
    headers = {
        'Authorization': tok,
        'User-Agent': 'NekoStudio-CustomDiscs-Sync/1.0',
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


def remote_sha1(version, filename):
    f = next((f for f in version.get('files', []) if f['filename'] == filename), None)
    if not f:
        return None
    return (f.get('hashes') or {}).get('sha1')


def create_version(manifest, it, tok, content):
    filename = pathlib.Path(it['file']).name
    payload = {
        'name': it['name'],
        'version_number': it['version_number'],
        'changelog': it.get('changelog', ''),
        'dependencies': it['dependencies'],
        'game_versions': it['game_versions'],
        'version_type': it.get('version_type', 'release'),
        'loaders': it['loaders'],
        'featured': True,
        'status': it.get('status', 'listed'),
        'project_id': manifest['project_id'],
        'file_parts': [filename],
        'primary_file': filename,
    }
    _, created = request('POST', '/version', tok, payload, [(filename, content)])
    _, check = request('GET', '/version/' + created['id'], tok)
    assert check['game_versions'] == it['game_versions'], '游戏版本不符'
    assert it['loaders'][0] in check['loaders'], '加载器不符'
    assert remote_sha1(check, filename) == hashlib.sha1(content).hexdigest(), '回读 sha1 不一致'
    return created['id']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true', help='只做本地一致性校验，不联网')
    ap.add_argument('--go', action='store_true', help='真正执行写操作（默认只预演）')
    ap.add_argument('--replace-mismatch', action='store_true',
                    help='文件已变的版本删旧重建（需 VERSION_DELETE 权限）')
    args = ap.parse_args()

    manifest = load_manifest()
    errs = local_check(manifest)
    print('本地校验：%d 个版本，错误 %d 条' % (len(manifest['versions']), len(errs)))
    for e in errs:
        print('  ! ' + e)
    if errs:
        sys.exit(1)
    print('  全部通过：jar 存在、sha1 一致、压缩包完好、jar 内版本声明与清单一致。')
    if args.check_only:
        return

    tok = token()
    _, project = request('GET', '/project/' + manifest['project_id'], tok)
    print('项目：%s（slug=%s，状态=%s）' % (
        project.get('title'), project.get('slug'), project.get('status')))
    _, existing = request('GET', '/project/%s/version' % manifest['project_id'], tok)
    by_vn = {}
    for x in existing:
        by_vn.setdefault(x.get('version_number'), []).append(x)
    print('M 站现有版本条目：%d 个' % len(existing))

    plan = []
    for it in manifest['versions']:
        filename = pathlib.Path(it['file']).name
        olds = by_vn.get(it['version_number'], [])
        if len(olds) == 0:
            plan.append((it, olds, 'create'))
        elif len(olds) > 1:
            plan.append((it, olds, 'duplicate' if args.replace_mismatch else 'warn-duplicate'))
        elif remote_sha1(olds[0], filename) == it['sha1']:
            plan.append((it, olds, 'skip'))
        else:
            plan.append((it, olds, 'replace' if args.replace_mismatch else 'warn-mismatch'))

    label = {
        'create': '新建版本', 'skip': '已一致，跳过', 'replace': '删旧 + 重建',
        'duplicate': '清理重复 + 重建', 'warn-duplicate': '重复条目（需 --replace-mismatch）',
        'warn-mismatch': '文件已变（需 --replace-mismatch）',
    }
    print('\n%-9s %-9s %s' % ('版本', '动作', '说明'))
    for it, olds, act in plan:
        print('  %-8s %-10s %s' % (it['mc'], act, label[act]))
    n_create = sum(1 for _, _, a in plan if a in ('create', 'replace', 'duplicate'))
    n_skip = sum(1 for _, _, a in plan if a == 'skip')
    print('\n汇总：新建/替换 %d，跳过 %d，警告 %d' % (
        n_create, n_skip, sum(1 for _, _, a in plan if a.startswith('warn'))))

    if not args.go:
        print('\n[预演结束] 未发送任何写请求。确认后加 --go。')
        return
    if n_create == 0:
        print('\n无需写入：全部版本已与 M 站一致。')
        return

    ok = fail = 0
    for idx, (it, olds, act) in enumerate(plan, 1):
        if act in ('skip', 'warn-duplicate', 'warn-mismatch'):
            continue
        filename = pathlib.Path(it['file']).name
        content = (ROOT / it['file']).read_bytes()
        try:
            if act in ('replace', 'duplicate'):
                for x in olds:
                    assert x.get('version_number') == it['version_number'], '拒绝删除清单外版本'
                    request('DELETE', '/version/' + x['id'], tok)
            vid = create_version(manifest, it, tok, content)
            ok += 1
            print('[%2d/%d] %-8s %s -> id=%s' % (idx, len(plan), it['mc'], label[act], vid))
        except Exception as e:
            fail += 1
            print('[%2d/%d] %-8s 失败：%s' % (idx, len(plan), it['mc'], str(e)[:220]))

    # 最终复核：清单内每个版本恰好一条，且文件哈希一致；清单外条目数量不变
    _, final = request('GET', '/project/%s/version' % manifest['project_id'], tok)
    final_by = {}
    for x in final:
        final_by.setdefault(x.get('version_number'), []).append(x)
    bad = []
    for it in manifest['versions']:
        filename = pathlib.Path(it['file']).name
        xs = final_by.get(it['version_number'], [])
        if len(xs) != 1:
            bad.append('%s：条目数=%d' % (it['mc'], len(xs)))
        elif remote_sha1(xs[0], filename) != it['sha1']:
            bad.append('%s：远端 sha1 与本地不一致' % it['mc'])
        elif xs[0].get('game_versions') != [it['mc']]:
            bad.append('%s：游戏版本=%s' % (it['mc'], xs[0].get('game_versions')))
    planned_names = {it['version_number'] for it in manifest['versions']}
    outside_before = sum(1 for x in existing if x.get('version_number') not in planned_names)
    outside_after = sum(1 for x in final if x.get('version_number') not in planned_names)
    print('\n=== 最终复核 ===')
    print('本轮写入成功 %d / 失败 %d' % (ok, fail))
    print('M 站版本条目总数 %d；清单外条目：之前 %d、现在 %d（应相等）' % (
        len(final), outside_before, outside_after))
    print('异常 %d 条' % len(bad))
    for b in bad:
        print('  ! ' + b)
    if fail or bad or outside_after != outside_before:
        sys.exit(1)
    print('\n同步完成：清单内 %d 个版本全部与 M 站一致。' % len(manifest['versions']))


if __name__ == '__main__':
    main()
