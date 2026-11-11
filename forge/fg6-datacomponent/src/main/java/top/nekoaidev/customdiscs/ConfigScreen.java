package top.nekoaidev.customdiscs;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Forge 原生配置界面，不依赖 Cloth Config。 */
public class ConfigScreen extends Screen {
    private final Screen parent;
    private EditBox pathBox;

    public ConfigScreen(Screen parent) {
        super(Component.literal("Neko Custom Discs 设置"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        int x = this.width / 2 - 110;
        pathBox = new EditBox(this.font, x, 60, 220, 20, Component.literal("音乐源文件夹"));
        pathBox.setMaxLength(256);
        pathBox.setValue(DiscManager.getSourcePath());
        this.addRenderableWidget(pathBox);

        this.addRenderableWidget(Button.builder(Component.literal("保存并重新扫描"), b -> {
            DiscManager.setSourcePath(pathBox.getValue());
            DiscManager.saveConfig();
            DiscManager.load();
            DiscManager.writePack();
            if (this.minecraft != null) this.minecraft.setScreen(parent);
        }).bounds(x, 95, 220, 20).build());

        this.addRenderableWidget(Button.builder(Component.literal("完成"), b -> {
            if (this.minecraft != null) this.minecraft.setScreen(parent);
        }).bounds(x, 125, 220, 20).build());
    }

    /** 1.21+ 是 4 参 renderBackground；反射兼容，避免为每个小版本分源码。 */
    private void drawBackground(GuiGraphics g) {
        try {
            java.lang.reflect.Method m = Screen.class.getMethod(
                    "renderBackground", GuiGraphics.class, int.class, int.class, float.class);
            m.invoke(this, g, 0, 0, 0.0f);
        } catch (ReflectiveOperationException ignored) {
            // 由 super.render 自行绘制
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float delta) {
        drawBackground(g);
        g.drawCenteredString(this.font, this.title, this.width / 2, 25, 0xFFFFFF);
        g.drawString(this.font, "音乐源文件夹（相对游戏目录）", this.width / 2 - 110, 45, 0xA0A0A0);
        g.drawString(this.font, "新增唱片需重启游戏生效", this.width / 2 - 110, 158, 0x808080);
        super.render(g, mouseX, mouseY, delta);
    }
}
