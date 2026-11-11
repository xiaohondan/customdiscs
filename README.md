# Neko Custom Discs

**English** — A Fabric mod that turns your local `.ogg` music files into custom Minecraft music discs. It provides an in-game configuration screen (via Cloth Config) to set the music source folder.

**中文** — 让玩家用本地 `.ogg` 音乐文件自定义《我的世界》唱片的 Fabric 模组，并提供游戏内设置界面（Cloth Config）来配置音乐源文件夹。

- **Modrinth**: [modrinth.com/mod/nekocustomdiscs](https://modrinth.com/mod/nekocustomdiscs)
- **License / 许可证**: MIT
- **Author / 作者**: 小红蛋
- **Supported versions / 覆盖版本**: **21 Minecraft versions** — `1.20.1`–`1.20.6`, `1.21`–`1.21.11`, `26.1`–`26.3`

> ### Disclosure / 如实披露
> 1. **Relation to the similarly named project / 与同名项目的关系**: There is another public project named "Custom Discs"; per the author's understanding it has incomplete version support or is no longer maintained. **Neko Custom Discs** is unrelated to it — independently designed and implemented from scratch, with no copied, ported, or rewritten source code or assets. **无任何借鉴与抄袭。**
> 2. **AI-assisted content / AI 生成内容**: The source code in this repository was produced with AI assistance, implemented against the official public API documentation of Fabric / Fabric API / Cloth Config. If a platform asks, disclose this truthfully — no concealment or evasion.
> 3. **Test status / 测试状态**: `1.0.0-26.3` has been play-tested by the author on Minecraft 26.3 and loads correctly. The other 20 builds have only passed compilation, CRC, class-count and metadata checks — not in-game verification. The recent unified naming and icon update only changed display text and resource files, not any code logic.
> 4. Known functional gaps are listed in Section 6 below / 已知功能缺口见第六节。

---

## 1. Push-to-Modrinth Auto Sync / 一、推送即自动同步到 Modrinth

**English** — Neither Modrinth nor CurseForge offers a "bind GitHub repo and auto-sync" toggle, so this is done with GitHub Actions:

**中文** — Modrinth 与 CurseForge 本身都没有「绑定 GitHub 仓库就自动同步」的开关，这里用 GitHub Actions 实现：

```
Edit jars in dist/ or release-manifest.json
        ↓  git push
.github/workflows/publish-modrinth.yml triggers
        ↓
tools/sync_modrinth.py reads the manifest, compares each version against Modrinth
        ↓
  missing        → create version and upload jar
  file changed   → delete and recreate that entry (won't touch versions outside the manifest)
  already identical → skip (re-running never creates duplicates)
        ↓
read back and verify game_versions / loaders / sha1
```

The workflow only triggers when `dist/**`, `release-manifest.json`, the sync script, or the workflow itself changes; **editing source or this README alone will not trigger an upload**. You can also run it manually via `workflow_dispatch` on the Actions page.

### First-time setup: one Secret / 首次配置：只需一个 Secret

Repo → Settings → Secrets and variables → Actions → New repository secret:

| Name / 名称 | Value / 值 |
| --- | --- |
| `MODRINTH_TOKEN` | Modrinth personal access token, at least `VERSION_CREATE`; add `VERSION_DELETE` if you need to replace existing versions |

The token is only injected as an environment variable from the Secret; it is never written to any repo file, and the script never prints it. Modrinth tokens expire — **regenerate and update this Secret before expiry**, otherwise the CI fails.

---

## 2. Releasing or Updating a Version / 二、发布或更新一个版本

1. Build with the matching toolchain to get `customdiscs-1.0.0-<mc>.jar`.
   用对应工具链编译，得到新的 `customdiscs-1.0.0-<mc>.jar`；
2. Overwrite the same-named jar in `dist/`.
   覆盖 `dist/` 里同名 jar；
3. **Update the `sha1` for that entry in `release-manifest.json`** (the script's `--check-only` enforces this check to prevent manifest/product drift).
   **更新 `release-manifest.json` 中该条的 `sha1`**（脚本的 `--check-only` 会强制校验，防止清单和产物脱节）；
4. `git add` → `git commit` → `git push`, and CI syncs to Modrinth automatically.
   `git add` → `git commit` → `git push`，CI 自动同步到 Modrinth。

> Replacing an existing version deletes the old entry — **that entry's download statistics may be cleared by the platform**. To simply add a new Minecraft version, just add a line to the manifest; existing entries are untouched.
> 替换已存在的版本会删除旧的版本条目，**该条目的下载量统计可能被平台清掉**。如果只是补一个新 Minecraft 版本，直接在清单里加一条即可，不会动已有条目。

---

## 3. Directory Layout / 三、目录结构

```
.
├── .github/workflows/publish-modrinth.yml   # Auto-sync workflow / 自动同步工作流
├── release-manifest.json                    # Single source of truth for 21 versions / 21 个版本唯一事实来源
├── tools/sync_modrinth.py                   # Idempotent sync script (dry-run by default) / 幂等同步脚本（默认预演）
├── dist/                                    # 21 prebuilt jars (~588 KB) / 21 个已构建 jar（约 588 KB）
├── legacy/                                  # 1.20.1–1.21.11 source (old Loom + JDK 21)
├── modern26/                                # 26.1–26.3 source (unmapped Loom + JDK 25)
├── forge/                                   # 21 Forge versions source / 21 个 Forge 版本源码
├── LICENSE
└── .gitignore
```

`dist/` holds jars on purpose: all 21 packages total under 600 KB, far faster, more stable and more reproducible than re-running two Loom build chains in CI (each new MC version must re-deobfuscate dependencies; locally measured 4–13 minutes per version). Build caches, the Mojang client jar, and any credentials are excluded in `.gitignore` and never committed.

---

## 4. Two Build Chains / 四、两套构建链

| | `legacy/` (1.20.1–1.21.11) | `modern26/` (26.1–26.3) |
| --- | --- | --- |
| JDK | 21 | **25** (mandated by Mojang from 26.1) |
| Gradle | 8.14 | 9.8.2 |
| Loom | `fabric-loom` 1.10 / 1.12 / 1.13 (tiered by MC version) | `net.fabricmc.fabric-loom` 1.20.0-alpha.19 (unmapped) |
| Mappings | Yarn | **None** (MC no longer obfuscated from 26.1; Yarn discontinued) |
| Source class names | Yarn names / `MusicDiscItem` or `jukeboxPlayable` | Mojang official names (`Component`, `Item.Properties`, `PackRepository`, etc.) |

Build command examples (toolchains from the table above must be prepared locally; the repo does not bundle a Gradle Wrapper):

```bash
cd legacy   && gradle build -Pmc=1.20.1      # output in build/libs/
cd modern26 && gradle build -Pmc=26.3       # output in build/libs/
```

> **A multi-version build pitfall / 多版本构建的一个坑**: when `processResources` injects `${mc}` via `expand`, `mc` must be declared as a Gradle input (`inputs.property`); otherwise incremental builds skip resource processing and the jar's internal `fabric.mod.json` keeps the previous version despite a correct filename. Both build chains handle this.
> 必须把 `mc` 声明为 Gradle 输入（`inputs.property`），否则增量构建会跳过资源处理，导致 jar 文件名对但内部 `fabric.mod.json` 仍是上一次的版本。两套构建都已处理。

### Player runtime dependencies / 玩家运行时依赖

All versions require **Fabric Loader**, **Fabric API**, and **Cloth Config API**; **Mod Menu** is optional (provides the in-game settings entry). 26.x additionally requires **Java 25** and Loader ≥ `0.20.1`. Exact coordinates per MC version are in `legacy/上传清单.csv` and `modern26/26.x上传清单.csv`.

---

## 5. Features / 五、功能概览

| Feature / 功能 | Implementation / 实现 |
| --- | --- |
| In-game settings UI / 游戏内设置界面 | Mod Menu → Neko Custom Discs → Configure (Cloth Config) |
| Configure music source / 配置音乐源路径 | Relative-to-game-dir or absolute path; scans all `.ogg` in the folder |
| Generate discs / 生成唱片 | Registers one custom disc per file |
| Music loading / 音乐加载 | Writes `resourcepacks/CustomDiscs/` (`sounds.json` + ogg) and best-effort auto-enables the pack |
| How to obtain / 获取方式 | Creative tab, `/customdiscs give <id> [数量]`, crafting recipe |

---

## 6. Known Gaps / 六、已知缺口（发布前务必看）

1. **Play-test scope / 实机验证范围**: `1.0.0-26.3` was play-tested by the author on Minecraft 26.3; the other 20 packages have only passed compilation, CRC, class-count and metadata checks — never launched in-game.
2. **Jukebox playback not wired / 唱片机播放链路未打通**: the item side has the `jukeboxPlayable` component, but lacks the `data/minecraft/jukebox_song/*.json` data-driven resource, so a disc may not play when inserted.
3. `fabric.mod.json` `environment` is `"client"` while the main entry also registers a server-side command, so **dedicated servers will not load it**; supporting servers requires changing to `"*"` and re-building/verifying.
4. Resource-pack auto-mount is best-effort; on failure enable it manually under Options → Resource Packs / 「选项 → 资源包」.
5. Icons are ready (`icon.png` 512×512 / `icon-256.png` 256×256, original art); cover banner and project-description art are not yet prepared.
6. 26.x uses a Loom alpha branch; once a stable release lands, re-validate against it.
7. CurseForge still requires manual upload; auto-sync is currently Modrinth-only / CurseForge 目前仍需手动上传，自动同步只接了 Modrinth。

---

## 7. Run the Sync Script Locally / 七、本地手动运行同步脚本

```bash
export MODRINTH_TOKEN='your token'
python tools/sync_modrinth.py --check-only                 # local-only check, no network / 只校验本地，不联网
python tools/sync_modrinth.py                             # dry-run with network, writes nothing / 联网预演，不写任何东西
python tools/sync_modrinth.py --go                        # only add missing versions / 只补缺失版本
python tools/sync_modrinth.py --go --replace-mismatch     # add missing + replace changed versions / 补缺失 + 替换文件已变的版本
```

The script **never deletes version entries outside `release-manifest.json`**, and every run performs a final check, printing whether the count of out-of-manifest entries stayed unchanged.

---

*Organized by 小红蛋 / 为小红蛋整理*
