#!/usr/bin/env bash
# 一键构建 Neko Custom Discs 支持的全部版本（Linux / macOS / Git Bash）
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV="$ROOT/.buildenv"
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-/tmp/ghome}"

if [ -x "$ENV/jdk/jdk-21.0.13+9/bin/java" ]; then
  export JAVA_HOME="$ENV/jdk/jdk-21.0.13+9"
  export PATH="$JAVA_HOME/bin:$PATH"
elif ! command -v java >/dev/null 2>&1; then
  echo "[错误] 未检测到 Java，请先安装 JDK 21 并配置 JAVA_HOME。"
  exit 1
fi

VERSIONS="1.20.1 1.20.2 1.20.3 1.20.4 1.20.5 1.20.6 1.21 1.21.1 1.21.2 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10 1.21.11"
ok=0
fail=0
for v in $VERSIONS; do
  echo "============================================"
  echo "  构建版本 $v"
  echo "============================================"
  if [ -x "$ENV/gradle-8.14/bin/gradle" ]; then
    "$ENV/gradle-8.14/bin/gradle" build -Pmc="$v" --no-daemon --console=plain
  else
    "$ROOT/gradlew" build -Pmc="$v" --no-daemon --console=plain
  fi
  if [ $? -eq 0 ]; then ok=$((ok+1)); echo "[成功] $v"; else fail=$((fail+1)); echo "[失败] $v"; fi
done
echo
echo "========== 构建汇总：成功 $ok 个，失败 $fail 个 =========="
echo "实际产物："; ls -1 build/libs/customdiscs-*.jar 2>/dev/null || echo "(无任何 jar)"
if [ "$fail" -gt 0 ]; then echo; echo "[未全部完成] 有 $fail 个版本失败"; else echo; echo "全部完成"; fi
