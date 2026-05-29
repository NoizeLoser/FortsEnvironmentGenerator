import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
from generator_backend import FortsModBackend

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    theme_path = resource_path("red_theme.json")
    if os.path.exists(theme_path):
        ctk.set_default_color_theme(theme_path)
    else:
        ctk.set_default_color_theme("blue")
except Exception:
    ctk.set_default_color_theme("blue")

ctk.set_appearance_mode("Dark")


class LayerRow(ctk.CTkFrame):
    def __init__(self, master, index, remove_callback, default_zoom="0", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.index = index
        self.remove_callback = remove_callback
        self.texture_path = ""

        self.pack(fill="x", pady=4, padx=5)

        self.lbl_num = ctk.CTkLabel(self, text=f"Слой {index}", font=("Arial", 12, "bold"), width=60)
        self.lbl_num.pack(side="left", padx=5)

        self.btn_file = ctk.CTkButton(self, text="Выбрать файл", width=180, fg_color="#34495e", hover_color="#5d6d7e",
                                      command=self.choose_texture)
        self.btn_file.pack(side="left", padx=15)

        self.ent_zoom = ctk.CTkEntry(self, placeholder_text="0", width=80, justify="center")
        self.ent_zoom.insert(0, default_zoom)
        self.ent_zoom.pack(side="left", padx=15)

        self.ent_scroll_x = ctk.CTkEntry(self, placeholder_text="0", width=80, justify="center")
        self.ent_scroll_x.insert(0, "0")
        self.ent_scroll_x.pack(side="left", padx=15)

        self.ent_scroll_y = ctk.CTkEntry(self, placeholder_text="0", width=80, justify="center")
        self.ent_scroll_y.insert(0, "0")
        self.ent_scroll_y.pack(side="left", padx=15)

        # 6. Переключатель Спереди/Бэк (Ширина: 100)
        self.switch_fore = ctk.CTkSwitch(self, text="Включить", width=100)
        self.switch_fore.pack(side="left", padx=15)

        self.btn_del = ctk.CTkButton(self, text="❌", width=40, fg_color="#c0392b", hover_color="#e74c3c",
                                     command=lambda: self.remove_callback(self))
        self.btn_del.pack(side="right", padx=5)

    def choose_texture(self):
        """Проводник для выбора файла текстуры слоя"""
        file_path = filedialog.askopenfilename(filetypes=[("Forts Textures", "*.tga *.dds *.png")])
        if file_path:
            self.texture_path = file_path
            self.btn_file.configure(text=os.path.basename(file_path), fg_color="#2e7d32")

    def get_data(self):
        try:
            zoom_val = float(self.ent_zoom.get() or 0)
        except ValueError:
            zoom_val = 0.0
        return {
            "texture_path": self.texture_path,
            "zoom": zoom_val,
            "scroll_x": float(self.ent_scroll_x.get() or 0),
            "scroll_y": float(self.ent_scroll_y.get() or 0),
            "foreground": self.switch_fore.get() == 1
        }


class FortsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Forts Advanced Environment Mod Generator")
        self.geometry("980x750")
        self.resizable(False, False)

        self.output_dir = tk.StringVar()
        self.mod_name = tk.StringVar(value="My Compiled Map Mod")
        self.theme_id = tk.StringVar(value="atlantis")
        self.display_en = tk.StringVar(value="Atlantis")
        self.display_ru = tk.StringVar(value="Атлантида")
        self.is_override = tk.BooleanVar(value=False)
        self.override_target = tk.StringVar(value="trainingground")

        self.audio_paths = {"ambient": "", "idle": "", "intense": "", "win": "", "lose": ""}
        self.audio_labels = {}
        self.layers = []

        self.init_ui()

        self.add_layer_with_val("0.0", False)
        self.add_layer_with_val("0.03", False)
        self.add_layer_with_val("0.15", True)

        try:
            icon_path = resource_path("FortsEnvironmentGeneratorIcon.ico")
            if os.path.exists(icon_path):
                self.wm_iconbitmap(icon_path)
        except Exception:
            pass

    def init_ui(self):
        meta_frame = ctk.CTkFrame(self)
        meta_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(meta_frame, text="Глобальные параметры мода", font=("Arial", 13, "bold")).grid(row=0, column=0,
                                                                                                    columnspan=3,
                                                                                                    sticky="w", padx=10,
                                                                                                    pady=5)
        ctk.CTkEntry(meta_frame, textvariable=self.output_dir, width=580,
                     placeholder_text="Укажите папку Mods вашей игры Forts...").grid(row=1, column=0, columnspan=2,
                                                                                     padx=10, pady=5, sticky="w")
        ctk.CTkButton(meta_frame, text="Обзор папки", width=120, command=self.browse_folder).grid(row=1, column=2,
                                                                                                  padx=10, pady=5)

        ctk.CTkLabel(meta_frame, text="Папка мода:").grid(row=2, column=0, sticky="w", padx=10)
        ctk.CTkEntry(meta_frame, textvariable=self.mod_name, width=200).grid(row=2, column=1, sticky="w", pady=2)

        ctk.CTkLabel(meta_frame, text="ID темы:").grid(row=3, column=0, sticky="w", padx=10)
        ctk.CTkEntry(meta_frame, textvariable=self.theme_id, width=200).grid(row=3, column=1, sticky="w", pady=2)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        tab_visual = self.tabview.add("Слои (Параллакс)")
        tab_audio = self.tabview.add("Звуки и Музыка")
        tab_preview = self.tabview.add("🎬 Видео-предпросмотр")

        ctrl_box = ctk.CTkFrame(tab_visual, fg_color="transparent")
        ctrl_box.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(ctrl_box, text="+ Добавить слой", command=lambda: self.add_layer_with_val("0.05", False),
                      fg_color="#2980b9").pack(side="right")

        header = ctk.CTkFrame(tab_visual, fg_color="#2c3e50", height=30)
        header.pack(fill="x", pady=2, padx=5)

        ctk.CTkLabel(header, text="№", font=("Arial", 11, "bold"), width=60).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Файл текстуры", font=("Arial", 11, "bold"), width=180).pack(side="left", padx=15)
        ctk.CTkLabel(header, text="ZoomFactor", font=("Arial", 11, "bold"), width=80).pack(side="left", padx=15)
        ctk.CTkLabel(header, text="Скорость X", font=("Arial", 11, "bold"), width=80).pack(side="left", padx=15)
        ctk.CTkLabel(header, text="Скорость Y", font=("Arial", 11, "bold"), width=80).pack(side="left", padx=15)
        ctk.CTkLabel(header, text="Спереди", font=("Arial", 11, "bold"), width=100).pack(side="left", padx=15)
        ctk.CTkLabel(header, text="Удалить", font=("Arial", 11, "bold"), width=40).pack(side="right", padx=5)

        self.scroll_canvas = ctk.CTkScrollableFrame(tab_visual)
        self.scroll_canvas.pack(fill="both", expand=True, padx=5)

        audio_container = ctk.CTkScrollableFrame(tab_audio)
        audio_container.pack(fill="both", expand=True, padx=5, pady=5)
        sound_types = [
            ("ambient", "Фоновый эмбиент карты (ветер, океан):", "ambient.mp3"),
            ("idle", "Музыка: Спокойное состояние (строительство):", "music_calm.mp3"),
            ("intense", "Музыка: Активная фаза (бой):", "music_battle.mp3"),
            ("win", "Музыка: Экран победы (Win):", "music_win.mp3"),
            ("lose", "Музыка: Экран поражения (Lose):", "music_lose.mp3")
        ]
        for row_idx, (key, title, default) in enumerate(sound_types):
            frame = ctk.CTkFrame(audio_container)
            frame.pack(fill="x", pady=6, padx=5)
            ctk.CTkLabel(frame, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10,
                                                                             pady=5)
            self.audio_labels[key] = ctk.CTkLabel(frame, text=f"Не выбран ({default})", text_color="#7f8c8d")
            self.audio_labels[key].grid(row=1, column=0, sticky="w", padx=10, pady=2)
            ctk.CTkButton(frame, text="Выбрать MP3", width=140, command=lambda k=key: self.select_audio(k)).grid(row=1,
                                                                                                                 column=1,
                                                                                                                 padx=10,
                                                                                                                 pady=5,
                                                                                                                 sticky="e")
            frame.grid_columnconfigure(0, weight=1)

        preview_box = ctk.CTkFrame(tab_preview, fg_color="transparent")
        preview_box.pack(expand=True)
        ctk.CTkLabel(preview_box, text="Генератор демо-ролика параллакса", font=("Arial", 16, "bold")).pack(pady=10)
        btn_render_gif = ctk.CTkButton(preview_box, text="🎬 СГЕНЕРИРОВАТЬ И ПОКАЗАТЬ РОЛИК", font=("Arial", 14, "bold"),
                                       fg_color="#d35400", hover_color="#e67e22", height=45,
                                       command=self.render_and_open_gif)
        btn_render_gif.pack(pady=20)

        btn_build = ctk.CTkButton(self, text="СГЕНЕРИРОВАТЬ СТРУКТУРУ МОДА", font=("Arial", 15, "bold"),
                                  fg_color="#27ae60", hover_color="#2ecc71", height=45, command=self.build_mod)
        btn_build.pack(padx=20, pady=10, fill="x")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: self.output_dir.set(folder)

    def select_audio(self, key):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.ogg")])
        if file_path:
            self.audio_paths[key] = file_path
            self.audio_labels[key].configure(text=os.path.basename(file_path), text_color="#2ecc71")

    def add_layer_with_val(self, zoom, is_fore):
        row = LayerRow(self.scroll_canvas, index=len(self.layers) + 1, remove_callback=self.remove_layer,
                       default_zoom=zoom)
        if is_fore: row.switch_fore.select()
        self.layers.append(row)
        self.update_layer_indices()

    def remove_layer(self, row_instance):
        row_instance.pack_forget()
        row_instance.destroy()
        self.layers.remove(row_instance)
        self.update_layer_indices()

    def update_layer_indices(self):
        for idx, row in enumerate(self.layers, 1):
            row.lbl_num.configure(text=f"Слой {idx}")
            row.index = idx

    def get_backend_instance(self):
        return FortsModBackend(
            output_dir=self.output_dir.get(),
            mod_name=self.mod_name.get(),
            theme_id=self.theme_id.get(),
            display_en=self.display_en.get(),
            display_ru=self.display_ru.get(),
            is_override=self.is_override.get(),
            override_target=self.override_target.get()
        )
    def render_and_open_gif(self):
        if not self.output_dir.get():
            messagebox.showerror("Ошибка", "Укажите путь сохранения вверху окна!")
            return
        try:
            compiled_layers = [row.get_data() for row in self.layers]
            backend = self.get_backend_instance()
            gif_res_path = backend.generate_preview_gif(compiled_layers)
            os.startfile(gif_res_path)
        except Exception as e:
            messagebox.showerror("Ошибка рендеринга", str(e))

    def build_mod(self):
        if not self.output_dir.get():
            messagebox.showerror("Ошибка", "Укажите папку генерации мода!")
            return
        try:
            compiled_layers = [row.get_data() for row in self.layers]
            backend = self.get_backend_instance()
            generated_path = backend.generate(compiled_layers, self.audio_paths)
            messagebox.showinfo("Успех", f"Мод со всеми ресурсами успешно собран!\n\nПуть: {generated_path}")
        except Exception as e:
            messagebox.showerror("Ошибка сборки", str(e))

if __name__ == "__main__":
    app = FortsApp()
    app.mainloop()
