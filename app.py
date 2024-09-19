from flask import Flask, render_template, request, redirect, url_for, jsonify, session # For flask implementation
from bson import ObjectId # For ObjectId to work
from pymongo import MongoClient
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
title = "TODO Application"
# heading = "TODO App with Flask and MongoDB-Pushkar"
heading = "TODO App by:Pushkar "
app.secret_key = "pushkar_secret_key"

client = MongoClient("mongodb://127.0.0.1:27017") #host uri
db = client.mymongodb    #Select the database
todos = db.todo #Select the collection name
users = db.users

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/login")  # Redirect to login page if not logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data from the request
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if the user already exists
        if users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 400

        # Hash the password before saving it
        hashed_password = generate_password_hash(password)

        # Insert the user into the database
        users.insert_one({
            "email": email,
            "password": hashed_password
        })

        return redirect("/login")  # Redirect to login after successful registration
    
    # Render the registration form
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login submission
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Find the user in the database
        user = users.find_one({"email": email})
        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Set a session for the user
        session['user_id'] = str(user['_id'])  # Using Flask session
        return redirect("/list")
    
    # If it's a GET request, render the login form
    return render_template("login.html")

@app.route("/logout", methods=['GET'])
def logout():
    # Clear the session to log the user out
    session.clear()
    return redirect("/login")


def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')


@app.route("/list")
@login_required
def lists():
    # Display the all Tasks for the logged-in user
    user_id = session['user_id']
    todos_l = todos.find({"user_id": ObjectId(user_id)})  # Filter tasks by user_id
    a1 = "active"
    return render_template('index.html', a1=a1, todos=todos_l, t=title, h=heading)


@app.route("/")
@app.route("/uncompleted")
@login_required
def tasks():
    # Display the Uncompleted Tasks for the logged-in user
    user_id = session['user_id']
    todos_l = todos.find({"done": "no", "user_id": ObjectId(user_id)})  # Filter by user_id
    a2 = "active"
    return render_template('index.html', a2=a2, todos=todos_l, t=title, h=heading)


@app.route("/completed")
@login_required
def completed():
    # Display the Completed Tasks for the logged-in user
    user_id = session['user_id']
    todos_l = todos.find({"done": "yes", "user_id": ObjectId(user_id)})  # Filter by user_id
    a3 = "active"
    return render_template('index.html', a3=a3, todos=todos_l, t=title, h=heading)

@app.route("/done")
@login_required
def done():
    # Done-or-not ICON
    id = request.values.get("_id")
    user_id = session['user_id']
    task = todos.find_one({"_id": ObjectId(id), "user_id": ObjectId(user_id)})  # Ensure the task belongs to the user
    if task:
        if task["done"] == "yes":
            todos.update_one({"_id": ObjectId(id)}, {"$set": {"done": "no"}})
        else:
            todos.update_one({"_id": ObjectId(id)}, {"$set": {"done": "yes"}})
    redir = redirect_url()
    return redirect(redir)

# @app.route("/action", methods=['POST'])
# def action ():
# 	#Adding a Task
# 	name=request.values.get("name")
#     print("name", name)
# 	desc=request.values.get("desc")
#     print("desc", desc)
# 	date=request.values.get("date")
#     print("date", date)
# 	pr=request.values.get("pr")
#     print("pr", pr)
# 	todos.insert({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
# 	return redirect("/list")

@app.route("/action", methods=['POST'])
@login_required
def action():
    # Adding a Task
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("date")
    pr = request.values.get("pr")
    user_id = session['user_id']  # Get the logged-in user's ID from the session
    try:
        todos.insert_one({
            "name": name, 
            "desc": desc, 
            "date": date, 
            "pr": pr, 
            "done": "no", 
            "user_id": ObjectId(user_id)  # Store the user ID with the task
        })
    except Exception as E:
        print("Exception:", E)
    return redirect("/list")

@app.route("/remove")
@login_required
def remove():
    # Deleting a Task for the logged-in user
    key = request.values.get("_id")
    user_id = session['user_id']
    try:
        todos.delete_one({"_id": ObjectId(key), "user_id": ObjectId(user_id)})  # Ensure the task belongs to the user
    except Exception as E:
        print("Error:", E)
    return redirect("/")

@app.route("/update")
@login_required
def update ():
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	return render_template('update.html',tasks=task,h=heading,t=title)

@app.route("/action3", methods=['POST'])
@login_required
def action3():
    # Updating a Task with various references
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("date")
    pr = request.values.get("pr")
    id = request.values.get("_id")
    user_id = session['user_id']  # Get the logged-in user's ID from the session

    # Ensure that the task being updated belongs to the logged-in user
    task = todos.find_one({"_id": ObjectId(id), "user_id": ObjectId(user_id)})
    
    if task:
        todos.update_one(
            {"_id": ObjectId(id), "user_id": ObjectId(user_id)},
            {'$set': {"name": name, "desc": desc, "date": date, "pr": pr}}
        )
        return redirect("/list")
    else:
        return jsonify({"error": "Task not found or you don't have permission to update it"}), 404


@app.route("/search", methods=['GET'])
@login_required
def search():
    # Searching for a Task with various references
    key = request.values.get("key")
    print("key",key)
    refer = request.values.get("refer")
    print("refer",refer)
    user_id = session['user_id']  # Get the logged-in user's ID from the session
    print("user_id ",user_id)

    # Build the query, ensuring it filters by user_id
    query = {"user_id": ObjectId(user_id)}

    if refer == "_id":
        # If searching by _id, ensure it's a valid ObjectId
        try:
            query["_id"] = ObjectId(key)
        except Exception:
            return jsonify({"error": "Invalid ID format"}), 400
    else:
        # Otherwise, search by other field references
        query[refer] = key

    # Find the tasks that match the query and belong to the logged-in user
    todos_l = todos.find(query)
    
    return render_template('searchlist.html', todos=todos_l, t=title, h=heading)


if __name__ == "__main__":
    app.run()