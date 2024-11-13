import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'src')))
from models.Nodo import Nodo


class Arbol:
    def __init__(self, root=None):
        self.root = root
    
    def addNodo(self, father, newNodo):
        nodo_father = self.searchNodo(father)
        if nodo_father:
            if isinstance(newNodo, Nodo):
                nodo_father.addSon(newNodo)
                return True
        return False
    
    def searchNodo(self, value):
        if not self.root:
            return None
        return self._searchRecursiveNodo(self.root, value)
    
    def _searchRecursiveNodo(self, nodo, value):
        if nodo.value == value:
            return nodo
        for son in nodo.sons:
            result = self._searchRecursiveNodo(son, value)
            if result:
                return result
        return None
    
    def showTree(self):
        """Visualiza el árbol en formato jerárquico."""
        if not self.root:
            return "El árbol está vacío"
        return self._showRecursiveTree(self.root, "")
    
    def _showRecursiveTree(self, nodo, prefijo):
        representation = f"{prefijo}{nodo.value} (Duración: {nodo.duration})\n"
        for son in nodo.sons:
            representation += self._showRecursiveTree(son, prefijo + "  ")
        return representation
    
    def calcularRutaCritica(self, pert=False):
        tiempo_total, ruta_critica = self._calcularRutaCriticaRecursive(self.root, 0, [], pert)
        return ruta_critica, tiempo_total

    
    def _calcularRutaCriticaRecursive(self, nodo, tiempo_acumulado, actividades, pert=False):
        tiempo_acumulado += nodo.duration
        actividades.append(nodo)
    
        if not nodo.sons:
             return tiempo_acumulado, actividades
    
        max_tiempo = 0
        mejor_ruta = []
        for son in nodo.sons:
             tiempo_hijo, ruta_hijo = self._calcularRutaCriticaRecursive(son, tiempo_acumulado, actividades.copy(), pert)
             if tiempo_hijo > max_tiempo:
                   max_tiempo = tiempo_hijo
                   mejor_ruta = ruta_hijo
    
        return max_tiempo, mejor_ruta