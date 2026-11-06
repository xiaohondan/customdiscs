package top.nekoaidev.customdiscs.client;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;
import net.minecraft.client.gui.screen.Screen;

/**
 * 把本模组的设置界面接入 Mod Menu（在游戏内 Mods 列表中点 Configure 打开）。
 */
public class ModMenuEntrypoint implements ModMenuApi {
    @Override
    public ConfigScreenFactory<Screen> getModConfigScreenFactory() {
        return ConfigScreenProvider::build;
    }
}
