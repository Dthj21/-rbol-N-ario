class Nodo:
    def __init__(self, value, duration, desviacion=0, optimista=None, mas_probable=None, pesimista=None):
        self.value = value
        self.sons = []
        self.duration = duration
        self.desviacion = desviacion
        self.predecesores = []
        
        if optimista is not None and mas_probable is not None and pesimista is not None:
            self.pert_duration = self.calcularDuracionPERT(optimista, mas_probable, pesimista)
        else:
            self.pert_duration = self.duration

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
        return f"Valor: {self.value}, Duración: {self.duration}, Duración PERT: {self.pert_duration}, Hijos: {len(self.sons)}"
    
    def calcularDuracionPERT(self, optimista, mas_probable, pesimista):
        """Calcula la duración utilizando la fórmula PERT."""
        return (optimista + 4 * mas_probable + pesimista) / 6
