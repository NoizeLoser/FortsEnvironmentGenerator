import os
import shutil
from PIL import Image, ImageDraw


class FortsModBackend:
    def __init__(self, output_dir, mod_name, theme_id, display_en, display_ru, is_override, override_target):
        self.output_dir = output_dir
        self.mod_name = mod_name
        self.theme_id = theme_id.strip().lower().replace(" ", "")
        self.display_en = display_en
        self.display_ru = display_ru
        self.is_override = is_override
        self.override_target = override_target

    def generate(self, layers_data, audio_data):
        mod_root = os.path.join(self.output_dir, self.mod_name)
        env_root = os.path.join(mod_root, "environment", self.theme_id)
        bg_root = os.path.join(env_root, "background")
        audio_root = os.path.join(env_root, "audio")
        music_root = os.path.join(mod_root, "music")
        scripts_root = os.path.join(mod_root, "scripts")

        for folder in [mod_root, env_root, bg_root, audio_root, music_root, scripts_root]:
            os.makedirs(folder, exist_ok=True)

        with open(os.path.join(mod_root, "mod.lua"), "w", encoding="utf-8") as f:
            if self.is_override:
                f.write(f'Selectable = true\nInclude = {{"{self.override_target}"}}\n')
            else:
                f.write("-- Deliberately empty.\n")

        with open(os.path.join(mod_root, "displayname.lua"), "w", encoding="utf-8") as f:
            f.write(
                f"DisplayName =\n{{\n    ['English'] = L\"{self.display_en}\",\n    ['Russian'] = L\"{self.display_ru}\",\n}}\n")

        with open(os.path.join(mod_root, "publishedfileid.lua"), "w", encoding="utf-8") as f:
            f.write("0\n")

        def copy_resource(src_path, dest_folder, default_name):
            if src_path and os.path.exists(src_path):
                filename = os.path.basename(src_path)
                shutil.copy(src_path, os.path.join(dest_folder, filename))
                return filename
            return default_name

        with open(os.path.join(bg_root, "background.lua"), "w", encoding="utf-8") as f:
            f.write("BackgroundColour = { 0, 0, 0, 255 }\n\nLayers =\n{\n")
            for idx, layer in enumerate(layers_data, 1):
                tex_file = copy_resource(layer['texture_path'], bg_root, f"layer_{idx}.tga")

                f.write(f"    -- Слой {idx}\n    {{\n")
                f.write(f"        ZoomFactor = {layer['zoom']},\n")
                f.write(f"        ScrollRateX = {layer['scroll_x']},\n")
                f.write(f"        ScrollRateY = {layer['scroll_y']},\n")
                f.write(f"        TextureScrollRateX = 0,\n        TextureScrollRateY = 0,\n")
                f.write(f"        Foreground = {str(layer['foreground']).lower()},\n")
                f.write(f"        GridTileOffsetX = -0.5,\n        GridTileOffsetY = -0.5,\n")
                f.write(
                    f"        Tiles = {{ {{ GridX = 0, GridY = 0, ClampT = true, TextureFileName = bgpath .. \"{tex_file}\" }} }},\n")
                f.write("    },\n")
            f.write("}\n")

        ambient_file = copy_resource(audio_data['ambient'], audio_root, f"enviro_{self.theme_id}_wind_01.mp3")
        idle_file = copy_resource(audio_data['idle'], music_root, f"{self.theme_id}_calm.mp3")
        intense_file = copy_resource(audio_data['intense'], music_root, f"{self.theme_id}_battle.mp3")
        win_file = copy_resource(audio_data['win'], music_root, f"{self.theme_id}_victory.mp3")
        lose_file = copy_resource(audio_data['lose'], music_root, f"{self.theme_id}_defeat.mp3")

        with open(os.path.join(env_root, "ambient.lua"), "w", encoding="utf-8") as f:
            f.write(
                f"LifeSpan = 5\nEffects =\n{{\n    {{\n        Type = \"sound\",\n        TimeToTrigger = 0,\n        FadeInPeriod = 0.5,\n")
            f.write(f"        LocalPosition = {{ x = 0, y = 0, z = 0 }},\n")
            f.write(f"        Sound = path .. \"/environment/{self.theme_id}/audio/{ambient_file}\",\n")
            f.write(
                "        Volume = 0.5,\n        Falloff = false,\n        Priority = 128,\n        Repeat = true,\n        RandomiseStart = true,\n    },\n}\n")

        with open(os.path.join(scripts_root, "music.lua"), "w", encoding="utf-8") as f:
            f.write(f'MusicState.Idle.Series = path .. "/music/{idle_file}"\n')
            f.write(f'MusicState.Intense.Series = path .. "/music/{intense_file}"\n')
            f.write(f'MusicState.Win.Series = path .. "/music/{win_file}"\n')
            f.write(f'MusicState.Lose.Series = path .. "/music/{lose_file}"\n')

        open(os.path.join(mod_root, "preview.jpg"), "w").close()
        open(os.path.join(env_root, "preview.jpg"), "w").close()

        return mod_root

    def generate_preview_gif(self, layers_data):
        mod_root = os.path.join(self.output_dir, self.mod_name)
        os.makedirs(mod_root, exist_ok=True)
        gif_path = os.path.join(mod_root, "parallax_preview.gif")

        W, H = 800, 400
        center_y = H / 2
        frames = []

        layer_styles = [
            ("#2c3e50", "#34495e"),
            ("#16a085", "#1abc9c"),
            ("#2980b9", "#3498db"),
            ("#d35400", "#e67e22")
        ]

        for step in range(30):
            import math
            cam_x = math.sin(step * (2 * math.pi / 30)) * 150

            img = Image.new("RGB", (W, H), "#1a1a1a")
            draw = ImageDraw.Draw(img)

            back_layers = [l for l in layers_data if not l['foreground']]
            fore_layers = [l for l in layers_data if l['foreground']]

            for idx, layer in enumerate(back_layers):
                zoom = layer['zoom']
                offset_x = - (cam_x * zoom * 5)
                style_idx = idx % len(layer_styles)
                color, decor_color = layer_styles[style_idx]

                display_name = os.path.basename(layer['texture_path']) if layer[
                    'texture_path'] else f"layer_{idx + 1}.tga"

                for tile_i in range(-2, 3):
                    x_start = (W / 2) + offset_x + (tile_i * 400)
                    draw.rectangle([x_start - 200, center_y - 20 + (idx * 15), x_start + 200, H], fill=color)
                    draw.polygon([
                        x_start - 100, center_y - 20 + (idx * 15),
                        x_start, center_y - 80 + (idx * 15),
                        x_start + 100, center_y - 20 + (idx * 15)
                    ], fill=decor_color)
                    draw.text((x_start - 30, center_y + 40 + (idx * 20)), display_name, fill="#ecf0f1")

            world_offset_x = - (cam_x * 2.5)
            w_center_x = (W / 2) + world_offset_x
            draw.rectangle([w_center_x - 150, center_y + 30, w_center_x + 150, center_y + 50], fill="#27ae60",
                           outline="#2ecc71", width=2)
            draw.rectangle([w_center_x - 120, center_y - 20, w_center_x - 80, center_y + 30], fill="#7f8c8d")
            draw.rectangle([w_center_x + 80, center_y - 20, w_center_x + 120, center_y + 30], fill="#7f8c8d")
            draw.text((w_center_x - 110, center_y), "FORT A", fill="white")
            draw.text((w_center_x + 90, center_y), "FORT B", fill="white")

            for idx, layer in enumerate(fore_layers):
                zoom = layer['zoom']
                offset_x = - (cam_x * zoom * 5)
                display_name = os.path.basename(layer['texture_path']) if layer['texture_path'] else "front_layer.tga"
                for tile_i in range(-2, 3):
                    x_start = (W / 2) + offset_x + (tile_i * 300)
                    draw.ellipse([x_start - 50, center_y - 60, x_start - 40, center_y - 50], fill="#ffffff")
                    draw.ellipse([x_start + 60, center_y, x_start + 70, center_y + 10], fill="#ffffff")
                    draw.text((x_start, center_y - 80), f"Front: {display_name}", fill="#f1c40f")

            frames.append(img)

        frames.save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0)
        return gif_path
