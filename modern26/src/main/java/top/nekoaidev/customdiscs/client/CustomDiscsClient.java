package top.nekoaidev.customdiscs.client;

import net.fabricmc.api.ClientModInitializer;
import top.nekoaidev.customdiscs.disc.ResourcePackSetup;

/**
 * 客户端入口：准备本地音乐资源包（复制 ogg、生成 sounds.json 与配方并挂载）。
 */
public class CustomDiscsClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        ResourcePackSetup.setup();
    }
}
