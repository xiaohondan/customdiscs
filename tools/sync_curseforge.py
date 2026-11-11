# -*- coding: utf-8 -*-
"""按 release-manifest.json 把 dist/ 里的 jar 幂等同步到 CurseForge。

设计原则（对齐 tools/sync_modrinth.py）：
  * 清单是唯一事实来源；脚本**绝不删除清单以外的文件**。
  * 默认只联网预演（打印将上传清单与游戏版本映射，不发任何写请求）；--go 才真正上传。
  * 上传前先校验项目身份（name 必须含 Neko Custom Discs），防止传错项目。
  * 已存在同名文件 -> 跳过（幂等）。
  * 令牌只从环境变量 CURSEFORGE_TOKEN 读取，不写文件、不打印、不进日志。
  * 游戏版本映射（MC 版本名 -> CF version id，loader 名 -> CF modloader id）自动从 API 拉取并缓存。

用法：
  python tools/sync_curseforge.py --check-only            # 只做本地一致性校验，不联网
  python tools/sync_curseforge.py                         # 联网预演：校验身份 + 拉映射 + 列出将上传清单
  python tools/sync_curseforge.py --go                    # 真正上传缺失文件
"""
import argparse
import hashlib
import json
import os
import pathlib
import ssl
import sys
import urllib.error
import urllib.request
import uuid
import zipfile

API = 'https://minecraft.curseforge.com/api/v1'
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'release-manifest.json'
PROJECT_ID = '1784647'  # CurseForge 项目 ID（由项目方提供）


def ssl_ctx():
    # 本地调试若遇证书拦截可设 SSL_VERIFY=0；CI 用默认校验。
    if os.environ.get('SSL_VERIFY', '1') == '0':
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def token():
    t = os.environ.get('CURSEFORGE_TOKEN', '').strip()
    if not t:
        sys.exit('缺少 CURSEFORGE_TOKEN：CI 中请配置为仓库 Actions Secret；本地可设环境变量。')
    return t


def req(method, path, tok=None, payload=None, files=None):
    headers = {
        'User-Agent': 'NekoStudio-CustomDiscs-Sync/1.0',
        'Accept': 'application/json',
    }
    if tok:
        headers['X-Api-Token'] = tok
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

        if payload is not None:
            part('metadata', json.dumps(payload, ensure_ascii=False).encode('utf-8'), 'application/json')
        for name, content in files:
            part(name, content, 'application/java-archive', name)
        buf.extend(('--' + boundary + '--\r\n').encode())
        body = bytes(buf)
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    elif payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    url = API + path
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, context=ssl_ctx(), timeout=180) as resp:
            raw = resp.read()
            data = json.loads(raw) if raw else None
            if isinstance(data, dict):
                return data.get('data', data)
            return data
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:600]
        raise RuntimeError('%s %s -> HTTP %s: %s' % (method, path, e.code, detail))


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
            errors.append('%s：sha1 与清单不符' % it['file'])
            continue
        try:
            with zipfile.ZipFile(p) as z:
                if z.testzip() is not None:
                    errors.append('%s：压缩包 CRC 异常' % it['file'])
                    continue
                meta = json.loads(z.read('fabric.mod.json').decode('utf-8'))
            if meta.get('version') != it['version_number']:
                errors.append('%s：jar 内 version=%s，清单=%s' % (
                    it['file'], meta.get('version'), it['version_number']))
            if meta.get('depends', {}).get('minecraft') != '=' + it['mc']:
                errors.append('%s：jar 内 minecraft 声明与清单不符' % it['file'])
        except Exception as e:
            errors.append('%s：无法读取 fabric.mod.json（%s）' % (it['file'], e))
    return errors


def load_mc_versions(tok):
    versions = req('GET', '/minecraft/version', tok)
    return {v['name']: v['id'] for v in versions}


