import os
import pymongo
from pymongo import ReturnDocument
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


votes = None
votes_cache = {}


def connect_to_db():
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    print("Connecting to DB...")
    client = pymongo.MongoClient(f"mongodb+srv://{db_user}:{db_pass}@mikolasanwebsite.afnov.mongodb.net/{db_name}?retryWrites=true&w=majority")
    db = client[db_name]
    print("Getting 'votes'")
    global votes
    votes = db["votes"]


def trim_ending_slash(url):
    if len(url) > 0 and url[-1] == '/':
        return url[:-1]
    return url


connect_to_db()
app = FastAPI()

origins = [
    "https://neupokoev.xyz",
    "http://localhost",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/likes")
def read_likes(url: str):
    url = trim_ending_slash(url)
    cursor = votes.find({ "path": url })
    scores = {x['vote']: x['score'] for x in cursor.clone()}
    if len(scores) > 0:
        global votes_cache
        if url not in votes_cache:
            votes_cache[url] = {x['vote']: x['_id'] for x in cursor.clone()}
        
        return {
            "scores": scores
        }
    
    return {}


class Like(BaseModel):
    url: str
    like: str


@app.post("/like", status_code=201)
def like_url(body: Like):
    url = body.url
    vote_name = body.like
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
    
    return {
        "scoreName": vote_name,
        "score": score
    }




