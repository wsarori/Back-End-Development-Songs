from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))



# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=['GET'])
def check_health():
    return {"status":"OK"}

@app.route("/count", methods=['GET'])
def count_docs():
    count=db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=['GET'])
def songs():
    result = db.songs.find({})
    result_list = list(result)
    songs_list=json_util.dumps(result_list)
    return json_util.dumps(result_list), 200

@app.route("/song/<int:id>", methods=['GET'])
def get_song_by_id(id):
    result = db.songs.find_one({"id": id})
    #if not result or len(result_list) < 1:
     #   return jsonify({"message": "song with id not found"}), 404
    #songs_list=json_util.dumps(result_list)
    return json_util.dumps(result), 200

from flask import jsonify, request
@app.route("/song", methods=['POST'])
def create_song():
    request_data=request.json
    id=int(request_data['id'])
    song = db.songs.find_one({"id": id})
    if not song:
       db.songs.insert_one(request_data)
       result = db.songs.find_one({"id": id})
       uid=result["_id"]
       return jsonify({"": f"uid: {uid}."}), 201
    return jsonify({"": f"song with id {id} already present"}), 302


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song = request.get_json()
    existing_song = db.songs.find_one({"id": id})

    if not existing_song:
        return jsonify({"message": f"song with id {id} not found"}), 404

    # Update the existing song with the new data
    if song["title"]==existing_song["title"]:
        return jsonify({"message":"song found, but nothing updated"}), 200
    updated_song = {
        "$set": song
    }
    result = db.songs.find({"id": id})
    result_list = list(result)


    songs_list=json_util.dumps(result_list)
    
    db.songs.update_one({"id": id}, updated_song)

    
    #result_list = list(result)
    return json_util.dumps(existing_song), 201
    #return json_util.dumps(existing_song["title"]), 200

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    
    result=db.songs.delete_one({"id": id})
    deleted_count = result.deleted_count
    if deleted_count==0:
       return "message :song not found", 404 


   
    return json_util.dumps(result), 204
    #return json_util.dumps(existing_song["title"]), 200
