# La BeagleBone Black y por qué corre Arch Linux ARM (explicado desde cero)

Este documento explica, para alguien que nunca ha tocado hardware embebido ni
distribuciones de Linux, **qué es exactamente la BeagleBone Black (BBB)**, cuáles
son sus características reales, y **por qué se eligió Arch Linux ARM** como
sistema operativo para correr todo el software del proyecto (`lora_parser.py`,
`fb_dashboard.py`, `web_server.py`, y más adelante la red neuronal).


<img width="1194" height="901" alt="image" src="https://github.com/user-attachments/assets/bbc49c5f-e5ed-4b6a-9eab-4db8887a6a5f" />

---

## 1. ¿Qué es la BeagleBone Black?

La BeagleBone Black es una **computadora de placa única** (en inglés,
*Single Board Computer* o SBC): toda la computadora — procesador, memoria,
puertos, todo — está soldada en una sola placa del tamaño de una tarjeta de
crédito grande. Es parecida en concepto a una Raspberry Pi, pero pensada desde
el origen para **electrónica y control de hardware** (tiene más pines de
propósito general y un par de coprocesadores dedicados a eso), mientras que la
Raspberry Pi está más orientada a multimedia/uso general.

Es el tipo de computadora ideal para un proyecto como el de la paca digestora:
no necesitas un PC de escritorio completo para leer sensores, correr una red
neuronal pequeña, y mostrar un dashboard — necesitas algo pequeño, barato, de
bajo consumo, y que puedas dejar encendido 24/7 junto a la paca.

---

## 2. Características reales de la BBB (y qué significa cada una)

| Característica | Valor típico de la BBB | Qué significa en criollo |
|---|---|---|
| **Procesador (SoC)** | Texas Instruments **AM3358**, núcleo **ARM Cortex-A8** a ~1 GHz, **un solo núcleo** | El "SoC" (*System on Chip*) es el cerebro: CPU + varios controladores integrados en un solo chip. "Un solo núcleo" es clave: **no puede hacer varias tareas pesadas realmente en paralelo** como sí puede un PC moderno con 4, 8 o más núcleos — todo se reparte por turnos rapidísimos entre un único núcleo. |
| **RAM** | 512 MB DDR3 | La memoria de trabajo. Para referencia, un celular gama media de hoy tiene 10-20 veces más. Esto obliga a evitar programas pesados que reserven mucha memoria de golpe. |
| **Almacenamiento** | 4 GB de **eMMC** integrado (memoria flash soldada a la placa) + ranura para **microSD** | El eMMC es como un "disco duro" pequeño soldado dentro de la placa; la microSD es opcional/removible, y se suele usar para instalar un sistema operativo distinto al que viene de fábrica. |
| **GPU** | PowerVR SGX530 | Existe una GPU, pero es muy limitada para gráficos 3D modernos — **no** es un uso realista para renderizar interfaces pesadas o videojuegos. Por eso el dashboard visual del proyecto se dibuja directo en el framebuffer (ver el documento anterior) en vez de depender de aceleración gráfica. |
| **GPIO** | 2 conectores de expansión ("capes") con decenas de pines digitales/analógicos | GPIO (*General Purpose Input/Output*) son pines que se pueden programar para leer o escribir señales eléctricas — así es como, en general, este tipo de placas se conectan a sensores y actuadores. |
| **PRU (2x)** | Dos **microcontroladores auxiliares** (Programmable Realtime Units) dentro del mismo chip | Son "ayudantes" pequeños e independientes del núcleo principal, pensados para tareas de temporización muy exigente (como generar señales exactas a microsegundos) sin que el sistema operativo principal interfiera. En este proyecto no se usan directamente (la lectura de sensores la hace el ESP32), pero es una de las razones de diseño por las que la BBB existe: está pensada para *control en tiempo real*, no solo para "ser una mini-PC". |
| **Puertos serie / UART** | Varios, expuestos por los pines de expansión | Es justo el puerto (`/dev/ttyS1`) que usa `lora_parser.py` para recibir los datos del receptor LoRa — sin necesitar ningún adaptador USB extra. |
| **Consumo eléctrico** | Muy bajo (pocos vatios) | Importante para un dispositivo que va a estar encendido de forma continua junto a la paca, posiblemente con alimentación limitada (batería/solar), como ya se documentó en el notebook de entrenamiento (los cortes de energía que corrompían el CSV). |

### En resumen, lo que hay que recordar de estas características

La BBB es **muy limitada comparada con un PC o incluso con un celular moderno**:
un solo núcleo de CPU, poca RAM, sin GPU real, alimentación que puede fallar.
**Esta es la razón de fondo detrás de casi todas las decisiones técnicas que ya
se documentaron en el proyecto**: no instalar TensorFlow en la BBB (solo numpy
puro), dibujar directo sobre el framebuffer en vez de usar un entorno gráfico
completo, usar Flask (liviano) en vez de un framework web pesado, etc. Todo el
proyecto está diseñado "hacia abajo", pensando primero en qué puede soportar
realmente este hardware.

---

## 3. ¿Qué es una distribución de Linux, y por qué hay que elegir una?

Cuando compras/consigues una BeagleBone Black, no viene "vacía" — viene con un
sistema operativo, generalmente alguna versión de **Debian** preinstalada en el
eMMC. Pero **el sistema operativo se puede reemplazar completamente**, instalando
otra distribución (por ejemplo, en una microSD, o reescribiendo el eMMC).

