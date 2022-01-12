#! /usr/bin/python
from datetime import datetime
from pymongo import MongoClient
from pymongo.cursor import CursorType
from urllib.parse import urlencode, quote_plus
from urllib.request import urlopen, Request
from urllib import parse
from datetime import datetime
from datetime import timedelta
import sys, json, requests, os, func

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
    with open("/home/ec2-user/bot/kakao_code_friends_refresh.json","r") as fp:
        tokens = json.load(fp)
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
                "web_url":"http://3.35.252.82:5000/"
            }
        })
    }
    print('-----------message------------')
    print(message)
    print('------------------------------')
    response = requests.post(send_url, headers=headers, data=data)
    print(response.text)
    response.status_code
        
def set_temp_data(local, date):
    weather_db = func.find_item(mongo, {"local":local, "date":{"$regex":"^"+date}}, "alarm", "weather")
    temp = []
    for i in weather_db:
        temp.append(int(i['tmp']))
    temp_max = max(temp)
    temp_min = min(temp)
    return temp_max, temp_min

def set_rain_data(local, date):
    weather_db = func.find_item(mongo, {"local":local, "date":{"$regex":"^"+date}}, "alarm", "weather")
    rain = []
    for i in weather_db:
        rain.append(int(i['rain']))
    mid = int(len(rain) / 2)
    am = max(rain[:mid])
    pm = max(rain[mid:])
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
    setting_time = func.find_item(mongo, None, "alarm", "setting")
    func.kakao_owner_token()
    func.kakao_friends_update()
    for i in setting_time:
        user_name = i['name']
        user_local = i['local']
        user_content = i['content']
        user_db = func.find_item(mongo, {"name":user_name}, "alarm", "kakao")
        for j in user_db:
            user_uuid = j['uuid']
        flag = check_day(i['day'])
        if flag == 1:
            if set_time(i['time']) == now.hour:  
                today = func.nowtime() 
                temp_max, temp_min = set_temp_data(user_local, today[:8])
                am, pm = set_rain_data(user_local, today[:8])
                user_dust, dust_n = get_dust(user_local)
                message = set_message()
                kakao_friends_send(message, user_uuid)
                print(j['name'] + "에게 알림 전송완료")

def get_dust(local):  
    station = select_dust_area(local)
    try:
        CallBackURL = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'
        key = 'XIjRFoewvUDp4EDhRpATADoatwElkiQ%2F1J0tDooGjBTKStjRtuW3Zu89iE9cBsK%2Bz299IJwkbaE%2F%2F7SzcVo2yA%3D%3D'
        params = f'?{parse.quote_plus("ServiceKey")}={key}&'+parse.urlencode({
            parse.quote_plus('returnType') : 'json',
            parse.quote_plus('numOfRows') : '1',
            parse.quote_plus('stationName') : station,
            parse.quote_plus('dataTerm') : 'DAILY',
            parse.quote_plus('ver') : '1.0'
        })
        request = Request(CallBackURL + params)
        response_body = urlopen(request).read() 
        data = json.loads(response_body)
        dust = int(data['response']['body']['items'][0]['pm10Value'])
        if dust <= 19:
            dust_state = '매우 좋음'
        elif dust <= 29:
            dust_state = '좋음'
        elif dust <= 39:
            dust_state = '보통'
        elif dust <= 69:
            dust_state = '나쁨'
        elif dust <= 89:
            dust_state = '매우 나쁨'
        else:
            dust_state = '최악임'
        return dust_state, dust
    except:
        return '점검중', 0

def select_dust_area(local):
    user_station = func.find_item(mongo, {"city":local}, "alarm", "local")
    for j in user_station:
            station = j['dust_area']
    return station

def read_log():
    log = open('bot.log', 'rt')
    line_log = []
    loglines = log.readlines()
    # print(len(loglines))
    loglines = loglines[-100:]
    for line in loglines:
        line_log.append(line)
    log.close()
    # print(line_log)
    func.delete_item_many(mongo, {}, "alarm", "log")
    for i in line_log:
        func.insert_item_one(mongo, {'log':str(i)}, 'alarm', 'log')
    print('readed log')



if __name__ == '__main__':
    host = "172.17.0.4"
    port = "27017"
    func.nowtime()
    now = datetime.now()
    mongo = MongoClient(host, int(port))
    print('')
    print('')
    print('################start################')
    print(str(now.year)+"년 " + str(now.month)+"월 "+str(now.day)+ "일 " + str(now.hour)+"시 " + str(now.minute)+ "분")
    # url = 'https://kauth.kakao.com/oauth/authorize?client_id=91d3b37e4651a9c3ab0216abfe877a50&redirect_uri=http://3.35.252.82:5000/kakao_owner_code&response_type=code&scope=talk_message,friends'
    data = func.find_item(mongo, None, "alarm", "code")
    for i in data:
        code = i['code']
    # func.kakao_to_friends_get_ownertokens(code)
    func.kakao_to_friends_get_refreshtokens()
    send_message()
    read_log()
    # func.kakao_friends_update()    

# if __name__ == '__main__':
#     host = "172.17.0.4"
#     port = "27017"
#     func.nowtime()
#     now = datetime.now()
#     mongo = MongoClient(host, int(port))
#     read_log()

    
    
    
    
    
            
