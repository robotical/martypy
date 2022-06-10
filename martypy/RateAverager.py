import time

class RateAverager:
    
    def __init__(self, windowSizeMinSecs = 1):
        self.sampleCount = 0
        self.windowSizeMinSecs = windowSizeMinSecs
        self.lastCalcSecs = time.time()
        self.prevVal = 0
        self.totalCount = 0

    def addSample(self):
        self.sampleCount += 1
        self.totalCount += 1

    def getAvg(self):
        if self.lastCalcSecs + self.windowSizeMinSecs < time.time():
            rsltVal = self.sampleCount / (time.time() - self.lastCalcSecs)
            self.lastCalcSecs = time.time()
            self.sampleCount = 0
            self.prevVal = rsltVal
            return round(rsltVal,2)
        return round(self.prevVal,2)

    def getTotal(self):
        return self.totalCount
