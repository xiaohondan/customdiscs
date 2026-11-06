package top.nekoaidev.customdiscs;

/**
 * 跨版本兼容层。
 *
 * 这里原先通过 SharedConstants.getGameVersion().getName() 读取运行版本、再查一张
 * pack_format 版本表。问题有两个：GameVersion.getName() 自 1.21.6 起被移除（导致
 * 1.21.6/1.21.7/1.21.8 编译失败），而那张表里还写了一批并不存在的 Minecraft
 * 版本（1.22 及以后）与推测出来的格式号。现改为完全不依赖 MC 版本 API 的实现。
 *
 * ResourcePackSetup 生成 pack.mcmeta 时会同时写入 supported_formats 宽范围，
 * 因此这里只需给出一个所有版本都能读取的基线 pack_format（1.20.1 的 15）。
 *
 * RecordItem 构造签名差异由 Gradle 的变体 sourceSet（src/v-old、src/v-new、
 * src/v-modern）在编译期选择，不在这里处理。
 */
public final class Compat {
    private Compat() {}

    /** 资源包基线格式号（1.20.1 的值）；跨版本兼容由 supported_formats 范围负责。 */
    public static int currentPackFormat() {
        return 15;
    }
}
