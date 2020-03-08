from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, url_for
from functools import wraps

import json
import os

#load process constructor
from backend.core.redis.rediz_workers import processworkerprocess

#load redis
from backend.core.redis.rediz import rediz

#load config
from backend.core.confload.confload import config
from backend.core.redis.rediz import rediz

#load routes
from backend.core.routes.routes import routes

app = Flask(__name__)
app.secret_key = os.urandom(12)

#login decorator
def login_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == config().apikey:
            return view_function(*args, **kwargs)
        else:
          return redirect(url_for('denied'))
    return decorated_function

#utility route - denied
@app.route("/denied", methods = ['GET', 'POST'])
def denied():
  response_object = {
    'status': 'error',
        'data': {
            'response': 'forbidden'
        }
    }
  return jsonify(response_object), 401

#utility route - error
@app.route("/error", methods = ['GET', 'POST'])
def error():
  status_code = request.args.get("status_code", False)
  err = request.args.get("error", False)
  response_object = {
    'status': 'error',
        'data': {
            'task_result': str(err)
        }
    }
  return jsonify(response_object), status_code

#deploy a configuration
@app.route("/setconfig", methods = ['POST'])
@login_required
def setconfig():
  try:
    if request.method == 'POST':
      req_data = request.get_json()
      host = req_data.get("host", False)
      reds.check_and_create_q_w(hst=host)
      r = reds.sendtask(q=host,exe='setconfig',kwargs=req_data)
      resp = jsonify(r)
      return resp, 201
    else:
      return redirect(url_for('error', error="POST required", status_code=500))
  except Exception as e:
    return redirect(url_for('error', error=e, status_code=500))
    pass

#get specific task 
@app.route("/task/<task_id>", methods=['GET'])
@login_required
def get_status(task_id):
  try:
    r = reds.fetchtask(task_id=task_id)
    if r:
      resp = jsonify(r)
      return resp, 200
    else:
      return redirect(url_for('error', error="task not foud", status_code=404))
  except Exception as e:
    return redirect(url_for('error', error=str(e), status_code=500))
    pass

#get all tasks in queue
@app.route("/taskqueue/", methods=['GET'])
@login_required
def get_tasklist():
  try:
    r = reds.getjoblist(q=False)
    if r:
      resp = jsonify(r)
      return resp, 200
  except Exception as e:
    return redirect(url_for('error', error=str(e), status_code=500))
    pass

#task view route for specific host
@app.route("/taskqueue/<host>", methods=['GET'])
@login_required
def get_host_tasklist(host):
  try:
    r = reds.getjobliststatus(q=host)
    if r:
      resp = jsonify(r)
      return resp, 200
    else:
      return redirect(url_for('error', error="host not foud", status_code=404))
  except Exception as e:
    return redirect(url_for('error', error=str(e), status_code=500))
    pass


#read config
@app.route("/getconfig", methods = ['POST'])
@login_required
def getconfig():
  try:
    if request.method == 'POST':
      req_data = request.get_json()
      host = req_data.get("host", False)
      reds.check_and_create_q_w(hst=host)
      r = reds.sendtask(q=host,exe='getconfig',kwargs=req_data)
      resp = jsonify(r)
      return resp, 201
    else:
      return redirect(url_for('error', error="POST required", status_code=500))
  except Exception as e:
    return redirect(url_for('error', error=str(e), status_code=500))
    pass


#template routes
@app.route("/template", methods = ['GET', 'POST', 'DELETE'])
@login_required
def template():
  try:
    if request.method == 'GET':
      r = routes["gettemplate"]()
      resp = jsonify(r)
      return resp, 200
    elif request.method == 'POST':
      req_data = request.get_json()
      r = routes["addtemplate"](kwargs=req_data)
      resp = jsonify(r)
      return resp, 201
    elif request.method == 'DELETE':
      req_data = request.get_json()
      r = routes["removetemplate"](kwargs=req_data)
      resp = jsonify(r)
      return resp, 200
      #return redirect(url_for('error', error="GET required", status_code=500))
  except Exception as e:
    return redirect(url_for('error', error=str(e), status_code=500))
    pass

if __name__ == '__main__':
   processworkerprocess()
   reds = rediz()
   app.run(host=config().listen_ip, port=config().listen_port, debug=True, threaded=True)