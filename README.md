# proyecto-mineria-asociacion

# Pipeline de Minería de Reglas de Asociación

Proyecto de análisis de Cadena Detallista y Tecnologías de Software orientado a la generación de recomendaciones comerciales.

Se desarrolló un pipeline en Python que transforma datos crudos en reglas de asociación interpretables utilizando los algoritmos Apriori y ECLAT.

---

## ¿Qué hace el proyecto?

- Carga y limpieza automática de datos (duplicados, nulos, estandarización)
- Transformación a formato transaccional
- Análisis Exploratorio de Datos (EDA)
- Generación de reglas de asociación
- Evaluación mediante soporte, confianza y lift
- Interpretación de reglas para propuestas de negocio

---
## Estructura del Proyecto
* **dashboard**: Contiene lo necesario para que el dasboard funcione correctamente.
* **data**: Contiene los datos crudos, procesados e imágenes de los gráficos del EDA.
* **notebooks**: Se alojan los notebooks del pipeline principal Eda por separado de cada conjunto de datos y las reglas de asociación respectivas.
* **src**: Se encuentran las clases para el entrenamiento de los modelos, del pipeline y utils para reutilizar en el proyecto. 
## Tecnologías utilizadas

- Python  
- Pandas y NumPy  
- Implementación de Apriori y ECLAT  
- Matplotlib / Visualización de métricas  
- Arquitectura modular tipo pipeline
- mlxtend 
- NetworkX
---
 Desarrolladores:
---
* Nubia Brenes Valerín
* Gilary Granados Calvo
