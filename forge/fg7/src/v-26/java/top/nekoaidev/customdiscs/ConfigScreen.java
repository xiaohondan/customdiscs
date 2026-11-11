package top.nekoaidev.customdiscs;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * 26.x 的界面渲染改为「提取渲染状态」模型：
 * GuiGraphics -> GuiGraphicsExtractor，render -> extractRenderState，
 * drawString -> text，drawCenteredString -> centeredText。
 * 背景由 Screen.extractRenderStateWithTooltipAndSubtitles 统一绘制，这里不再重复调用。
 */
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
            if (this.minecraft != null) this.minecraft.setScreenAndShow(parent);
        }).bounds(x, 95, 220, 20).build());

        this.addRenderableWidget(Button.builder(Component.literal("完成"), b -> {
            if (this.minecraft != null) this.minecraft.setScreenAndShow(parent);
        }).bounds(x, 125, 220, 20).build());
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
        g.centeredText(this.font, this.title, this.width / 2, 25, 0xFFFFFF);
        g.text(this.font, "音乐源文件夹（相对游戏目录）", this.width / 2 - 110, 45, 0xA0A0A0);
        g.text(this.font, "新增唱片需重启游戏生效", this.width / 2 - 110, 158, 0x808080);
        super.extractRenderState(g, mouseX, mouseY, delta);
    }
}
