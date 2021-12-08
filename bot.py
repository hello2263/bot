#! /usr/bin/python

from datetime import datetime
from pymongo import MongoClient
from pymongo.cursor import CursorType
from urllib.parse import urlencode, unquote, quote_plus
from urllib.request import urlopen, Request
from urllib import parse
from datetime import datetime
from datetime import timedelta
import sys, json, requests, os, xmltodict

# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname('__file__')))+"/docker/flask/")
# import app1

def find_item(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False}).sort('date')
    return result

def update_item_one(mongo, condition=None, update_value=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].update_one(filter=condition, update=update_value, upsert=True)
    return result

def get_corona():
    url = 'https://api.corona-19.kr/korea/?serviceKey=fbBHzjSOLvpkMa6ZyArcWIRYdoGV39U25'
    response = urlopen(url)
    response_message = response.read().decode('utf8')
    data = json.loads(response_message)
    corona = str(data['TotalCaseBefore']) + '명'
    corona_time = data['updateTime']
    return corona, corona_time

def set_day():
    weekday_check = 0
    weekend_check = 0 
    everyday_check = 0
    day = datetime.today().weekday()
    if day >= 0 and day < 5:
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
        if everyday_check == 1:
            flag = 1
    return flag

def set_time(time):
    user_time = int(time[:-1])
    return user_time

