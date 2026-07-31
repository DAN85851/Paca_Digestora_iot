#!/usr/bin/env python3
"""
Servidor web - Dashboard de la Paca Digestora.

Sirve una página con el mismo dashboard que se muestra en la pantalla
local, leyendo el mismo archivo compartido que escribe lora_parser.py.

Requiere en la BBB (Arch Linux ARM):
    pacman -S python-flask

Uso:
    python3 web_server.py
    Luego abre http://<ip-de-la-bbb>:8080 desde otro dispositivo en la red.
"""

import json
import time
from flask import Flask, jsonify, render_template_string

DATA_FILE = "/tmp/paca_data.json"
HOST = "0.0.0.0"
PORT = 8080

app = Flask(__name__)


def leer_datos():
    try:
        with open(DATA_FILE) as f:
            datos = json.load(f)
    except Exception:
        datos = {
            "t_int": None, "t_ext": None, "h_int": None, "h_ext": None,
            "estado": "SIN_DATOS", "estado_ia": None, "confianza_ia": None,
            "conectado": False, "ultima_actualizacion": 0,
        }
    datos["servidor_ts"] = time.time()
    return datos


@app.route("/api/data")
def api_data():
    return jsonify(leer_datos())


@app.route("/")
def index():
    return render_template_string(PAGINA_HTML)


