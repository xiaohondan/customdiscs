package top.nekoaidev.customdiscs;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.RecordItem;

import java.util.function.Supplier;

/** 1.20.x：继承原版唱片物品，只改显示名。 */
public class CustomRecordItem extends RecordItem {
    private final DiscEntry entry;

    public CustomRecordItem(DiscEntry entry, Supplier<SoundEvent> sound) {
        super(0, sound, new Item.Properties().stacksTo(1).rarity(Rarity.RARE), entry.lengthSeconds());
        this.entry = entry;
    }

    @Override
    public Component getName(ItemStack stack) {
        return Component.literal(entry.displayName());
    }

    @Override
    public MutableComponent getDisplayName() {
        return Component.literal(entry.displayName());
    }

    public DiscEntry entry() {
        return entry;
    }
}
