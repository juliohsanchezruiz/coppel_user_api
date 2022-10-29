import hashlib
import os

import requests
from flask import Flask, json, Response
from flask import request
from flask import make_response
from jsonschema import ValidationError
from flask_mongoengine import MongoEngine
from flask_expects_json import expects_json
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from flask import jsonify

UPLOAD_FOLDER = 'static/files'
ONSALE_DATE = "onsaleDate"
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__, template_folder='template')
app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '06e95112ae112198a7103d9aac2f336a7660649d'
app.config["JWT_SECRET_KEY"] = "06e95112ae112198a7103d9aac2f336a7660649d"  # Change this!
jwt = JWTManager(app)
print('mongodb://' + os.environ.get("MONGO_USER") + '@' + os.environ.get("MONGO_HOST") + ':' + os.environ.get(
        "MONGO_PORT") + '/' + os.environ.get("MONGO_DB"))
app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://' + os.environ.get("MONGO_USER") + '@' + os.environ.get("MONGO_HOST") + ':' + os.environ.get(
        "MONGO_PORT") + '/' + os.environ.get("MONGO_DB"),
    "username": os.environ.get("MONGO_USER"),
    "password": os.environ.get("MONGO_PASS"),
}

db = MongoEngine(app)

if __name__ == "__main__":
    app.run()

schemaRegister = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "age": {"type": "number"},
        "password": {"type": "string"},
    },
    "required": ["email", "name", "age", "password"]
}


@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({'error': original_error.message}), 400)
    # handle other "Bad Request"-errors
    return error


@app.route("/api/login", methods=["POST"])
def login():
    username = request.json.get("email", None)
    password = request.json.get("password", None)
    user = User.objects(email=username).first()
    if user is None:
        return Response(response=json.dumps({"msg": "Bad username or password"}), status=401,
                        mimetype='application/json')
    if not check_password(user, password):
        return Response(response=json.dumps({"msg": "Bad username or password"}), status=401,
                        mimetype='application/json')
    access_token = create_access_token(identity=username)
    response = {
        "mensaje": "Seresitro correctamente",
        "id": str(user.id),
        "name": str(user.name),
        "age": str(user.age),
        "token": access_token,
    }
    return Response(response=json.dumps(response), status=201, mimetype='application/json')


@app.route('/api/user', methods=["POST"])
@expects_json(schemaRegister)
def user_store():
    email = request.json["email"]
    userExist = User.objects(email=email).first()
    if userExist == None:
        user = User(
            name=request.json["name"],
            age=request.json["age"],
            email=email,
            password=generate_password_hash(request.json["password"], method='sha256')
        )
        user.save()
        access_token = create_access_token(identity=email)
        response = {
            "mensaje": "Seresitro correctamente",
            "id": str(user.id),
            "name": str(user.name),
            "age": str(user.age),
            "token": access_token,
        }
        return Response(response=json.dumps(response), status=201, mimetype='application/json')
    else:
        response = {
            "mensaje": "El usuario ya existe"
        }
        return Response(response=json.dumps(response), status=400, mimetype='application/json')


@app.route('/api/user', methods=["GET"])
@jwt_required()
def user_show():
    email = get_jwt_identity()
    user = User.objects(email=email).first()
    if user is not None:
        response = {
            "id": str(user.id),
            "name": str(user.name),
            "email": str(user.email),
            "age": str(user.age),
        }
        return Response(response=json.dumps(response), status=200, mimetype='application/json')
    response = {
        "mensaje": "El usuario no existe"
    }
    return Response(response=json.dumps(response), status=400, mimetype='application/json')


@app.route('/api/user', methods=["PUT"])
@expects_json(schemaRegister)
@jwt_required()
def user_update():
    email = get_jwt_identity()
    user = User.objects(email=email).first()
    if user is not None:
        email = request.json["email"]
        data = {
            "name": request.json["name"],
            "age": request.json["age"],
            "email": email,
        }
        if request.json["password"]:
            data["password"] = generate_password_hash(request.json["password"], method='sha256')
        User.replace_one(user.id, data, True)
        response = {
            "mensaje": "El usuario se actializo correctamente"
        }
        return Response(response=json.dumps(response), status=200, mimetype='application/json')
    response = {
        "mensaje": "El usuario no existe"
    }
    return Response(response=json.dumps(response), status=400, mimetype='application/json')


class Comics(db.Document):
    comic_id = db.IntField()
    name = db.StringField()
    imagen = db.StringField()
    onsaleDate = db.StringField()


class User(db.Document):
    __tablename__ = 'users'
    name = db.StringField(required=True)
    age = db.IntField()
    email = db.StringField()
    password = db.StringField()
    comics = db.ListField()


def check_password(user, password):
    return check_password_hash(user.password, password)
