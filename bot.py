from datetime import datetime
from pymongo import MongoClient
from pymongo.cursor import CursorType
import sys, json, requests, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname('__file__')))+"/docker/flask/")
import app1

def find_item(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False}).sort('date')
    return result

def set_day():
    weekday_check = 0
    weekend_check = 0 
    everyday_check = 0
    day = datetime.today().weekday()
    if day > 0 and day < 5:
        weekday_check = 1
        everyday_check = 1
    else:
        weekend_check = 1
        everyday_check = 1
    return weekday_check, weekend_check, everyday_check

def check_day(user_day):
    global flag
    flag = 0
    if user_day == '평일':
        if weekday_check == 1:
            flag = 1
    elif user_day == '주말':
        if weekend_check == 1:
            flag = 1
    elif user_day == '매일':
        flag = 1
    return flag

def set_time(time):
    user_time = int(time[:-1])
    return user_time

def kakao_friends_send(message, friend_uuid):
    with open("kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    print(tokens)
    print('token check finish')
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
    print('-----------message------------')
    print(message)
    print('------------------------------')
    response = requests.post(send_url, headers=headers, data=data)
    response.status_code
    print(response)
        
def set_temp_data(local, date):
    weather_db = find_item(mongo, {"local":local, "date":{"$regex":"^"+date}}, "alarm", "weather")
    temp = []
    for i in weather_db:
        temp.append(int(i['tmp']))
    temp_max = max(temp)
    temp_min = min(temp)
    return temp_max, temp_min

def set_rain_data(local, date):
    weather_db = find_item(mongo, {"local":local, "date":{"$regex":"^"+date}}, "alarm", "weather")
    rain = []
    for i in weather_db:
        rain.append(int(i['rain']))
    am = max(rain[:12])
    pm = max(rain[12:])
    return am, pm
    
def set_message():
    global message
    message = ''
    message += today[4:6] + "월 "+today[6:8]+"일의 " 
    message += user_local +" 날씨는 \n최고온도 "+str(temp_max)+"도 \n"+"최저온도 "+str(temp_min)+"도 입니다."
    message += "\n오전 강수확률은 "+str(am)+"%이며 \n오후 강수확률은 "+str(pm)+"%입니다."
    return message

def send_message():
    global weekday_check, weekend_check, everyday_check, today, user_local, temp_max, temp_min, am, pm
    weekday_check, weekend_check, everyday_check = set_day()
    setting_time = find_item(mongo, None, "alarm", "setting")
    app1.kakao_owner_token()
    app1.kakao_owner_check()
    app1.kakao_friends_update()
    for i in setting_time:
        user_name = i['name']
        user_local = i['local']
        user_db = find_item(mongo, {"name":user_name}, "alarm", "kakao")
        for j in user_db:
            user_uuid = j['uuid']
        flag = check_day(i['day'])
        if flag == 1:
            if set_time(i['time']) == now.hour: 
                today = app1.nowtime()  
                temp_max, temp_min = set_temp_data(user_local, today[:8])
                am, pm = set_rain_data(user_local, today[:8])
                message = set_message()
                kakao_friends_send(message, user_uuid)

if __name__ == '__main__':
    host = "172.17.0.2"
    port = "27017"
    app1.nowtime()
    now = datetime.now()
    mongo = MongoClient(host, int(port))
    # https://kauth.kakao.com/oauth/authorize?client_id=91d3b37e4651a9c3ab0216abfe877a50&redirect_uri=https://3.34.129.77/kakao_friend&response_type=code&scope=talk_message,friends
    # print('code를 입력하세요.')
    # code = input()
    # app1.kakao_to_friends_get_ownertokens(code)
    send_message()
    
    
    
    
    
            
