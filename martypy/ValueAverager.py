class ValueAverager:
    
    def __init__(self, windowSize = 10):
        self.valList = []
        self.windowSize = windowSize

    def add(self, newVal):
        self.valList = self.valList[-self.windowSize:]
        self.valList.append(newVal)

    def getAvg(self):
        if len(self.valList) > 0:
            return round(sum(self.valList)/len(self.valList),2)
        return 0