def load_modloaders(tok):
    loaders = req('GET', '/minecraft/modloader', tok)
    return {l['name'].lower(): l['id'] for l in loaders}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true', help='只做本地一致性校验，不联网')
    ap.add_argument('--go', action='store_true', help='真正执行上传（默认只预演）')
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

    # 1) 校验项目身份，防止传错项目
    proj = req('GET', '/projects/' + PROJECT_ID, tok)
    pname = proj.get('name', '')
    pslug = proj.get('slug', '')
    if 'neko custom discs' not in pname.lower():
        sys.exit('项目身份校验失败：id=%s 的项目名是 %r（slug=%s），疑似不是 Neko Custom Discs。'
                 '中止以防传错项目。' % (PROJECT_ID, pname, pslug))
    print('项目校验通过：%s（slug=%s，id=%s）' % (pname, pslug, PROJECT_ID))

    # 2) 拉取版本映射
    mc_map = load_mc_versions(tok)
    loader_map = load_modloaders(tok)
    print('已加载 MC 版本映射 %d 条、loader 映射 %d 条。' % (len(mc_map), len(loader_map)))

    # 3) 列出已存在文件（按 fileName 幂等）
    existing = req('GET', '/projects/%s/files?pageSize=50' % PROJECT_ID, tok) or []
    existing_names = {f.get('fileName') for f in existing}
    print('CF 项目现有文件：%d 个' % len(existing_names))

    # 4) 组装计划
    plan = []
    for it in manifest['versions']:
        filename = pathlib.Path(it['file']).name
        gv = []
        mc_id = mc_map.get(it['mc'])
        if mc_id is None:
            print('  ! %s：找不到 CF 版本 id（%s），将跳过' % (filename, it['mc']))
            plan.append((it, filename, [], 'skip-noversion'))
            continue
        gv.append(mc_id)
        for ld in it.get('loaders', []):
            lid = loader_map.get(ld.lower())
            if lid is not None:
                gv.append(lid)
        act = 'skip' if filename in existing_names else 'upload'
        plan.append((it, filename, gv, act))

    print('\n%-40s %-7s %s' % ('文件', '动作', 'CF 游戏版本 id'))
    for it, filename, gv, act in plan:
        print('  %-38s %-7s %s' % (filename, act, gv))

    n_up = sum(1 for _, _, _, a in plan if a == 'upload')
    n_sk = sum(1 for _, _, _, a in plan if a in ('skip', 'skip-noversion'))
    print('\n汇总：将上传 %d，跳过 %d' % (n_up, n_sk))

    if not args.go:
        print('\n[预演结束] 未发送任何写请求。确认项目名与游戏版本映射无误后，加 --go 上传。')
        return
    if n_up == 0:
        print('\n无需上传：清单内文件已全部存在于 CF 项目。')
        return

    ok = fail = 0
    for idx, (it, filename, gv, act) in enumerate(plan, 1):
        if act != 'upload':
            continue
        content = (ROOT / it['file']).read_bytes()
        meta = {
            'displayName': it['name'],
            'releaseType': it.get('version_type', 'release'),
            'gameVersions': gv,
            'changelog': it.get('changelog', ''),
            'changelogType': 'markdown',
            'parentFileID': 0,
        }
        try:
            req('POST', '/projects/%s/upload-file' % PROJECT_ID, tok,
                payload=meta, files=[(filename, content)])
            ok += 1
            print('[%2d/%d] %-38s 上传成功（gameVersions=%s）' % (idx, n_up, filename, gv))
        except Exception as e:
            fail += 1
            print('[%2d/%d] %-38s 失败：%s' % (idx, n_up, filename, str(e)[:220]))

    # 最终复核
    final = req('GET', '/projects/%s/files?pageSize=50' % PROJECT_ID, tok) or []
    final_names = {f.get('fileName') for f in final}
    missing = [pathlib.Path(it['file']).name
               for it in manifest['versions']
               if pathlib.Path(it['file']).name not in final_names]
    print('\n=== 最终复核 ===')
    print('本轮上传成功 %d / 失败 %d' % (ok, fail))
    print('CF 项目文件总数 %d；清单内缺失 %d 个' % (len(final_names), len(missing)))
    for m in missing:
        print('  ! 缺失：' + m)
    if fail or missing:
        sys.exit(1)
    print('\n同步完成：清单内 %d 个版本全部已存在于 CF 项目。' % len(manifest['versions']))


if __name__ == '__main__':
    main()
