from datetime import datetime
from pymongo import MongoClient
from pymongo.cursor import CursorType

def find_item(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False})
    return result

if __name__ == '__main__':
    host = "172.17.0.2"
    port = "27017"
    mongo = MongoClient(host, int(port))
    now = datetime.now()
    setting_time = find_item(mongo, None, "alarm", "setting")
    print(setting_time)
    for i in setting_time:
        print(i)