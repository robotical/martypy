import time

class RateAverager:
    
    def __init__(self, windowSizeMinSecs = 1):
        self.instCount = 0
        self.windowSizeMinSecs = windowSizeMinSecs
        self.lastCalcSecs = time.time()
        self.prevVal = 0
        self.totalCount = 0

    def inst(self):
        self.instCount += 1
        self.totalCount += 1

    def getAvg(self):
        if self.lastCalcSecs + self.windowSizeMinSecs < time.time():
            rsltVal = self.instCount / (time.time() - self.lastCalcSecs)
            self.lastCalcSecs = time.time()
            self.instCount = 0
            self.prevVal = rsltVal
            return rsltVal
        return self.prevVal

    def getTotal(self):
        return self.totalCount
