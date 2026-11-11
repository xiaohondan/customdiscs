package top.nekoaidev.customdiscs;

import net.minecraft.resources.ResourceLocation;

import java.nio.file.Path;

/** 一个本地 .ogg 文件对应一张唱片。1.21 起 ResourceLocation 构造私有，改用静态工厂。 */
public record DiscEntry(String path, String displayName, Path file, int lengthSeconds) {
    public ResourceLocation id() {
        return ResourceLocation.fromNamespaceAndPath(NekoCustomDiscsForge.MODID, path);
    }

    public ResourceLocation soundId() {
        return id();
    }
}
