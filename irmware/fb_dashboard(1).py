#!/usr/bin/env python3
"""
Dashboard de la Paca Digestora, dibujado DIRECTO sobre /dev/fb0 (sin X).

Lee el archivo compartido que escribe lora_parser.py y dibuja tarjetas
grandes con temperatura/humedad interna y externa, más un banner de estado.

Tamaños de fuente calculados como proporción de la altura real de la
pantalla detectada (para que se vean grandes también en un panel de 7").

Requiere en la BBB (Arch Linux ARM):
    pacman -S python-pillow python-numpy ttf-dejavu

Uso:
    python3 fb_dashboard.py
    (Ctrl+C para salir)
"""

import time
import json
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    print("Falta Pillow o numpy. Instala con:")
    print("  pacman -S python-pillow python-numpy")
    sys.exit(1)


FB_DEVICE = "/dev/fb0"
DATA_FILE = "/tmp/paca_data.json"

# --- Paleta (tema "panel de instrumentos" industrial) ---
COLOR_BG = (18, 21, 26)
COLOR_CARD = (28, 33, 40)
COLOR_BORDER = (42, 47, 56)
COLOR_TEXT = (232, 230, 225)
COLOR_MUTED = (139, 147, 161)
COLOR_ACCENT = (217, 142, 43)     # ambar
COLOR_OK = (76, 175, 109)         # verde
COLOR_ALERTA = (229, 72, 77)      # rojo
COLOR_GRIS = (100, 106, 116)      # desconectado / sin datos

ESTADO_COLOR = {
    # estados calculados por umbrales en el ESP32
    "OPTIMO": COLOR_OK,
    "NORMAL": COLOR_ACCENT,
    "ALERTA_TEMP": COLOR_ALERTA,
    "ALERTA_HUMEDAD": COLOR_ALERTA,
    "SIN_DATOS": COLOR_GRIS,
    "DESCONOCIDO": COLOR_GRIS,
    # estados predichos por la red neuronal (nombres del notebook de entrenamiento)
    "Termofilico": COLOR_ALERTA,
    "Mesofilico": COLOR_ACCENT,
    "Enfriamiento": (90, 150, 220),  # azul, distinto para diferenciar a simple vista
}

FONT_PATHS_BOLD = [
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]
FONT_PATHS_REGULAR = [
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def cargar_fuente(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def get_fb_info():
    # Intento 1: sysfs (ruta estándar en la mayoría de distros)
    for base in ["/sys/class/graphics/fb0", "/sys/class/graphics/fb1"]:
        try:
            with open(f"{base}/virtual_size") as f:
                w, h = f.read().strip().split(",")
            with open(f"{base}/bits_per_pixel") as f:
                bpp = int(f.read().strip())
            return int(w), int(h), bpp
        except FileNotFoundError:
            continue

    # Intento 2: fbset (más universal, viene en casi cualquier distro)
    try:
        import subprocess
        out = subprocess.check_output(["fbset", "-s"], text=True)
        w = h = bpp = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("geometry"):
                partes = line.split()
                w, h = int(partes[1]), int(partes[2])
            elif line.startswith("rgba") or line.startswith("mode"):
                pass
        # bpp viene en la linea "geometry <xres> <yres> <vxres> <vyres> <bpp>"
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("geometry"):
                partes = line.split()
                w, h, bpp = int(partes[1]), int(partes[2]), int(partes[5])
        if w and h and bpp:
            return w, h, bpp
    except Exception:
        pass

    print("No se pudo detectar la resolución/bpp automáticamente.")
    print("Instala fbset (pacman -S fbset) o revisa 'ls /sys/class/graphics/'")
    sys.exit(1)


def rgb_to_fb_bytes(img: Image.Image, bpp: int) -> bytes:
    arr = np.array(img.convert("RGB"), dtype=np.uint16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    if bpp == 16:
        pixels = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        return pixels.astype("<u2").tobytes()
    elif bpp == 32:
        a = np.full_like(r, 255)
        pixels = np.dstack([b, g, r, a]).astype(np.uint8)
        return pixels.tobytes()
    elif bpp == 24:
        pixels = np.dstack([b, g, r]).astype(np.uint8)
        return pixels.tobytes()
    else:
        raise ValueError(f"bpp no soportado: {bpp}")


def leer_datos():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {
            "t_int": None, "t_ext": None, "h_int": None, "h_ext": None,
            "estado": "SIN_DATOS", "estado_ia": None, "confianza_ia": None,
            "conectado": False, "ultima_actualizacion": 0,
        }


def fmt_valor(v, unidad):
    if v is None:
        return "--"
    return f"{v:.1f}{unidad}"


def dibujar_tarjeta(draw, x, y, w, h, titulo, valor_txt, font_titulo, font_valor, color_valor):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 12,
                            fill=COLOR_CARD, outline=COLOR_BORDER, width=2)

    draw.text((x + w * 0.06, y + h * 0.10), titulo, font=font_titulo, fill=COLOR_MUTED)

    bbox = draw.textbbox((0, 0), valor_txt, font=font_valor)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x + (w - tw) / 2, y + h * 0.42), valor_txt, font=font_valor, fill=color_valor)


