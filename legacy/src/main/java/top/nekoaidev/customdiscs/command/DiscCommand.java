package top.nekoaidev.customdiscs.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.item.ItemStack;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import top.nekoaidev.customdiscs.CustomDiscs;
import top.nekoaidev.customdiscs.disc.CustomRecordItem;

import java.util.Collection;

/**
 * /customdiscs give <disc_id> [count]
 * 方便测试与获取唱片。唱片也可在创造模式标签页直接拿，或按合成配方合成。
 */
public class DiscCommand {

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
        dispatcher.register(CommandManager.literal("customdiscs")
                .then(CommandManager.literal("give")
                        .then(CommandManager.argument("id", StringArgumentType.word())
                                .executes(ctx -> give(ctx, StringArgumentType.getString(ctx, "id"), 1)))
                        .then(CommandManager.argument("count", IntegerArgumentType.integer(1, 64))
                                .executes(ctx -> give(ctx, StringArgumentType.getString(ctx, "id"), IntegerArgumentType.getInteger(ctx, "count"))))));
    }

    private static int give(CommandContext<ServerCommandSource> ctx, String id, int count) {
        CustomRecordItem item = CustomDiscs.REGISTERED_DISCS.get(id.toLowerCase());
        if (item == null) {
            ctx.getSource().sendError(Text.translatable("customdiscs.command.give.unknown", id));
            return 0;
        }
        Collection<ServerPlayerEntity> players = ctx.getSource().getPlayer() != null
                ? java.util.Collections.singletonList(ctx.getSource().getPlayer())
                : ctx.getSource().getServer().getPlayerManager().getPlayerList();

        int finalCount = Math.min(count, 64);
        for (ServerPlayerEntity player : players) {
            player.getInventory().insertStack(new ItemStack(item, finalCount));
        }
        ctx.getSource().sendFeedback(() -> Text.translatable("customdiscs.command.give.ok", finalCount, item.getEntry().displayName), true);
        return finalCount;
    }
}
