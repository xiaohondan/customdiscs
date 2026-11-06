# Neko Custom Discs —— 我的世界自定义唱片模组（Fabric 多版本）

让玩家用**本地 `.ogg` 音乐文件**自定义唱片，并通过**游戏内设置界面**配置音乐源路径。
玩家把音乐放进指定文件夹后，模组会扫描并为每个文件注册一张自定义唱片，可在创造标签页、命令、合成配方中获取。

> 基于 **Fabric + Fabric API + Cloth Config**（必需），**Mod Menu**（可选）。
> **合计支持 21 个版本**：本目录 18 个（`1.20.1`–`1.20.6`、`1.21`–`1.21.11`），
> 加上 `CustomDiscs26/` 目录单独交付的 3 个（`26.1`、`26.2`、`26.3`）。
> **版本编号更正**：Mojang 自 2026 年起改用「年份.第几次更新」编号，`26.1` / `26.1.1` / `26.1.2` / `26.2` / `26.3`
> 都是**真实存在的正式版**（官方清单当前最新正式版为 `26.3`）。真正不存在的是旧编号的 `1.22` 及以上；
> 早期文档把两者混写成 `1.26.3`，那是占位假数据，已删除。**26.1 / 26.2 / 26.3 已于同日单独出包**，见下方专节。

---

## 一、当前交付状态（2026-11-06）

- `build/libs/` 下 **18 个 jar 全部出齐**，逐个校验通过：压缩包 CRC 无错误、每个 11 个 class、
  `fabric.mod.json` 的 `minecraft` 声明为精确 `=对应版本`（不会被平台展开成全版本兼容）。
- 一次性打包：`CustomDiscs-1.0.0-all-18-versions.zip`（内含全部 18 个 jar，CRC 复核通过）。
- 上传对照表：`上传清单.csv`（jar 文件名 ↔ MC 版本 ↔ 平台版本标签 ↔ 依赖）。
- 发布步骤：`发布指南.md`（中文，M 站 / C 站）。
- **重要**：`1.0.0-26.3` 已由作者在 Minecraft 26.3 实机测试通过；本目录其余包目前只通过编译与压缩包校验，**尚未在真实游戏里启动验证**；已知功能缺口见第六节。

### 26.x 已单独交付（26.1 / 26.2 / 26.3）

这三个版本走的是**另一条构建链**，产物在平级目录 `CustomDiscs26/` 中，与本项目 18 个包互不混用：

- 交付：`CustomDiscs-1.0.0-26.x-3-versions.zip`（3 个 jar）、`26.x上传清单.csv`、`26.x发布说明.md`；
  三个包 CRC、11 个 class、`version` 与 `minecraft` 精确声明、`authors=["小红蛋"]` 均逐个校验通过。
- 工具链：JDK 25 + Gradle 9.8.2 + `net.fabricmc.fabric-loom 1.20.0-alpha.19`（免重映射），
  不再用 Yarn mappings；玩家运行时需 Java 25、Fabric Loader ≥ 0.20.1。
- 依赖：Fabric API `0.145.1+26.1` / `0.161.0+26.2` / `0.165.2+26.3`，
  Cloth Config `26.1.154` / `26.2.155` / `26.3.159`，Mod Menu `18.0.2` / `20.0.3` / `21.0.0`。
- 上传方式：**作为 3 个新版本追加到同一 M 站 / C 站项目**，不要删掉已有的 18 个版本条目。

详细构建改动、已知缺口与上传步骤见 `CustomDiscs26/26.x发布说明.md`。
两个目录共用同一套功能设计，因此第六节列出的功能缺口（尤其唱片机播放链路未打通、未实机验证）
对 26.x 同样成立。

---

## 二、功能概览

| 需求 | 实现 |
| --- | --- |
| 游戏内设置界面 | Mod Menu → Neko Custom Discs → Configure，基于 Cloth Config |
| 本地音乐源路径配置 | 设置项「音乐源文件夹」，支持相对（相对游戏目录）或绝对路径 |
| 指定音乐源后生成唱片 | 启动时扫描该文件夹所有 `.ogg`，为每个文件注册一张自定义唱片 |
| 音乐加载 | 生成 `resourcepacks/CustomDiscs/`（含 `assets/customdiscs/sounds.json` 与 ogg），并尽量调用 `ResourcePackManager` 挂载 |
| 唱片获取方式 | ① 创造标签页 ② `/customdiscs give <id> [数量]` ③ 合成配方（默认开启） |

---

## 三、多版本架构（真实情况）

- **核心代码** `src/main/java` 全版本通用。
- **1.20.x**：yarn 里唱片类实际叫 `MusicDiscItem`，构造为 `(int, SoundEvent, Item.Settings, int)`。
  `src/v-old`、`src/v-new` 两份变体目前内容一致，仅为日后区分保留。
- **1.21+**：Mojang 删除 `MusicDiscItem`，唱片改为 `JukeboxSong` 数据驱动注册表；
  `src/v-modern` 改为继承 `Item`，用 `settings.jukeboxPlayable(RegistryKey.of(RegistryKeys.JUKEBOX_SONG, id))`。
- **动态资源包**：`FabricResourcePackBuilder` 已被 Fabric 移除，现写入 `resourcepacks/CustomDiscs/` 后
  best-effort 调用 `ResourcePackManager` 挂载。
- **Java**：1.20.x 编译目标 17，1.21+ 编译目标 21；本机只需一个 **JDK 21**（靠 `--release` 兼容低版本字节码）。
- **构建插件**：`settings.gradle` 按 `-Pmc` 选 Fabric Loom：
  `1.20.1`–`1.21.8` 用 `1.10.+`，`1.21.9`/`1.21.10` 用 `1.12.7`（unpick V3/V4），
  `1.21.11` 用 `1.13.6`（该版本依赖由 Loom 1.13.3 构建，旧版会被拒绝）。Loom 1.14 起要求 Gradle 9.2，本机 8.14 用不了。
