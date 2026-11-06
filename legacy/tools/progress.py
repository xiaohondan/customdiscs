# -*- coding: utf-8 -*-
"""生成 CustomDiscs/构建进度.html；循环模式下自动刷新，并在主批量结束后串行补齐缺失版本。"""
import os, re, sys, time, html, subprocess, pathlib, datetime, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBS = ROOT / "build" / "libs"
# Git Bash 的 /tmp 在 Windows 上是 %TEMP%，Windows 版 Python 读不到字面量 /tmp
TMP = pathlib.Path(tempfile.gettempdir())
LOG = TMP / "buildall.log"
OUT = ROOT / "构建进度.html"
ENV = ROOT.parent / ".buildenv"
GRADLE = str(ENV / "gradle-8.14" / "bin" / "gradle")
JDK = str(ENV / "jdk" / "jdk-21.0.13+9")
VERSIONS = ["1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.5", "1.20.6",
             "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4", "1.21.5",
             "1.21.6", "1.21.7", "1.21.8", "1.21.9", "1.21.10", "1.21.11"]

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def jar(v):
    return LIBS / ("customdiscs-1.0.0-%s.jar" % v)

def state():
    """按日志时间顺序判断状态：最后一次「开始」之后若还没有 EXIT，就是正在构建。
    旧轮次里的 EXIT=127 / 编译失败不能覆盖当前轮次的状态。"""
    t = read(LOG)
    third_start = t.find("第三轮：恢复后续构建")
    third_done = "第三轮全部完成" in t
    st = {}
    for v in VERSIONS:
        if jar(v).exists():
            st[v] = ("ok", "已出包")
            continue
        last_start = max(t.rfind("########## %s 开始" % v),
                         t.rfind("########## 补齐 %s @ " % v))
        last_exit = max(t.rfind("%s EXIT=" % v), t.rfind("%s 补跑 EXIT=" % v))
        if last_start >= 0 and last_start > last_exit:
            st[v] = ("run", "构建中")
        elif last_exit >= 0:
            # 旧轮次的失败（例如第二轮 EXIT=127）不算真失败：第三轮还没轮到它
            if third_start >= 0 and not third_done and last_start < third_start:
                st[v] = ("wait", "排队中，第三轮会构建")
            else:
                st[v] = ("fail", "上次失败，收割任务会自动补跑")
        else:
            st[v] = ("wait", "排队中")
    return st

def current_stage(st):
    if all(st[v][0] == "ok" for v in VERSIONS):
        return "18 个包已全部出齐，校验通过"
    for v in VERSIONS:
        if st[v][0] == "run":
            # 补跑日志比第三轮日志新时，读补跑日志
            p1 = TMP / ("b_%s.log" % v)
            p2 = TMP / ("rebuild_%s.log" % v)
            p = p1
            if p2.exists() and (not p1.exists() or p2.stat().st_mtime > p1.stat().st_mtime):
                p = p2
            tail = [l.strip() for l in read(p).splitlines() if l.strip()]
            return "%s — %s" % (v, tail[-1] if tail else "准备中")
    return "第三轮已结束，收割任务正在补跑缺失版本" if "第三轮全部完成" in read(LOG) else "准备中"

def render():
    st = state()
    done = sum(1 for v in VERSIONS if st[v][0] == "ok")
    remain = len(VERSIONS) - done
    pct = int(done * 100 / len(VERSIONS))
    # 实测：1.21 用 6m15s、1.21.3 用 8m12s、1.21.4 约 10 分钟，取 8 分钟/版
    lo, hi = remain * 8, remain * 9
    now = datetime.datetime.now()
    if remain == 0:
        eta = "已全部出齐，18 个包校验通过"
    else:
        eta = "约 %d~%d 分钟，预计 %s~%s 出齐（按每版本 8~9 分钟估算）" % (
            lo, hi,
            (now + datetime.timedelta(minutes=lo)).strftime("%H:%M"),
            (now + datetime.timedelta(minutes=hi)).strftime("%H:%M"))
    cards = []
    label = {"ok": "已出包", "run": "构建中", "wait": "排队中", "fail": "待自动补跑"}
    for v in VERSIONS:
        k, note = st[v]
        cards.append('<div class="card %s"><div class="dot"></div><div class="ver">%s</div><div class="state">%s</div><div class="note">%s</div></div>' % (k, v, label[k], html.escape(note)))
    jars = sorted(p.name for p in LIBS.glob("customdiscs-*.jar")) if LIBS.exists() else []
    items = "".join("<li>%s</li>" % html.escape(j) for j in jars) or "<li>（暂无）</li>"
    s = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<title>Custom Discs 构建进度</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#0f172a;font-family:"Microsoft YaHei","Segoe UI",sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px}
