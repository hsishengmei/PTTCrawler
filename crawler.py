import requests
#from multiprocessing import Process
from bs4 import BeautifulSoup
import time
import sys, os
from enum import Enum
from wrapper import WordWrapper, DateWrapper
from subprocess import Popen

# --------------------------------------------------------------------------------------------------
# functions for download
# --------------------------------------------------------------------------------------------------

def downloadPage(filename, forumName, page, link, directory):
    a = time.time()
    pageText = getPageText(link)
    b = time.time()
    # directory = 'ptt_new/' + forumName + '/' + dateStr + '/'
    directory += str(page) + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filePath = directory + str(page) + '_' + filename + ".txt"
    f = open(filePath, 'w')
    f.write(link+'\n'+pageText)
    f.close()
    print('download to %s, time: %f' % (filePath, round(b-a, 2)))

def downloadForum(forumName, startPage, totalPage, directory):
    pageNum=startPage
    errorCount=0
    for i in range(totalPage):
        # if(i % 5 == 0):
        #     time.sleep(2)
        articleCount=0
        prevPage='https://www.ptt.cc/bbs/'+forumName+'/index'+str(pageNum)+'.html'
        print('page', pageNum)
        try:
            pageText = getPageText(prevPage)
        except Exception as e:
            print('Error: getPageText')
            errorCount += 1
            if(errorCount >= 3):
                pageNum -= 1
            continue

        soup = BeautifulSoup(pageText, 'lxml')
        articles = soup.find_all('div', 'r-ent')

        NOT_EXIST = BeautifulSoup('<a>本文已被刪除</a>', 'lxml').a

        for article in articles:
            meta = article.find('div', 'title').find('a') or NOT_EXIST
            if(meta == NOT_EXIST):
                link = 'empty'
                print(link)
            else:
                link = meta.get('href')
                print(link, end=' ')
                try:    
                    downloadPage(str(articleCount), forumName, pageNum, 'https://www.ptt.cc'+link, directory)
                except Exception as e:
                    print(' Error: downloadPage')
            articleCount += 1
        #next page
        pageNum += 1

def downloadMissingPage(forumName, startPage, endPage, directory):
    print('downloading', forumName, 'from page', startPage, 'to', endPage, '...')
    for page in range(startPage, endPage+1):
        if not os.path.isdir(directory):
            try:                
                print('page', page, 'missing')
                downloadForum(forumName, page, 1, directory)
            except Exception as e:
                 print('Error: incorrect directory', directory)

def downloadMultiProcess(forumName, startPage, endPage, n_processes, dateStr):
    pages = int((endPage - startPage) / n_processes)
    if(pages > n_processes): pages += 1
    start = []
    for n in range(n_processes):
        start.append(startPage+n*pages)
    start.append(endPage+1)
    print(start)

    # write a summary file  
    
    directory = 'ptt_new/' + forumName + '/' + dateStr + '/'  
    if not os.path.exists(directory):
        os.makedirs(directory)
    filePath = directory + 'summary.txt'
    f = open(filePath, 'w')
    f.write(str(startPage) + ' ' + str(endPage))
    f.close()

    for i in range(n_processes):
        Popen(['python3', 'crawler.py', '-d', 'Gossiping', str(start[i]), str(start[i+1]-start[i]), dateStr])



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
    
def getDate(text):
    soup = BeautifulSoup(text, 'lxml')
    s=soup.find_all('span', 'article-meta-value')
    timeStr=s[3].text
    dateStr=timeStr[4:10]
    return(dateStr)

def countPushes(soup):
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
    dateptr = ''
    findEqual = True
    indexRange = []

    for i in range(2):
        found = False
        stage = 0
        pageJump = 64
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
def searchText(text,keyword, ww):
    #a = time.time()
    soup = BeautifulSoup(text, 'lxml')
    #title
    title = getTitle(soup)
    n_t = searchKeyword(title,keyword)
    ww.titleNum += n_t
    #content
    content = getContent(soup)
    n_ct = searchKeyword(content,keyword)
    ww.contentNum += n_ct
    #pushes
    pushes = soup.find_all('div', 'push')
    n_cm_total = 0
    for push in pushes:
        #ptt_id = push.find('span', 'f3 hl push-userid').getText()
        comment = push.find('span', 'f3 push-content').getText()
        n_cm = searchKeyword(comment,keyword)
        if(n_cm != 0):
            #print(comment)
            ww.commentCount += 1
        n_cm_total += n_cm
    ww.commentNum += n_cm_total

    if(n_t + n_ct + n_cm_total != 0):
        ww.articleCount += 1

    return ww

