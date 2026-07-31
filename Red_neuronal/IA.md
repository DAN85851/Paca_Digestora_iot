
# Cómo entrené la red neuronal de mi Paca Digestora (explicado desde cero)

Este documento explica, paso a paso y **sin dar por sentado que sabes nada de IA**,
todo lo que hace el notebook `entrenamiento_paca_digestora_3_.ipynb`: qué problema
resuelve, qué librerías usa, qué significa cada término técnico, y por qué elegí
cada camino (y no otro) en cada decisión del proyecto.

---

## 1. ¿Cuál es el problema que quiero resolver?

Tengo una **paca digestora** (un sistema de compostaje/biodigestión) con sensores
que miden temperatura y humedad, tanto dentro de la paca como en el ambiente.
Un proceso de compostaje pasa por **fases biológicas** según la actividad de los
microorganismos:

- **Termofílico**: fase caliente, de alta actividad microbiana (temperatura alta).
- **Mesofílico**: fase templada, actividad moderada.
- **Enfriamiento**: fase de maduración, la temperatura baja de forma sostenida.

Quiero que un programa, con solo leer los datos de los sensores, **adivine en qué
fase está la paca en este momento**. Eso es exactamente lo que hace una red
neuronal de clasificación: recibe números (temperatura, humedad, etc.) y devuelve
una categoría (una de las 3 fases).

El modelo final no se queda solo en la computadora: se traslada a una
**BeagleBone Black (BBB)**, una minicomputadora de bajos recursos que va a estar
físicamente junto a la paca haciendo las predicciones en tiempo real.

---

## 2. Librerías usadas y para qué sirve cada una

| Librería | Para qué la usé |
|---|---|
| **numpy** | Maneja números y matrices de forma eficiente. Es la base matemática de casi todo lo demás. |
| **pandas** | Maneja los datos en forma de tabla (como un Excel programable): leer el CSV, limpiar filas, calcular columnas nuevas. |
| **matplotlib** | Dibuja las gráficas (temperatura en el tiempo, matriz de confusión, curvas de entrenamiento). |
| **tensorflow / keras** | Es el "motor" que construye y entrena la red neuronal. Keras es la parte de TensorFlow con la que se arma la red de forma sencilla, capa por capa. |
| **scikit-learn (sklearn)** | Trae herramientas para *evaluar* qué tan bien funciona el modelo (matriz de confusión, F1-score, etc.) y para calcular los "pesos de clase" que se explican más abajo. |

**Dato importante:** TensorFlow **solo se usa en la computadora/Colab, para
entrenar**. En la BeagleBone Black nunca se instala TensorFlow (el hardware es
muy limitado: un solo núcleo, sin GPU). Ahí solo corre `numpy`, haciendo a mano
las mismas cuentas que ya se explican en la sección 8.

---

## 3. Diccionario de términos 

- **Red neuronal**: un conjunto de "neuronas" organizadas en capas, que
  transforman números de entrada en una predicción de salida. En este proyecto,
  la entrada son 5 lecturas de sensores y la salida es "a cuál de las 3 fases se
  parece más esto".
- **Neurona**: básicamente hace una cuenta simple: multiplica cada entrada por un
  número (su "peso"), suma todo, le suma un número extra (el "sesgo" o *bias*), y
  el resultado pasa por una función de activación.
- **Capa (layer)**: un grupo de neuronas que reciben la misma entrada. Este modelo
  tiene:
  - Una **capa de entrada** (los 5 valores de los sensores, sin neuronas de por
    medio, solo son los datos).
  - Una **capa oculta** (`Dense`, con activación `relu`): aquí es donde la red
    realmente "aprende" a combinar los sensores de forma no obvia.
  - Una **capa de salida** (`Dense` con activación `softmax`): entrega 3 números
    que suman 1.0, es decir, la probabilidad de cada fase.
- **Pesos (weights) y sesgos (bias)**: son los números internos que la red ajusta
  durante el entrenamiento. Al principio son aleatorios; al final del
  entrenamiento son los que hacen que la red acierte. Cuando hablo de "exportar
  los pesos", me refiero a guardar estos números para poder reconstruir la red en
  otra máquina sin usar TensorFlow.
