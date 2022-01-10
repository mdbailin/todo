from flask import Flask, url_for, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask.templating import render_template
from flask_migrate import Migrate
import sys
import json

from sqlalchemy.orm import session



GLOBAL_ID = 1

#create app instance, config, db instance, and migrate instance
app = Flask(__name__)
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


@app.route('/lists/create', methods=['POST'])
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


#route, POST wrapper over create_todo() method, try/catch block in case POST fails
@app.route('/todos/create', methods=['POST'])
def create_todo():
  error = False
  body = {}
  try:
    description = request.get_json()['description']
    todo = Todo(description=description, list_id=GLOBAL_ID)
    print(todo)
    print(todo.list_id)
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
@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    global GLOBAL_ID
    GLOBAL_ID = list_id
    return render_template('index.html', 
    lists = TodoList.query.all(),
    active_list=TodoList.query.get(list_id),
    todos=Todo.query.filter_by(list_id=list_id).order_by('id')
    .all()
    )

@app.route('/')
def index():
  return redirect(url_for('get_list_todos', list_id=1))
    
