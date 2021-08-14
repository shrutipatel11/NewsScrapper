import flask
from flask import request, jsonify
import pymongo
import pickle

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["news"]

security = []
with (open("symbols.pickle", "rb")) as openfile:
    objects = pickle.load(openfile)
for i in range(200):
    security.append(objects['symbol'][i])

app = flask.Flask(__name__)

@app.route('/<date>/<src>', methods = ['GET'])
def getJSON(date,src):
    myquery = { "story_date": str(date),"source":str(src)}
    count = 0
    for i in security:
        mycol = mydb[i]
        mydoc = mycol.find(myquery)
        for x in mydoc:
            count+=1
    return(str(count))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5001', threaded=True, debug = True)