- **`minecraft` 声明**：`processResources` 在构建时把 `=目标版本` 注入 `fabric.mod.json`，每个 jar 只声明自己那一个版本。

### 构建

```bash
# 构建单个版本
./gradlew build -Pmc=1.20.1
./gradlew build -Pmc=1.21.11

# 一键构建全部 18 个版本
bash tools/build_all.sh        # Windows 用 tools/build_all.bat
```

产物在 `build/libs/`，文件名带版本后缀（如 `customdiscs-1.0.0-1.20.1.jar`），互不覆盖。
工具链在 `.buildenv/`（JDK 21 + Gradle 8.14），`GRADLE_USER_HOME` 复用缓存目录。

---

## 四、依赖版本映射（节选，完整见 `build.gradle` 的 `pins` 表）

| Minecraft | yarn | loader | fabric-api | cloth-config | modmenu |
| --- | --- | --- | --- | --- | --- |
| 1.20.1 | 1.20.1+build.10 | 0.14.21 | 0.91.0+1.20.1 | 13.0.121 | 9.0.0 |
| 1.20.6 | 1.20.6+build.1 | 0.15.11 | 0.97.8+1.20.6 | 14.0.129 | 11.0.0 |
| 1.21 | 1.21+build.9 | 0.16.14 | 0.102.0+1.21 | 15.0.140 | 11.0.5 |
| 1.21.6 | 1.21.6+build.1 | 0.16.14 | 0.128.2+1.21.6 | 19.0.147 | 15.0.2 |
| 1.21.11 | 1.21.11+build.6 | 0.17.3 | 0.141.6+1.21.11 | 21.11.151 | 17.0.1 |

18 个版本的依赖号都按各 Maven 仓库 metadata 核对过，均返回 200。

---

## 五、使用步骤

### 1. 放入音乐文件
必须是 **`.ogg`（Ogg Vorbis）**，MP3 / WAV 无法被游戏声音系统读取。默认目录
`<游戏目录>/config/customdiscs/music/`。转换示例：`ffmpeg -i in.mp3 -c:a libvorbis out.ogg`。
增删音乐文件后需**重启游戏**才能注册新的唱片物品。

### 2. 打开设置界面
`Esc → Mods → Neko Custom Discs → Configure`：音乐源文件夹、唱片音量（预留）、启用合成配方、重新扫描。

### 3. 获取并使用唱片
- 创造模式标签页「自定义唱片」；
- 命令 `/customdiscs give <唱片id> [数量]`，id 为文件名去扩展名（小写）；
- 合成：主材料（默认金锭）环绕一张纸；
- 播放：放进唱片机，受游戏「唱片」音量控制。

---

## 六、已知限制与发布前待办（如实列出）

1. **1.21+ 播放链路未打通**：`JukeboxSong` 需要 `data/minecraft/jukebox_song/*.json` 数据包条目，
   当前只做了物品侧的 `JukeboxPlayable` 组件；动态资源包只写 `assets`、不写 `data`。
   因此 1.21 及以上版本的唱片机**可能不响**，尚未实机验证。
2. **除 26.3 外的包仅通过编译，未实机启动验证**。建议发布前至少用 1.20.1 与 1.21.11 各跑一次游戏。
3. `fabric.mod.json` 的 `environment` 仍是 `client`，但代码注册了服务端命令
   `/customdiscs give`；专用服务器不会加载本模组，该命令在服务器上不可用。
   若要支持服务器需改为 `"*"` 并重新构建。
4. `authors` 已统一改为 `["小红蛋"]`（18 个 jar 内元数据 + 源码模板 + 总包同步，无需重新编译）。
5. **如实披露**：原 Custom Discs 项目版本不全或已停更；本 Neko Custom Discs 为重新自行设计、独立实现，未复制或改写该项目任何源代码与素材，无任何借鉴与抄袭。本仓库源码由 AI 辅助生成（依据 Fabric / Cloth Config 官方公开 API 文档），平台询问时如实披露。`1.0.0-26.3` 已实机测试通过。
6. 图标已备（`icon.png` / `icon-256.png`，原创）、MIT `LICENSE` 已备；封面图尚未准备。

---

## 七、项目结构

```
CustomDiscs/
├── build.gradle / gradle.properties / settings.gradle
├── tools/build_all.bat / build_all.sh / progress.py
├── 构建进度.html                  # 每 10 秒刷新的构建进度页
├── CustomDiscs-1.0.0-all-18-versions.zip
├── 上传清单.csv
├── README.md / 发布指南.md
├── src/
│   ├── main/java/top/nekoaidev/customdiscs/    # 核心逻辑（全版本通用）
│   │   ├── CustomDiscs.java                     # 注册 SoundEvent / 物品 / 标签页 / 命令
│   │   ├── Compat.java                          # 跨版本兼容层（不依赖 MC 版本 API）
│   │   ├── config/  disc/  command/  client/
│   │   └── client/                              # 设置界面 + Mod Menu 入口
│   ├── v-old/java/.../disc/CustomRecordItem.java     # 1.20.1–1.20.4
│   ├── v-new/java/.../disc/CustomRecordItem.java     # 1.20.5–1.20.6
│   └── v-modern/java/.../disc/CustomRecordItem.java  # 1.21+
└── build/libs/customdiscs-1.0.0-<mc>.jar  × 18
```

---

*为小红蛋整理喵~*
