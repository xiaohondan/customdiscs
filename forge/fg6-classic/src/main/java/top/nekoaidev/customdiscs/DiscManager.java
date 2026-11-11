package top.nekoaidev.customdiscs;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraftforge.fml.loading.FMLPaths;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;

/** 读取配置、扫描 .ogg、生成动态资源包。纯文件操作，不碰 Minecraft 注册表。 */
public final class DiscManager {
    public static final List<DiscEntry> DISCS = new ArrayList<>();
    private static Path gameDir;
    private static Path musicDir;
    private static Path packDir;
    private static String sourcePath = "customdiscs_music";
    private static boolean enableCrafting = true;

    private DiscManager() {}

    public static String getSourcePath() { return sourcePath; }
    public static void setSourcePath(String value) { sourcePath = value; }
    public static boolean isCraftingEnabled() { return enableCrafting; }
    public static List<DiscEntry> discs() { return DISCS; }

    public static void load() {
        gameDir = FMLPaths.GAMEDIR.get();
        Path cfg = gameDir.resolve("config/nekocustomdiscs.json");
        try {
            if (Files.exists(cfg)) {
                JsonObject o = JsonParser.parseString(Files.readString(cfg, StandardCharsets.UTF_8)).getAsJsonObject();
                if (o.has("musicSourcePath")) sourcePath = o.get("musicSourcePath").getAsString();
                if (o.has("enableCrafting")) enableCrafting = o.get("enableCrafting").getAsBoolean();
            } else {
                saveConfig();
            }
        } catch (Exception e) {
            NekoCustomDiscsForge.LOGGER.warn("读取配置失败，使用默认值：{}", e.toString());
        }
        Path raw = Paths.get(sourcePath);
        musicDir = (raw.isAbsolute() ? raw : gameDir.resolve(raw)).normalize();
        packDir = gameDir.resolve("resourcepacks/NekoCustomDiscs");
        DISCS.clear();
        if (!Files.isDirectory(musicDir)) {
            try { Files.createDirectories(musicDir); } catch (IOException ignored) {}
            return;
        }
        try (Stream<Path> s = Files.walk(musicDir)) {
            s.filter(f -> Files.isRegularFile(f)
                    && f.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(".ogg"))
             .sorted()
             .forEach(f -> {
                 String rel = musicDir.relativize(f).toString().replace('\\', '/');
                 String base = rel.substring(0, rel.length() - 4);
                 String fileName = f.getFileName().toString();
                 String shown = fileName.substring(0, fileName.length() - 4);
                 DISCS.add(new DiscEntry(sanitize(base), shown, f, 120));
             });
        } catch (IOException e) {
            NekoCustomDiscsForge.LOGGER.warn("扫描音乐目录失败：{}", e.toString());
        }
    }

    /** 把 .ogg 复制进一个标准资源包，并写 sounds.json 与 pack.mcmeta。 */
    public static void writePack() {
        try {
            Path sounds = packDir.resolve("assets/customdiscs/sounds");
            Files.createDirectories(sounds);
            JsonObject root = new JsonObject();
            for (DiscEntry e : DISCS) {
                Path dest = sounds.resolve(e.path() + ".ogg");
                Files.createDirectories(dest.getParent());
                Files.copy(e.file(), dest, StandardCopyOption.REPLACE_EXISTING);
                JsonObject event = new JsonObject();
                JsonObject entry = new JsonObject();
                entry.addProperty("name", e.soundId().toString());
                entry.addProperty("stream", true);
                com.google.gson.JsonArray arr = new com.google.gson.JsonArray();
                arr.add(entry);
                event.add("sounds", arr);
                root.add(e.soundId().toString(), event);
            }
            Files.writeString(packDir.resolve("assets/customdiscs/sounds.json"),
                    root.toString(), StandardCharsets.UTF_8);
            Files.writeString(packDir.resolve("pack.mcmeta"),
                    "{\"pack\":{\"pack_format\":15,\"description\":\"Neko Custom Discs 动态资源包\","
                    + "\"supported_formats\":[1,9999]}}", StandardCharsets.UTF_8);
        } catch (IOException e) {
            NekoCustomDiscsForge.LOGGER.warn("生成动态资源包失败：{}", e.toString());
        }
    }

    public static void saveConfig() {
        try {
            Path cfg = FMLPaths.GAMEDIR.get().resolve("config/nekocustomdiscs.json");
            Files.createDirectories(cfg.getParent());
            JsonObject o = new JsonObject();
            o.addProperty("musicSourcePath", sourcePath);
            o.addProperty("enableCrafting", enableCrafting);
            o.addProperty("volume", 1.0);
            Files.writeString(cfg, o.toString(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            NekoCustomDiscsForge.LOGGER.warn("保存配置失败：{}", e.toString());
        }
    }

    private static String sanitize(String raw) {
        StringBuilder b = new StringBuilder();
        for (char c : raw.toLowerCase(Locale.ROOT).toCharArray()) {
            b.append((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
                    || c == '_' || c == '/' || c == '.' || c == '-' ? c : '_');
        }
        String s = b.toString();
        return s.isEmpty() ? "disc" : s;
    }
}
