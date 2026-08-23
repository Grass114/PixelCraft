from PIL import Image

PALETTES = {
    "自动": None,
    "GameBoy (4色)": [(15,56,15),(48,98,48),(139,172,15),(155,188,15)],
    "NES (20色)": [
        (0,0,0),(255,255,255),(252,0,0),(0,252,0),
        (0,0,252),(252,252,0),(252,0,252),(0,252,252),
        (252,128,0),(0,128,0),(0,0,128),(128,0,128),
        (128,128,0),(0,128,128),(128,128,128),(192,192,192),
        (252,128,128),(128,252,128),(128,128,252),(252,252,128)
    ],
    "CGA 4色": [(0,0,0),(255,255,255),(0,255,255),(255,0,255)],
    "CGA 16色": [
        (0,0,0),(0,0,170),(0,170,0),(0,170,170),
        (170,0,0),(170,0,170),(170,85,0),(170,170,170),
        (85,85,85),(85,85,255),(85,255,85),(85,255,255),
        (255,85,85),(255,85,255),(255,255,85),(255,255,255)
    ],
    "Commodore 64 (16色)": [
        (0,0,0),(255,255,255),(136,0,0),(170,255,238),
        (204,68,204),(0,204,85),(0,0,170),(238,238,119),
        (221,136,85),(102,68,0),(255,119,119),(51,51,51),
        (119,119,119),(170,255,102),(0,68,204),(187,85,0)
    ],
    "ZX Spectrum (15色)": [
        (0,0,0),(0,0,192),(0,192,0),(0,192,192),
        (192,0,0),(192,0,192),(192,192,0),(192,192,192),
        (0,0,255),(0,255,0),(0,255,255),(255,0,0),
        (255,0,255),(255,255,0),(255,255,255)
    ],
    "Atari 2600 (8色)": [
        (0,0,0),(255,255,255),(255,0,0),(0,255,0),
        (0,0,255),(255,255,0),(255,0,255),(0,255,255)
    ],
    "PICO-8 (16色)": [
        (0,0,0),(29,43,83),(126,37,83),(0,135,81),
        (171,82,54),(95,87,79),(194,195,199),(255,241,232),
        (255,0,77),(255,163,0),(255,236,39),(0,228,54),
        (41,173,255),(131,118,156),(255,119,168),(255,204,170)
    ]
}

def process_image(img, block, colors, palette):
    w, h = img.size
    if img.mode == 'RGBA':
        r,g,b,a = img.split()
        rgb_img = Image.merge('RGB', (r,g,b))
        has_alpha = True
    else:
        rgb_img = img.convert('RGB')
        has_alpha = False

    bw = max(1, w // block)
    bh = max(1, h // block)

    small = rgb_img.resize((bw, bh), Image.NEAREST)

    if palette:
        small = apply_palette(small, palette)
    else:
        if colors < 256:
            small = small.quantize(colors=colors, method=Image.MEDIANCUT)
            small = small.convert('RGB')

    result_rgb = small.resize((w, h), Image.NEAREST)

    if has_alpha:
        small_a = a.resize((bw, bh), Image.NEAREST)
        result_a = small_a.resize((w, h), Image.NEAREST)
        result = Image.merge('RGBA', (*result_rgb.split(), result_a))
    else:
        result = result_rgb

    return result

def apply_palette(image, palette_colors):
    pixels = image.load()
    w, h = image.size
    for y in range(h):
        for x in range(w):
            r,g,b = pixels[x,y]
            best = min(palette_colors, key=lambda c: (r-c[0])**2 + (g-c[1])**2 + (b-c[2])**2)
            pixels[x,y] = best
    return image