# search from file
def searchText_Date(text,keyword, dw):
    #a = time.time()
    soup = BeautifulSoup(text, 'lxml')
    #title
    dateStr = getDate(text)
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

# --------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------
def main():
    if(len(sys.argv) == 1): # no option
        argv = ['-h']
    else:
        argv=sys.argv[1:]
    
    u_help = '-h'
    u_download = '-d "forumName" "date(MMDD)"\n -d "forumName" "startPage" "pages" "date(MMDD)"'
    u_search = '-s "forumName" "date(MMDD)" [-kw -id -ip] (id or ip)'

    if(argv[0] == '-h'):
        print('[OPTION]    | [USAGE]') 
        print('HELP        |', u_help)
        print('DOWNLOAD    |', u_download)
        print('SEARCH      |')
        print(' -from file |', u_search)
    elif(argv[0] == '-d'):
        if(len(argv) == 5):
            # -d "forumName" "startPage" "pages" "date(MMDD)"
            start = time.time()
            forumName = argv[1]
            startPage = int(argv[2])
            pages = int(argv[3])
            dateStr = argv[4]
            directory = 'ptt_new/' + forumName + '/' + dateStr + '/'

            downloadForum(forumName, startPage, pages, directory)

            end = time.time()
            print('time:', end - start, 'seconds')
        elif(len(argv) == 3):
            # -d "forumName" "date(MMDD)"
            start = time.time()
            forumName = argv[1]
            dateStr = argv[2]
            #download forum from web
            dateCP = getIndexDate(forumName, dateStr)
            n_processes = 8

            downloadMultiProcess(forumName, dateCP[1], dateCP[0], n_processes, dateStr)
            #downloadMissingPage(forumName, dateCP[1], dateCP[0])
            #downloadForum(forumName, startPage, pages)
            end = time.time()
            print('time:', end - start, 'seconds')
        else:
            print('usage:', u_download)
            sys.exit()

    elif(argv[0] == '-s'):
        # '-s "forumName" "date(MMDD)" [-kw -id -ip] (id or ip)'
        if(len(argv) < 4):
            print('usage:', u_search)
            sys.exit()


        a = time.time()

        keyword=['台女', '母豬']

        en_titleSearch=True # Use title to filter OR not
        searchDate=False # print date distribution OR word summary

        if(en_titleSearch): 
            titleword=['女']

        a_count = 0

        ww = WordWrapper(keyword)
        forumName = argv[1]
        # startPage = int(argv[2])
        # pages = int(argv[3])
        # opt = argv[4]
        dateStr = argv[2]
        opt = argv[3]

        fileCount = 0
        emptyFile = 0

        directory = 'ptt_new/' + forumName + '/' + dateStr + '/'
        if not os.path.exists(directory):
            print('Error: No such forum or not downloaded yet ', end='')
            print('('+forumName+')')
            print(usage)
            sys.exit()

        f = open(directory+'summary.txt', 'r')
        pageStr = f.read().split(' ')

        if(opt == '-kw'):
            #search from text file       
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
                                dateStr=getDate(text)
                                if(searchDate):
                                    dw_title.addDate(dateStr)
                                    dw = searchText_Date(text, keyword, dw)
                                else:
                                    ww = searchText(text, keyword, ww)
                        else:
                            if(searchDate):
                                dw = searchText_Date(text, keyword, dw)
                            else:
                                ww = searchText(text, keyword, ww)
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
            ww.printSummary()
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
                        _id = getIDFromText(text)
                        if(givenID):                                        
                            index = 0 
                            for id_s in idList:
                                if(_id == id_s): 
                                    matchCount[index] += 1
                                    matchPageList[index].append(str(j)+'_'+str(i))
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
                        _ip = getIPFromText(text)
                        if(givenIP):                                        
                            index = 0 
                            for ip_s in ipList:
                                if(_ip == ip_s): 
                                    matchCount[index] += 1
                                    matchPageList[index].append(str(j)+'_'+str(i))
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
        else:
            print('option not correct')
            sys.exit()

    

if __name__ == '__main__':
    main()

