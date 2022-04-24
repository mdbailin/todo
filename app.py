from pickle import GLOBAL
from unittest import result
from urllib import response
from wsgiref import headers
import requests
import os
from flask import Flask, url_for, request, redirect, jsonify, abort, session, _request_ctx_stack, make_response
from flask.templating import render_template
from models import setup_db, Todo, TodoList
from datetime import datetime
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
import sys
import json
from six.moves.urllib.request import urlopen
from functools import wraps
from auth import requires_auth, AuthError
from flask_cors import cross_origin
from jose import jwt
from flask_cors import CORS

def create_app(test_config=None):
  app = Flask(__name__)
  setup_db(app)
  CORS(app)
  header = None

  GLOBAL_ID = 70

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                          'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                          'GET,PATCH,POST,DELETE,OPTIONS')

    return response

  @app.errorhandler(AuthError)
  def handle_auth_error(ex):
      response = jsonify(ex.error)
      response.status_code = ex.status_code
      return response

  ENV_FILE = find_dotenv()
  if ENV_FILE:
      load_dotenv(ENV_FILE)

  #authentication
  app.secret_key = env.get("APP_SECRET_KEY")
  ALGORITHMS = ["RS256"]

  oauth = OAuth(app)
  oauth.register(
      "auth0",
      client_id=env.get("AUTH0_CLIENT_ID"),
      client_secret=env.get("AUTH0_CLIENT_SECRET"),
      api_base_url='https://dev-lzgwqs5u.us.auth0.com',
      access_token_url='https://dev-lzgwqs5u.us.auth0.com/oauth/token',
      authorize_url='https://dev-lzgwqs5u.us.auth0.com/authorize',
      client_kwargs={
          "scope": "openid profile email",
      },
      server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
  )

  @app.route("/login")
  def login():
      return oauth.auth0.authorize_redirect(
          redirect_uri=url_for("callback", _external=True),
          audience=env.get("AUTH0_AUDIENCE")
      )
  @app.route("/callback", methods=["GET", "POST"])
  def callback():
      global header
      token = oauth.auth0.authorize_access_token()
      session["user"] = token
      access_token = session["user"]["access_token"]
      header = 'Bearer {}'.format(access_token)
      # session["headers"] = HEADERS
      

      return redirect(url_for('get_list_todos', list_id=70, header=header))
      
  @app.route("/logout")
  def logout():
      session.clear()
      return redirect(
          "https://" + env.get("AUTH0_DOMAIN")
          + "/v2/logout?"
          + urlencode(
              {
                  "returnTo": url_for("get_list_todos", list_id=70, _external=True),
                  "client_id": env.get("AUTH0_CLIENT_ID"),
              },
              quote_via=quote_plus,
          )
      )

  def format_todo(event):
      return {
          "description": event.description,
          "id": event.id,
          "completed": event.completed,
          "list_id": event.list_id
      }


  @app.route('/lists/create', methods=['POST'])
  @requires_auth('create: todolist')
  def create_todo_list(jwt):
    list_error = False
    body = {}
    try:
      body = request.get_json()
      name = body['name']
      list = (TodoList(name=name))
      list.insert()
    except:
      list_error = True
      print(sys.exc_info())
    if list_error:
      abort (422)
    else:
      return jsonify({'name': name}), 200
    
  #route, POST wrapper over create_todo() method, try/catch block in case POST fails
  @app.route('/todos/create', methods=['POST'])
  @requires_auth('create: todo')
  def create_todo(jwt):
    error = False
    body = {}
    try:
      if GLOBAL_ID is None:
        list_num = request.get_json['list_id']
      else:
        list_num = GLOBAL_ID
      description = request.get_json()['description']
      todo = (Todo(description=description, completed=False, list_id=list_num))
      todo.insert()
      body['description'] = todo.description
    except:
      error = True
      print(sys.exc_info())
    if error:
        abort (422)
    else:
        return jsonify(body), 200

  #route, handles when a list is completed
  @app.route('/lists/<list_id>/set-completed', methods=['POST'])
  @requires_auth('complete: todolist')
  def set_completed_list(jwt, list_id):
    try:
      headers = header
      completed = request.get_json()['completed']
      todoList = TodoList.query.get(list_id)
      todoList.completed = completed
      for todo in todoList.todos:
        todo.completed = completed
      todoList.update()
    except:
      abort(422)
    return redirect(url_for('index', header=headers)), 200

  #route, handles when a task is completed
  @app.route('/todos/<todo_id>/set-completed', methods=['POST'])
  @requires_auth('complete: todo')
  def set_completed_todo(jwt, todo_id):
    try:
      headers = header
      completed = request.get_json()['completed']
      todo = Todo.query.get(todo_id)
      todo.completed = completed
      todo.update()
    except:
      abort(422)
    return redirect(url_for('index', header=headers)), 200

  @app.route('/lists/<list_button_id>/button-clicked', methods=['DELETE'])
  @requires_auth('delete: todolist')
  def remove_list(jwt, list_button_id):
    try:
      headers = header
      todolist = TodoList.query.get(list_button_id)
      if todolist is None:
        abort(404)
      for todo in todolist.todos:
        todo.delete()
      todolist.delete()
    except Exception as e:
      print(e)
      abort(422)
    return jsonify({
            'success': True,
            'deleted_list_button_id': list_button_id
        }), 200

  @app.route('/todos/<button_id>/button-clicked', methods=['DELETE'])
  @requires_auth('delete: todo')
  def remove_todo(jwt, button_id):
    try:
      headers = header
      todo = Todo.query.get(button_id)
      if todo is None:
        abort(404)
      todo.delete()
    except Exception as e:
      print(e)
      abort(422)
    return jsonify({
            'success': True,
            'deleted_button_id': button_id
        }), 200

  #method to render index.html template
  @app.route('/lists/<list_id>', methods=['GET'])
  def get_list_todos(list_id):
      global GLOBAL_ID
      GLOBAL_ID = list_id
      if TodoList.query.get(list_id) is None:
        return jsonify({
          'success': False,
          'error': 404,
          'message': 'Not found'
        }), 404
      else:
        return render_template(
          'index.html', 
          lists = TodoList.query.all(),
          active_list=TodoList.query.get(list_id),
          todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
        ), 200

  #GET: get an existing to-do
  @app.route('/todos/<todo_id>', methods=['GET'])
  def get_todo(todo_id):
    try:
      if Todo.query.get(todo_id) is None:
        return jsonify({
          'success': False,
          'error': 404,
          'message': 'Not found'
        }), 404
      else:
        event = Todo.query.get(todo_id)
        formatted_event = format_todo(event)
        return formatted_event
    except Exception as e:
      print(e)
      abort(403)


  #PATCH: edit an existing to-do
  @app.route('/todos/<todo_id>', methods=['PATCH'])
  @requires_auth('update: todo')
  def update_todo(jwt, todo_id):
    try:
      body = request.get_json()
      todo = Todo.query.filter(Todo.id == todo_id).one_or_none()
      description = body.get('description')
      todo.description = description
      todo.update()
      formatted_todo = format_todo(todo)
      return formatted_todo
    except Exception as e:
        print(e)
        abort(403)
  
  #error handling
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404
  
  @app.errorhandler(AuthError)
  def not_authorized(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code


  @app.route('/', methods=['GET'])
  def index():
    headers = header
    return redirect(url_for('login', header=headers))
  
  return app

app = create_app()

if __name__ == '__main__':
    app.run()
      
