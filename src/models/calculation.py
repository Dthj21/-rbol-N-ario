import csv
import sys
import os
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'src')))
from models.Nodo import Nodo
from models.Arbol import Arbol

def construirArbolDesdeCSV(archivo_csv):
    arbol = Arbol()
    nodos = {}

    with open(archivo_csv, 'r') as f:
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
            
            # Calcular tiempo esperado y desviación estándar para PERT
            tiempo_esperado = (optimista + 4 * mas_probable + pesimista) / 6
            desviacion_estandar = (pesimista - optimista) / 6
            
            # Crear el nodo si no existe y asignar tiempo esperado como duración
            if actividad not in nodos:
                nodo = Nodo(actividad, tiempo_esperado, desviacion_estandar)
                nodos[actividad] = nodo
                if not arbol.root:
                    arbol.root = nodo
            
            # Agregar los predecesores
            for predecesor in predecesores:
                if predecesor not in nodos:
                    nodos[predecesor] = Nodo(predecesor, 0, 0)
                arbol.addNodo(predecesor, nodos[actividad])

    return arbol

# Función para calcular PERT y CPM
def calcularPERTyCPM(archivo_csv):
    arbol = construirArbolDesdeCSV(archivo_csv)
    
    ruta_critica, duracion_total = arbol.calcularRutaCritica(pert=True)
    
    desviacion_total = math.sqrt(sum(nodo.desviacion ** 2 for nodo in ruta_critica))
    
    return ruta_critica, duracion_total, desviacion_total

archivo_csv = '/home/diego/Descargas/actividades.csv'
ruta_critica, duracion_total, desviacion_total = calcularPERTyCPM(archivo_csv)

print("Ruta crítica:", " → ".join(nodo.value for nodo in ruta_critica))
print(f"Duración total esperada (CPM): {duracion_total:.2f} días")
print(f"Desviación estándar total (PERT): {desviacion_total:.2f} días")