import requests
from bs4 import BeautifulSoup
import time
import sys, os
from wrapper import WordWrapper, DateWrapper
from subprocess import Popen
import numpy as np
import matplotlib.pyplot as plt
import csv

# --------------------------------------------------------------------------------------------------
# get functions
# --------------------------------------------------------------------------------------------------

def getPageText(link):
    #a = time.time()
    if(link == 'empty'):
        pageText='This page has been deleted.'
    else:
        pageText=requests.get(link, cookies={'over18':'1'}).text
    #b = time.time()
    #print('get page text time:', b-a)
    return pageText

def text2soup(text):
    return BeautifulSoup(text, 'lxml')

def getTitle(soup):
    s=soup.find_all('span', 'article-meta-value')
    return s[2].getText()

def getTitleFromText(text):
    soup=text2soup(text)
    return getTitle(soup)

def getContent(soup):
    s=soup.find_all('span', 'f6')
    for i in s:
        i.decompose()

    content = soup.find(id="main-content")
    s1 = content.find_all('div', 'article-metaline')
    for i in s1:
        i.decompose()
    s2 = content.find_all('div', 'article-metaline-right')
    for i in s2:
        i.decompose()

    target_back = '※ 發信站: 批踢踢實業坊(ptt.cc)'
    content = content.text.split(target_back)
    main_content = content[0]
    return main_content

def getID(soup):
    s=soup.find_all('span', 'article-meta-value')
    id = s[0].getText()
    return id[:id.find('(')-1]

def getIDFromText(text):
    soup=text2soup(text)
    return getID(soup)

def getIP(soup):
    s=soup.find_all('span', 'f2')
    target= '※ 發信站: 批踢踢實業坊(ptt.cc), 來自: '
    for i in s:
        text = i.getText()
        if (text.find(target)>=0):
            return text[27:-1]

def getIPFromText(text):
    soup=text2soup(text)
    return getIP(soup)
    
def getTime(soup):
    s=soup.find_all('span', 'article-meta-value')
    return s[3].text

def getTimeFromText(text):
    soup = text2soup(text)
    return getTime(soup)

def getDate(soup):
    timeStr = getTime(soup)
    dateStr = timeStr[4:10]
    return dateStr

def getDateFromText(text):
    soup = text2soup(text)
    return getDate(soup)

def countPushes(text):
    soup = text2soup(text)
    pushes = soup.find_all('span', 'hl push-tag')
    n_push = len(pushes)
    boos = soup.find_all('span', 'f1 hl push-tag')
    n_boo = 0
    n_arrow = 0
    for p in boos:
        if(p.text == '噓 '): n_boo += 1
        else: n_arrow += 1
    n_list=[]
    n_list.append(n_push)
    n_list.append(n_boo)
    n_list.append(n_arrow)
    # print('推:', n_push, '\t噓:', n_boo,'\t箭頭:', n_arrow)
    return n_list

def invalidDate(dateStr):
    if(len(dateStr)!=4): return True
    try:
        month = int(dateStr[0:2])
        day = int(dateStr[2:4])
    except Exception as e:
        return True

    if(day<1): return True
    if(month<1 or month>12): return True

    if month in (1,3,5,7,8,10,12):
        if(day>31): return True
    elif(month==2):
        if(day>29): return True
    else:
        if(day>30): return True

    return False

def index2date(pageText):
    soup = text2soup(pageText)
    dateStr = soup.find('div', 'date').text
    return dateStr

def getIndexDate(forumName, dateStr):
    # '0727' to ' 7/27' 
    # '1225' to '12/25'
    if(invalidDate(dateStr)): 
        print('invalid date', dateStr)
        sys.exit()
    if(dateStr[0] == '0'):
        date = ' ' + dateStr[1] + '/' + dateStr[2:4]
    else:
        date = dateStr[0:2] + '/' + dateStr[2:4]
    print('finding', date)

    url1 = 'https://www.ptt.cc/bbs/'+forumName+'/index'
    url2 = '.html'  
    pageText = getPageText(url1+url2)
    pageNum = getPrevPage(text2soup(pageText))
    pageJumpDefault = 64
    # problems need to be fixed if forum is not Gossiping
    # pageJump too big, cnnot find correct startpage
    dateptr = ''
    findEqual = True
    indexRange = []

    for i in range(2):
        found = False
        stage = 0
        pageJump = pageJumpDefault
        while(not found):        
            pageText = getPageText(url1+str(pageNum)+url2) # text of prev page
            dateptr = index2date(pageText) # get date from index page
            print(pageNum, dateptr)
            if (not (findEqual ^ (dateptr == date))): # XNOR
                if (pageJump != 1):
                    pageJump = pageJump >> 1 # divide by 2
                    pageNum += pageJump
                else:
                    found = True
                    findEqual = False
            else:
                pageNum -= pageJump
        # loop breaks
        indexRange.append(pageNum)

    print('')
    return indexRange

