package top.nekoaidev.customdiscs.client;

import me.shedaniel.clothconfig2.api.ConfigBuilder;
import me.shedaniel.clothconfig2.api.ConfigCategory;
import me.shedaniel.clothconfig2.api.ConfigEntryBuilder;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.text.Text;
import top.nekoaidev.customdiscs.CustomDiscs;
import top.nekoaidev.customdiscs.disc.DiscManager;
import top.nekoaidev.customdiscs.disc.ResourcePackSetup;

/**
 * 游戏内设置界面（基于 Cloth Config）。
 *
 * 配置项：
 *   - 音乐源文件夹路径（本地唱片音乐源的路径/文件位置）
 *   - 唱片音量（预留，当前走游戏“唱片”音量）
 *   - 是否启用合成配方
 *   - “重新扫描音乐文件夹”按钮
 *
 * 保存时会重新扫描并刷新动态资源包。注意：修改了音乐源文件夹中文件的增减后，
 * 新增/删除的唱片物品需要重启游戏才能注册；音频本身会热更新。
 */
@Environment(EnvType.CLIENT)
public class ConfigScreenProvider {
    public static Screen build(Screen parent) {
        DiscManager mgr = DiscManager.get();

        ConfigBuilder builder = ConfigBuilder.create()
                .setParentScreen(parent)
                .setTitle(Text.translatable("customdiscs.config.title"));

        builder.setSavingRunnable(() -> {
            mgr.saveConfig();
            mgr.scan();
            mgr.saveDiscs();
            ResourcePackSetup.setup();
            MinecraftClient.getInstance().reloadResources(); // 热更新音频
            // 1.21.2 起 ClientPlayerEntity.sendMessage 改为两参，跨版本签名不一致；
            // 这里不直接向玩家发消息，改由日志记录，保证同一套代码可在各版本编译。
            CustomDiscs.LOGGER.info("[CustomDiscs] 配置已保存，音乐已重新扫描，资源已重载");
        });

        ConfigEntryBuilder eb = builder.entryBuilder();
        ConfigCategory cat = builder.getOrCreateCategory(Text.literal("Neko Custom Discs"));

        cat.addEntry(eb.startStrField(
                        Text.translatable("customdiscs.config.musicSourcePath"),
                        mgr.getConfig().musicSourcePath)
                .setTooltip(Text.translatable("customdiscs.config.musicSourcePath.tooltip"))
                .setSaveConsumer(v -> mgr.getConfig().musicSourcePath = v)
                .build());

        cat.addEntry(eb.startDoubleField(
                        Text.translatable("customdiscs.config.volume"),
                        mgr.getConfig().volume)
                .setMin(0.0).setMax(1.0)
                .setSaveConsumer(v -> mgr.getConfig().volume = v.floatValue())
                .build());

        cat.addEntry(eb.startBooleanToggle(
                        Text.translatable("customdiscs.config.enableCrafting"),
                        mgr.getConfig().enableCraftingRecipes)
                .setSaveConsumer(v -> mgr.getConfig().enableCraftingRecipes = v)
                .build());

        cat.addEntry(eb.startBooleanToggle(
                        Text.translatable("customdiscs.config.scan"),
                        false)
                .setSaveConsumer(v -> {
                    if (v) {
                        mgr.scan();
                        mgr.saveDiscs();
                    }
                })
                .build());

        return builder.build();
    }
}
