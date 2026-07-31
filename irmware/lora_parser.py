#!/usr/bin/env python3
"""
Receptor/parser LoRa para la Paca Digestora.

Lee líneas JSON desde /dev/ttyS1 (enviadas por el ESP32 transmisor) y las
escribe en un archivo compartido (/tmp/paca_data.json) que leen tanto el
dashboard de pantalla (fb_dashboard.py) como el servidor web (web_server.py).

Escribe con reemplazo atómico (tempfile + os.replace) para que ningún
lector encuentre nunca el archivo a medio escribir.

Uso:
    python3 lora_parser.py
"""

import serial
import json
import time
import os
import tempfile

PORT = "/dev/ttyS1"
BAUD = 9600
OUTPUT_FILE = "/tmp/paca_data.json"
TIMEOUT_SIN_DATOS = 30  # segundos sin recibir nada -> se marca "desconectado"


def escribir_estado(data: dict, conectado: bool):
    data = dict(data)
    data["conectado"] = conectado
    data["ultima_actualizacion"] = time.time()

    dir_tmp = os.path.dirname(OUTPUT_FILE) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_tmp)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, OUTPUT_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def main():
    print(f"Iniciando receptor LoRa en {PORT} a {BAUD} baudios...")

    ultimo_dato = {
        "t_int": None,
        "t_ext": None,
        "h_int": None,
        "h_ext": None,
        "estado": "SIN_DATOS",
    }
    ultima_recepcion = 0
    marcado_desconectado = False

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print("Puerto serie abierto con éxito. Esperando mensajes...")
    except Exception as e:
        print(f"Error abriendo puerto serie: {e}")
        return

    # Estado inicial para que dashboard/web tengan algo que leer desde el arranque
    escribir_estado(ultimo_dato, conectado=False)

    try:
        while True:
            try:
                if ser.in_waiting > 0:
                    raw_line = ser.readline()
                    line = raw_line.decode("utf-8", errors="ignore").strip()

                    if line:
                        try:
                            payload = json.loads(line)
                            ultimo_dato.update({
                                "t_int": payload.get("t_int"),
                                "t_ext": payload.get("t_ext"),
                                "h_int": payload.get("h_int"),
                                "h_ext": payload.get("h_ext"),
                                "estado": payload.get("estado", "DESCONOCIDO"),
                            })
                            ultima_recepcion = time.time()
                            marcado_desconectado = False
                            escribir_estado(ultimo_dato, conectado=True)
                            print(f"[LoRa RX] {line}")
                        except json.JSONDecodeError:
                            print(f"[LoRa RX - no JSON, ignorado] {line}")

                # Si pasó demasiado tiempo sin datos, marcar desconectado (solo una vez)
                if (ultima_recepcion and not marcado_desconectado
                        and (time.time() - ultima_recepcion > TIMEOUT_SIN_DATOS)):
                    marcado_desconectado = True
                    escribir_estado(ultimo_dato, conectado=False)
                    print("[LoRa] Sin datos recientes, marcado como desconectado.")

                time.sleep(0.1)

            except Exception as e:
                print(f"Error en el puerto serie: {e}")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceptor detenido por el usuario.")
    finally:
        if ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