PAGINA_HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paca Digestora · Panel de monitoreo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #12151a;
    --bg-grid: #171b21;
    --surface: #1c2128;
    --border: #2a2f38;
    --text: #e8e6e1;
    --muted: #8b93a1;
    --accent: #d98e2b;
    --accent-dim: #7a5620;
    --ok: #4caf6d;
    --alerta: #e5484d;
    --gris: #646a74;
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    background:
      linear-gradient(var(--bg-grid) 1px, transparent 1px) 0 0 / 100% 34px,
      var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    padding: 28px 20px 60px;
  }

  .wrap { max-width: 980px; margin: 0 auto; }

  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--border);
    padding-bottom: 18px;
    margin-bottom: 28px;
  }

  .brand-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.18em;
    color: var(--accent);
    text-transform: uppercase;
    margin: 0 0 6px;
  }

  h1 {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin: 0;
  }

  .conexion {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--muted);
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--gris);
    box-shadow: 0 0 0 0 rgba(76,175,109,0.6);
  }

  .dot.on {
    background: var(--ok);
    animation: pulso 2s infinite;
  }

  .dot.off { background: var(--alerta); }

  @keyframes pulso {
    0%   { box-shadow: 0 0 0 0 rgba(76,175,109,0.55); }
    70%  { box-shadow: 0 0 0 8px rgba(76,175,109,0); }
    100% { box-shadow: 0 0 0 0 rgba(76,175,109,0); }
  }

  .banners-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-bottom: 28px;
  }

  @media (max-width: 640px) {
    .banners-row { grid-template-columns: 1fr; }
  }

  .estado-banner {
    border-radius: 14px;
    padding: 22px 26px;
    background: var(--gris);
    transition: background 0.4s ease;
  }

  .estado-banner .fila-superior {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .estado-banner .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(0,0,0,0.55);
    margin: 0 0 4px;
  }

  .estado-banner .valor {
    font-size: 26px;
    font-weight: 800;
    color: #14161a;
    margin: 0;
  }

  .estado-banner .ts {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: rgba(0,0,0,0.5);
    text-align: right;
  }

  .confianza-barra-fondo {
    margin-top: 12px;
    height: 6px;
    border-radius: 3px;
    background: rgba(0,0,0,0.18);
    overflow: hidden;
  }

  .confianza-barra-relleno {
    height: 100%;
    background: rgba(20,22,26,0.75);
    width: 0%;
    transition: width 0.4s ease;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }

  @media (max-width: 640px) {
    .grid { grid-template-columns: 1fr; }
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px 22px;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(160deg, rgba(217,142,43,0.06), transparent 55%);
    pointer-events: none;
  }

  .card-titulo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 14px;
  }

  .gauge-row {
    display: flex;
    align-items: center;
    gap: 18px;
  }

  .gauge-valor {
    font-family: 'JetBrains Mono', monospace;
    font-size: 40px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
    min-width: 130px;
  }

  svg.gauge { flex-shrink: 0; }

  .rango {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
  }

  footer {
    margin-top: 34px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.04em;
  }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <p class="brand-eyebrow">Sistema de biodigestión &middot; Monitoreo remoto</p>
      <h1>Paca Digestora</h1>
    </div>
    <div class="conexion">
      <span class="dot" id="dot"></span>
      <span id="conexion-txt">CONECTANDO&hellip;</span>
    </div>
  </header>

  <div class="banners-row">
    <div class="estado-banner" id="estado-banner">
      <div class="fila-superior">
        <div>
          <p class="label">Estado (umbral ESP32)</p>
          <p class="valor" id="estado-valor">&mdash;</p>
        </div>
        <div class="ts" id="ultima-actualizacion">sin datos aún</div>
      </div>
    </div>

    <div class="estado-banner" id="estado-ia-banner">
      <div class="fila-superior">
        <div>
          <p class="label">Predicción (red neuronal)</p>
          <p class="valor" id="estado-ia-valor">&mdash;</p>
        </div>
        <div class="ts" id="confianza-ia-txt">sin modelo</div>
      </div>
      <div class="confianza-barra-fondo">
        <div class="confianza-barra-relleno" id="confianza-ia-barra"></div>
      </div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <p class="card-titulo">Temperatura interna</p>
      <div class="gauge-row">
        <svg class="gauge" width="100" height="60" viewBox="0 0 100 60">
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#2a2f38" stroke-width="10" stroke-linecap="round"/>
          <path id="arc-t-int" d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#d98e2b" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 126"/>
        </svg>
        <div class="gauge-valor" id="t_int">--&deg;C</div>
      </div>
      <div class="rango"><span>20&deg;C</span><span>65&deg;C</span></div>
    </div>

    <div class="card">
      <p class="card-titulo">Temperatura externa</p>
      <div class="gauge-row">
        <svg class="gauge" width="100" height="60" viewBox="0 0 100 60">
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#2a2f38" stroke-width="10" stroke-linecap="round"/>
          <path id="arc-t-ext" d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#d98e2b" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 126"/>
        </svg>
        <div class="gauge-valor" id="t_ext">--&deg;C</div>
      </div>
      <div class="rango"><span>10&deg;C</span><span>40&deg;C</span></div>
    </div>

    <div class="card">
      <p class="card-titulo">Humedad interna</p>
      <div class="gauge-row">
        <svg class="gauge" width="100" height="60" viewBox="0 0 100 60">
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#2a2f38" stroke-width="10" stroke-linecap="round"/>
          <path id="arc-h-int" d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#d98e2b" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 126"/>
        </svg>
        <div class="gauge-valor" id="h_int">--%</div>
      </div>
      <div class="rango"><span>30%</span><span>95%</span></div>
    </div>

    <div class="card">
      <p class="card-titulo">Humedad externa</p>
      <div class="gauge-row">
        <svg class="gauge" width="100" height="60" viewBox="0 0 100 60">
          <path d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#2a2f38" stroke-width="10" stroke-linecap="round"/>
          <path id="arc-h-ext" d="M 10 55 A 40 40 0 0 1 90 55" fill="none" stroke="#d98e2b" stroke-width="10" stroke-linecap="round" stroke-dasharray="0 126"/>
        </svg>
        <div class="gauge-valor" id="h_ext">--%</div>
      </div>
      <div class="rango"><span>20%</span><span>90%</span></div>
    </div>
  </div>

  <footer>PACA-01 &middot; LoRa 9600 baud &middot; actualiza cada 2s</footer>
</div>

<script>
const RANGOS = {
  t_int: [20, 65], t_ext: [10, 40],
  h_int: [30, 95], h_ext: [20, 90],
};
const ARC_LARGO = 126; // longitud aproximada del arco en el viewBox 0..100

