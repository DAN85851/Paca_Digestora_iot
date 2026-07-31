# Sistema Inteligente de Monitoreo IoT para Pacas Digestoras

## 📋 Descripción General del Proyecto
Este proyecto consiste en un **sistema embebido autónomo y de bajo costo** diseñado para la adquisición, transmisión inalámbrica y análisis inteligente de variables físico-químicas en **pacas digestoras** (sistemas de descomposición orgánica). 

El núcleo del sistema está compuesto por una **tarjeta de circuito impreso (PCB) a medida** equipada con sensores de alta precisión para medir en tiempo real la **temperatura interna (sonda)**, **humedad interna de la materia orgánica**, así como la **temperatura y humedad ambiental**. 

### ⚙️ Arquitectura del Sistema
1. **Nodo Sensor (PCB + Microcontrolador):** Recolecta los datos de los sensores de la paca de forma autónoma.
2. **Enlace Inalámbrico LoRa:** Transmite los paquetes de datos a larga distancia de manera eficiente y con bajo consumo energético.
3. **Gateway y Procesamiento en Borde (BeagleBone Black):** Recibe la telemetría inalámbrica y ejecuta modelos de **Inteligencia Artificial / Machine Learning** para predecir estados térmicos (fases mesofílicas y termofílicas) y detectar anomalías en la descomposición.
4. **Servidor Local y Visualización (Dashboard):** Levanta un servidor web local accesible mediante interfaz gráfica de pantalla local y páginas web conectadas en red, permitiendo visualizar métricas históricas, curvas en tiempo real y alertas del proceso biológico.

---

## 🛠️ Estructura del Repositorio

```text
/
├── 📁 firmware/          # Código fuente para microcontroladores y scripts de la BeagleBone Black
├── 📁 hardware/          # Archivos de diseño PCB (KiCad), esquemáticos y renders 3D
├── 📁 cad_enclosures/    # Diseños mecánicos y archivos STEP/STL para la carcasa 3D
├── 📁 data_analysis/     # Datasets históricos, scripts en Python, PyQt6 y modelos de IA
├── 📁 docs/              # Documentación técnica, manuales y notas sobre el proceso biológico
└── 📄 README.md          # Documentación principal del proyecto
