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
