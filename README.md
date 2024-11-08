# Proyecto de Árbol N-ario

Este proyecto tiene como objetivo crear una aplicación de escritorio para la gestión y visualización de estructuras de datos tipo árbol n-ario, permitiendo el manejo de estimaciones de tiempo asociadas a cada nodo del árbol. La aplicación se centra en facilitar el análisis de tiempos estimados mediante la integración de gráficos PERT (Program Evaluation and Review Technique) y CPM (Critical Path Method), además de una interfaz que permita la carga de archivos y la consulta de registros.

## Características

1. **Gestión de Árboles N-arios**:
   - Creación, visualización y gestión de estructuras n-arias.
   - Opción para añadir múltiples árboles n-arios, cada uno con sus propias estimaciones y nodos.

2. **Cálculo de Estimaciones de Tiempo**:
   - Cada nodo del árbol podrá contener una estimación de tiempo calculada mediante métodos de tiempos optimistas, más probables y pesimistas.
   - Ajuste de estimaciones para adaptarse a un período de uno o dos días por tarea, buscando mayor realismo en los cálculos.

3. **Carga de Archivos de Excel**:
   - Posibilidad de cargar archivos de Excel para importar datos de manera rápida y estructurada.
   - Automatización de cálculos basados en los datos del archivo.

4. **Visualización de Gráficos PERT y CPM**:
   - La aplicación mostrará los diagramas de PERT y CPM para representar visualmente el flujo y la secuencia de tareas.
   - Acceso a gráficos en ventanas modales que permitirán observar detalles específicos de cada árbol y sus tiempos estimados.

5. **Registro y Consulta de Árboles**:
   - Una tabla en la ventana principal registrará todos los árboles y estimaciones creadas, permitiendo un fácil acceso y consulta.
   - Posibilidad de acceder a cada registro para obtener información detallada y análisis visual.

## Estructura del Proyecto

- **Ventana Principal**: Contiene un botón para agregar un nuevo árbol n-ario y una tabla para listar todos los árboles y estimaciones existentes.
- **Modal de Detalles**: Al seleccionar un árbol en la tabla, se abrirá una ventana modal donde se podrán visualizar los gráficos PERT y CPM, y revisar las estimaciones detalladas.
- **Cálculos de Tiempos**: Implementación de funciones para calcular tiempos de estimación y ajustar el plazo a tareas de uno o dos días, buscando mayor precisión en los tiempos del proyecto.
- **Módulo de Carga de Excel**: Para la importación de datos y generación de árboles n-arios en base a los datos cargados desde un archivo.
