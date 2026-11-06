package top.nekoaidev.customdiscs.disc;

import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.MusicDiscItem;
import net.minecraft.sound.SoundEvent;
import net.minecraft.text.MutableText;
import net.minecraft.text.Text;
import top.nekoaidev.customdiscs.config.DiscEntry;

/**
 * 自定义唱片物品（新 API 变体，Minecraft 1.20.5+）。
 * 1.20.5 起 RecordItem 改名 MusicDiscItem，构造额外接收 lengthInSeconds。
 */
public class CustomRecordItem extends MusicDiscItem {
    private final DiscEntry entry;

    public CustomRecordItem(DiscEntry entry,
                            SoundEvent sound,
                            Item.Settings settings,
                            int comparatorOutput,
                            int lengthInSeconds) {
        super(comparatorOutput, sound, settings, lengthInSeconds);
        this.entry = entry;
    }

    @Override
    public Text getName(ItemStack stack) {
        return Text.literal(entry.displayName);
    }

    @Override
    public MutableText getDescription() {
        return Text.literal(entry.displayName);
    }

    public DiscEntry getEntry() {
        return entry;
    }
}
