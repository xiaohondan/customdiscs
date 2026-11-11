package top.nekoaidev.customdiscs;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;

/**
 * 1.21 起原版删除了 RecordItem，唱片改由 jukeboxPlayable 数据组件驱动。
 * 组件指向 data/customdiscs/jukebox_song/ 下的同名数据文件（由 DiscManager 生成）。
 */
public class CustomRecordItem extends Item {
    private final DiscEntry entry;

    public CustomRecordItem(DiscEntry entry) {
        super(new Item.Properties()
                .stacksTo(1)
                .rarity(Rarity.RARE)
                .jukeboxPlayable(ResourceKey.create(Registries.JUKEBOX_SONG, entry.soundId()))
                .component(DataComponents.ITEM_NAME, Component.literal(entry.displayName())));
        this.entry = entry;
    }

    public DiscEntry entry() {
        return entry;
    }
}
