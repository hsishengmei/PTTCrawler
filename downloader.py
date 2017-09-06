import requests
from bs4 import BeautifulSoup
import time
import sys, os
from subprocess import Popen
from crawler import getPageText, getIndexDate

# --------------------------------------------------------------------------------------------------
# download functions
# --------------------------------------------------------------------------------------------------

def downloadPage(filename, forumName, page, link, directory):
    a = time.time()
    pageText = getPageText(link)
    b = time.time()
    # directory = 'ptt/' + forumName + '/' + dateStr + '/'
    directory += str(page) + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filePath = directory + str(page) + '_' + filename + ".txt"
    f = open(filePath, 'w')
    f.write(link+'\n'+pageText)
    f.close()
    print('download to %s, time: %f' % (filePath, round(b-a, 2)))

def downloadIndexPage(forumName, indexNum, directory):
    url='https://www.ptt.cc/bbs/'+forumName+'/index'+str(indexNum)+'.html'
    print('page', indexNum)
    
    pageText = getPageText(url)

    soup = BeautifulSoup(pageText, 'lxml')
    articles = soup.find_all('div', 'r-ent')

    NOT_EXIST = BeautifulSoup('<a>Empty</a>', 'lxml').a

    articleCount=0
    for article in articles:
        meta = article.find('div', 'title').find('a') or NOT_EXIST
        if(meta == NOT_EXIST):
            link = 'empty'
            print(link)
        else:
            link = meta.get('href')
            print(link, end=' ')
            try: 
                downloadPage(str(articleCount), forumName, indexNum, 'https://www.ptt.cc'+link, directory)
            except Exception as e:
                 print('Error: downloadPage')
        articleCount += 1
    try:
        downloadPage('index', forumName, indexNum, url, directory)
    except Exception as e:
        print('Error: downloadPage')

def downloadMissingPage(forumName, startPage, endPage, directory):
    print('downloading', forumName, 'from page', startPage, 'to', endPage)
    for indexNum in range(startPage, endPage+1):
        if not os.path.isdir(directory + str(indexNum) + '/'):
            try:                
                # print('page', indexNum, 'missing')
                downloadIndexPage(forumName, indexNum, directory)
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
    directory = 'ptt/' + forumName + '/' + dateStr + '/'  
    if not os.path.exists(directory):
        os.makedirs(directory)
    filePath = directory + 'summary.txt'
    f = open(filePath, 'w')
    f.write(str(startPage) + ' ' + str(endPage))
    f.close()

    for i in range(n_processes):
        # downloadMissingPage
        Popen(['python', 'downloader.py', 'Gossiping', str(start[i]), str(start[i+1]), dateStr])

# --------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------
def main():
    argv = sys.argv[1:]
    if(len(argv) == 4):
        # "forumName" "startPage" "pages" "date(MMDD)"
        start = time.time()
        forumName = argv[0]
        startPage = int(argv[1])
        endPage = int(argv[2])
        dateStr = argv[3]
        directory = 'ptt/' + forumName + '/' + dateStr + '/'

        downloadMissingPage(forumName, startPage, endPage, directory)

        end = time.time()
        print('time:', end - start, 'seconds')
    elif(len(argv) == 2):
        # "forumName" "date(MMDD)"
        start = time.time()
        forumName = argv[0]
        dateStr = argv[1]
        #download forum from web
        dateCP = getIndexDate(forumName, dateStr)
        n_processes = 8

        downloadMultiProcess(forumName, dateCP[1], dateCP[0], n_processes, dateStr)

        end = time.time()
        print('time:', end - start, 'seconds')
    else:
        print('usage: "forumName" "date(MMDD)"')
        sys.exit()

    
  
if __name__ == '__main__':
    main()