- **Función de activación**:
  - `ReLU` (*Rectified Linear Unit*): si el número es negativo lo vuelve 0, si es
    positivo lo deja igual. Le da a la red la capacidad de aprender relaciones no
    lineales (no solo líneas rectas).
  - `Softmax`: convierte 3 números cualquiera en 3 probabilidades que suman 1
    (por ejemplo: 70% Mesofílico, 20% Termofílico, 10% Enfriamiento).
- **Entrenamiento (`fit`)**: proceso en el que la red ve ejemplos ya etiquetados
  (sensores → fase real) muchas veces, y va ajustando sus pesos para equivocarse
  cada vez menos.
- **Época (epoch)**: una pasada completa por todos los datos de entrenamiento.
  Aquí se entrenó con 60 épocas.
- **Batch / batch size**: en vez de ajustar los pesos leyendo un dato a la vez, se
  agrupan de a 32 (`batch_size=32`) y se ajusta después de ver cada grupo. Es un
  balance entre velocidad y estabilidad del entrenamiento.
- **Optimizador (`adam`)**: es el algoritmo que decide *cómo* ajustar los pesos en
  cada paso para reducir el error. `Adam` es una opción estándar y confiable, buena
  por defecto para este tipo de problemas pequeños.
- **Función de pérdida (`loss`, `sparse_categorical_crossentropy`)**: es la
  fórmula que mide qué tan "equivocada" está la red. El entrenamiento
  literalmente intenta hacer que este número baje lo más posible.
- **Normalización (`mu`, `sigma`)**: los sensores no están en la misma escala
  (temperatura vs. humedad, por ejemplo). Normalizar significa restarle el
  promedio (`mu`) y dividir por la desviación estándar (`sigma`) a cada columna,
  para que todas queden en rangos comparables. Esto ayuda mucho a que la red
  entrene mejor y más rápido.
- **Overfitting (sobreajuste)**: cuando el modelo "memoriza" los datos de
  entrenamiento en vez de aprender el patrón general, y por eso falla con datos
  nuevos. Es uno de los riesgos que se vigiló al comparar arquitecturas.
- **Accuracy (exactitud)**: porcentaje de aciertos totales. Suena bien, pero puede
  ser engañoso (ver sección 6).
- **F1-score / F1-macro**: una métrica que combina qué tan bien detecta cada
  clase (no solo cuántas acierta en total), y con "macro" se le da el mismo peso
  a las 3 fases aunque tengan distinta cantidad de datos.
- **Matriz de confusión**: una tabla que muestra, para cada fase real, en qué fase
  la clasificó el modelo. Sirve para ver *en qué se equivoca*, no solo cuánto.

---

## 4. Paso 1: Cargar y limpiar los datos

El notebook lee el CSV con las lecturas de los sensores, pero antes de dejar que
`pandas` lo interprete, hace una limpieza especial:

<img width="1289" height="690" alt="datos" src="https://github.com/user-attachments/assets/04545fc5-7576-44fb-8535-a917a7a4c3f7" />


- Los datos vienen de la BeagleBone Black, y hubo **cortes de energía
  (brownouts)** durante el registro. Eso corrompió algunas filas con bytes nulos
  mezclados en el texto. Por eso primero se lee el archivo en binario y se quitan
  esos bytes nulos antes de convertirlo a texto.
- Luego se fuerza a que las columnas que deberían ser números (`Temp_Sonda_C`,
  `Hum_Tierra_Pct`, etc.) realmente lo sean; lo que no se pueda convertir se marca
  como dato faltante.
- Las filas que quedaron con datos faltantes en columnas clave se descartan, y el
  notebook imprime cuántas filas se perdieron por esta corrupción, para que quede
  documentado y sea justificable ante el profesor.

**Por qué este camino:** la alternativa era ignorar el problema y dejar que
`pandas` fallara o metiera texto corrupto disfrazado de número. Limpiar a mano en
binario es más robusto porque ataca la causa real (bytes nulos por los cortes de
luz) en vez de solo "tapar" el síntoma.

<img width="1289" height="490" alt="datos procesados" src="https://github.com/user-attachments/assets/5ebbdb45-301c-4f12-adc1-78ebad4e2007" />
  
---

## 5. Paso 2: Etiquetar el estado biológico (porque el CSV no lo trae)

El CSV solo trae lecturas de sensores, **no trae la fase biológica**. Así que se
construyó con reglas basadas en la biología del compostaje:

- Si la temperatura de la sonda supera **45 °C** → `Termofílico`.
- Si la temperatura está bajando de forma sostenida (calculado con una
  **pendiente móvil**, el promedio de cuánto cambia la temperatura en las
  últimas 6 lecturas) y no llegó a los 45 °C → `Enfriamiento`.
