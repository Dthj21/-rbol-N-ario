#Código de algoritmos de cálculo (PERT Y CPM)
import csv
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'src')))
from models.Nodo import Nodo
from models.Arbol import Arbol


def construirArbolDesdeCSV(archivo_csv):
    arbol = Arbol()
    nodos = {}  # Diccionario para almacenar nodos por nombre
    
    # Leer el CSV
    with open(archivo_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            actividad = row['actividad']
            duracion = int(row['duracion'])
            predecesores = row['predecesores'].split(',') if row['predecesores'] else []
            
            # Crear el nodo si no existe
            if actividad not in nodos:
                nodo = Nodo(actividad, duracion)
                nodos[actividad] = nodo
                if not arbol.root:
                    arbol.root = nodo  # Asignar el primer nodo como raíz
            
            # Agregar los predecesores
            for predecesor in predecesores:
                if predecesor not in nodos:
                    nodos[predecesor] = Nodo(predecesor)  # Crear predecesor si no existe
                arbol.addNodo(predecesor, nodos[actividad])  # Relacionar predecesor con la actividad
                nodos[actividad].addPredecesor(nodos[predecesor])  # Relacionar predecesor con la actividad

    return arbol

def calcularRutaCriticaDesdeCSV(archivo_csv):
    arbol = construirArbolDesdeCSV(archivo_csv)
    ruta_critica, actividades = arbol.calcularRutaCritica()
    print(f"Duración de la ruta crítica: {ruta_critica} días")
    print(f"Actividades en la ruta crítica: {' -> '.join(actividades)}")


# Llamada para calcular la ruta crítica
calcularRutaCriticaDesdeCSV('/home/diego/Descargas/actividades.csv')