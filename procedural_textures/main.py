from PIL import Image, ImageDraw, ImageFilter

# Dimensions
WIDTH, HEIGHT = 1024, 600

# Create base image (woodgrain background)
bg = Image.new("RGB", (WIDTH, HEIGHT), (60, 30, 20))  # deep brown wood

# Optional: draw vertical stripes to mimic woodgrain
draw = ImageDraw.Draw(bg)
for x in range(0, WIDTH, 40):
    draw.line([(x, 0), (x, HEIGHT)], fill=(70, 35, 25), width=2)

# Add parchment panel
MARGIN = 60
parchment = Image.new("RGB", (WIDTH - 2*MARGIN, HEIGHT - 2*MARGIN), (240, 228, 210))
bg.paste(parchment, (MARGIN, MARGIN))

# Add feathered edge using mask
mask = Image.new("L", (WIDTH, HEIGHT), 255)
edge = ImageDraw.Draw(mask)
edge.rectangle((MARGIN-10, MARGIN-10, WIDTH-MARGIN+10, HEIGHT-MARGIN+10), fill=0)
mask = mask.filter(ImageFilter.GaussianBlur(8))
bg.putalpha(mask)

# Save or preview
bg = bg.convert("RGB")
bg.save("monopoly_panel.png")

