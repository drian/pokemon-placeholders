import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# === USER INPUT ===
set_id = input("Enter TCGDex set ID (e.g. sv03): ").strip()
border_color = input("Enter border color (e.g. orange or #FF6600): ").strip()
include_reverse = input("Generate reverse holo placeholders too? (y/n): ").strip().lower() == "y"

# === SETTINGS ===
dpi = 300
card_width_mm = 63
card_height_mm = 88
font_path = "arial.ttf"
output_dir = f"{set_id.upper()}_AutoPlaceholders"

# === SIZING ===
def mm_to_px(mm): return int((mm / 25.4) * dpi)
card_w, card_h = mm_to_px(card_width_mm), mm_to_px(card_height_mm)
os.makedirs(output_dir, exist_ok=True)

# === FONTS ===
def get_font(size):
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

font_title = get_font(44)
font_number = get_font(40)
font_set = get_font(34)
font_rarity = get_font(30)
font_variant = get_font(28)

# === FETCH SET DATA ===
url = f"https://api.tcgdex.net/v2/en/sets/{set_id}"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()
cards = data["cards"]
set_name = data.get("name", "Unknown Set")
logo_url = data.get("logo", "")
official_count = data.get("cardCount", {}).get("official", len(cards))

# === DOWNLOAD SET LOGO ===
logo_img = None
if logo_url:
    try:
        logo_response = requests.get(logo_url)
        logo_img = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        logo_img.thumbnail((120, 60))
    except:
        logo_img = None

print(f"\n🎴 Generating placeholders for {len(cards)} cards in '{set_name}'")
print(f"📂 Output directory: {output_dir}")
print(f"🔁 Including Reverse Holos: {'Yes' if include_reverse else 'No'}")
print(f"🎯 Reverse Holos limited to first {official_count} cards\n")

# === DRAW FUNCTION ===
def draw_card(name, number, rarity, variant_label):
    img = Image.new("RGB", (card_w, card_h), "white")
    draw = ImageDraw.Draw(img)

    margin = 40

    # Border
    draw.rounded_rectangle(
        [(margin, margin), (card_w - margin, card_h - margin)],
        radius=20,
        outline=border_color,
        width=10
    )

    # Title: "#number - name"
    title_line = f"{name} - {number}/{official_count}"
    draw.text((card_w / 2, card_h * 0.20), title_line, font=font_title, fill="black", anchor="mm")

    # Rarity
    if rarity:
        draw.text((card_w / 2, card_h * 0.30), rarity, font=font_rarity, fill="black", anchor="mm")

    # Card number (again, middle of card visually — optional redundancy)
    draw.text((card_w / 2, card_h * 0.48), f"# {number}", font=font_number, fill="black", anchor="mm")

    # Set name
    draw.text((card_w / 2, card_h * 0.65), set_name, font=font_set, fill="black", anchor="mm")

    # Variant
    if variant_label:
        draw.text((card_w / 2, card_h * 0.77), variant_label, font=font_variant, fill="black", anchor="mm")

    # Logo
    if logo_img:
        logo_x = card_w - logo_img.width - margin
        logo_y = card_h - logo_img.height - margin
        img.paste(logo_img, (logo_x, logo_y), logo_img)

    # Trim lines
    trim_len = 20
    trim_color = "#999"
    for (x, y) in [(0, 0), (card_w, 0), (0, card_h), (card_w, card_h)]:
        draw.line([(x, y), (x+trim_len if x == 0 else x-trim_len, y)], fill=trim_color, width=2)
        draw.line([(x, y), (x, y+trim_len if y == 0 else y-trim_len)], fill=trim_color, width=2)

    return img

# === GENERATE IMAGES ===
for idx, c in enumerate(cards):
    name = c.get("name", "Unknown")
    number = c.get("localId", "???")
    rarity = c.get("rarity", "")
    safe_name = name.replace(" ", "_").replace("/", "-")

    num_padded = number.zfill(3)

    # Normal
    normal_filename = f"{num_padded}-{safe_name}-Normal.png"
    normal_path = os.path.join(output_dir, normal_filename)
    img = draw_card(name, number, rarity, "Normal")
    img.save(normal_path, dpi=(dpi, dpi))
    print(f"✅ {normal_filename}")

    # Reverse Holo
    is_ex = name.lower().strip().endswith(" ex")
    if include_reverse and idx < official_count and not is_ex:
        reverse_filename = f"{num_padded}-{safe_name}-Reverse_Holo.png"
        reverse_path = os.path.join(output_dir, reverse_filename)
        img = draw_card(name, number, rarity, "Reverse Holo")
        img.save(reverse_path, dpi=(dpi, dpi))
        print(f"✅ {reverse_filename}")


print(f"\n🎉 All placeholders saved to: {output_dir}")
