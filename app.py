from importlib.metadata import requires
from pickle import GLOBAL
from flask import Flask, url_for, request, redirect, jsonify, abort, session, _request_ctx_stack
from flask_sqlalchemy import SQLAlchemy
from flask.templating import render_template
from flask_migrate import Migrate
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
  CORS(app)

  @app.errorhandler(AuthError)
  def handle_auth_error(ex):
      response = jsonify(ex.error)
      response.status_code = ex.status_code
      return response

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                          'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                          'GET,PATCH,POST,DELETE,OPTIONS')
    print(response)
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
      access_token_url='https://dev-lzgwqs5u.us.auth0.com/oauth/token',
      authorize_url='https://dev-lzgwqs5u.us.auth0.com/authorize',
      client_kwargs={
          "scope": "openid profile email",
      },
      server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
  )

  #create app instance, config, db instance, and migrate instance
  #set up database
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://matthewbailin@localhost:5432/todo_db'
  db = SQLAlchemy(app)
  migrate = Migrate(app, db)

  #create parent schema 
  class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, 
      default=False)
    todos = db.relationship('Todo', cascade='all,delete', backref='list', lazy='select')


  #create child schema 
  class Todo(db.Model):
      __tablename__ = 'todos'
      id = db.Column(db.Integer, primary_key=True)
      description = db.Column(db.String(), nullable=False)
      completed = db.Column(db.Boolean, nullable=False, 
      default=False)
      list_id = db.Column(db.Integer, db.ForeignKey('todolists.id', ondelete='CASCADE'), nullable=False)

      def __repr__(self):
          return f'<Todo {self.id} {self.description}>'

  @app.route("/login")
  def login():
      return oauth.auth0.authorize_redirect(
          redirect_uri=url_for("callback", _external=True)
      )
  @app.route("/callback", methods=["GET", "POST"])
  def callback():
      token = oauth.auth0.authorize_access_token()
      session["user"] = token
      # print(session["user"]["access_token"])
      # token['id_token'] = env.get('ADMIN_JWT')
      return redirect(url_for('get_list_todos', list_id=70))
      
  def format_todo(event):
      return {
          "description": event.description,
          "id": event.id,
          "completed": event.completed,
          "list_id": event.list_id
      }


  @app.route('/lists/create', methods=['POST'])
  # @requires_auth('create: todolist')
  def create_todo_list():
    list_error = False
    body = {}
    try:
      name = request.get_json()['name']
      list = TodoList(name=name)
      db.session.add(list)
      db.session.commit()
      body['name'] = list.name
    except:
      list_error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
        db.session.close()
    if list_error:
        abort (400)
    else:
        return jsonify({name: list.name})
    
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


  #route, POST wrapper over create_todo() method, try/catch block in case POST fails
  @app.route('/todos/create', methods=['POST'])
  # @requires_auth('create:todo')
  def create_todo():
    error = False
    body = {}
    try:
      list_num = GLOBAL_ID
      description = request.get_json()['description']
      todo = Todo(description=description, list_id=list_num)
      db.session.add(todo)
      db.session.commit()
      body['description'] = todo.description
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort (400)
    else:
        return jsonify(body)

  #route, handles when a list is completed
  @app.route('/lists/<list_id>/set-completed', methods=['POST'])
  def set_completed_list(list_id):
    try:
      completed = request.get_json()['completed']
      todoList = TodoList.query.get(list_id)
      todoList.completed = completed
      for todo in todoList.todos:
        todo.completed = completed
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()
    return redirect(url_for('index'))

  #route, handles when a task is completed
  @app.route('/todos/<todo_id>/set-completed', methods=['POST'])
  def set_completed_todo(todo_id):
    try:
      completed = request.get_json()['completed']
      todo = Todo.query.get(todo_id)
      todo.completed = completed
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()
    return redirect(url_for('index'))

  @app.route('/lists/<list_button_id>/button-clicked', methods=['DELETE'])
  def remove_list(list_button_id):
    try:
      todolist = TodoList.query.get(list_button_id)
      for todo in todolist.todos:
        db.session.delete(todo)
      db.session.delete(todolist)
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close()
    return redirect(url_for('index'))


  @app.route('/todos/<button_id>/button-clicked', methods=['DELETE'])
  def remove_todo(button_id):
    try:
      todo = Todo.query.get(button_id)
      todo.query.filter_by(id=button_id).delete()
      db.session.commit()
    except:
      db.session.rollback()
    finally:
      db.session.close
    return redirect(url_for('index'))

  #method to render index.html template
  @app.route('/lists/<list_id>', methods=['GET'])
  def get_list_todos(list_id):
      global GLOBAL_ID
      GLOBAL_ID = list_id
      print("global id is", GLOBAL_ID)
      return render_template(
        'index.html', 
        lists = TodoList.query.all(),
        active_list=TodoList.query.get(list_id),
        todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
      )

  #PATCH: edit an existing to-do
  @app.route('/todos/<todo_id>', methods=['PATCH'])
  def update_todo(todo_id):
    request_params = request.get_json()
    event = db.session.query(Todo).filter_by(id=todo_id).first()
    formatted_event = format_todo(event)
    description = request_params['description']
    formatted_event.update(dict(description = description))
    db.session.commit()
    return formatted_event

  @app.route('/', methods=['GET'])
  def index():
    return redirect(url_for('login'))
  
  return app

app = create_app()

if __name__ == '__main__':
    app.run()
      
