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
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"})

@app.route("/count", methods=["GET"])
def count():
    count = db.songs.count_documents({})
    return jsonify({"count": count})

@app.route("/song", methods=["GET"])
def songs():
    cursor = db.songs.find({})
    songs_json = json_util.dumps({"songs": list(cursor)})
    return make_response(songs_json, 200, {'Content-Type': 'application/json'})

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    find_id = db.songs.find_one({"id": id})
    if find_id:
        song_json = json_util.dumps({"song": find_id})
        return make_response(song_json, 200, {'Content-Type': 'application/json'})
    else:
        return make_response(jsonify({"message": "Song with id not found"}), 404)

@app.route("/song", methods=["POST"])
def create_song():
    try:
        song_data = request.json

        if not song_data:
            return jsonify({"error": "No data provided"}), 400

        if db.songs.find_one({"id": song_data.get("id")}):
            return make_response(jsonify({"Message": f"Song with id {song_data.get('id')} already present"}), 409)

        db.songs.insert_one(song_data)
        return make_response(jsonify({"Message": "Song created successfully"}), 201)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        song_data = request.json
        existing_song = db.songs.find_one({"id": id})
        if not existing_song:
            return jsonify({"message": "Song not found"}), 404

        db.songs.update_one({"id": id}, {"$set": song_data})
        
        updated_song = db.songs.find_one({"id": id})
        
        updated_song_json = json.loads(json_util.dumps(updated_song))
        
        return make_response(jsonify(updated_song_json), 201)
    except Exception as e:
        return jsonify({"error": "An error occurred processing your request", "details": str(e)}), 500

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    
    if result.deleted_count == 0:
        return jsonify({"message": "Song not found"}), 404
    else:
        return '', 204
######################################################################
