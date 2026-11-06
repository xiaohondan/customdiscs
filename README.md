# Neko Custom Discs

让玩家用**本地 `.ogg` 音乐文件**自定义《我的世界》唱片，并通过游戏内设置界面配置音乐源路径的 Fabric 模组。

- M 站项目：[modrinth.com/mod/nekocustomdiscs](https://modrinth.com/mod/nekocustomdiscs)
- 许可证：MIT
- 作者：小红蛋
- 覆盖 **21 个 Minecraft 版本**：`1.20.1`–`1.20.6`、`1.21`–`1.21.11`、`26.1`–`26.3`

> **如实披露**
> 1. **与同名项目的关系**：市面上另有同名的 Custom Discs 项目，据作者了解其存在支持版本不全或已停止更新的情况。本项目 **Neko Custom Discs** 与其无任何关联，系重新自行设计、独立实现，未复制、移植或改写该项目的任何源代码与素材，**无任何借鉴与抄袭**。
> 2. **AI 生成内容**：本仓库源码由 AI 辅助生成，实现依据为 Fabric / Fabric API / Cloth Config 的官方公开 API 文档；平台若询问，按此如实披露，不隐瞒、不改写规避。
> 3. **测试状态**：`1.0.0-26.3` 已由作者在 Minecraft 26.3 **实机测试通过**（模组正常加载）；其余 20 个版本仍仅通过编译、CRC、class 数与元数据校验，未做实机验证。本次统一名称与补图标仅改显示文本与资源文件，未改动任何代码逻辑。
> 4. 已知功能缺口见下方第六节。

---

## 一、这个仓库做什么：push 即自动同步到 M 站

M 站 / C 站本身**没有「绑定 GitHub 仓库就自动同步」的开关**，这里用 GitHub Actions 实现：

```
改 dist/ 里的 jar 或 release-manifest.json
        ↓  git push
.github/workflows/publish-modrinth.yml 触发
        ↓
tools/sync_modrinth.py 读清单，逐个比对 M 站现有版本
        ↓
  缺失 → 新建版本并上传 jar
  文件变了 → 删掉该条重建（不会碰清单外的版本）
  已一致 → 跳过（所以重复运行不会产生重复版本）
        ↓
逐个回读校验 game_versions / loaders / sha1
```

工作流只在 `dist/**`、`release-manifest.json`、同步脚本或工作流本身变化时触发；
**只改源码或 README 不会触发上传**。也可以在 Actions 页面手动 `workflow_dispatch` 运行。

### 首次使用只需配一个 Secret

仓库 → Settings → Secrets and variables → Actions → New repository secret：

| 名称 | 值 |
| --- | --- |
| `MODRINTH_TOKEN` | M 站个人访问令牌，权限至少 `VERSION_CREATE`，需要替换已存在版本时再加 `VERSION_DELETE` |

令牌**只从 Secret 注入环境变量**，不写入任何仓库文件，脚本也不会打印它。
M 站令牌有有效期，**到期前请重新生成并更新这个 Secret**，否则 CI 会失败。

---

## 二、发一个新版本／更新一个版本的操作

1. 用对应工具链编译，得到新的 `customdiscs-1.0.0-<mc>.jar`；
2. 覆盖 `dist/` 里同名 jar；
3. **更新 `release-manifest.json` 中该条的 `sha1`**（脚本的 `--check-only` 会强制校验，防止清单和产物脱节）；
4. `git add` → `git commit` → `git push`，CI 自动同步到 M 站。

> 注意：替换已存在的版本会删除旧的版本条目，**该条目的下载量统计可能被平台清掉**。
> 如果只是补一个新 Minecraft 版本，直接在清单里加一条即可，不会动已有条目。

---

## 三、目录结构

```
.
├── .github/workflows/publish-modrinth.yml   # 自动同步工作流
├── release-manifest.json                    # 21 个版本的唯一事实来源
├── tools/sync_modrinth.py                   # 幂等同步脚本（默认预演）
├── dist/                                    # 21 个已构建好的 jar（约 588 KB）
├── legacy/                                  # 1.20.1–1.21.11 源码（旧 Loom + JDK 21）
│   ├── src/{main,v-old,v-new,v-modern}/java
│   ├── build.gradle / settings.gradle / gradle.properties
│   ├── README.md / 发布指南.md / 上传清单.csv
│   └── tools/
├── modern26/                                # 26.1–26.3 源码（免重映射 Loom + JDK 25）
│   ├── src/main/java
│   ├── build.gradle / settings.gradle / gradle.properties
│   ├── 26.x发布说明.md / 26.x上传清单.csv
│   └── tools/
├── LICENSE
└── .gitignore
```

`dist/` 里放 jar 是刻意为之：21 个包总共不到 600 KB，比在 CI 里重跑两套 Loom 构建链
（每个新 MC 版本都要重新反混淆依赖，本机实测单版本 4～13 分钟）更快、更稳、更可复现。
构建缓存、Mojang 客户端 jar 和任何凭据都在 `.gitignore` 里，不入库。

---

## 四、两套构建链

| | `legacy/`（1.20.1–1.21.11） | `modern26/`（26.1–26.3） |
| --- | --- | --- |
| JDK | 21 | **25**（Mojang 26.1 起强制） |
| Gradle | 8.14 | 9.8.2 |
| Loom | `fabric-loom` 1.10 / 1.12 / 1.13（按 MC 版本分级） | `net.fabricmc.fabric-loom` 1.20.0-alpha.19（免重映射） |
| 映射 | Yarn | **无**（26.1 起 MC 不再混淆，Yarn 停更） |
| 源码类名 | Yarn 名 / `MusicDiscItem` 或 `jukeboxPlayable` | Mojang 官方名（`Component`、`Item.Properties`、`PackRepository` 等） |

构建命令示例（需自备上表工具链，仓库未附 Gradle Wrapper）：

```bash
cd legacy   && gradle build -Pmc=1.20.1      # 产物 build/libs/
cd modern26 && gradle build -Pmc=26.3       # 产物 build/libs/
```

> **多版本构建的一个坑**：`processResources` 用 `expand` 注入 `${mc}` 时，必须把 `mc`
> 声明为 Gradle 输入（`inputs.property`），否则增量构建会跳过资源处理，
> 导致 jar 文件名对但内部 `fabric.mod.json` 仍是上一次的版本。两套构建都已处理。

### 玩家运行时依赖

统一需要 **Fabric Loader**、**Fabric API**、**Cloth Config API**；**Mod Menu** 可选（提供游戏内设置入口）。
26.x 额外要求 **Java 25**、Loader ≥ `0.20.1`。各 MC 版本对应的具体坐标见
`legacy/上传清单.csv` 与 `modern26/26.x上传清单.csv`。

---

## 五、功能概览

| 功能 | 实现 |
| --- | --- |
| 游戏内设置界面 | Mod Menu → Neko Custom Discs → Configure（Cloth Config） |
| 配置音乐源路径 | 相对游戏目录或绝对路径，扫描文件夹内所有 `.ogg` |
| 生成唱片 | 为每个文件注册一张自定义唱片 |
| 音乐加载 | 写 `resourcepacks/CustomDiscs/`（`sounds.json` + ogg），并尽力自动启用资源包 |
| 获取方式 | 创造标签页、`/customdiscs give <id> [数量]`、合成配方 |

---

## 六、已知缺口（发布前务必看）

1. **实机验证范围**：`1.0.0-26.3` 已由作者在 Minecraft 26.3 实机测试通过；其余 20 个包只做过编译、CRC、class 数量与元数据声明校验，未进过游戏。
2. **唱片机播放链路未打通**：物品侧有 `jukeboxPlayable` 组件，但缺少
   `data/minecraft/jukebox_song/*.json` 数据驱动资源，唱片可能放上去不响。
3. `fabric.mod.json` 的 `environment` 为 `"client"`，但主入口注册了服务端命令，
   专用服务器不会加载；要支持服务器需改成 `"*"` 并重新构建验证。
4. 资源包自动挂载是 best-effort，失败时需在「选项 → 资源包」手动启用。
5. 图标已备（`icon.png` 512×512 / `icon-256.png` 256×256，原创）；封面横幅与项目描述配图尚未准备。
6. 26.x 用的是 Loom alpha 分支，后续出稳定版建议回归一次。
7. C 站目前仍需手动上传，自动同步只接了 M 站。

---

## 七、本地手动运行同步脚本

```bash
export MODRINTH_TOKEN='你的令牌'
python tools/sync_modrinth.py --check-only                 # 只校验本地，不联网
python tools/sync_modrinth.py                             # 联网预演，不写任何东西
python tools/sync_modrinth.py --go                        # 只补缺失版本
python tools/sync_modrinth.py --go --replace-mismatch     # 补缺失 + 替换文件已变的版本
```

脚本**绝不删除 `release-manifest.json` 之外的版本条目**，并且每次运行都会做最终复核，
打印清单外条目数量是否保持不变。

---

*为小红蛋整理喵~*