- En cualquier otro caso → `Mesofílico`.

**Por qué se usa la pendiente y no solo la temperatura:** la diferencia entre
"Mesofílico" (temperatura moderada estable) y "Enfriamiento" (temperatura
moderada, pero *bajando*) no está en el valor de temperatura sino en la
*tendencia*. Por eso se calcula cuánto ha cambiado la temperatura en las últimas
lecturas (la pendiente), no solo su valor actual.

Después de etiquetar, se grafica la temperatura coloreada por fase para
**revisar visualmente** que el etiquetado tenga sentido biológico. Estos
umbrales (45 °C y la pendiente de enfriamiento) no son universales: hay que
ajustarlos según lo que se observe en los datos reales de cada paca, y eso es
justamente lo que se documenta como decisión de diseño para poder explicarla.

---

## 6. Paso 3: Preparar los datos para entrenar (split y normalización)

### 6.1 ¿Por qué no se dividió el tiempo en "pasado = entrenamiento, futuro = prueba"?

Lo más correcto en series de tiempo es entrenar con el pasado y probar con el
futuro (para que el modelo nunca "vea" datos que vienen después). Pero con solo
3-4 días de datos de una sola paca, la fase Termofílica ocurrió **completa al
final** de la ventana capturada. Si se hiciera un corte simple 80% pasado / 20%
futuro, la red **nunca vería un solo ejemplo de fase Termofílica** durante el
entrenamiento, y sería imposible que aprendiera a reconocerla.

### 6.2 La solución adoptada: bloques de tiempo entrelazados

En vez de un solo corte, el tiempo se dividió en bloques pequeños y contiguos (de
5 lecturas cada uno), y **1 de cada 5 bloques** se separa para el conjunto de
prueba (test), alternando a lo largo de todo el periodo. Así:

- Se reduce (aunque no se elimina del todo) la fuga de información entre
  entrenamiento y prueba, porque los bloques siguen siendo tramos contiguos de
  varios minutos, no puntos sueltos mezclados al azar.
- Se garantiza que las 3 fases biológicas aparezcan tanto en entrenamiento como
  en prueba.

Esta es una decisión con un **trade-off reconocido**: no es tan limpia como un
split cronológico puro, pero es la única forma práctica de que el modelo pueda
aprender las 3 clases con tan pocos días de datos. Es un buen punto para mencionar
como limitación honesta en la presentación del proyecto: con más días de datos
(varios ciclos completos de la paca), se podría volver al split cronológico puro.

### 6.3 Normalización

La media (`mu`) y la desviación estándar (`sigma`) para normalizar los datos se
calculan **solo con el conjunto de entrenamiento**, y luego se aplican también al
conjunto de prueba. Si se calcularan con todos los datos juntos, información del
conjunto de prueba "se filtraría" indirectamente al entrenamiento, lo cual
haría que la evaluación final fuera menos confiable.

---

## 7. Paso 4: Probar varias arquitecturas (barrido)

En vez de adivinar de una vez cuántas neuronas usar en la capa oculta, el
notebook entrena **5 versiones distintas** del modelo, cambiando solo ese número:
**4, 8, 16, 32 y 64 neuronas ocultas**. Todas comparten la misma estructura:

```
Entrada (5 sensores) → Capa oculta (ReLU, N neuronas) → Capa de salida (Softmax, 3 fases)
```

### 7.1 El problema del desbalance de clases

Con solo 3-4 días de datos, es normal que la paca haya pasado la mayor parte del
tiempo en una sola fase (por ejemplo, Mesofílico). Si eso pasa, un modelo
"tramposo" podría predecir siempre "Mesofílico" y aun así tener un accuracy
altísimo (95%+), sin haber aprendido nada útil sobre las otras fases.

Para evitar caer en esa ilusión, se usaron dos herramientas:

- **Class weights (pesos de clase)**: durante el entrenamiento, los errores en
  las clases minoritarias (Termofílico, Enfriamiento) "pesan más" en la cuenta
  del error total. Esto obliga a la red a prestarles más atención en vez de
  ignorarlas.
- **F1-macro** como métrica de comparación entre arquitecturas, en vez de
  accuracy simple. F1-macro le da el mismo peso a cada una de las 3 fases, así
  tengan pocos o muchos datos, así que no se deja engañar por una clase
  mayoritaria.

