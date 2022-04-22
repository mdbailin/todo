from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#create app instance, config, db instance, and migrate instance
#set up database
db = SQLAlchemy()


def setup_db(app):
    '''binds a flask application and a SQLAlchemy service'''
    app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://matthewbailin@localhost:5432/todo_db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)

#create parent schema 
class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, 
    default=False)
    todos = db.relationship('Todo', cascade='all,delete', backref='list', lazy='select')

    def __init__(self, name):
        self.name = name
    
    def insert(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

#create child schema 
class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, 
    default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, description, completed, list_id):
        self.description = description
        self.completed = completed
        self.list_id = list_id

    def insert(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'