# search from file
def searchText(text, wwList):
    #a = time.time()
    wwList_new = []
    for ww in wwList:
        kw = ww.keyword
        soup = BeautifulSoup(text, 'lxml')
        #title
        title = getTitle(soup)
        n_t = searchKeyword(title, kw)
        ww.titleNum += n_t
        #content
        content = getContent(soup)
        n_ct = searchKeyword(content, kw)
        ww.contentNum += n_ct
        #pushes
        pushes = soup.find_all('div', 'push')
        n_cm_total = 0
        for push in pushes:
            #ptt_id = push.find('span', 'f3 hl push-userid').getText()
            comment = push.find('span', 'f3 push-content').getText()
            n_cm = searchKeyword(comment, kw)
            if(n_cm != 0):
                #print(comment)
                ww.commentCount += 1
            n_cm_total += n_cm
        ww.commentNum += n_cm_total

        if(n_t + n_ct + n_cm_total != 0):
            ww.articleCount += 1

        wwList_new.append(ww)

    return wwList_new

# search from file
def searchText_Date(text,keyword, dw):
    #a = time.time()
    soup = BeautifulSoup(text, 'lxml')
    #title
    dateStr = getDate(soup)
    title = getTitle(soup)
    n_t = searchKeyword(title,keyword)
    #content
    content = getContent(soup)
    n_ct = searchKeyword(content,keyword)
    #pushes
    pushes = soup.find_all('div', 'push')
    n_cm_total = 0
    for push in pushes:
        #ptt_id = push.find('span', 'f3 hl push-userid').getText()
        comment = push.find('span', 'f3 push-content').getText()
        n_cm = searchKeyword(comment,keyword)
        n_cm_total += n_cm

    if(n_t + n_ct + n_cm_total != 0):
        print(dateStr)
        dw.addDate(dateStr)

    return dw

# get the number of previous page
def getPrevPage(soup):
    s = str(soup.find_all('a', 'btn wide')[1])
    x=s.find('index')
    y=s.find('.html')
    return int(s[x+5:y])

# how many times keyword appears in text
def searchKeyword(text,wordList):
    cnt=0
    for word in wordList:
        cnt += text.count(word)
    return cnt

def checkDirectory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def checkFileExists(filename):
    return os.path.isfile(filename)
# --------------------------------------------------------------------------------------------------
# plot
# --------------------------------------------------------------------------------------------------

def plotHisto(names, numbers, title, date, show = False):
    assert len(numbers) == len(names)
    N = len(numbers)
    ind = np.arange(N)    # the x locations for the groups
    width = 0.5      # the width of the bars: can also be len(x) sequence

    plt.figure(figsize=(1.2*N,4))
    p1 = plt.bar(ind, numbers, width)
    plt.title(title)
    plt.xticks(ind, names)

    for i, num in enumerate(numbers):
        plt.text(i, num, str(num))

    if(show): plt.show()
    else:  
        directory = '../results/' + date + '/'
        # checkDirectory(directory)
        plt.savefig(filename=directory+title+'_'+'_'.join(names)+'.png', format='png')

def plotMultiHisto(names, numbersList, titleList, plotTitle, date, show = False):
    Nhisto = len(numbersList)
    Nnames = len(numbersList[0])
    plt.figure(figsize=(1.5*Nnames,2.5*Nhisto))
    for i in range(Nplot):
        numbers = numbersList[i]
        N = len(numbers)
        ind = range(N)    # the x locations for the groups
        width = 0.5      # the width of the bars: can also be len(x) sequence

        subplotNum = Nplot*100+11+i
        plt.subplot(subplotNum)
        p1 = plt.bar(ind, numbers, width)
        plt.title(titleList[i])
        plt.xticks(ind, names)

        for j, num in enumerate(numbers):
            plt.text(j, num, str(num))

    if(show): plt.show()
    else:  
        directory = '../results/' + date + '/'
        # checkDirectory(directory)
        plt.savefig(filename=directory+plotTitle+'.png', format='png')

# --------------------------------------------------------------------------------------------------
# options
# --------------------------------------------------------------------------------------------------

def removeSpacesAndSplit(line):
    return ' '.join(line.split()).split()

