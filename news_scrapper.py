from multiprocessing import Process, Pool
from newspaper import Article
from datetime import datetime
from bs4 import BeautifulSoup
import pickle
import requests
import json
import pymongo
import sys
import os
import time

# sudo systemctl start mongodb
# sudo systemctl stop mongodb

#Finds article urls foe getting feeds---------------------------------------------
def find_articles(url,security,weblink,company):
    if '.com' in company:
        company.replace('.com','')
    article_links = []
    search = ''
    if 'finance.yahoo' in url:
        search = url.format(security,security)
    else:
        search = url.format(security)

    r = requests.get(search)
    page = r.content
    soup = BeautifulSoup(page, 'html5lib')

    #Foe each website, find urls from the html page and filter them
    #to get relevant articles
    if weblink == 'https://www.reuters.com':
        for link in soup.find_all('a'):
            urlname = link.get('href')
            if urlname is not None and urlname.startswith('https://www.reuters.com/article/'):
                if urlname not in article_links:
                    article_links.append(urlname)
    elif weblink == 'http://in.finance.yahoo.com':
        for link in soup.find_all('a'):
            urlname = link.get('href')
            if urlname is not None and urlname.startswith('/news/') and company.lower() in urlname :
                article_links.append(weblink+urlname)
    elif weblink == 'https://timesofindia.indiatimes.com':
        for link in soup.find_all('a'):
            urlname = link.get('href')
            if urlname is not None and urlname.startswith('/business/') and '.cms' in urlname:
                article_links.append(weblink+urlname)

    return article_links


#Fetch the feeds from the article url and store the feeds in MongoDB--------------------------------------------
def fetch_feeds(p):
    searchurl = p[0]
    weblink = p[1]
    security = p[2]
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient['news']

    for key in security:
        article_links = find_articles(searchurl,key,weblink,security[key])
        mydb[key].create_index([("story_date", pymongo.DESCENDING), ("title", pymongo.ASCENDING)],unique=True)
        mycol = mydb[key]

        for each_link in article_links:
            #Try downloading article. Skip fetching feeds from the url on error
            article = Article(each_link)
            try:
                article.download()
                article.parse()
            except:
                continue

            soup2 = BeautifulSoup(article.html, 'html5lib')
            titlename = (soup2.title.string).strip()
            tex = article.text

            #Find the source of the article from the url
            source = ''
            if 'yahoo' in each_link:
                source = "Yahoo Finance"
            elif 'reuters' in each_link:
                source = "Reuters"
            elif 'timesofindia'in each_link:
                source = "TOI"

            #Remove '.com' from the name of the company if present
            company = security[key]
            if '.com' in company:
                company.replace('.com','')

            #Remove leading and trailing spaces from the name
            company = company.strip()

            #Store the feed if company name is found in the body or title of the article
            if (company.lower() in titlename.lower() or company.lower() in tex.lower()):
                article.nlp()
                print(key,source)
                story_date = ''
                story_time = ''
                if article.publish_date is not None:
                    story_date = datetime.date(article.publish_date)
                    story_time = datetime.date(article.publish_date)
                temp = {"current_day":str(datetime.date(datetime.now())),
                        "authors":str(",".join(article.authors)),
                        "story_date":str(story_date),
                        "story_time":str(story_time),
                        "title":str(titlename),
                        "source":str(source),
                        "keywords":str(",".join(article.keywords)),
                        "summary":str(article.summary)}

                #Try inserting the record/document in the database. In case of
                #duplicate entry, skip adding the extry
                try:
                    x = mycol.insert_one(temp)
                except:
                    continue
    return


# Read the arguments
output_dir= sys.argv[1]
input_file = sys.argv[2]

#Create output directory
os.system('mkdir {}'.format(output_dir))

#Read websites from the input file
search_urls = []
weblink = []
f = open(input_file, "r")
for link in f:
    site = link.rstrip('\n')
    weblink.append(site)

    #Store the search url to be used for searching a company
    if 'finance.yahoo' in site:
        search_urls.append('https://in.finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch')
    elif 'reuters' in site:
        search_urls.append('https://www.reuters.com/companies/{}')
    elif 'timesofindia' in site:
        search_urls.append('https://timesofindia.indiatimes.com/topic/{}')


# Read the securities and company name from pickle file
security = {}
with (open("symbols.pickle", "rb")) as openfile:
    objects = pickle.load(openfile)
for i in range(200):
    security[objects['symbol'][i]] = objects['company'][i].split(" ")[0]
# print(security)


# Find articles and extract feed from each website simultaneously
cmdarg = []
temp = []
temp.append(search_urls[0])
temp.append(weblink[0])
temp.append(security)
cmdarg.append(temp)

temp = []
temp.append(search_urls[2])
temp.append(weblink[2])
temp.append(security)
cmdarg.append(temp)

pool = Pool(processes=4)
pool.map(fetch_feeds, cmdarg)

cmdarg = []
temp = []
temp.append(search_urls[1])
temp.append(weblink[1])
temp.append(security)
cmdarg.append(temp)

pool = Pool(processes=4)
pool.map(fetch_feeds, cmdarg)


#Create files for each security and add data to it
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient['news']
for key in security:
    mycol = mydb[key]
    f = open("{}/{}".format(output_dir,key),"w+")
    for x in mycol.find({},{"_id":0}):
        entry = json.dumps(x)
        f.write(entry)
    f.close()
