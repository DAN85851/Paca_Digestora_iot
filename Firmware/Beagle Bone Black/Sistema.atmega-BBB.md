# Cómo funciona el software de la BeagleBone Black (recepción, dashboards y web)

Este documento explica, para alguien que nunca ha visto el proyecto, **qué hace
cada uno de los 3 programas** que corren en la BeagleBone Black (BBB), cómo se
comunican entre sí, qué le llega exactamente desde el ESP32 por LoRa, y por qué
se diseñaron así.

---

## 1. Panorama general: ¿quién le habla a quién?

```
   ESP32 (junto a la paca)
        │  mide temperatura/humedad,
        │  arma un JSON, lo manda por LoRa
        ▼
   Radio LoRa (receptor) ── puerto serie /dev/ttyS1 @ 9600 baudios
        ▼
┌───────────────────────────┐
│      lora_parser.py       │   <- lee el puerto serie, guarda el último dato
└───────────────────────────┘
        │
        │  escribe (siempre el mismo archivo)
        ▼
   /tmp/paca_data.json   <- "buzón" compartido, un solo archivo
        │
        ├──────────────┐
        ▼              ▼
┌────────────────┐  ┌──────────────┐
│ fb_dashboard.py │  │ web_server.py│
│ (pantalla local)│  │ (navegador)  │
└────────────────┘  └──────────────┘
```

La idea central es: **un solo programa recibe los datos (`lora_parser.py`)**, y
**los deja en un archivo compartido**. Los otros dos programas (pantalla local y
servidor web) simplemente **leen ese archivo** cada cierto tiempo, sin tener que
saber nada de LoRa, puertos seriales, ni de la red neuronal. Esto es una
separación de responsabilidades: si mañana cambias la forma de recibir los datos
(por ejemplo, WiFi en vez de LoRa), solo tendrías que tocar `lora_parser.py`, y
los dos dashboards seguirían funcionando igual.

---

## 2. Diccionario de términos usados en estos 3 scripts

- **Puerto serie (`/dev/ttyS1`)**: es como un "cable de datos" por el que la BBB
  recibe, byte por byte, lo que manda el receptor LoRa. En Linux, los puertos
  serie se ven como archivos especiales (`/dev/ttyS...`).
- **Baudios (`BAUD = 9600`)**: la velocidad a la que se transmite la información
  por el puerto serie (9600 "símbolos" por segundo). Emisor y receptor deben
  usar la misma velocidad o los datos llegan corruptos.
- **JSON**: un formato de texto simple para representar datos estructurados,
  tipo `{"t_int": 42.3, "t_ext": 21.1, "estado": "NORMAL"}`. El ESP32 arma un
  JSON con las lecturas y lo envía como una línea de texto por LoRa.
- **Escritura atómica (`tempfile` + `os.replace`)**: en vez de escribir
  directamente sobre `/tmp/paca_data.json`, primero se escribe en un archivo
  temporal aparte y, solo cuando ya está completo, se "renombra" para
  reemplazar al archivo real (`os.replace`). Esto evita que otro programa lea el
  archivo justo en el instante en que se está escribiendo y se encuentre con un
  JSON incompleto o corrupto.
- **Polling**: la técnica de "revisar cada cierto tiempo si hay algo nuevo", en
  vez de recibir un aviso automático. Tanto la pantalla local como el servidor
  web funcionan así: leen el archivo compartido cada 1-2 segundos.
- **Framebuffer (`/dev/fb0`)**: es la memoria de video cruda de la pantalla,
  a la que se le puede escribir directamente los colores de cada píxel, **sin
  necesidad de un entorno gráfico (X11) corriendo**. Es la forma más liviana de
  dibujar algo en pantalla en un dispositivo con pocos recursos como la BBB.
- **Flask**: una librería de Python para crear un servidor web pequeño y
  sencillo. Aquí se usa para servir tanto la página HTML del dashboard como un
  endpoint (`/api/data`) que entrega los datos en JSON.
- **Endpoint / API**: una URL específica del servidor que responde con datos (en
  vez de una página completa). Aquí, `/api/data` responde solo el JSON con las
  últimas lecturas, y la página web lo consulta automáticamente cada 2 segundos
  con JavaScript para actualizar los medidores sin recargar la página.
- **`estado` vs `estado_ia`**: hay **dos** clasificaciones de fase mostradas en
  los dashboards, y no son lo mismo:
  - `estado`: lo calcula el **ESP32** con reglas simples de umbral (por ejemplo,
    "si la temperatura supera X, es ALERTA_TEMP"). Viaja ya calculado dentro del
    JSON que llega por LoRa.
  - `estado_ia` / `confianza_ia`: es la predicción de la **red neuronal**
    entrenada en el notebook (`Termofilico`, `Mesofilico`, `Enfriamiento`), junto
    con qué tan segura está la red de esa predicción (0.0 a 1.0). Estos dos
    campos hoy no los llena `lora_parser.py` — es el "enchufe" donde se debe
    conectar la función `predecir_numpy(...)` del notebook (ver sección 5).

