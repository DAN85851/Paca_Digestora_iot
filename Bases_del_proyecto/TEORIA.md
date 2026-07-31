## 🌿 ¿Qué es una Paca Digestora?
Una paca digestora (o biorreactor orgánico artesanal) es un sistema diseñado para la gestión y descomposición acelerada de residuos orgánicos urbanos (restos de cocina, hojas, poda, etc.) mediante prensado y compactación aeróbico-anaeróbica estructurada. Su objetivo principal es transformar los residuos en abono (o digestato estabilizado) de forma limpia, sin malos olores y evitando la atracción de vectores.

<img width="387" height="516" alt="image" src="https://github.com/user-attachments/assets/3eafc857-8ba3-43d6-a5c8-36a345a1a730" />


[Conoce la implementaciòn de pacas digestoras por el grupo "Uchuchui"]([https://www.enlace-externo.com)](https://www.instagram.com/reel/DWkxsq8jWWW/?igsh=Y2NidnpndTg1eWFn)

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
  * *Por qué se escogió:* Funcionan como variables de calibración y contexto. Permiten aislarhttps://minas.medellin.unal.edu.co/noticias/5036-pacas-biodigestoras-una- el impacto del clima exterior (como frentes de frío o lluvias) sobre las fluctuaciones térmicas superficiales del núcleo de la paca.


---

## 🔌 Selección de Transductores y Hardware de Adquisición

Para llevar estas variables físicas al dominio digital con alta fiabilidad, se seleccionó una arquitectura de transductores específica, priorizando la robustez ante las condiciones corrosivas y de alta humedad de la paca digestora:

* **Sensor Ambiental (AM1011A):** *(Nota: Reemplazando la referencia previa por el sensor de temperatura y humedad ambiental estándar)*.
  * **Por qué se escogió:** Encargado de registrar la temperatura y humedad del aire circundante con gran precisión lineal. Su ubicación externa permite medir el clima de referencia sin someterse a los gases corrosivos del interior de la paca.
  *<img width="554" height="554" alt="image" src="https://github.com/user-attachments/assets/a04bf64e-ac80-4033-8ba3-292497b71bca" />


* **Sonda de Temperatura de Núcleo (Termistor NTC de 10 kΩ):**
  * **Por qué se escogió:** Se seleccionó un termistor NTC encapsulado en una sonda metálica estanca debido a su excelente sensibilidad y rango de respuesta térmica en el intervalo de $0^\circ\text{C}$ a $100^\circ\text{C}$. Al estar en contacto directo con el núcleo, resiste las exigencias mecánicas del prensado orgánico.
  * <img width="447" height="447" alt="image" src="https://github.com/user-attachments/assets/10a704fb-6ed6-42a1-8dae-07a3aa70825d" />


* **Sensor de Humedad de Suelo/Materia Orgánica (Sensor Capacitivo de Humedad - Modelo V1.2 / Estilo YL-69 capacitivo):** *(Nota: Corrección de la referencia comercial del sensor)*.
  * **Por qué se escogió:** A diferencia de los sensores resistivos tradicionales, los sensores capacitivos miden la permitividad dieléctrica del medio circundante sin exposición galvánica directa del metal al electrolito orgánico.
  * **Estrategia de Protección Eléctrica contra Electrólisis y Oxidación:** Dado que la materia orgánica húmeda y rica en sales genera un entorno altamente corrosivo propicio para la corrosión electroquímica y la oxidación acelerada, **los sensores enterrados en la paca se alimentaron mediante estrategias de conmutación de energía por ciclos (pulsos de excitación)**. En lugar de mantenerlos energizados de manera continua (lo que polariza los electrodos y oxida el cobre o destruye el circuito por electrólisis en pocos días), el firmware activa la alimentación del sensor únicamente durante los milisegundos necesarios para realizar la lectura analógica, apagándolos el resto del tiempo. Esto prolonga drásticamente su vida útil operativa en campo.
<img width="554" height="554" alt="image" src="https://github.com/user-attachments/assets/70c907b8-d6b0-4eb3-a86f-c5344eef17c3" />

Referencias extra: (https://minas.medellin.unal.edu.co/noticias/5036-pacas-biodigestoras-una-) \
                  [artìculo unal](./Bases_del_proyecto/Cartilla-pacas-digestoras-Silva.pdf)
