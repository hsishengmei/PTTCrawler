# PTTCrawler
A web crawler for PTT, course project of Psychoinformatics and Neuroinformatics 2017 Spring
-	Sending web requests and automatically clones articles from PTT for further analysis
-	Search these cloned articles by user ID, IP address, title, or keyword in content
-	Calculate the upvotes and downvotes of the selected articles

### Usage
- `python downloader.py "forumName" "date(MMDD)"`
- `python crawler.py -s "forumName" "date(MMDD)" [-kw / -ti / -id / -ip] (desired Keyword / title / ID / IP)`

### Environment:
- recommend using Linux or Mac
- `Python 3.5+`, `requests`, `bs4`, `lxml`, `numpy`, `matplotlib`
