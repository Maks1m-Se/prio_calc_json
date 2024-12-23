from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import pandas as pd
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

print('Test ############ Script working')

# Set the working directory to the directory of the script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# File path for JSON storage
JSON_FILE = 'data.json'



### Global Vars and Funcs ###
attribute = "Importance"
tasks_list = []
first_task = ''
reset_task_scores = False



#### Helper functions ####

# Init file for data
def initialize_data_file():
    """Ensures the data.json file starts empty."""
    with open(JSON_FILE, 'w') as file:
        json.dump({"tasks": []}, file, indent=4)
    print("data.json file initialized to empty structure.")  # Debugging


# READ from JSON
def read_tasks():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as file:
            json.dump({"tasks": []}, file)
    with open(JSON_FILE, 'r') as file:
        print('Tasks file read:', file)  # Debugging
        return json.load(file)

# WRITE to JSON
def write_tasks(data):
    with open(JSON_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# GET ALL tasks
def get_all_tasks():
    data = read_tasks()
    return data['tasks']

# ADD a task
def add_task(name):
    data = read_tasks()
    new_task = {
        "id": len(data['tasks']) + 1,
        "name": name,
        "done": False,
        "importance": 0,
        "urgency": 0,
        "effort": 0,
        "rated": {"importance": False, "urgency": False, "effort": False}
    }
    data['tasks'].append(new_task)
    write_tasks(data)

# UPDATE a task
def update_task(task_id, updates):
    data = read_tasks()
    for task in data['tasks']:
        if task['id'] == task_id:
            task.update(updates)
            break
    write_tasks(data)

# Get task names from JSON
def get_tasks_list():
    """Retrieve the list of task names from the JSON file."""
    tasks = get_all_tasks()
    return [task['name'] for task in tasks]



#### ROUTES ####
#Main Page
@app.route('/')
def index():
    global tasks_list, reset_task_scores
    print('\nINDEX PAGE') # Debugging

    tasks_list = get_tasks_list()
    print('Task List:\n', tasks_list) # Debugging

    # Placeholder for todo_list rendering
    todo_list = get_all_tasks()
    print("\nTodo List:", todo_list, '\n')  # Debugging

    reset_task_scores = True
    print('reset_task_scores: ', reset_task_scores)
    
    return render_template('index.html', title='Main Page',
                           todo_list=todo_list)

# Return to Main Page
@app.route('/return_to_index', methods=['POST'])
def return_to_index():
    return render_template('index.html', title='Main Page')


# Add Task
@app.route('/add_task', methods=['POST'])
def add_task_route():
    name = request.form.get("name")
    add_task(name)
    return redirect(url_for("index"))

# Update DONE Tasks
@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task_route(task_id):
    # Toggle the "done" status of a task
    data = read_tasks()
    for task in data['tasks']:
        if task['id'] == task_id:
            task['done'] = not task['done']
            break
    write_tasks(data)
    return redirect(url_for("index"))

# Delete Tasks
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task_route(task_id):
    data = read_tasks()
    data['tasks'] = [task for task in data['tasks'] if task['id'] != task_id]
    write_tasks(data)
    return redirect(url_for("index"))


# Evalute Tasks
@app.route('/evaluate_tasks', methods=['GET', 'POST'])
def evaluate_tasks_route():
    global tasks_list, first_task, reset_task_scores
    print('\nEVALUATE PAGE')  # Debugging

    print('reset_task_scores: ', reset_task_scores)

    data = read_tasks()

    if reset_task_scores: # resetin scores and rated states
        for task in data['tasks']:
            task['importance'] = 0
            task['urgency'] = 0
            task['effort'] = 0
            task['rated']['importance'] = False
            task['rated']['urgency'] = False
            task['rated']['effort'] = False
        write_tasks(data)
        reset_task_scores = False
        print('reset_task_scores: ', reset_task_scores)

    print('tasks_list: ', tasks_list) ###TESTING
    
    if not tasks_list:  # Check if the queue is empty
        tasks_fully_rated = [] # check if all rasks are rated (true)
        for task in data['tasks']:
            tasks_fully_rated.append(all(task['rated'].values()))
        if all(tasks_fully_rated): # if all tasks completely rate redirect
            print("All tasks have been evaluated. Redirecting to results.")
            return redirect(url_for("show_results"))  # Redirect to results page
        
        tasks_list = get_tasks_list()  # Ensure the list is initialized if empty

    if not tasks_list:  # If still empty after initialization, all tasks are done
        print("All tasks have been evaluated. Redirecting to results.")
        return redirect(url_for("show_results"))  # Redirect to results page

    # Get the first task
    first_task = tasks_list[0]
    print(f"Current Task for Evaluation: {first_task}")  # Debugging

    return render_template('evaluate.html', title='Evaluate Page', first_task=first_task, tasks=data['tasks'])


# Update Scores
@app.route('/update_scores', methods=['POST'])
def update_scores():
    global tasks_list, first_task

    print('\nUPDATE SCORES')  # Debugging

    print('Task List:\n', tasks_list) # Debugging

    rated_attribute = request.form.get("rated").lower() # Convert to lowercase for consistency
    score = int(request.form.get("value", 0))

    data = read_tasks()

    print('Rated attribute:\n', rated_attribute) # Debugging
    print('Score:\n', score) # Debugging

    for task in data['tasks']:
        if task['name'] == first_task:
            if rated_attribute == "importance":
                task['importance'] += score
                task['rated']['importance'] = True
            elif rated_attribute == "urgency":
                task['urgency'] += score
                task['rated']['urgency'] = True
            elif rated_attribute == "effort":
                task['effort'] += score
                task['rated']['effort'] = True
            break

    write_tasks(data)

    # Check if the task is fully rated
    fully_rated = all(task['rated'].values())
    if fully_rated:
        print(f"Task '{first_task}' fully rated")  # Debugging
        if tasks_list:
            tasks_list.pop(0)  # Remove the completed task from the list
            print(f"Task '{first_task}' removed from queue.")  # Debugging

    return redirect(url_for("evaluate_tasks_route"))   


@app.route('/show_results')
def show_results():
    data = read_tasks()
    sorted_tasks = sorted(data['tasks'], key=lambda t: t['importance'] + t['urgency'] - t['effort'], reverse=True)

    print("Final Results:")
    for task in sorted_tasks:
        print(f"{task['name']}: Importance={task['importance']}, Urgency={task['urgency']}, Effort={task['effort']}")

    return render_template(
        'results.html', 
        title='Task Evaluation Results', 
        tasks=sorted_tasks
    )



#### END ROUTES ####



#### Main ####
if __name__ == '__main__':
    initialize_data_file()  # Clear the data.json file on app start
    app.run(debug=True, port=5000)