---

## 3. Qué le llega exactamente a la BeagleBone (el JSON del ESP32)

El ESP32, junto a la paca, envía por LoRa una línea de texto en formato JSON,
algo como:

```json
{"t_int": 46.2, "t_ext": 24.8, "h_int": 61.0, "h_ext": 55.3, "estado": "ALERTA_TEMP"}
```

`lora_parser.py` toma exactamente estos 5 campos del payload:

| Campo | Qué es |
|---|---|
| `t_int` | Temperatura interna de la paca (sonda dentro del material). |
| `t_ext` | Temperatura ambiente / externa. |
| `h_int` | Humedad interna (de la "tierra"/material). |
| `h_ext` | Humedad ambiente. |
| `estado` | Clasificación por umbral, ya calculada en el propio ESP32 (`OPTIMO`, `NORMAL`, `ALERTA_TEMP`, `ALERTA_HUMEDAD`, o `DESCONOCIDO` si el ESP32 mandó algo no esperado). |

Si la línea que llega no es JSON válido (por ruido en la transmisión LoRa, por
ejemplo), `lora_parser.py` simplemente la ignora y sigue esperando la siguiente,
en vez de caerse.

---

## 4. `lora_parser.py`: el receptor (el corazón del sistema)

Esto es lo que hace, en orden:

1. Abre el puerto serie `/dev/ttyS1` a 9600 baudios.
2. Escribe un estado inicial "vacío" en `/tmp/paca_data.json` (para que los
   dashboards tengan algo que mostrar desde el primer segundo, aunque todavía no
   haya llegado ningún dato real).
3. En un bucle infinito:
   - Si hay bytes esperando en el puerto serie, lee una línea completa.
   - Intenta interpretarla como JSON. Si funciona, actualiza `t_int`, `t_ext`,
     `h_int`, `h_ext`, `estado`, marca `conectado = True`, y guarda la hora
     exacta de esta recepción.
   - Guarda el resultado en el archivo compartido usando **escritura atómica**.
4. En paralelo, revisa si han pasado más de **30 segundos (`TIMEOUT_SIN_DATOS`)**
   sin recibir nada. Si es así, marca `conectado = False` **una sola vez** (no en
   cada vuelta del bucle, para no llenar la consola de mensajes repetidos), pero
   **conserva las últimas lecturas** — así el dashboard puede mostrar "SIN SEÑAL"
   y aun así seguir mostrando el último valor conocido, en vez de borrarlo de
   golpe.

**Por qué la escritura atómica:** los otros dos programas (`fb_dashboard.py` y
`web_server.py`) están leyendo este mismo archivo constantemente, en paralelo,
sin ningún tipo de coordinación explícita entre procesos. Si `lora_parser.py`
escribiera directo sobre `/tmp/paca_data.json`, existiría una ventana de tiempo
en la que el archivo tiene texto a medias, y un lector podría toparse con un
JSON roto justo en ese instante. Escribir en un archivo aparte y luego
reemplazar con `os.replace` hace que, desde el punto de vista de cualquier
lector, el archivo **siempre esté completo o no exista todavía** — nunca a
medio escribir.

---

## 5. `fb_dashboard.py`: el panel en la pantalla física (sin necesitar X11)

Este script dibuja un dashboard **directamente sobre la pantalla conectada a la
BBB**, sin necesitar un entorno de escritorio (X11/Wayland) corriendo, algo que
sería demasiado pesado para el hardware disponible.

Cómo funciona:

1. **Detecta automáticamente la resolución y profundidad de color** de la
   pantalla (`get_fb_info`), primero probando leer archivos del sistema
   (`/sys/class/graphics/fb0`), y si eso falla, usando el comando `fbset` como
   respaldo. Esto hace que el mismo script sirva tanto para una pantalla pequeña
   como para un panel de 7" sin tener que tocar el código.
2. Con Pillow (PIL) **dibuja una imagen en memoria** (no en la pantalla
   todavía): título, dos indicadores de conexión, 4 tarjetas (temperatura y
   humedad interna/externa) y dos banners de estado — uno con el estado por
   umbral del ESP32, y otro con la predicción de la red neuronal (`estado_ia`,
   `confianza_ia`), cada uno con su propio color según la fase.
3. Convierte esa imagen a los bytes crudos que espera el framebuffer
   (`rgb_to_fb_bytes`), soportando los 3 formatos de color más comunes (16, 24 y
   32 bits por píxel), porque no todas las pantallas/controladores usan el mismo
   formato.
4. Escribe esos bytes directamente en `/dev/fb0`, y repite el ciclo completo
   cada 1 segundo.

