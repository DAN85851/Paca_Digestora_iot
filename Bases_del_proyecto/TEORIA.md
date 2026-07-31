# Fundamentos Teóricos y Biológicos: Pacas Digestoras

## 🌿 ¿Qué es una Paca Digestora?
Una paca digestora (o biorreactor orgánico artesanal) es un sistema diseñado para la gestión y descomposición acelerada de residuos orgánicos urbanos (restos de cocina, hojas, poda, etc.) mediante prensado y compactación aeróbico-anaeróbica estructurada. Su objetivo principal es transformar los residuos en abono (o digestato estabilizado) de forma limpia, sin malos olores y evitando la atracción de vectores.

---

## 🔬 Fases Termodinámicas y Microbiológicas del Proceso
El proceso de descomposición dentro de la paca no es estático; evoluciona a través de distintas etapas gobernadas por la temperatura y la sucesión de grupos microbianos específicos:

1. **Etapa Psicrofílica (Fría / Inicio):** 
   * **Temperatura:** $< 20^\circ\text{C}$.
   * **Dinámica:** Fase inicial donde la actividad microbiana es lenta y dominada por microorganismos psicrófilos adaptados al ambiente.

2. **Etapa Mesofílica (Temperatura Moderada):**
   * **Rango:** $20^\circ\text{C} \text{ a } 45^\circ\text{C}$.
   * **Dinámica:** Colonización rápida por bacterias mesófilas que degradan azúcares y proteínas sencillas. Este metabolismo genera calor de forma natural, elevando la temperatura del sistema.

3. **Etapa Termofílica (Alta Temperatura / Saneamiento):**
   * **Rango:** $45^\circ\text{C} \text{ a } 70^\circ\text{C}$ (con picos óptimos alrededor de los $55^\circ\text{C}$ a $60^\circ\text{C}$).
   * **Dinámica:** Es la fase crítica de control y máxima eficiencia. Los microorganismos termófilos degradan compuestos complejos (como celulosa). **Función clave:** Este nivel de calor actúa como un proceso de esterilización natural que destruye patógenos (como *E. coli*), parásitos y semillas de malas hierbas. *(Nota: En este proyecto, se implementaron técnicas de saturación/inundación controlada para acelerar artificialmente la llegada a esta fase en los primeros días).*

4. **Etapa de Enfriamiento y Maduración:**
   * **Dinámica:** Al agotarse los nutrientes lábiles, la actividad biológica decae, la temperatura desciende gradualmente hacia la ambiental, y hongos actinomicetos estabilizan la materia en un humus maduro.

---

## 📊 Justificación de Variables Seleccionadas para el Sensado IoT

Para automatizar la supervisión del estado del biorreactor, nuestra PCB embebida y la red de sensores recolectan las siguientes variables críticas:

* **Temperatura Interna de la Paca (`Temp_Sonda_C`):**
  * *Por qué se escogió:* Es el indicador biológico fundamental. Permite identificar en tiempo real si el sistema se encuentra en fase mesofílica o si ha logrado el salto exitoso a la fase termofílica para garantizar el saneamiento.
* **Humedad Interna de la Materia Orgánica (`Hum_Tierra_Pct`):**
  * *Por qué se escogió:* La actividad microbiana requiere un rango hídrico óptimo (típicamente entre $50\%$ y $80\%$). Una paca muy seca detiene el proceso biológico; una paca excesivamente inundada ahoga a los microorganismos por falta de oxígeno.
* **Temperatura y Humedad Ambiental (`Temp_Amb_C` / `Hum_Amb_Pct`):**
  * *Por qué se escogió:* Funcionan como variables de calibración y contexto. Permiten aislar el impacto del clima exterior (como frentes de frío o lluvias) sobre las fluctuaciones térmicas superficiales del núcleo de la paca.