def dibujar_dashboard(w, h, datos, fonts):
    img = Image.new("RGB", (w, h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    margen = int(w * 0.02)

    # --- Encabezado ---
    draw.text((margen, int(h * 0.02)), "PACA DIGESTORA", font=fonts["header"], fill=COLOR_TEXT)

    conectado = datos.get("conectado", False)
    dot_color = COLOR_OK if conectado else COLOR_ALERTA
    dot_r = int(h * 0.012)
    dot_x = w - margen - dot_r * 2
    dot_y = int(h * 0.045)
    draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], fill=dot_color)
    txt_conexion = "EN LINEA" if conectado else "SIN SEÑAL"
    bbox = draw.textbbox((0, 0), txt_conexion, font=fonts["small"])
    tw = bbox[2] - bbox[0]
    draw.text((dot_x - dot_r * 2 - tw - 10, dot_y - (bbox[3] - bbox[1]) / 2 - bbox[1]),
              txt_conexion, font=fonts["small"], fill=COLOR_MUTED)

    # --- Grid de 4 tarjetas (2x2) ---
    top_grid = int(h * 0.14)
    grid_h = int(h * 0.60)
    gap = int(w * 0.02)
    card_w = (w - margen * 2 - gap) / 2
    card_h = (grid_h - gap) / 2

    tarjetas = [
        ("TEMP. INTERNA", fmt_valor(datos.get("t_int"), "°C"), 0, 0),
        ("TEMP. EXTERNA", fmt_valor(datos.get("t_ext"), "°C"), 1, 0),
        ("HUMEDAD INTERNA", fmt_valor(datos.get("h_int"), "%"), 0, 1),
        ("HUMEDAD EXTERNA", fmt_valor(datos.get("h_ext"), "%"), 1, 1),
    ]

    for titulo, valor_txt, col, row in tarjetas:
        x = margen + col * (card_w + gap)
        y = top_grid + row * (card_h + gap)
        dibujar_tarjeta(draw, x, y, card_w, card_h, titulo, valor_txt,
                         fonts["card_titulo"], fonts["card_valor"], COLOR_ACCENT)

    # --- Banners de estado (dos mitades, abajo): umbral (ESP32) e IA ---
    banner_y = top_grid + grid_h + gap
    banner_h = h - banner_y - int(h * 0.02)
    mitad_w = (w - margen * 2 - gap) / 2

    def dibujar_banner_estado(x, ancho, etiqueta, estado_txt, subtitulo, color):
        draw.rounded_rectangle([x, banner_y, x + ancho, banner_y + banner_h],
                                radius=banner_h // 6, fill=color)

        draw.text((x + ancho * 0.05, banner_y + banner_h * 0.10), etiqueta,
                   font=fonts["banner_label"], fill=(20, 20, 20))

        texto = estado_txt.replace("_", " ")
        bbox = draw.textbbox((0, 0), texto, font=fonts["estado"])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x + (ancho - tw) / 2, banner_y + banner_h * 0.36 - bbox[1]),
                   texto, font=fonts["estado"], fill=(20, 20, 20))

        if subtitulo:
            bbox2 = draw.textbbox((0, 0), subtitulo, font=fonts["banner_label"])
            tw2 = bbox2[2] - bbox2[0]
            draw.text((x + (ancho - tw2) / 2, banner_y + banner_h * 0.80),
                      subtitulo, font=fonts["banner_label"], fill=(30, 30, 30))

    # Izquierda: estado por umbrales (calculado en el ESP32)
    estado = datos.get("estado", "SIN_DATOS")
    color_estado = ESTADO_COLOR.get(estado, COLOR_GRIS)
    dibujar_banner_estado(margen, mitad_w, "UMBRAL (ESP32)", estado, None, color_estado)

    # Derecha: prediccion de la red neuronal
    estado_ia = datos.get("estado_ia")
    confianza_ia = datos.get("confianza_ia")
    if estado_ia:
        color_ia = ESTADO_COLOR.get(estado_ia, COLOR_GRIS)
        subtitulo_ia = f"confianza {confianza_ia:.0%}" if confianza_ia is not None else None
        dibujar_banner_estado(margen + mitad_w + gap, mitad_w, "PREDICCION IA", estado_ia, subtitulo_ia, color_ia)
    else:
        dibujar_banner_estado(margen + mitad_w + gap, mitad_w, "PREDICCION IA", "SIN MODELO", None, COLOR_GRIS)

    return img


def main():
    w, h, bpp = get_fb_info()
    print(f"Framebuffer detectado: {w}x{h}, {bpp}bpp")

    fonts = {
        "header": cargar_fuente(FONT_PATHS_BOLD, int(h * 0.055)),
        "small": cargar_fuente(FONT_PATHS_REGULAR, int(h * 0.030)),
        "card_titulo": cargar_fuente(FONT_PATHS_BOLD, int(h * 0.032)),
        "card_valor": cargar_fuente(FONT_PATHS_BOLD, int(h * 0.11)),
        "estado": cargar_fuente(FONT_PATHS_BOLD, int(h * 0.045)),
        "banner_label": cargar_fuente(FONT_PATHS_BOLD, int(h * 0.022)),
    }

    fb = open(FB_DEVICE, "wb")
    try:
        while True:
            datos = leer_datos()
            img = dibujar_dashboard(w, h, datos, fonts)
            data = rgb_to_fb_bytes(img, bpp)
            fb.seek(0)
            fb.write(data)
            fb.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        fb.close()


if __name__ == "__main__":
    main()