const ESTADO_COLORES = {
  // estados por umbral (ESP32)
  OPTIMO: "#4caf6d",
  NORMAL: "#d98e2b",
  ALERTA_TEMP: "#e5484d",
  ALERTA_HUMEDAD: "#e5484d",
  SIN_DATOS: "#646a74",
  DESCONOCIDO: "#646a74",
  // estados predichos por la red neuronal (nombres del notebook de entrenamiento)
  Termofilico: "#e5484d",
  Mesofilico: "#d98e2b",
  Enfriamiento: "#5a96dc",
};

function setArco(id, valor, [min_v, max_v]) {
  const el = document.getElementById(id);
  if (valor === null || valor === undefined) {
    el.setAttribute("stroke-dasharray", `0 ${ARC_LARGO}`);
    return;
  }
  const frac = Math.max(0, Math.min(1, (valor - min_v) / (max_v - min_v)));
  const largo = frac * ARC_LARGO;
  el.setAttribute("stroke-dasharray", `${largo} ${ARC_LARGO}`);
}

function actualizar() {
  fetch("/api/data")
    .then(r => r.json())
    .then(d => {
      document.getElementById("t_int").innerHTML = d.t_int != null ? `${d.t_int.toFixed(1)}&deg;C` : "--&deg;C";
      document.getElementById("t_ext").innerHTML = d.t_ext != null ? `${d.t_ext.toFixed(1)}&deg;C` : "--&deg;C";
      document.getElementById("h_int").innerHTML = d.h_int != null ? `${d.h_int.toFixed(1)}%` : "--%";
      document.getElementById("h_ext").innerHTML = d.h_ext != null ? `${d.h_ext.toFixed(1)}%` : "--%";

      setArco("arc-t-int", d.t_int, RANGOS.t_int);
      setArco("arc-t-ext", d.t_ext, RANGOS.t_ext);
      setArco("arc-h-int", d.h_int, RANGOS.h_int);
      setArco("arc-h-ext", d.h_ext, RANGOS.h_ext);

      const estado = d.estado || "SIN_DATOS";
      document.getElementById("estado-valor").textContent = estado.replace(/_/g, " ");
      document.getElementById("estado-banner").style.background = ESTADO_COLORES[estado] || "#646a74";

      const estadoIaValor = document.getElementById("estado-ia-valor");
      const confianzaTxt = document.getElementById("confianza-ia-txt");
      const confianzaBarra = document.getElementById("confianza-ia-barra");
      const bannerIa = document.getElementById("estado-ia-banner");

      if (d.estado_ia) {
        estadoIaValor.textContent = d.estado_ia.replace(/_/g, " ");
        bannerIa.style.background = ESTADO_COLORES[d.estado_ia] || "#646a74";
        if (d.confianza_ia != null) {
          const pct = Math.round(d.confianza_ia * 100);
          confianzaTxt.textContent = `confianza ${pct}%`;
          confianzaBarra.style.width = `${pct}%`;
        } else {
          confianzaTxt.textContent = "";
          confianzaBarra.style.width = "0%";
        }
      } else {
        estadoIaValor.textContent = "SIN MODELO";
        bannerIa.style.background = "#646a74";
        confianzaTxt.textContent = "";
        confianzaBarra.style.width = "0%";
      }

      const dot = document.getElementById("dot");
      const conexionTxt = document.getElementById("conexion-txt");
      if (d.conectado) {
        dot.className = "dot on";
        conexionTxt.textContent = "EN LINEA";
      } else {
        dot.className = "dot off";
        conexionTxt.textContent = "SIN SEÑAL";
      }

      if (d.ultima_actualizacion) {
        const fecha = new Date(d.ultima_actualizacion * 1000);
        document.getElementById("ultima-actualizacion").textContent =
          "actualizado " + fecha.toLocaleTimeString("es-CO");
      }
    })
    .catch(() => {
      document.getElementById("dot").className = "dot off";
      document.getElementById("conexion-txt").textContent = "SERVIDOR NO RESPONDE";
    });
}

actualizar();
setInterval(actualizar, 2000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print(f"Dashboard web en http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
