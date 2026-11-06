package top.nekoaidev.customdiscs.disc;

import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.sound.SoundEvent;
import net.minecraft.text.Text;
import top.nekoaidev.customdiscs.config.DiscEntry;

/**
 * 自定义唱片物品（Minecraft 1.21+ 变体）。
 *
 * 1.21 起 Mojang 删除了 MusicDiscItem，唱片机改为读取 JukeboxSong 数据驱动注册表，
 * 物品只通过 JukeboxPlayable 组件携带一个指向该注册表的 key。因此这里直接继承 Item，
 * 并在构造时把 jukeboxPlayable 组件写进 Item.Settings。
 *
 * 注意：对应的 JukeboxSong 条目（data/minecraft/jukebox_song/*.json）属于数据包内容，
 * 需由资源/数据包提供；本类只负责物品侧，运行时能否播放取决于该条目是否存在。
 */
public class CustomRecordItem extends Item {
    private final DiscEntry entry;

    public CustomRecordItem(DiscEntry entry,
                            SoundEvent sound,
                            Item.Settings settings,
                            int comparatorOutput,
                            int lengthInSeconds) {
        super(settings.jukeboxPlayable(RegistryKey.of(RegistryKeys.JUKEBOX_SONG, entry.getSoundId())));
        this.entry = entry;
    }

    @Override
    public Text getName(ItemStack stack) {
        return Text.literal(entry.displayName);
    }

    public DiscEntry getEntry() {
        return entry;
    }
}
