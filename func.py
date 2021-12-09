from urllib.parse import urlencode, quote_plus
from urllib.request import urlopen, Request
from urllib import parse
import sys, json, requests, os

def find_item(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False}).sort('date')
    return result

def find_item_one(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].find(condition, {"_id":False})
    return result

def update_item_one(mongo, condition=None, update_value=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].update_one(filter=condition, update=update_value, upsert=True)
    return result

def insert_item_one(mongo, data, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].insert_one(data).inserted_id
    return result

def delete_item_one(mongo, condition=None, db_name=None, collection_name=None):
    result = mongo[db_name][collection_name].delete_one(condition)
    return result





def kakao_to_friends_get_ownertokens(code):
    url = 'https://kauth.kakao.com/oauth/token'
    authorize_code = code
    data = {
        'grant_type':'authorization_code',
        'client_id':'91d3b37e4651a9c3ab0216abfe877a50',
        'redirect_uri':'http://3.35.252.82:5000/kakao_owner_code',
        'code': authorize_code,
        }
    response = requests.post(url, data=data)
    tokens = response.json()
    with open("kakao_code_friends_owner.json","w") as fp:
        json.dump(tokens, fp)
    return str(tokens['refresh_token'])

def kakao_to_friends_get_refreshtokens():
    with open("kakao_code_friends_owner.json","r") as fp:
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

def kakao_owner_token():
    with open("kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    url="https://kapi.kakao.com/v1/user/access_token_info"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    response = requests.post(url, headers=headers)
    return response.text

def kakao_friends_token():
    with open("./kakao_code_friends_friends.json","r") as fp:
        tokens = json.load(fp)
    url="https://kapi.kakao.com/v1/user/access_token_info"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    response = requests.post(url, headers=headers)
    return response.text

def kakao_friends_update():
    with open("kakao_code_friends_owner.json","r") as fp:
        tokens = json.load(fp)
    friend_url = "https://kapi.kakao.com/v1/api/talk/friends"
    headers={"Authorization" : "Bearer " + tokens["access_token"]}
    result = json.loads(requests.get(friend_url, headers=headers).text)
    friends_list = result.get("elements")
    try:
        for friend in friends_list:
            func.update_item_one(mongo, {"uuid":str(friend['uuid'])}, {"$set": {"id":str(friend['id']), "name":str(friend['profile_nickname']), "image":str(friend['profile_thumbnail_image'])}}, "alarm", "kakao")
        print("friends_update success")
    except:
        print('friends_update fail')

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
