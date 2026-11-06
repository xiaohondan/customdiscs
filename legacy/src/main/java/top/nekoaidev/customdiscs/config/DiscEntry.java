package top.nekoaidev.customdiscs.config;

import com.google.gson.annotations.SerializedName;
import java.util.Locale;
import net.minecraft.util.Identifier;
import top.nekoaidev.customdiscs.CustomDiscs;

/**
 * 单张自定义唱片的元数据。
 * 玩家把 .ogg 放进音乐源文件夹后，DiscManager 会为每个文件生成一个 DiscEntry；
 * 玩家也可在 discs.json 中手动修改 displayName / material / color / lengthInSeconds。
 */
public class DiscEntry {
    /** 唱片唯一 id（文件名去扩展名，全小写） */
    public String id = "";

    /** 物品显示名 */
    public String displayName = "";

    /** 音乐源文件夹中的文件名，例如 my_song.ogg */
    public String fileName = "";

    /** 合成配方使用的主材料（物品 id），默认金锭 */
    @SerializedName("material")
    public String material = "minecraft:gold_ingot";

    /** 物品提示框颜色 */
    public int color = 0xFF66CC;

    /** 音乐时长（秒），仅用于唱片比较器输出与显示 */
    public int lengthInSeconds = 180;

    public DiscEntry() {}

    public DiscEntry(String id, String fileName) {
        this.id = id;
        this.fileName = fileName;
        this.displayName = prettyName(id);
    }

    /** 把 file_name_like_this 变成 File Name Like This */
    private static String prettyName(String raw) {
        String s = raw.replace('_', ' ').replace('-', ' ');
        StringBuilder sb = new StringBuilder();
        boolean upper = true;
        for (char c : s.toCharArray()) {
            if (c == ' ') {
                upper = true;
                sb.append(c);
            } else if (upper) {
                sb.append(Character.toUpperCase(c));
                upper = false;
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    public Identifier getItemId() {
        return Identifier.of(CustomDiscs.MOD_ID, "disc_" + id);
    }

    public Identifier getSoundId() {
        return Identifier.of(CustomDiscs.MOD_ID, "disc_" + id);
    }
}