def kakao_friends_send(message, friend_uuid):
    with open("/home/ec2-user/bot/kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    # print(tokens)
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
    corona, corona_time = get_corona()
    message = ''
    message += today[4:6]+"월 "+today[6:8]+"일 "+user_local+"의" 
    if '1' in user_content:
        message += " \n최고온도 "+str(temp_max)+"도 \n"+"최저온도 "+str(temp_min)+"도 입니다."
    if '2' in user_content:
        message += "\n오전 강수확률은 "+str(am)+"%이며 \n오후 강수확률은 "+str(pm)+"%입니다."
    if '4' in user_content:
        message += '\n미세먼지는 ' + user_dust + '입니다.'
    if '3' in user_content:
        message += "\n"+corona_time +'\n확진자 수는 ' +corona+ '입니다.'
    return message

def send_message():
    global weekday_check, weekend_check, everyday_check, today, user_local, user_content, temp_max, temp_min, am, pm, user_dust
    weekday_check, weekend_check, everyday_check = set_day()
    setting_time = find_item(mongo, None, "alarm", "setting")
    # app1.kakao_owner_token()
    # app1.kakao_owner_check()
    # app1.kakao_friends_update()
    # kakao_owner_check()
    kakao_owner_token()
    kakao_friends_update()
    for i in setting_time:
        user_name = i['name']
        user_local = i['local']
        user_content = i['content']
        user_db = find_item(mongo, {"name":user_name}, "alarm", "kakao")
        for j in user_db:
            user_uuid = j['uuid']
        flag = check_day(i['day'])
        if flag == 1:
            if set_time(i['time']) == now.hour: 
                # today = app1.nowtime()  
                today = nowtime() 
                temp_max, temp_min = set_temp_data(user_local, today[:8])
                am, pm = set_rain_data(user_local, today[:8])
                user_dust = get_dust(user_local)
                message = set_message()
                kakao_friends_send(message, user_uuid)
                print(j['name'] + "에게 알림 전송완료")

def kakao_to_friends_get_refreshtokens():
    with open("/home/ec2-user/bot/kakao_code_friends_owner.json","r") as fp:
        token_data = json.load(fp)
    refresh = token_data['refresh_token']
    url = "https://kauth.kakao.com/oauth/token"
    rest_api_key = '91d3b37e4651a9c3ab0216abfe877a50'
    data = {
        "grant_type": "refresh_token",
        "client_id": f"{rest_api_key}",
        "refresh_token": refresh
    }
    response = requests.post(url, data=data)
    tokens = response.json()

    with open("kakao_code_friends_refresh.json", "w") as fp:
        json.dump(tokens, fp)

    return tokens['access_token']


#--------------------------------------------------------------------------------------------
def kakao_to_friends_get_ownertokens(code):
    url = 'https://kauth.kakao.com/oauth/token'
    authorize_code = code
    data = {
        'grant_type':'authorization_code',
        'client_id':'91d3b37e4651a9c3ab0216abfe877a50',
        'redirect_uri':'https://3.35.252.82/kakao_friend',
        'code': authorize_code,
        }
    response = requests.post(url, data=data)
    tokens = response.json()
    print(tokens)
    with open("/home/ec2-user/bot/kakao_code_friends_owner.json","w") as fp:
        json.dump(tokens, fp)
    return str(tokens['refresh_token'])

def nowtime():
    now = datetime.now()
    if now.month < 10:
        today_month = '0'+str(now.month)
    else:
        today_month = str(now.month) 
    if now.day < 10:
        today_day = '0'+str(now.day)
    else:
        today_day = str(now.day)
    if now.hour < 10:
        today_hour = '0'+str(now.hour)
    else:
        today_hour = str(now.hour)
    today_date = str(now.year)+today_month+today_day
    today_time = today_hour+'00'
    return str(today_date + '-' + today_time)

def kakao_owner_token():
    with open("/home/ec2-user/bot/kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    url="https://kapi.kakao.com/v1/user/access_token_info"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    response = requests.post(url, headers=headers)
    # print(response.text)
    # print("kakao_owner_token_finish")
    return response.text

def kakao_friends_update():
    with open("/home/ec2-user/bot/kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    friend_url = "https://kapi.kakao.com/v1/api/talk/friends"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    result = json.loads(requests.get(friend_url, headers=headers).text)
    friends_list = result.get("elements")
    try:
        for friend in friends_list:
            update_item_one(mongo, {"uuid":str(friend['uuid'])}, {"$set": {"id":str(friend['id']), "name":str(friend['profile_nickname']), "image":str(friend['profile_thumbnail_image'])}}, "alarm", "kakao")
        print("friends_update success")
    except:
        print('friends_update fail')

def get_dust(local):     # 기상청에 API를 요청하여 데이터를 받음
    CallBackURL = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty'
    key = 'XIjRFoewvUDp4EDhRpATADoatwElkiQ%2F1J0tDooGjBTKStjRtuW3Zu89iE9cBsK%2Bz299IJwkbaE%2F%2F7SzcVo2yA%3D%3D'
    params = f'?{parse.quote_plus("ServiceKey")}={key}&'+parse.urlencode({
        parse.quote_plus('returnType') : 'xml',
        parse.quote_plus('stationName') : local,
        parse.quote_plus('dataTerm') : 'DAILY',
    })
    
    response = requests.get(CallBackURL+params)
    dust = (CallBackURL+params).find(key)
    if dust <= 30:
        dust_state = '아주 좋음'
    elif dust <= 60:
        dust_state = '좋음'
    elif dust <= 90:
        dust_state = '보통'
    elif dust <= 120:
        dust_state = '나쁨'
    else:
        dust_state = '매우나쁨'
    return dust_state


if __name__ == '__main__':
    host = "172.17.0.2"
    port = "27017"
    # app1.nowtime()
    nowtime()
    now = datetime.now()
    mongo = MongoClient(host, int(port))
    print(str(now.year)+"년 " + str(now.month)+"월 "+str(now.day)+ "일 " + str(now.hour)+"시 " + str(now.minute)+ "분")
    # https://kauth.kakao.com/oauth/authorize?client_id=91d3b37e4651a9c3ab0216abfe877a50&redirect_uri=https://3.35.252.82/kakao_friend&response_type=code&scope=talk_message,friends
    # print('code를 입력하세요.')
    # code = input()
    # app1.kakao_to_friends_get_ownertokens(code)
    # kakao_to_friends_get_ownertokens(code)
    kakao_to_friends_get_refreshtokens()
    send_message()
    
    
    
    
    
            
