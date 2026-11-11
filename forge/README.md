# Forge Source / Forge 版源码

This directory contains the **Forge** loader implementation of Neko Custom Discs, alongside the Fabric implementation in `legacy/` and `modern26/`.

本目录是 Neko Custom Discs 的 **Forge 加载器** 源码，与 `legacy/`、`modern26/` 中的 Fabric 版并列。

## Supported Versions / 支持的版本

- **21 Minecraft versions**, `1.20.1` → `26.3`
- Forge loader only (Fabric source lives in the repo root `legacy/` + `modern26/`).

## Source Layout / 源码结构

The Forge port is split into build-family subprojects because the Minecraft / Forge API changed across versions (Screen API, `jukebox_song` data components, EventBus 7, ForgeGradle 7):

Forge 移植按构建族拆分为多个子工程，因为不同 MC 版本间 API 有变动（界面 API、jukebox_song 数据组件、EventBus 7、ForgeGradle 7）：

| Subproject / 子工程 | Minecraft Versions / 版本 | Notes / 说明 |
| --- | --- | --- |
| `fg6-classic/` | `1.20.1` – `1.20.6`, `1.21` | ForgeGradle 6, classic `Screen` API |
| `fg6-datacomponent/` | `1.21.1` – `1.21.10` | `jukebox_song` data-component registration |
| `fg6-eb7/` | `1.21.6` – `1.21.10` | EventBus 7 (`BusGroup`) variant |
| `fg7/` | `1.21.11`, `26.1`, `26.1.1`, `26.1.2`, `26.2`, `26.3` | ForgeGradle 7; `src/main` shared classes + `src/v-1211` & `src/v-26` ConfigScreen variants |

## Build / 构建

Each subproject is an independent Gradle project. Set the target version via `gradle.properties` (`mc=` / `forgeVer=`) and run:

每个子工程是独立的 Gradle 工程。通过 `gradle.properties` 指定目标版本（`mc=` / `forgeVer=`）后构建：

```bash
gradle build
```

Prebuilt artifacts (21 jars, `1.20.1` → `26.3`) are distributed via Modrinth; see the project wiki for the download matrix.

预编译产物（21 个 jar，`1.20.1` → `26.3`）通过 Modrinth 分发，下载矩阵见项目 Wiki。

## License / 许可证

MIT — Author / 作者: 小红蛋 (Xiaohongdan). Source is AI-assisted, based on official public Fabric / Forge / Cloth Config API documentation.

MIT 许可证 — 作者：小红蛋。源码由 AI 辅助生成，依据 Fabric / Forge / Cloth Config 官方公开 API 文档。
