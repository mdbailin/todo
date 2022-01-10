Todo App
-----

## Introduction

Here is a simple application for writing todo lists. This app has backend capabilities and uses SQLalchemy to manage a relational database, as well as Migrate for version control. The app allows you to create multiple lists, and "check" and delete all items in a list at once by checking/deleting the list itself. The database was made using PostGRESql.



## Main Files: Project Structure

  ```sh
  ├── README.md
  ├── app.py 
  ├── migrations (you will fill these in with your own version control)
  └── templates
      ├── index.html
  ```

## How to run

Download the repository from Github, and in the project's path, run

```
FLASK_APP=app.py FLASK_DEBUG=true flask run
```

from your terminal.