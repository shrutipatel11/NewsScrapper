# NEWS-SCRAPPER

News Scrapper is a simple prototype of a centralised newsfeed system. 

# Input:
 The system takes simple text file containing news sites as input. Currently, the system supports for 3 news websites as follows:
  -  https://www.reuters.com
  - http://in.finance.yahoo.com
  - https://timesofindia.indiatimes.com

# Fetching articles
For all the securities mentioned in the file "symbols.pickle", the system finds urls of all the articles present in the search webpage of the security. For searching articles of a security, url for each website for search is as follows:
 -  https://in.finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch
  - https://www.reuters.com/companies/{}
  - https://timesofindia.indiatimes.com/topic/{}

The {} should be replaced with the security. 
The system uses BeautifulSoup api for fetching urls from the website. However, not all the fetched urls will be artilces of the security we are searching for. Some may be other news articles or advertisement links. Hence, the system filters the urls based on the website from which it is obtained. 

After fetching the urls, the system uses newspaper3k api to fetch details of the news articles. The data contains the following fields:
   -  **Current date**  : The date on which the program is run
   -  **Authors**   : The authors of the story
   -  **Story date**    : The date on which story is published
   -  **Story time**    : The time at which story is published
   -  **Title** : Title of the story
   -  **Summary**   : Summary of the story
   -  **Source**    : The website name from which the story is obtained
   -  **Keywords**  : The relevant topics present in the article

# Storing the data
A collection is created for each security in MongoDb database. The data for each article is stored in thie corresponding collections in the database.
After the database is populated, the data is retrieved and stored in json files in the output directory (given as an argument to the program).

# Features
  - The feeds are fetched parallely from the websited using python Pool library.
  - The database is indexed on two fields namely story date and title, and its uniqueness property is set to true. Hence, there are no duplicate records in the database.
  - A flask API is develped on top of the results which allows basec queries like:
    - Number of articles captured by a source on a given date