def readOptions():
    f = open('../dofile.txt', 'r')
    options = f.read().split('\n')
    for option in options:
        argv = removeSpacesAndSplit(option)
        doOptions(argv)

def doOptions(argv):
    u_help = '-h'
    u_search = '-s "forumName" "date(MMDD)" [-kw -id -ip] (Keyword / ID / IP)'
    u_dofile = '-f'

    if(argv[0] == '-s'):
        # '-s "forumName" "date(MMDD)" [-kw -id -ip] (id or ip)'
        if(len(argv) < 4):
            print('usage:', u_search)
            sys.exit()

        a = time.time()

        forumName = argv[1]
        dateStr = argv[2]
        opt = argv[3]

        directory = '../results/' + dateStr + '/'
        checkDirectory(directory)
        directory += 'summary.csv'
        if not checkFileExists(directory):
            with open(directory, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['搜尋方式', '看板', '時間', '作者ID', 'IP', '標題', '推', '噓', '箭頭', '檔案位置', 'URL'])  

        fileCount = 0
        emptyFile = 0

        directory = '../pttData/' + forumName + '/' + dateStr + '/'
        if not os.path.exists(directory):
            print('Error: No such forum or not downloaded yet ', end='')
            print('('+forumName+')')
            print(usage)
            sys.exit()

        f = open(directory+'summary.txt', 'r')
        pageStr = f.read().split(' ')

        dataList = []
        if(opt == '-kw'):
            #search from text file  
            if(len(argv) < 5): 
                print('Error: Please input keywords after "-kw"')
                sys.exit()        
            keywordList=argv[4:]

            # not in use
            en_titleSearch=False # Use title to filter OR not
            searchDate=False # print date distribution OR word summary
            if(en_titleSearch): 
                titleword=['女']

            a_count = 0

            _index = 0
            wwList = []
            for keyword in keywordList:
                wwList.append(WordWrapper(keyword))   

            if(searchDate):
                dw = DateWrapper()
                if(en_titleSearch): dw_title = DateWrapper()

            for j in range(int(pageStr[0]), int(pageStr[1])+1):
                print('page', j)
                for i in range(20):
                    try:
                        file = open(directory+str(j)+'/'+str(j)+'_'+str(i)+'.txt', 'r')
                        text = file.read()
                        title = getTitleFromText(text)
                        if(en_titleSearch):
                            in_title=False 
                            for t in titleword:
                                if(title.find(t)!= -1): 
                                    #print(t, 'in title')
                                    in_title=True
                            if(in_title): 
                                print(title)
                                a_count += 1
                                dateStr=getDateFromText(text)
                                if(searchDate):
                                    dw_title.addDate(dateStr)
                                    dw = searchText_Date(text, keyword, dw)
                                else:
                                    wwList = searchText(text, wwList)
                        else:
                            if(searchDate):
                                dw = searchText_Date(text, keyword, dw)
                            else:
                                wwList = searchText(text, wwList)
                        file.close()
                        fileCount += 1
                    except Exception as e:
                        emptyFile += 1
            b = time.time()
            print('Total time:', round(b-a, 2))
            if(searchDate):
                if(en_titleSearch):
                    print()
                    print('titles that contain:', titleword)
                    dw_title.printSummary() #print date the the title has titlewords
                print()
                print('in these articles that contain:', keyword)
                dw.printSummary() #print date that the article has keywords
                sys.exit()
            else:
                print('Total articles:', fileCount)

            
            print('In', forumName, 'from page', pageStr[0], 'to', pageStr[1])
            if(en_titleSearch): print('Total titles that contain', titleword, ':', a_count)

            numbersList = [[], [], [], [], []]
            names = []
            titleList = ['標題出現次數', '內文出現次數', '推文出現次數', 
                '有多少篇文章出現此關鍵字', '有多少則推文出現此關鍵字']

            for ww in wwList:
                ww.printSummary()
                numbersList[0].append(ww.titleNum)
                numbersList[1].append(ww.contentNum)
                numbersList[2].append(ww.commentNum)
                numbersList[3].append(ww.articleCount)
                numbersList[4].append(ww.commentCount)
                names.append(ww.keyword)

            title = dateStr + '_' + forumName + '_Keyword_'
            title += '_'.join(names)
            plotMultiHisto(names, numbersList, titleList, title, dateStr)

        elif(opt == '-id'):
            givenID = False
            matchCount = []
            if(len(argv) > 4):
                givenID = True
                idList = argv[4:]
                matchPageList = []
                for n in idList:
                    matchCount.append(0)
                    matchPageList.append([])

            for j in range(int(pageStr[0]), int(pageStr[1])+1):
                print('page', j)
                for i in range(20):
                    try:
                        file = open(directory+str(j)+'/'+str(j)+'_'+str(i)+'.txt', 'r')
                        text = file.read()
                        soup = text2soup(text)
                        _id = getID(soup)
                        if(givenID):                                        
                            index = 0 
                            for id_s in idList:
                                if(_id == id_s): 
                                    matchCount[index] += 1
                                    matchPageList[index].append(str(j)+'_'+str(i))
                                    #
                                    data = []
                                    data.append('ID_search')
                                    data.append(forumName)
                                    data.append(getTime(soup))
                                    data.append(getID(soup))
                                    data.append(getIP(soup))
                                    data.append(getTitle(soup))
                                    for n in countPushes(text): # 推 噓 箭頭
                                        data.append(n)
                                    data.append(str(j)+'_'+str(i))
                                    data.append(text[:text.find('\n')]) # URL
                                    #
                                    dataList.append(data)
                                index += 1
                        else: 
                            print(_id, end='/')
                        file.close()
                    except Exception as e:
                        emptyFile += 1
                if(not givenID): print('')

            index=0
            if(givenID): 
                for id_s in idList:
                    print('\nID', id_s, 'found:', matchCount[index])
                    if(len(matchPageList[index]) != 0):
                        print('articles:', end=' ')
                        for i in matchPageList[index]:
                            print(i, end=' ')
                        print()
                    index += 1
                title = dateStr + '_' + forumName + '_ID'
                plotHisto(idList, matchCount, title, dateStr)

                with open('../results/' + dateStr + '/summary.csv', 'a', newline='') as f:
                    writer = csv.writer(f)  
                    writer.writerows(dataList)



        elif(opt == '-ip'):
            givenIP = False
            matchCount = []
            if(len(argv) > 4):
                givenIP = True
                ipList = argv[4:]
                matchPageList = []
                for n in ipList:
                    matchCount.append(0)
                    matchPageList.append([])

            for j in range(int(pageStr[0]), int(pageStr[1])+1):
                print('page', j)
                for i in range(20):
                    try:
                        file = open(directory+str(j)+'/'+str(j)+'_'+str(i)+'.txt', 'r')
                        text = file.read()
                        soup = text2soup(text)
                        _ip = getIP(soup)
                        if(givenIP):                                        
                            index = 0 
                            for ip_s in ipList:
                                if(_ip == ip_s): 
                                    matchCount[index] += 1
                                    matchPageList[index].append(str(j)+'_'+str(i))
                                    #
                                    data = []
                                    data.append('IP_search')
                                    data.append(forumName)
                                    data.append(getTime(soup))
                                    data.append(getID(soup))
                                    data.append(getIP(soup))
                                    data.append(getTitle(soup))
                                    for n in countPushes(text): # 推 噓 箭頭
                                        data.append(n)
                                    data.append(str(j)+'_'+str(i))
                                    data.append(text[:text.find('\n')]) # URL
                                    #
                                    dataList.append(data)
                                index += 1
                        else: 
                            print(_ip, end='/')
                        file.close()
                    except Exception as e:
                        emptyFile += 1
                if(not givenIP): print('')

            index=0
            if(givenIP): 
                for ip_s in ipList:
                    print('\nIP', ip_s, 'found:', matchCount[index])
                    if(len(matchPageList[index]) != 0):
                        print('articles:', end=' ')
                        for i in matchPageList[index]:
                            print(i, end=' ')
                        print()
                    index += 1
                title = dateStr + '_' + forumName + '_IP'
                plotHisto(ipList, matchCount, title, dateStr)
                
                with open('../results/' + dateStr + '/summary.csv', 'a', newline='') as f:
                    writer = csv.writer(f)  
                    writer.writerows(dataList)
                    
        else:
            print('option not correct: [-kw -id -ip] (id or ip)')

    else:        
        print('[OPTION]    | [USAGE]') 
        print('HELP        |', u_help)
        print('SEARCH      |', u_search)
        print('DOFILE      |', u_dofile)
        sys.exit()

# --------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------

def main():
    if not checkFileExists('../dofile.txt'):
        with open('../dofile.txt', 'w') as f:
            f.write('--- type "py crawler.py" in cmd to see help ---\n')
            f.write('---       delete all before you start       ---\n')                  

    checkDirectory('../results/')
    checkDirectory('../pttData/')
    if(len(sys.argv) == 1): # no option
        argv = ['-h']
    else:
        argv = sys.argv[1:]

    if(argv[0] == '-f'): readOptions()
    else: doOptions(argv)
    
  
if __name__ == '__main__':
    main()

