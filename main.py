#!/usr/bin/env python
from bottle import route, run, template, get, abort, error, put
import subprocess
import json

def exec_command(cmd):
    res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return res.decode('ascii').strip()

def validate_container_name(container_name):
    if container_name not in get_containers():
        raise KeyError(container_name)

def get_containers():
    containers = exec_command(['lxc-ls','-1']).split('\n')
    return containers

def get_container_status(container_name):
    container_status = exec_command(['lxc-info', '-n', container_name, '-sH'])
    return {'name': container_name, 'status': container_status}

def start_container(container_name):
    try:
        result = exec_command(['lxc-start', '-d', '-n', container_name])
    except subprocess.CalledProcessError as cpe:
        raise RuntimeError(cpe.output.decode('ascii'))

def stop_container(container_name):
    try:
        result = exec_command(['lxc-stop', '-n', container_name])
    except subprocess.CalledProcessError as cpe:
        raise RuntimeError(cpe.output.decode('ascii'))

@error(404)
def error404(error):
    return json.dumps({'message': error.status_line})

@error(409)
def error409(error):
    return json.dumps({'message': error.body})

@error(500)
def error500(error):
    return json.dumps({'message': error.status_line})

@get('/containers')
def rest_get_containers():
    container_list = []
    for container in get_containers():
        container_list.append(get_container_status(container))
    return json.dumps(container_list)

@get('/containers/<container_name>')
def rest_get_container(container_name):
    try:
        validate_container_name(container_name)
        return get_container_status(container_name)
    except KeyError:
        abort(404)

@put('/containers/<container_name>/state/<action>')
def rest_put_container(container_name, action):
    try:
        validate_container_name(container_name)
        if action == 'start':
            start_container(container_name)
        elif action == 'stop':
            stop_container(container_name)
        elif action == 'restart':
            try:
                stop_container(container_name)
            except RuntimeError as re:
                if 'is not running' not in str(re):
                    raise
            start_container(container_name)
        return get_container_status(container_name)
    except RuntimeError as re:
        abort(409, str(re).strip())
    except KeyError:
        abort(404)
    except BaseException:
        raise

run(host='localhost', port=8080, debug=True, reloader=True)
