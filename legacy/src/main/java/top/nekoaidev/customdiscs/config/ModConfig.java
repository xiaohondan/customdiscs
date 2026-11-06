package top.nekoaidev.customdiscs.config;

import com.google.gson.annotations.SerializedName;

/**
 * 模组全局设置。持久化到 <游戏目录>/config/customdiscs/config.json。
 */
public class ModConfig {
    /** 音乐源文件夹路径。相对路径相对于游戏目录解析。 */
    @SerializedName("music_source_path")
    public String musicSourcePath = "config/customdiscs/music";

    /** 是否给每张唱片生成合成配方 */
    @SerializedName("enable_crafting_recipes")
    public boolean enableCraftingRecipes = true;

    /** 预留：自定义唱片音量（当前版本走游戏“唱片”音量滑块） */
    @SerializedName("volume")
    public float volume = 1.0f;

    public ModConfig() {}
}
