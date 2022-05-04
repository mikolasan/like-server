from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os
import pymongo
from pymongo import ReturnDocument


votes = None
votes_cache = {}


def connect_to_db():
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    print("Connecting to DB...", db_user, db_pass, db_name)
    client = pymongo.MongoClient(f"mongodb+srv://{db_user}:{db_pass}@mikolasanwebsite.afnov.mongodb.net/{db_name}?retryWrites=true&w=majority")
    db = client[db_name]
    print("Getting 'votes'")
    global votes
    votes = db["votes"]


def trim_ending_slash(url):
    if len(url) > 0 and url[-1] == '/':
        return url[:-1]
    return url


# https://pythonbasics.org/webserver/
# https://gist.github.com/roughy/157036bed7d4ead34113


class LikeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        origin = self.headers.get('origin')
        self.send_response(200)
        self.send_header("Content-Type", "application/json;charset=UTF-8")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
        response = {}
        # path vote score
        u = urlparse(self.path)
        if u.path == "/likes":
            query_components = parse_qs(u.query)
            url = trim_ending_slash(query_components["url"][0])
            cursor = votes.find({ "path": url })
            scores = {x['vote']: x['score'] for x in cursor.clone()}
            if len(scores) > 0:
                global votes_cache
                if url not in votes_cache:
                    votes_cache[url] = {x['vote']: x['_id'] for x in cursor.clone()}
                response = {
                    "scores": scores
                }
            self.wfile.write(json.dumps(response).encode('utf8'))
        elif u.path == "/like":
            pass
        else:
            pass

    def do_POST(self):
        if self.path == "/like":
            origin = self.headers.get('origin')
            self.send_response(201)
            self.send_header("Content-Type", "application/json;charset=UTF-8")
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf8'))
            #print(data['url'], data['like'])
            url = data['url']
            vote_name = str(data['like'])
            score = 0
            global votes_cache
            if url not in votes_cache:
                inserted = votes.insert_one({
                    "path": url,
                    "vote": vote_name,
                    "score": 1
                })
                votes_cache[url] = {vote_name: inserted.inserted_id}
                score = 1
            elif vote_name not in votes_cache[url]:
                inserted = votes.insert_one({
                    "path": url,
                    "vote": vote_name,
                    "score": 1
                })
                votes_cache[url][vote_name] = inserted.inserted_id
                score = 1
            else:
                updated = votes.find_one_and_update(
                    { "_id": votes_cache[url][vote_name] },
                    { "$inc": {"score": 1} },
                    return_document=ReturnDocument.AFTER)
                score = updated["score"]
            
            print(vote_name, score)
            #send response:
            self.wfile.write(json.dumps({
                "scoreName": vote_name,
                "score": score
            }).encode('utf8'))

    def do_OPTIONS(self) :
        if self.path.startswith("/like"):
            origin = self.headers.get('origin')
            self.send_response(200)            
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            #send response:
            self.wfile.write(json.dumps({}).encode('utf8'))


if __name__ == "__main__":
    connect_to_db()
    hostName = "0.0.0.0"
    serverPort = int(os.environ.get('PORT', 10000))
    webServer = HTTPServer((hostName, serverPort), LikeServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
