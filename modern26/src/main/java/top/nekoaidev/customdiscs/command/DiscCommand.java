package top.nekoaidev.customdiscs.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.chat.Component;
import top.nekoaidev.customdiscs.CustomDiscs;
import top.nekoaidev.customdiscs.disc.CustomRecordItem;

import java.util.Collection;

/**
 * /customdiscs give <disc_id> [count]
 * 方便测试与获取唱片。唱片也可在创造模式标签页直接拿，或按合成配方合成。
 */
public class DiscCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("customdiscs")
                .then(Commands.literal("give")
                        .then(Commands.argument("id", StringArgumentType.word())
                                .executes(ctx -> give(ctx, StringArgumentType.getString(ctx, "id"), 1)))
                        .then(Commands.argument("count", IntegerArgumentType.integer(1, 64))
                                .executes(ctx -> give(ctx, StringArgumentType.getString(ctx, "id"), IntegerArgumentType.getInteger(ctx, "count"))))));
    }

    private static int give(CommandContext<CommandSourceStack> ctx, String id, int count) {
        CustomRecordItem item = CustomDiscs.REGISTERED_DISCS.get(id.toLowerCase());
        if (item == null) {
            ctx.getSource().sendFailure(Component.translatable("customdiscs.command.give.unknown", id));
            return 0;
        }
        Collection<ServerPlayer> players = ctx.getSource().getPlayer() != null
                ? java.util.Collections.singletonList(ctx.getSource().getPlayer())
                : ctx.getSource().getServer().getPlayerList().getPlayers();

        int finalCount = Math.min(count, 64);
        for (ServerPlayer player : players) {
            player.getInventory().add(new ItemStack(item, finalCount));
        }
        ctx.getSource().sendSuccess(() -> Component.translatable("customdiscs.command.give.ok", finalCount, item.getEntry().displayName), true);
        return finalCount;
    }
}
