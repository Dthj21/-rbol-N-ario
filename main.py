import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from models.Nodo import Nodo
from models.Arbol import Arbol


def main():
    raiz = Nodo(1)
    arbol = Arbol(raiz)

    #Se agrega nodos en distintos niveles
    nodo2 = Nodo(2)
    nodo3 = Nodo(3)
    nodo4 = Nodo(4)
    nodo5 = Nodo(5)
    nodo6 = Nodo(6)
    nodo7 = Nodo(7)

    #Estructura del árbol
    arbol.addNodo(1, nodo2)  
    arbol.addNodo(1, nodo3)  
    arbol.addNodo(2, nodo4)  
    arbol.addNodo(2, nodo5)  
    arbol.addNodo(3, nodo6)  
    arbol.addNodo(5, nodo7) 

    # Se muestra la estructura del árbol
    print("Estructura del árbol con múltiples hijos y niveles:")
    print(arbol.showTree())

    # Se busca un nodo
    nodo_buscado = arbol.searchNodo(5)
    print("Nodo encontrado:", nodo_buscado)


if __name__ == "__main__":
    main()

