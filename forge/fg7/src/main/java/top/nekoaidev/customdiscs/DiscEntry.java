package top.nekoaidev.customdiscs;

import net.minecraft.resources.Identifier;

import java.nio.file.Path;

/**
 * 一个本地 .ogg 文件对应一张唱片。
 * 1.21.11 / 26.x 起 Mojang 把 ResourceLocation 改名为 Identifier，
 * 构造方式仍是静态工厂 fromNamespaceAndPath。
 */
public record DiscEntry(String path, String displayName, Path file, int lengthSeconds) {
    public Identifier id() {
        return Identifier.fromNamespaceAndPath(NekoCustomDiscsForge.MODID, path);
    }

    public Identifier soundId() {
        return id();
    }
}
