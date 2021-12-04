from datetime import datetime
from pymongo import MongoClient
from pymongo.cursor import CursorType
import sys, json, requests
# sys.path.append('/home/ec2-user/docker/flask')
# from . import app
global flag

flag = 0

def find_item(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False})
    return result

def set_day():
    weekday_check = 0
    weekend_check = 0 
    everyday_check = 0
    day = datetime.today().weekday()
    if day > 0 & day < 5:
        weekday_check = 1
        everyday_check = 1
    else:
        weekend_check = 1
        everyday_check = 1
    return weekday_check, weekend_check, everyday_check

def check_day(user_day):
    if user_day == '평일':
        if weekday_check == 1:
            flag = 1
    elif user_day == '주말':
        if everyday_check == 1:
            flag = 1
    elif user_day == '매일':
        flag = 1

    return flag



def set_time(time):
    if time[:2] == '오전':
        user_time = 0
    elif time[:2] == '오후':
        user_time = 12
    user_time += int(time[3:-1])
    return user_time


def kakao_friends_send(message, friend_uuid):
    with open("/home/ec2-user/docker/flask/kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    print(tokens)
    friend_url = "https://kapi.kakao.com/v1/api/talk/friends"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    result = json.loads(requests.get(friend_url, headers=headers).text)
    friends_list = result.get("elements")
    send_url= "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
    data={
        'receiver_uuids':'["{}"]'.format(friend_uuid),
        "template_object": json.dumps({
            "object_type":"text",
            "text":message,
            "link":{
                "web_url":"www.naver.com"
            }
        })
    }
    print(message)
    response = requests.post(send_url, headers=headers, data=data)
    response.status_code
    print('kakao to friend sended')
        


if __name__ == '__main__':
    host = "172.17.0.2"
    port = "27017"
    now = datetime.now()
    mongo = MongoClient(host, int(port))
    weekday_check, weekend_check, everyday_check = set_day()
    setting_time = find_item(mongo, None, "alarm", "setting")
    
    for i in setting_time:
        print(i)
        flag = check_day(i['day'])
        if flag == 1:
            print(set_time(i['time']))
            print(now.hour)
            if set_time(i['time']) == now.hour:   
                kakao_friends_send('테스트', 'nquYqpmpn6qGt4W8hL2IuIu7l6GVoJemk_Q')
            
