import sys
import datetime
import pdb

def test_logger():
    """Test logger.

    :return: test result.
    :rtype: bool
    """
    from src import mylogger
    try:
        m = mylogger.get_logger('test', '/root/da_design_myserver/log')
        m.debug('hi, debug')
    except Exception as e:
        print(e)
        return False
    return True

def test_config():
    """Test config.

    :return: test result.
    :rtype: bool
    """
    from src import myconfig
    try:
        m = myconfig.get_config('/root/da_design_myserver/share/test.config')
        print('key1=', m['general'].get('key1'))
        print('key2=', m['general'].get('key2'))
        print('key3=', m['logger'].get('key3'))
    except Exception as e:
        print(e)
        return False
    return True

def test_login(db):
    """Test login process.

    :param db: Database
    :type db: database instance
    :return: test result
    :rtype: bool
    """
    from src import user
    col_user = db['User']
    doc_user = user.check_passwd(col_user, 'skdlfjl', 'biggong')
    if not doc_user:
        return False
    print("Login test for user = ", doc_user["user_id"])

    session_key = user.generate_session(doc_user, col_user)
    if not session_key:
        return False
    print("generated session = {}".format(session_key))

    what_time_is_it = datetime.datetime.now()
    doc_user_result = user.check_session(col_user,
            session_key["session_id"],
            what_time_is_it.timestamp())
    if not doc_user_result:
        return False
    print("session user = {}".format(doc_user_result["user_id"]))
    return True



if __name__ == '__main__':
    target_step = []
    if len(sys.argv) >= 2:
        target_step = sys.argv[1].split(',')
    print('Test steps = ', target_step)

    import pymongo
    from pymongo import MongoClient
    db_info = {
        'ip': '127.0.0.1',
        'port': 27017,
        'db': 'JiHee_DB_design'}
    db_client = MongoClient(db_info['ip'], db_info['port'])
    db = db_client[db_info['db']]
    print('Success - DB connection')


    if not target_step or 'logger' in target_step:
        ret = test_logger()
        if not ret:
            raise Exception('Error when test_logger')
        print('Success - test_logger')

    if not target_step or 'config' in target_step:
        ret = test_config()
        if not ret:
            raise Exception('Error when test_config')
        print('Success - test_config')
    
    if not target_step or 'login' in target_step:
        if not db:
            raise Exception('Error when test_login (due to DB connection)')
        ret = test_login(db)
        if not ret:
            raise Exception('Error when test_login')
        print('Success - test_login')
        
    print('Test completed.')
