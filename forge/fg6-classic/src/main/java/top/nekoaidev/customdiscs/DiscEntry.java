package top.nekoaidev.customdiscs;

import net.minecraft.resources.ResourceLocation;

import java.nio.file.Path;

/** 一个本地 .ogg 文件对应一张唱片。 */
public record DiscEntry(String path, String displayName, Path file, int lengthSeconds) {
    public ResourceLocation id() {
        return new ResourceLocation(NekoCustomDiscsForge.MODID, path);
    }

    public ResourceLocation soundId() {
        return new ResourceLocation(NekoCustomDiscsForge.MODID, path);
    }
}
