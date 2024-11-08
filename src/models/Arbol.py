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
    
    def _showRecursiveTree(self,nodo, prefijo):
        representation = f"{prefijo}{nodo.value}\n"
        for son in nodo.sons:
            representation += self._showRecursiveTree(son, prefijo + "  ")
        return representation
