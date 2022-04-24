import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from app import create_app
from models import setup_db, TodoList, Todo

from os import environ as env
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

token = {'Authorization': env.get('ADMIN_JWT')}
viewer_token = {'Authorization': env.get('VIEWER_JWT')}

todo_patch = {'description': 'walk dogs'}
new_list = {'id': 100, 'name': 'Finances', 'completed': False}
new_todo = {'description': 'check if lists are working', 'list_id': 70}
checked = {'completed': False}


class BookTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        setup_db(self.app)

        self.new_todolist = {"id": "70", "name": "Unorganized", "completed": False}
        self.new_todolist = {"id": "100", "name": "Finances", "completed": False}

        self.new_todo = {"id": 1, "description": "walk dog", "completed": False, "list_id": 70}
        self.new_todo = {"id": 2, "description": "take out trash", "completed": False, "list_id": 70}
        self.new_todo = {"id": 3, "description": "pay bills", "completed": False, "list_id": 100}
        self.new_todo = {"id": 4, "description": "save for college", "completed": False, "list_id": 100}

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass
    
    def test_get_todo(self):
        """tests whether we get a valid todo"""
        res = self.client().get('todos/126')
        self.assertEqual(res.status_code, 200)
    
    def test_404_sent_requesting_invalid_todo(self):
        """tests whether a 404 error occurs if we request an invalid todo"""
        res = self.client().get('/todos/1000')
        data = json.loads(res.data)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'Not found')

        self.assertEqual(res.status_code, 404)

    def test_get_paginated_books(self):
        """Test whether we get Unorganized list"""
        res = self.client().get('/lists/70')
        self.assertEqual(res.status_code, 200)
    
    def test_404_sent_requesting_beyond_valid_page(self):
        """tests whether a 404 error occurs if we request an invalid page"""
        res = self.client().get('/lists/1000')
        data = json.loads(res.data)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'Not found')

        self.assertEqual(res.status_code, 404)

    def test_update_todo(self):
        """tests whether a todo's description is updated"""
        res = self.client().patch('todos/126', json=todo_patch, headers=token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['description'], 'walk dogs')

    def test_update_failure(self):
        """tests whether the PATCH fails because no JSON data is passed"""
        res = self.client().patch('todos/126', headers=token)
        
        self.assertEqual(res.status_code, 403)
    
    def test_create_list(self):
        """tests whether a list is created"""
        res = self.client().post('lists/create', json=new_list, headers=token)
        
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['name'], 'Finances')

    def test_create_list_failure(self):
        """tests whether the POST returns 422 if no data is provided"""
        res = self.client().post('lists/create', headers=token)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_create_todo(self):
        """tests whether a todo is created"""
        res = self.client().post('todos/create', json=new_todo, headers=token)
        
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['description'], 'check if lists are working')
    
    def test_create_todo_failure(self):
        """tests whether the POST returns 422 if no data is provided"""
        res = self.client().post('todos/create', headers=token)
        
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_check_list(self):
        """tests whether an existing list can be properly checkmarked"""

        res = self.client().post('lists/70/set-completed', json=checked, headers=token)
        self.assertEqual(res.status_code, 200)
    
    def test_check_list_failure(self):
        """tests whether the POST returns 422 if no data is provided"""
        res = self.client().post('lists/70/set-completed', headers=token)
        
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_check_todo(self):
        """tests whether an existing todo can be properly checkmarked"""

        res = self.client().post('todos/126/set-completed', json=checked, headers=token)
        self.assertEqual(res.status_code, 200)
    
    def test_check_todo_failure(self):
        """tests whether the POST returns 422 if no data is provided"""
        res = self.client().post('todos/126/set-completed', headers=token)
        
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')

    def test_delete_todolist (self):
        """tests if list can be deleted"""
        res = self.client().delete('lists/144/button-clicked', headers=token)
        data = json.loads(res.data)

    
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['deleted_list_button_id']))
    
    def test_delete_todolist_failure (self):
        """tests whether DELETE returns 404 if a list that doesn't exist is entered"""
        res = self.client().delete('lists/1000/button-clicked', headers=token)
        self.assertEqual(res.status_code, 422)

        data = json.loads(res.data)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    def test_delete_todo (self):
        """tests if todo can be deleted"""
        res = self.client().delete('todos/192/button-clicked', headers=token)
        data = json.loads(res.data)

    
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['deleted_button_id']))
    
    def test_delete_todo_failure (self):
        """tests whether DELETE returns 404 if a list that doesn't exist is entered"""
        res = self.client().delete('todos/1000/button-clicked', headers=token)
        self.assertEqual(res.status_code, 422)

        data = json.loads(res.data)

        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], 'unprocessable')
    
    #user tests on Viewer, each should fail because the viewer has no special permissions

    def test_viewer_patch(self):
        """tests whether viewer is unable to patch a todo because of missing permissions"""
        res = self.client().patch('todos/126', headers=viewer_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(data['message']['description'], 'Permission not found.')
    
    def test_viewer_delete(self):
        """tests whether viewer is unable to patch a todo because of missing permissions"""
        res = self.client().delete('todos/177/button-clicked', headers=viewer_token)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(data['message']['description'], 'Permission not found.')
        


    
    

    

if __name__ == "__main__":
    unittest.main()