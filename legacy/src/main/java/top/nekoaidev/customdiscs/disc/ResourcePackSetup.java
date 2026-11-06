package top.nekoaidev.customdiscs.disc;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.resource.ResourcePackManager;
import top.nekoaidev.customdiscs.Compat;
import top.nekoaidev.customdiscs.CustomDiscs;
import top.nekoaidev.customdiscs.config.DiscEntry;
import top.nekoaidev.customdiscs.config.ModConfig;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

/**
 * 把玩家本地音乐文件桥接进 Minecraft 的声音系统。
 *
 * 做法：把扫描到的 .ogg 复制到运行目录下的 resourcepacks/CustomDiscs/，并在其中生成
 *   - assets/customdiscs/sounds.json      （声明每张唱片的 SoundEvent 与 ogg 路径）
 *   - assets/customdiscs/sounds/disc/*.ogg
 *   - data/customdiscs/recipes/*.json     （可选的合成配方）
 *   - pack.mcmeta
 * 然后把这个目录作为「文件夹资源包」挂载（现代 Fabric 已移除 FabricResourcePackBuilder，
 * 故改为写入 resourcepacks/ 目录并由 ResourcePackManager 启用），SoundManager 在资源重载时
 * 就能像读取普通资源包一样加载这些本地音乐。
 */
public final class ResourcePackSetup {
    private static boolean registered = false;

    private ResourcePackSetup() {}

    public static void setup() {
        DiscManager mgr = DiscManager.get();
        Path gameDir = FabricLoader.getInstance().getGameDir();
        // 生成到 resourcepacks/CustomDiscs/，使其成为可被资源包界面发现的「文件夹资源包」
        Path assetsRoot = gameDir.resolve("resourcepacks/CustomDiscs");
        Path soundsDir = assetsRoot.resolve("assets/customdiscs/sounds/disc");
        Path dataDir = assetsRoot.resolve("data/customdiscs/recipes");

        try {
            Files.createDirectories(soundsDir);
            Files.createDirectories(dataDir);

            // 清理旧的音频，避免删掉的唱片残留
            try (DirectoryStream<Path> ds = Files.newDirectoryStream(soundsDir)) {
                for (Path p : ds) Files.deleteIfExists(p);
            }

            JsonObject soundsJson = new JsonObject();
            ModConfig cfg = mgr.getConfig();

            for (DiscEntry e : mgr.getDiscs()) {
                // 复制 ogg 到资源包目录
                Path src = mgr.musicFolder().resolve(e.fileName);
                if (Files.exists(src)) {
                    Files.copy(src, soundsDir.resolve(e.id + ".ogg"), StandardCopyOption.REPLACE_EXISTING);
                } else {
                    CustomDiscs.LOGGER.warn("[CustomDiscs] 找不到音乐文件：{}", src);
                }

                // sounds.json 中的一项
                JsonObject snd = new JsonObject();
                snd.addProperty("category", "record");
                JsonObject o = new JsonObject();
                o.addProperty("name", CustomDiscs.MOD_ID + ":disc/" + e.id);
                o.addProperty("stream", true);
                JsonArray list = new JsonArray();
                list.add(o);
                snd.add("sounds", list);
                soundsJson.add("disc_" + e.id, snd);

                // 合成配方
                if (cfg.enableCraftingRecipes) {
                    writeRecipe(dataDir, e);
                }
            }

            // 不启用合成时，清掉上次生成的配方
            if (!cfg.enableCraftingRecipes) {
                try (DirectoryStream<Path> ds = Files.newDirectoryStream(dataDir)) {
                    for (Path p : ds) Files.deleteIfExists(p);
                }
            }

            Files.writeString(assetsRoot.resolve("assets/customdiscs/sounds.json"),
                    DiscManager.GSON.toJson(soundsJson));
            // supported_formats 给一个很宽的范围，避免各版本 pack_format 不兼容被拒绝
            Files.writeString(assetsRoot.resolve("pack.mcmeta"),
                    "{\"pack\":{\"pack_format\":" + Compat.currentPackFormat()
                            + ",\"supported_formats\":[1,9999],\"description\":\"Custom Discs 动态资源包\"}}");

            // 仅首次挂载资源包；之后只要刷新文件并触发资源重载即可
            if (!registered) {
                mountResourcePack();
                registered = true;
                CustomDiscs.LOGGER.info("[CustomDiscs] 已生成资源包（共 {} 个唱片音频），路径：{}",
                        mgr.getDiscs().size(), assetsRoot);
            }
        } catch (IOException ex) {
            CustomDiscs.LOGGER.error("[CustomDiscs] 构建动态资源包失败", ex);
        }
    }

    /**
     * 把 resourcepacks/CustomDiscs 文件夹作为资源包启用。
     * 现代 Fabric 已无 FabricResourcePackBuilder，这里借助 ResourcePackManager
     * 重新扫描并启用该文件夹包（best-effort：任何异常都降级为「提示玩家手动启用」，
     * 资源包文件本身已经写好，不会丢）。
     */
    private static void mountResourcePack() {
        try {
            MinecraftClient client = MinecraftClient.getInstance();
            ResourcePackManager manager = client.getResourcePackManager();
            // 重新扫描以发现刚写好的文件夹资源包
            manager.scanPacks();
            // 文件夹型资源包的固定 id 形如 file/<文件夹名>
            String id = "file/CustomDiscs";
            if (manager.hasProfile(id)) {
                manager.enable(id);
                CustomDiscs.LOGGER.info("[CustomDiscs] 已自动启用 \"CustomDiscs\" 资源包，重启/进入世界即可加载本地音乐");
            } else {
                CustomDiscs.LOGGER.info("[CustomDiscs] 请在 选项 → 资源包 中手动启用 \"CustomDiscs\" 资源包以加载本地音乐");
            }
        } catch (Throwable t) {
            CustomDiscs.LOGGER.warn("[CustomDiscs] 自动挂载资源包失败，请手动在资源包界面启用 CustomDiscs", t);
        }
    }

    /** 合成配方：主材料环绕一张纸，产出对应唱片 */
    private static void writeRecipe(Path dataDir, DiscEntry e) throws IOException {
        JsonObject root = new JsonObject();
        root.addProperty("type", "minecraft:crafting_shaped");

        JsonArray pattern = new JsonArray();
        pattern.add(" A ");
        pattern.add("ABA");
        pattern.add(" A ");
        root.add("pattern", pattern);

        JsonObject key = new JsonObject();
        JsonObject a = new JsonObject();
        a.addProperty("item", e.material);
        JsonObject b = new JsonObject();
        b.addProperty("item", "minecraft:paper");
        key.add("A", a);
        key.add("B", b);
        root.add("key", key);

        JsonObject result = new JsonObject();
        result.addProperty("item", e.getItemId().toString());
        result.addProperty("count", 1);
        root.add("result", result);

        Files.writeString(dataDir.resolve("disc_" + e.id + ".json"), DiscManager.GSON.toJson(root));
    }
}
