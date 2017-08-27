class WordWrapper:

    def __init__(self, word):
        self.keyword = word
        self.titleNum = 0
        self.contentNum = 0
        self.commentNum = 0
        self.articleCount = 0
        self.commentCount = 0

    def printSummary(self):
        print('Total', self.keyword, 'in title:', self.titleNum)
        print('Total', self.keyword, 'in content:', self.contentNum)
        print('Total', self.keyword, 'in comment:', self.commentNum)
        print('Total articles that contain', self.keyword, ':', self.articleCount)
        print('Total pushes that contain', self.keyword, ':', self.commentCount) 

class DateWrapper:
    def __init__(self):
        self.Jun=[]
        self.May=[]
        self.Apr=[]
    def addDate(self, str):
        month=str[:3]
        date=int(str[3:])
        if(month=='Jun'):
            self.Jun.append(date)
        elif(month=='May'):
            self.May.append(date)
        elif(month=='Apr'):
            self.Apr.append(date)
    def printSummary(self):
        for j in range(1,31):
            count=0
            for i in self.Apr:
                if(i==j): count += 1
            if(count!=0): print('Apr', j, ':', count)
        print('')
        for j in range(1,32):
            count=0
            for i in self.May:
                if(i==j): count += 1
            if(count!=0): print('May', j, ':', count)
        print('')
        for j in range(1,31):
            count=0
            for i in self.Jun:
                if(i==j): count += 1
            if(count!=0): print('Jun', j, ':', count)