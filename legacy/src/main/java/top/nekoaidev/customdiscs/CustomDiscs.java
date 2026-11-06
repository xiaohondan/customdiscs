package top.nekoaidev.customdiscs;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.sound.SoundEvent;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import top.nekoaidev.customdiscs.config.DiscEntry;
import top.nekoaidev.customdiscs.disc.CustomRecordItem;
import top.nekoaidev.customdiscs.disc.DiscManager;
import top.nekoaidev.customdiscs.command.DiscCommand;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 模组主入口（common 端，服务端/客户端都会执行）。
 * 负责：读取配置 → 扫描音乐源 → 注册 SoundEvent 与自定义唱片物品 → 注册创造标签页 → 注册命令。
 */
public class CustomDiscs implements ModInitializer {
    public static final String MOD_ID = "customdiscs";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    public static final Identifier ITEM_GROUP_ID = Identifier.of(MOD_ID, "discs");

    /** id -> 已注册的唱片物品，供命令 / 合成配方复用 */
    public static final Map<String, CustomRecordItem> REGISTERED_DISCS = new LinkedHashMap<>();

    @Override
    public void onInitialize() {
        DiscManager mgr = DiscManager.get();
        mgr.loadConfig();
        mgr.loadDiscs();
        if (mgr.getDiscs().isEmpty()) {
            mgr.scan();
            mgr.saveDiscs();
        }

        registerDiscs();
        registerItemGroup();
        registerCommands();

        LOGGER.info("[CustomDiscs] 已加载 {} 张自定义唱片", REGISTERED_DISCS.size());
    }

    /** 为每个扫描到的音乐文件注册 SoundEvent 与对应的唱片物品 */
    private void registerDiscs() {
        DiscManager mgr = DiscManager.get();
        for (DiscEntry e : mgr.getDiscs()) {
            Identifier soundId = e.getSoundId();
            // 注册 SoundEvent（资源包中的 ogg 会在客户端资源重载时绑定到它）
            SoundEvent sound = SoundEvent.of(soundId);
            Registry.register(Registries.SOUND_EVENT, soundId, sound);

            int comparatorOutput = Math.min(15, Math.max(1, e.lengthInSeconds / 30 + 1));
            Item.Settings settings = new Item.Settings().maxCount(1);
            CustomRecordItem item = new CustomRecordItem(
                    e,
                    sound,
                    settings,
                    comparatorOutput,
                    Math.max(1, e.lengthInSeconds)
            );

            Identifier itemId = e.getItemId();
            Registry.register(Registries.ITEM, itemId, item);
            REGISTERED_DISCS.put(e.id, item);
        }
    }

    /** 把所有唱片放进一个独立的创造模式标签页 */
    private void registerItemGroup() {
        Item icon = REGISTERED_DISCS.isEmpty()
                ? Items.MUSIC_DISC_11
                : REGISTERED_DISCS.values().iterator().next();
        // 用 var 兼容 1.20.4- 的 CreativeModeTab 与 1.20.5+ 的 ItemGroup（同一套注册写法）
        var tab = FabricItemGroup.builder()
                .displayName(Text.literal("Neko Custom Discs"))
                .icon(() -> new ItemStack(icon))
                .entries((context, entries) -> REGISTERED_DISCS.values().forEach(entries::add))
                .build();
        Registry.register(Registries.ITEM_GROUP, ITEM_GROUP_ID, tab);
    }

    private void registerCommands() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
                DiscCommand.register(dispatcher));
    }
}