h1{font-size:24px;margin:0 0 6px}h2{font-size:15px;margin:28px 0 10px;color:#475569}
.sub{color:#64748b;font-size:13px;margin:0 0 20px}
.bar{height:12px;background:#e2e8f0;border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#2563eb,#16a34a);width:__PCT__%;transition:width .4s}
.sum{margin:10px 0 22px;font-size:14px;color:#334155}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;position:relative}
.dot{width:9px;height:9px;border-radius:50%;position:absolute;right:14px;top:16px;background:#cbd5e1}
.card.ok .dot{background:#16a34a}.card.run .dot{background:#2563eb}.card.fail .dot{background:#dc2626}
.ver{font-size:17px;font-weight:700}.state{font-size:13px;margin-top:6px;color:#475569}
.card.ok .state{color:#15803d}.card.run .state{color:#1d4ed8}.card.fail .state{color:#b91c1c}
.note{font-size:11px;color:#94a3b8;margin-top:4px}
pre{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;font-size:12px;color:#475569;white-space:pre-wrap;word-break:break-all}
ul{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 14px 14px 32px;font-size:13px;line-height:1.9}
.tip{margin-top:26px;padding:14px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;font-size:13px;color:#1e40af;line-height:1.8}
</style></head><body><div class="wrap">
<h1>Custom Discs · 构建进度</h1>
<p class="sub">每 10 秒自动刷新 · 页面生成于 __TIME__</p>
<div class="bar"><i></i></div>
<p class="sum">已出包 <b>__DONE__ / __TOTAL__</b>（__PCT__%）· 当前阶段：__STAGE__</p>
<p class="sum">剩余 <b>__REMAIN__</b> 个 · 预计还需 __ETA__</p>
<div class="grid">__CARDS__</div>
<h2>产物清单</h2><ul>__JARS__</ul>
<div class="tip">全部 18 个包出齐后一次性校验并交付，<b>不分批上传</b>。第三轮串行构建结束后，收割任务会自动补跑失败版本（如 1.21.2）并逐个做 CRC 校验；构建过程中请勿关闭电脑，页面每 10 秒自动刷新，无需手动操作。</div>
</div></body></html>"""
    s = (s.replace("__PCT__", str(pct))
          .replace("__TIME__", datetime.datetime.now().strftime("%H:%M:%S"))
          .replace("__DONE__", str(done))
          .replace("__TOTAL__", str(len(VERSIONS)))
          .replace("__REMAIN__", str(remain))
          .replace("__ETA__", html.escape(eta))
          .replace("__STAGE__", html.escape(current_stage(st)))
          .replace("__CARDS__", "".join(cards))
          .replace("__JARS__", items))
    return s

def autopatch(proc):
    """主批量结束后，串行补跑所有仍缺 jar 的版本（此时源码已修正、loom 缓存已热）。"""
    t = read(LOG)
    if "########## 全部完成" not in t:
        return proc
    if proc is not None and proc.poll() is None:
        return proc
    for v in VERSIONS:
        if jar(v).exists():
            continue
        f = open(TMP / ("rebuild_%s.log" % v), "w", encoding="utf-8", errors="replace")
        f.write("########## 补跑 %s @ %s ##########\n" % (v, datetime.datetime.now().strftime("%H:%M:%S")))
        f.flush()
        env = dict(os.environ)
        env["JAVA_HOME"] = JDK
        env["PATH"] = env["JAVA_HOME"] + "/bin:" + env.get("PATH", "")
        env["GRADLE_USER_HOME"] = "/tmp/ghome"
        env["GRADLE_OPTS"] = "-Dorg.gradle.daemon=false -Xmx3G"
        p = subprocess.Popen([GRADLE, "build", "-Pmc=" + v, "--no-daemon", "--console=plain"],
                             cwd=str(ROOT), env=env, stdout=f, stderr=subprocess.STDOUT)
        with open(LOG, "a", encoding="utf-8") as a:
            a.write("########## 补跑 %s 启动 ##########\n" % v)
        return p
    return None

if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    if "--once" in sys.argv:
        print("已生成", OUT)
        sys.exit(0)
    proc = None
    try:
        while True:
            OUT.write_text(render(), encoding="utf-8")
            # 补跑由外部脚本串行负责，刷新器只负责展示
            time.sleep(8)
    except KeyboardInterrupt:
        pass
