# Evolución y Versiones de la PCB: Sistema Embebido para Paca Digestora

## 🎯 Descripción General del Hardware
La tarjeta de circuito impreso (PCB) desarrollada para este proyecto **no es una placa de desarrollo genérica (como Arduino Uno o Nano comerciales), sino un sistema embebido diseñado a la medida** y optimizado de manera exclusiva para el monitoreo autónomo de pacas digestoras en campo. 

Los objetivos principales de su diseño físico y electrónico son dos:
1. **Factor de forma ultra compacto:** Reducir el tamaño de la placa al mínimo indispensable para facilitar su integración en gabinetes estancos y su manipulación en campo.
2. **Eficiencia energética extrema:** Minimizar el consumo de corriente en cada etapa del circuito para garantizar una larga autonomía operativa con baterías.

---

## 🛠️ Especificaciones de Diseño e Ingeniería

* **Entorno de Diseño:** Todo el schemático y el diseño del circuito impreso (PCB layout) fueron desarrollados utilizando **KiCad EDA**.
* **Microcontrolador Principal:** 
  * En las primeras etapas de prototipado y pruebas de banco se basó en el encapsulado **Atmega328P-PU** (DIP).
  * Para la versión final orientada a producción y reducción de espacio, se migró al encapsulado de montaje superficial **Atmega328P-AU** (TQFP), logrando una reducción drástica en el área de la tarjeta.
* **Comunicación Inalámbrica (Módulo LoRa Ebyte E32):**
  * Se integró la familia de módulos **Ebyte E32** operando a una lógica de **3.3V**, reconocidos por su excelente rendimiento en largo alcance y sus modos de bajo consumo energético (*Sleep / Power Saving*).
* **Sistema de Alimentación y Autonomía:**
  * **Alimentación de campo:** Diseñada para operar mediante un arreglo de baterías de **4.7V** (celdas orientadas a futura escalabilidad con carga autónoma mediante paneles solares).
  * **Regulación:** Se implementó una etapa de conversión de energía eficiente para adecuar los voltajes a la lógica de los sensores y el microcontrolador sin desperdiciar energía en calor.

---

