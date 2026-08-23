"""
Генератор высококачественной иконки WaterMetrics (ICO + PNG)
Использует исходное изображение assets/icon_source.png, выполняет точный кроп 
по геометрии 3D-сквиркла (392x392, центр x=512, y=286), накладывает субпиксельную
маску сглаживания (8x supersampling) с прозрачным фоном и генерирует
мульти-размерный ICO (256, 128, 64, 48, 32, 16) и PNG (512x512).
"""

import os
from PIL import Image, ImageDraw

def generate_icons(source_path: str = "assets/icon_source.png"):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Исходный файл {source_path} не найден!")

    orig = Image.open(source_path).convert("RGBA")

    # Точные координаты карточки-сквиркла внутри исходного изображения (1024x558)
    # [left=316, top=90, right=708, bottom=482], размер 392x392
    card = orig.crop((316, 90, 708, 482))

    # Создание суперсэмплированной маски скругления 8x
    scale = 8
    w, h = 392, 392
    mask_hi = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(mask_hi)
    radius = int(86 * scale)
    draw.rounded_rectangle([0, 0, w * scale - 1, h * scale - 1], radius=radius, fill=255)
    mask = mask_hi.resize((w, h), Image.Resampling.LANCZOS)

    # Применяем маску к карточке
    card.putalpha(mask)

    # Мастер-холст 512x512 с идеальным масштабированием
    master_512 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    card_512 = card.resize((480, 480), Image.Resampling.LANCZOS)
    master_512.alpha_composite(card_512, (16, 16))

    os.makedirs("assets", exist_ok=True)
    png_path = "assets/app_icon.png"
    ico_path = "assets/app_icon.ico"

    master_512.save(png_path, "PNG")

    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    master_512.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Иконки успешно сгенерированы:\n  - {png_path}\n  - {ico_path}")

if __name__ == "__main__":
    generate_icons()