### 7.2 Cómo se eligió la arquitectura final

De las 5 arquitecturas probadas, se elige automáticamente la que tenga el
**mejor F1-macro** (no el mejor accuracy). En caso de que dos arquitecturas
queden muy parejas, el criterio de desempate recomendado es preferir la que
tenga **menos neuronas**: menos parámetros significa menos riesgo de
sobreajuste, y un modelo más liviano y rápido para correr después en la
BeagleBone Black, que tiene recursos muy limitados.

---

## 8. Paso 5: Evaluar el modelo elegido

Con la arquitectura ganadora se generan:

- Un **reporte de clasificación** (`classification_report`): muestra, por cada
  fase, qué tan preciso y qué tan completo fue el modelo.
- Una **matriz de confusión**: para ver exactamente en qué fases se confunde el
  modelo entre sí (por ejemplo, si confunde Mesofílico con Enfriamiento).
- Curvas de **loss** (pérdida) y **accuracy** por época, tanto en entrenamiento
  como en validación, para revisar visualmente que el modelo no esté
  sobreajustando (si el error de entrenamiento sigue bajando pero el de
  validación empieza a subir, es señal de sobreajuste).

---


<img width="587" height="455" alt="aciertos" src="https://github.com/user-attachments/assets/572c6eac-f0ea-4e1c-bbc0-926438b4ee31" />


## 9. Paso 6: Exportar los pesos para correr en la BeagleBone Black, sin TensorFlow

Aquí está la parte de "qué son los pesos que elegí" en concreto. Una red de este
tamaño (5 entradas → N neuronas ocultas → 3 salidas) tiene exactamente 4 grupos
de números entrenados:

| Nombre | Qué es |
|---|---|
| **W1** | Los pesos que conectan las 5 entradas (sensores) con la capa oculta. |
| **b1** | El sesgo (bias) de cada neurona de la capa oculta. |
| **W2** | Los pesos que conectan la capa oculta con las 3 salidas (fases). |
| **b2** | El sesgo de cada una de las 3 neuronas de salida. |
| **mu, sigma** | El promedio y la desviación estándar usados para normalizar, para poder normalizar los datos nuevos exactamente igual en la BBB. |

Todo esto se guarda en un archivo `modelo_paca_pesos.npz` (formato comprimido de
numpy). **Por qué este camino:** la BeagleBone Black tiene un solo núcleo, sin
GPU y con alimentación limitada — instalar TensorFlow ahí sería excesivo e
inestable. Como la red es pequeña, hacer la predicción a mano equivale
literalmente a **dos multiplicaciones de matrices**, algo que numpy resuelve en
milisegundos sin necesitar ningún framework pesado:

```python
h = relu(x_normalizado @ W1 + b1)      # capa oculta
salida = softmax(h @ W2 + b2)          # capa de salida (probabilidades)
```

Para confirmar que esta reimplementación en numpy puro es idéntica a la de
TensorFlow, el notebook compara la predicción de ambas con el mismo dato de
prueba y verifica que coincidan exactamente antes de dar por bueno el modelo
para subirlo a la BBB.

---
<img width="1189" height="390" alt="finales" src="https://github.com/user-attachments/assets/030ec092-5347-435f-bcdf-d0e257ed5d6c" />


## 10. Resumen del flujo completo

1. **Cargar y limpiar** el CSV (bytes corruptos por cortes de luz → se filtran).
2. **Etiquetar** las 3 fases con reglas de temperatura + tendencia (pendiente).
3. **Dividir** los datos en train/test por bloques de tiempo entrelazados (para
   no perder ninguna fase del entrenamiento) y **normalizar** solo con datos de
   entrenamiento.
4. **Entrenar 5 arquitecturas** distintas con class weights, y elegir la mejor
   según F1-macro (no accuracy).
5. **Evaluar** con matriz de confusión y curvas de entrenamiento.
6. **Exportar los pesos** (W1, b1, W2, b2, mu, sigma) para correr la predicción
   con numpy puro en la BeagleBone Black, verificando que dé el mismo resultado
   que TensorFlow.

Cada decisión (limpieza binaria, pendiente móvil, split por bloques, class
weights, F1-macro, exportar a numpy) responde a una limitación real de los datos
o del hardware, no a una preferencia arbitraria — y esa es la justificación que
se puede dar si el profesor pregunta "¿por qué hiciste esto así?".
