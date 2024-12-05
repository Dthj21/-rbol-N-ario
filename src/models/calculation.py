import csv
import sys
import os
from io import StringIO
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'src')))
from models.Nodo import Nodo
from models.Arbol import Arbol

def construirArbolDesdeCSV(contenido_csv):
    """Construir el árbol PERT desde el contenido de un archivo CSV.

    Args:
        contenido_csv (str): Contenido del archivo CSV subido como cadena.

    Returns:
        Arbol: Árbol construido a partir del archivo CSV.
    """
    arbol = Arbol()
    nodos = {}

    f = StringIO(contenido_csv)
    reader = csv.reader(f, delimiter=',')
    encabezados = [encabezado.strip() for encabezado in next(reader)]
    
    reader = csv.DictReader(f, fieldnames=encabezados)
    for row in reader:
        print("Fila leída:", row)
        
        actividad = row['Actividad'].strip()
        predecesores = row['Predecesores'].strip().split(',') if row['Predecesores'].strip() else []
        optimista = int(row['Optimista'].strip())
        mas_probable = int(row['Mas probable'].strip())
        pesimista = int(row['Pesimista'].strip())
        
        tiempo_esperado = (optimista + 4 * mas_probable + pesimista) / 6
        desviacion_estandar = (pesimista - optimista) / 6
        
        if actividad not in nodos:
            nodo = Nodo(actividad, tiempo_esperado, desviacion_estandar)
            nodos[actividad] = nodo
            if not arbol.root:
                arbol.root = nodo
        
        for predecesor in predecesores:
            if predecesor not in nodos:
                nodos[predecesor] = Nodo(predecesor, 0, 0)
            arbol.addNodo(predecesor, nodos[actividad])

    return arbol

def calcularPERTyCPM(contenido_csv):
    """Calcular PERT y CPM desde el contenido de un archivo CSV.

    Args:
        contenido_csv (str): Contenido del archivo CSV.

    Returns:
        tuple: (ruta_critica, duracion_total, desviacion_total)
    """
    arbol = construirArbolDesdeCSV(contenido_csv)
    
    ruta_critica, duracion_total = arbol.calcularRutaCritica(pert=True)
    desviacion_total = math.sqrt(sum(nodo.desviacion ** 2 for nodo in ruta_critica))
    
    return ruta_critica, duracion_total, desviacion_total