Una "distribución" de Linux (o *distro*) es, en esencia: el núcleo de Linux +
un gestor de paquetes + un conjunto de decisiones sobre qué viene instalado por
defecto y cómo se actualiza todo. Debian, Ubuntu, Arch Linux, Fedora, etc., todas
usan el mismo núcleo Linux por debajo, pero difieren muchísimo en filosofía,
qué traen preinstalado, y cómo se actualizan.

En este proyecto se eligió **Arch Linux ARM** (la versión de Arch Linux
adaptada para procesadores ARM como el de la BBB, en vez de los procesadores
x86 de una PC normal) en vez de quedarse con la Debian que trae de fábrica.

---

## 4. Por qué Arch Linux ARM, específicamente, y no otra opción

### 4.1 Instalación mínima "desde cero" (no trae nada que no pediste)

Arch Linux sigue la filosofía de **empezar de un sistema base mínimo** y que
**tú decidas explícitamente qué instalar**, en vez de venir con un escritorio
gráfico, servicios, y programas preinstalados que nunca vas a usar. Con solo
512 MB de RAM y un solo núcleo, cada proceso corriendo de fondo que no aporta
nada al proyecto es memoria y CPU que le quitas a lo que sí importa (leer
sensores, correr la red neuronal, dibujar el dashboard). Una instalación
"gorda" tipo Ubuntu Desktop, en cambio, viene con un entorno gráfico completo y
decenas de servicios corriendo desde el arranque, la mayoría inútiles para un
dispositivo embebido headless (sin pantalla ni teclado conectados de forma
permanente).

### 4.2 Rolling release: siempre actualizado, sin "saltos" grandes de versión

Arch Linux es una distribución de **rolling release** (lanzamiento continuo):
en vez de sacar versiones grandes cada 1-2 años (como hace Ubuntu con sus LTS),
los paquetes se actualizan de forma continua y frecuente. Esto significa que
librerías como Python, Flask, Pillow o numpy están casi siempre en versiones
recientes, sin tener que esperar meses/años a un "salto de versión" grande y
arriesgado de la distro completa. Para un proyecto universitario que se sigue
tocando y mejorando durante meses, esto evita quedarse atascado con versiones
viejas de las librerías que se necesitan.

### 4.3 `pacman`: gestor de paquetes simple y directo

El gestor de paquetes de Arch (`pacman`) es rápido y con una sintaxis simple
(`pacman -S python-flask`, como se ve en los propios scripts del proyecto). No
hay curvas de aprendizaje complicadas ni herramientas gráficas pesadas de por
medio — coherente con la misma filosofía de "solo lo necesario" del resto del
proyecto.

### 4.4 Control total y transparencia (bueno para aprender y para depurar)

Arch no oculta las decisiones de configuración detrás de asistentes gráficos:
tú editas los archivos de configuración directamente y entiendes exactamente
qué está corriendo en tu sistema y por qué. Para un proyecto de universidad
donde hay que **justificar cada decisión técnica** (como ya se hizo con los
umbrales del modelo o el split de datos), esto es una ventaja real: cuando algo
falla (por ejemplo, el framebuffer no responde, o el puerto serie no aparece),
es mucho más fácil rastrear la causa en un sistema mínimo y transparente que en
uno con muchas capas de "magia" preconfigurada.

### 4.5 Buen soporte para ARM y para la comunidad BeagleBoard

Arch Linux ARM es un proyecto hermano de Arch Linux dedicado específicamente a
llevar esa misma filosofía a procesadores ARM (como el de la BBB, que no usa la
arquitectura x86 de una PC de escritorio). Tiene soporte activo y documentación
específica para BeagleBone, lo cual reduce fricción al momento de configurar
cosas específicas del hardware (framebuffer, UART, GPIO).

### 4.6 El trade-off honesto

Elegir Arch Linux ARM no es gratis: es **menos amigable para principiantes**
que Debian o Raspbian — no trae tantas cosas preconfiguradas por defecto, así
que hay que instalar y configurar más cosas a mano (justo lo que se ve en los
comentarios `pacman -S ...` al inicio de cada script del proyecto). El punto es
que, para un proyecto donde el hardware es limitado y donde parte del objetivo
académico es entender bien cada pieza del sistema, ese control manual es una
ventaja, no un obstáculo — pero es honesto reconocer que para alguien que solo
quiere "encender y usar" sin entender el sistema, Debian sería más rápido de
poner en marcha.

---

## 5. Cómo se conecta esto con el resto del proyecto

Todas las decisiones de software que ya se documentaron (no instalar
TensorFlow, dibujar directo sobre `/dev/fb0`, usar Flask en vez de un framework
pesado, escritura atómica de archivos) son consistentes con **por qué se
escogió este hardware y este sistema operativo en primer lugar**: la BBB con
Arch Linux ARM da control total sobre qué corre en la máquina, y ese control es
justamente lo que permite mantener el sistema liviano dentro de las
limitaciones reales del hardware (un núcleo, 512 MB de RAM, sin GPU real,
alimentación que puede fallar).

En una presentación o sustentación, esta es la cadena de justificación
completa:

**Hardware limitado (BBB)** → **SO mínimo y transparente (Arch Linux ARM)** →
**decisiones de software liviano** (numpy puro en vez de TensorFlow,
framebuffer en vez de X11, Flask en vez de un framework pesado, escritura
atómica de un solo archivo compartido en vez de una base de datos completa).
