package top.nekoaidev.customdiscs.disc;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import net.fabricmc.loader.api.FabricLoader;
import top.nekoaidev.customdiscs.CustomDiscs;
import top.nekoaidev.customdiscs.config.DiscEntry;
import top.nekoaidev.customdiscs.config.ModConfig;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 扫描音乐源文件夹、维护唱片列表，并负责配置文件的读写。
 * 这是一个进程内单例：common 端与 client 端共用同一份数据。
 */
public final class DiscManager {
    public static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private static final DiscManager INSTANCE = new DiscManager();
    public static DiscManager get() { return INSTANCE; }

    private final List<DiscEntry> discs = new ArrayList<>();
    private ModConfig config = new ModConfig();

    private DiscManager() {}

    public ModConfig getConfig() { return config; }
    public void setConfig(ModConfig c) { this.config = c; }
    public List<DiscEntry> getDiscs() { return discs; }

    private Path configDir() {
        return FabricLoader.getInstance().getGameDir().resolve("config/customdiscs");
    }

    /** 音乐源文件夹的绝对路径（相对路径相对于游戏目录解析） */
    public Path musicFolder() {
        Path p = Paths.get(config.musicSourcePath);
        if (!p.isAbsolute()) {
            p = FabricLoader.getInstance().getGameDir().resolve(p);
        }
        return p;
    }

    // ---------- 配置读写 ----------

    public void loadConfig() {
        Path file = configDir().resolve("config.json");
        try {
            if (Files.exists(file)) {
                config = GSON.fromJson(Files.readString(file), ModConfig.class);
                if (config == null) config = new ModConfig();
            } else {
                config = new ModConfig();
                saveConfig();
            }
        } catch (Exception e) {
            CustomDiscs.LOGGER.warn("[CustomDiscs] 读取 config.json 失败，使用默认配置", e);
            config = new ModConfig();
        }
    }

    public void saveConfig() {
        try {
            Files.createDirectories(configDir());
            Files.writeString(configDir().resolve("config.json"), GSON.toJson(config));
        } catch (IOException e) {
            CustomDiscs.LOGGER.error("[CustomDiscs] 写入 config.json 失败", e);
        }
    }

    public void loadDiscs() {
        Path file = configDir().resolve("discs.json");
        try {
            if (Files.exists(file)) {
                DiscEntry[] arr = GSON.fromJson(Files.readString(file), DiscEntry[].class);
                discs.clear();
                if (arr != null) {
                    for (DiscEntry e : arr) discs.add(e);
                }
            }
        } catch (Exception e) {
            CustomDiscs.LOGGER.warn("[CustomDiscs] 读取 discs.json 失败", e);
        }
    }

    public void saveDiscs() {
        try {
            Files.createDirectories(configDir());
            Files.writeString(configDir().resolve("discs.json"), GSON.toJson(discs));
        } catch (IOException e) {
            CustomDiscs.LOGGER.error("[CustomDiscs] 写入 discs.json 失败", e);
        }
    }

    // ---------- 扫描 ----------

    /**
     * 扫描音乐源文件夹中所有 .ogg 文件，生成唱片列表。
     * 已经存在的唱片（按 id 匹配）会保留玩家手动修改过的元数据。
     */
    public void scan() {
        Map<String, DiscEntry> old = new HashMap<>();
        for (DiscEntry e : discs) old.put(e.id, e);
        discs.clear();

        Path dir = musicFolder();
        if (!Files.isDirectory(dir)) {
            try {
                Files.createDirectories(dir);
                CustomDiscs.LOGGER.info("[CustomDiscs] 已创建音乐源文件夹：{}", dir);
            } catch (IOException e) {
                CustomDiscs.LOGGER.error("[CustomDiscs] 无法创建音乐源文件夹：{}", dir, e);
            }
            return;
        }

        try (DirectoryStream<Path> ds = Files.newDirectoryStream(dir, "*.{ogg,OGG}")) {
            for (Path f : ds) {
                String name = f.getFileName().toString();
                String id = name.replaceAll("\\.[oO][gG][gG]$", "").toLowerCase(Locale.ROOT);
                if (id.isEmpty()) continue;

                DiscEntry e = new DiscEntry(id, name);
                DiscEntry prev = old.get(id);
                if (prev != null) {
                    e.displayName = prev.displayName;
                    e.material = prev.material;
                    e.color = prev.color;
                    if (prev.lengthInSeconds > 0) e.lengthInSeconds = prev.lengthInSeconds;
                }
                discs.add(e);
            }
            CustomDiscs.LOGGER.info("[CustomDiscs] 扫描到 {} 个音乐文件", discs.size());
        } catch (IOException e) {
            CustomDiscs.LOGGER.error("[CustomDiscs] 扫描音乐源文件夹失败", e);
        }
    }

    /** 生成 sounds.json 需要的 JSON 内容（供 ResourcePackSetup 写入） */
    public JsonObject buildSoundsJson() {
        JsonObject root = new JsonObject();
        for (DiscEntry e : discs) {
            JsonObject sound = new JsonObject();
            sound.addProperty("category", "record");
            JsonObject entry = new JsonObject();
            entry.addProperty("name", CustomDiscs.MOD_ID + ":disc/" + e.id);
            entry.addProperty("stream", true);
            com.google.gson.JsonArray list = new com.google.gson.JsonArray();
            list.add(entry);
            sound.add("sounds", list);
            root.add("disc_" + e.id, sound);
        }
        return root;
    }
}
