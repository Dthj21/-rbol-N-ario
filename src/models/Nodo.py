class Nodo:
    def __init__(self, value, duration=0):
        self.value = value
        self.sons = []
        self.duration = duration  # Duración de la actividad
        self.predecesores = []  # Guardamos los predecesores (para facilitar el cálculo de la ruta crítica)

    def addSon(self, nodo):
        self.sons.append(nodo)

    def addPredecesor(self, nodo):
        self.predecesores.append(nodo)
    
    def deleteSon(self, value):
        for i, son in enumerate(self.sons):
            if son.value == value:
                del self.sons[i]
                return True
        return False
    
    def obtainSon(self):
        return self.sons
    
    def __str__(self):
        return f"Valor: {self.value}, Duración: {self.duration}, Hijos: {len(self.sons)}"
