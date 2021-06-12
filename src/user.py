import hashlib
import datetime
import pymongo
from pymongo import MongoClient
from bson.timestamp import Timestamp
import os
from src import myconfig
import pdb

project_root_path = os.getenv("DA_DESIGN_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
db_ip = cfg['db']['ip']
db_port = int(cfg['db']['port'])
db_name = cfg['db']['name']

db_client = MongoClient(db_ip, db_port)
db = db_client[db_name]

col_user = db[cfg['db']['col_user']]
col_schedule = db[cfg['db']['col_schedule']]
col_recipe = db[cfg['db']['col_recipe']]
col_main = db[cfg['db']['col_main']]

def convert_to_SHA256(x):
    """Convert a given string to SHA256-encoded string.

    :param x: arbitrary string.
    :type x: str
    :return: SHA256 encoded string
    :rtype: str
    """
    result = hashlib.sha256(x.encode())
    result = result.hexdigest()
    return result

def convert_to_bson_timestamp(ts):
    """Convert a given timestamp (of datetime) to bson Timestamp.

    :param ts: datetime timestamp
    :type ts: float
    :return: bson Timestamp
    :rtype: bson.timestamp.Timestamp
    """
    lowpart = int(ts)
    return Timestamp(lowpart, 1)

def check_passwd(userid, passwd):
    """Check if the password is correct or not.

    :param userid: user ID
    :type userid: str
    :param passwd: password
    :type passwd: str
    :return: user document (DB) or False
    :rtype: dict or bool
    """
    the_user = col_user.find_one({"user_id": userid})
    if not the_user:
        return False

    hashed_passwd = convert_to_SHA256(passwd)
    db_passwd = the_user['passwd']
    if hashed_passwd != db_passwd:
        return False
    return the_user

def generate_session(doc_user):
    """Generate session key.

    :param doc_user: user's document (DB)
    :type doc_user: dict
    :return: session key dictionary
    :rtype: dict
    """
    raw_string = doc_user["user_id"] + str(datetime.datetime.now())
    new_session_id = convert_to_SHA256(raw_string)
    i = 1
    while True:
        exist_session = col_user.find_one({"session_key.session_id": new_session_id})
        if not exist_session:
            break
        raw_string = doc_user["user_id"] + str(datetime.datetime.now()) * (i+1)
        new_session_id = convert_to_SHA256(raw_string)
        i += 1

    timestamp = datetime.datetime.now()
    timestamp = convert_to_bson_timestamp(timestamp.timestamp())
    doc_user["session_key"] = {"session_id": new_session_id,
            "timestamp": timestamp}
    col_user.find_one_and_replace({"user_id": doc_user["user_id"]}, doc_user)
    return doc_user["session_key"]

def check_session(session_id, timestamp, elapse_limit=60):
    """Check if the session is valid.

    :param session_id: session ID
    :type session_id: str
    :param timestamp: timestamp (usually, this is current timestamp)
    :type timestamp: float
    :param elapse_limit: time limit for checking session validity
    :type elapse_limit: int
    :return: user document (DB) or False
    :rtype: dict or bool
    """
    the_user = col_user.find_one({"session_key.session_id": session_id})
    if not the_user:
        return False

    the_timestamp = the_user["session_key"].get("timestamp")
    current_timestamp = convert_to_bson_timestamp(timestamp)

    elapsed = current_timestamp.time - the_timestamp.time
    if elapsed >= elapse_limit:
        return False
    return the_user

def login(user_id, passwd, logger):
    """Login.

    :param user_id: user ID
    :type user_id: str
    :param passwd: password
    :type passwd: str
    :param logger: Logger instance
    :type logger: logging.Logger
    :return: session_key or False
    :rtype: dict or bool
    """
    doc_user = check_passwd(user_id, passwd)
    if not doc_user:
        logger.info("Invalid user ID or password")
        return False

    session_key = generate_session(doc_user)
    if not session_key:
        logger.error("Failed to generate session of user {}".format(user_id))
        return False

    return session_key


def add_schedule(doc_user, mains, logger, main_limit=10):
    my_mains = col_main.find_one({"User": doc_user["_id"]})
    if my_mains == None:
        logger.info('{}: a main(schedule) list created'.format(
            doc_user["user_id"]))
        my_mains = {"User": doc_user["_id"],
            "Schedule": []}
        col_main.insert_one(my_mains)
    if len(my_mains["Schedule"]) >= main_limit:
        logger.info('{}: main(schedule) list is already full'.format(
            doc_user["user_id"]))
        return 0

    ret = 0
    for m in mains:
        doc_schedule = col_schedule.find_one({"title": m})
        if not doc_schedule:
            continue
        if doc_schedule["_id"] in my_mains["Schedule"]:
            continue
        my_mains["Schedule"] += [doc_schedule["_id"]]
        logger.info('{}: {} added into main list'.format(
            doc_user["user_id"], m))
        ret += 1

    if ret >= 1:
        col_main.find_one_and_replace({"User": doc_user["_id"]}, my_mains)

    return ret



def add_recipe(doc_user, mains, logger, main_limit=10):
    my_mains = col_main.find_one({"User": doc_user["_id"]})
    if my_mains == None:
        logger.info('{}: a main(recipe) list created'.format(
            doc_user["user_id"]))
        my_mains = {"User": doc_user["_id"],
            "Recipe": []}
        col_main.insert_one(my_mains)
    if len(my_mains["Recipe"]) >= main_limit:
        logger.info('{}: main(recipe) list is already full'.format(
            doc_user["user_id"]))
        return 0

    ret = 0
    for m in mains:
        doc_recipe = col_recipe.find_one({"name": m})
        if not doc_recipe:
            continue
        if doc_recipe["_id"] in my_mains["Recipe"]:
            continue
        my_mains["Recipe"] += [doc_schedule["_id"]]
        logger.info('{}: {} added into main list'.format(
            doc_user["user_id"], m))
        ret += 1

    if ret >= 1:
        col_main.find_one_and_replace({"User": doc_user["_id"]}, my_mains)

    return ret