**Por qué los tamaños de fuente son proporcionales a la altura de pantalla**
(`int(h * 0.055)`, etc.) **y no números fijos**: así, si mañana se cambia de una
pantallita pequeña a un panel de 7" con más resolución, el texto sigue viéndose
proporcional y legible sin tener que ajustar el código a mano para cada
pantalla.

---

## 6. `web_server.py`: el dashboard accesible desde el celular/PC

Este script expone el mismo dashboard, pero como una página web accesible desde
cualquier dispositivo en la misma red (celular, laptop, etc.), usando **Flask**.

Cómo funciona:

1. `leer_datos()` abre `/tmp/paca_data.json` (el mismo archivo que escribe
   `lora_parser.py`) y, si por algún motivo no existe o falla la lectura,
   devuelve un estado "vacío" en vez de caerse.
2. La ruta `/api/data` simplemente devuelve ese JSON tal cual, más una marca de
   tiempo del propio servidor.
3. La ruta `/` (la página principal) devuelve una página HTML completa, con su
   propio CSS (tema oscuro tipo panel industrial) y un poco de JavaScript.
4. Ese JavaScript, cada 2 segundos, llama a `/api/data` y actualiza en pantalla:
   los 4 medidores en forma de arco (temperatura/humedad interna y externa), el
   banner de estado por umbral, el banner de predicción de la red neuronal (con
   una barra de "confianza"), y un punto de color que indica si sigue habiendo
   señal LoRa reciente (`conectado`).

**Por qué se separa `/api/data` de la página HTML:** así el navegador solo pide
un JSON pequeño cada 2 segundos (rápido, poco tráfico) y actualiza los números
con JavaScript, en vez de recargar toda la página completa una y otra vez. Es el
mismo patrón que usan casi todos los dashboards en tiempo real.

**Por qué Flask y no algo más pesado (Django, etc.):** para un dashboard de
lectura simple con un solo endpoint, Flask es lo mínimo necesario — coherente
con la misma filosofía de todo el proyecto en la BBB: usar lo más liviano
posible dado el hardware limitado.

---

## 7. Cómo se conecta esto con la red neuronal del notebook

Los dos dashboards (`fb_dashboard.py` y `web_server.py`) **ya están preparados**
para mostrar `estado_ia` y `confianza_ia` (colores propios para `Termofilico`,
`Mesofilico`, `Enfriamiento`, y una barra de confianza), pero **hoy
`lora_parser.py` todavía no llena esos dos campos** — el ESP32 solo manda el
`estado` por umbral, no la predicción de la red.

El paso que falta (y que se explica al final del notebook de entrenamiento) es:

1. Cargar una sola vez, al iniciar `lora_parser.py`, el archivo
   `modelo_paca_pesos.npz` (los pesos `W1, b1, W2, b2, mu, sigma` exportados del
   notebook).
2. Cada vez que llega una lectura nueva y válida por LoRa, además de guardar
   `t_int, t_ext, h_int, h_ext, estado`, calcular también `pendiente_temp` (la
   misma tendencia de temperatura que se calculó al entrenar) y llamar a la
   función `predecir_numpy(...)` del notebook con esos 5 valores.
3. Guardar el resultado (`estado_ia` = nombre de la fase, `confianza_ia` =
   probabilidad de esa fase) en el mismo diccionario `ultimo_dato` antes de
   escribirlo con `escribir_estado(...)`.

Como la predicción con numpy puro son solo dos multiplicaciones de matrices, este
paso no le agrega ninguna carga real a la BBB — es justo lo que se verificó al
final del notebook (que la predicción en numpy coincide con la de TensorFlow).

---

## 8. Resumen del flujo completo

1. El **ESP32** mide sensores, calcula un estado simple por umbral, y manda todo
   como JSON por **LoRa**.
2. **`lora_parser.py`** recibe esa línea por el puerto serie, la valida, y la
   guarda de forma **atómica** en `/tmp/paca_data.json` — este es el único punto
   de contacto con el hardware de radio.
3. **`fb_dashboard.py`** lee ese archivo y dibuja un panel directo en la
   pantalla física, sin necesitar un entorno gráfico pesado.
4. **`web_server.py`** lee el mismo archivo y expone un dashboard web con Flask,
   accesible desde cualquier dispositivo en la red.
5. El **"enchufe" para la red neuronal** (`estado_ia`, `confianza_ia`) ya existe
   en ambos dashboards; solo falta que `lora_parser.py` cargue los pesos
   exportados del notebook y llene esos dos campos en cada lectura nueva.

Esta arquitectura (un receptor, un archivo compartido, y varios "lectores"
independientes) es la razón por la que se puede tener pantalla local **y**
dashboard web **y**, más adelante, la predicción de IA, sin que ninguno de los
tres programas necesite saber cómo funcionan los otros dos.
