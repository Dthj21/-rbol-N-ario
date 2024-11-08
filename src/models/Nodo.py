class Nodo:
    def __init__(self, value):
        self.value = value
        self.sons= []

    def addSon(self, nodo):
        self.sons.append(nodo)

    def deleteSon(self, value):
        for i, son in enumerate(self.sons):
            if son.value == value:
                del self.sons[i]
                return True
        return False
    
    def obtainSon(self):
        return self.sons
    
    def __str__(self):
        return f"Valor: {self.value}, Hijos: {len(self.sons)}"
