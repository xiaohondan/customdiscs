package top.nekoaidev.customdiscs;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.client.ConfigScreenHandler;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.LinkedHashMap;
import java.util.Map;

@Mod(NekoCustomDiscsForge.MODID)
public class NekoCustomDiscsForge {
    public static final String MODID = "customdiscs";
    public static final Logger LOGGER = LoggerFactory.getLogger("Neko Custom Discs");

    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    private static final Map<String, RegistryObject<Item>> DISC_ITEMS = new LinkedHashMap<>();

    public NekoCustomDiscsForge() {
        DiscManager.load();
        DiscManager.writePack();

        for (DiscEntry e : DiscManager.discs()) {
            RegistryObject<SoundEvent> sound = SOUNDS.register(
                    e.path(), () -> SoundEvent.createVariableRangeEvent(e.soundId()));
            DISC_ITEMS.put(e.path(), ITEMS.register(
                    e.path(), () -> new CustomRecordItem(e, sound)));
        }

        TABS.register("discs", () -> CreativeModeTab.builder()
                .title(Component.literal("Neko Custom Discs"))
                .icon(() -> DISC_ITEMS.values().stream().findFirst()
                        .map(r -> new ItemStack(r.get()))
                        .orElseGet(() -> new ItemStack(Items.DIRT)))
                .displayItems((params, output) ->
                        DISC_ITEMS.values().forEach(r -> output.accept(r.get())))
                .build());

        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ITEMS.register(modBus);
        SOUNDS.register(modBus);
        TABS.register(modBus);
        MinecraftForge.EVENT_BUS.addListener(this::onCommands);

        if (FMLEnvironment.dist.isClient()) {
            ModLoadingContext.get().registerExtensionPoint(
                    ConfigScreenHandler.ConfigScreenFactory.class,
                    () -> new ConfigScreenHandler.ConfigScreenFactory(
                            (mc, parent) -> new ConfigScreen(parent)));
        }
        LOGGER.info("Neko Custom Discs (Forge) 就绪：扫描到 {} 张自定义唱片", DISC_ITEMS.size());
    }

    private void onCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("customdiscs")
                .then(Commands.literal("give")
                        .then(Commands.argument("id", StringArgumentType.string())
                                .executes(ctx -> give(ctx.getSource(),
                                        StringArgumentType.getString(ctx, "id"), 1))
                                .then(Commands.argument("count", IntegerArgumentType.integer(1, 64))
                                        .executes(ctx -> give(ctx.getSource(),
                                                StringArgumentType.getString(ctx, "id"),
                                                IntegerArgumentType.getInteger(ctx, "count")))))));
    }

    private static int give(CommandSourceStack source, String id, int count) {
        RegistryObject<Item> item = DISC_ITEMS.get(id);
        if (item == null || !item.isPresent()) {
            source.sendFailure(Component.literal("未知唱片：" + id));
            return 0;
        }
        if (source.getEntity() instanceof Player player) {
            player.getInventory().add(new ItemStack(item.get(), count));
        }
        source.sendSuccess(() -> Component.literal("已给予 " + count + "x " + id), false);
        return 1;
    }
}
