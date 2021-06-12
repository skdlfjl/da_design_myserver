from flask import Flask
from flask import request
import os
from src import user, mylogger, myconfig
import pdb
import datetime

app = Flask(__name__)

# create a logger.
project_root_path = os.getenv("DA_DESIGN_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(
    project_root_path))
log_directory = cfg['logger'].get('log_directory')
loggers = dict()
loggers['login'] = mylogger.get_logger('login', log_directory)
loggers['schedule'] = mylogger.get_logger('schedule', log_directory)
loggers['recipe'] = mylogger.get_logger('recipe', log_directory)


@app.route('/login', methods=["POST"])
def login():
    """login API function.

    Specification can be found in `API.md` file.

    :return: JSON serialzed string containing the login result with session_id
    :rtype: str
    """
    #pdb.set_trace()

    user_id = request.json.get('user_id')
    passwd = request.json.get('passwd')
    loggers['login'].info('{}: login'.format(user_id))

    ret = {"result": None,
        "session_id": None,
        "msg": ""}

    session_key = user.login(user_id, passwd, loggers['login'])
    loggers['login'].info('{}: session_key = {}'.format(user_id, session_key))
    if not session_key:
        ret["result"] = False
        ret["msg"] = "Failed to login"
    else:
        ret["result"] = True
        ret["session_id"] = session_key["session_id"]

    #pdb.set_trace()
    loggers['login'].info('{}: login result = {}'.format(user_id, ret))
    return ret


@app.route('/main', methods=["POST"])
def main():
    """main (schedule) API function.

    Specification can be found in `API.md` file.

    :return: JSON serialized string containing the result with session_id
    :rtype: str
    """
    session_id = request.json.get('session_id')
    request_type = request.json.get('request_type')
    loggers['main'].info('{}: main(schedule) with request type = {}'.format(
        session_id, request_type))

    ret = {"result": None,
        "msg": ""}

    if request_type == 'schedule_add' or request_type == 'recipe_add':
        what_time_is_it = datetime.datetime.now()
        doc_user = user.check_session(session_id,
                what_time_is_it.timestamp())
        if not doc_user:
            msg = '{}: Invalid session'.format(session_id)
            loggers['main'].error(msg)
            ret['result'] = False
            ret['msg'] = msg
        else:
            if request_type == 'schedule_add':
                main = request.json.get('main_schedule')
                how_many_added = user.add_schedule(doc_user, main, loggers['main_schedule'])
            elif request_type ==  'recipe_add':
                main = request.json.get('main_recipe')
                how_many_added = user.add_recipe(doc_user, main, loggers['main_recipe'])


            new_session = user.generate_session(doc_user)
            if how_many_added:
                msg = '{}: {} main items added'.format(
                        session_id, how_many_added)
                ret['result'] = True
            else:
                msg = '{}: No main items added'.format(
                    session_id)
                ret['result'] = False
            ret['msg'] = msg
            ret['session_id'] = new_session["session_id"]
    elif request_type == 'get':
        pass
    else:
        msg = '{}: Invalid request type = {}'.format(
                session_id, request_type)
        loggers['main'].error(msg)
        ret['result'] = False
        ret['msg'] = msg

    loggers['main'].info('{}: main result = {}'.format(
        session_id, ret))
    return ret

