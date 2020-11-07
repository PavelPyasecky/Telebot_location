import os
import config
import base64
import requests
import mysql.connector
import telebot
import time
import json

from PIL import Image
from mysql.connector import errorcode

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

YandexAPI = os.environ.get('YandexAPI')


def get_adress_by_coordinates(coordinates):
    params = {
    "apikey":YandexAPI,
    "format":"json",
    "lang":"ru_RU",
    "kind":"house",
    "geocode": coordinates
    }
    try:
        url = 'https://geocode-maps.yandex.ru/1.x/'
        response = requests.get(url, params=params)

        json_data = response.json()
        address_str = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]["AddressLine"]
        return address_str

    except Exception as e:
        print("Some troubles with YandexAPI.")
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        return ""
    

try:
  mydb = mysql.connector.connect(
      host=DB_HOST,            
      user=DB_USER,                                                      
      password=DB_PASSWORD,                                                  
      port="3306",                                                                  
      database=DB_NAME                                                   
      )

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)


mycursor = mydb.cursor()

token = '1181480337:AAHZBCS4pt2tvAYDt_L1xxQAqssVfAjUnLQ'
bot = telebot.TeleBot(token, threaded=False)

data_place = {}

class Place:
    def __init__(self, user_id):
        self.user_id = user_id
        self.name = ''
        self.lon = None
        self.lat = None
        self.photo = None
 

@bot.message_handler(commands=['add'])
def add_location(message):
    msg = bot.send_message(message.chat.id, "Enter place name, please.")
    bot.register_next_step_handler(msg, process_placename_step)  

def process_placename_step(message):
    try:
        user_id = message.from_user.id

        place = Place(user_id)
        data_place[user_id] = place
        place.name = message.text

        query = ("SELECT user_id FROM user "
         "WHERE user_id LIKE %s ")
        value = (place.user_id,)
        mycursor.execute(query, value)
        user = mycursor.fetchone()

        if not user:
            sql = ("INSERT INTO ""user (user_id) ""VALUES (%s) ")                   
            val = (place.user_id,)
            mycursor.execute(sql, val)                                           
            mydb.commit()

        msg = bot.send_message(message.chat.id, 'Send your location, please.')
        
        bot.register_next_step_handler(msg, process_location_step)
    except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        bot.reply_to(message, type(e).__name__)
        


def process_location_step(message):
    try:
        user_id = message.from_user.id
        place = data_place[user_id]

        place.lon = message.location.longitude
        place.lat = message.location.latitude

        msg = bot.send_message(message.chat.id, 'Send a photo of the place, please.')
        bot.register_next_step_handler(msg, process_placephoto_step)

    except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        bot.reply_to(message, type(e).__name__)


def process_placephoto_step(message):
    try:
        user_id = message.from_user.id
        place = data_place[user_id]

        photo_id = message.photo[-1].file_id
        photo_info = bot.get_file(photo_id)
        photo_downloaded = bot.download_file(photo_info.file_path)

        place.photo = base64.b64encode(photo_downloaded)

        sql = "INSERT INTO place (name,lon,lat,photo,user_id) VALUES (%s,%s,%s, %s ,%s) "
        val = (place.name, place.lon, place.lat, place.photo, user_id)
        mycursor.execute(sql, val)
        mydb.commit()

        bot.send_message(message.chat.id, 'Place has been saved!')
        data_place.pop(user_id)
    except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        bot.reply_to(message, type(e).__name__)


@bot.message_handler(commands=['list'])
def place_list(message):
    try:
        user_id = message.from_user.id
        query = ("SELECT name, lon, lat, photo FROM place "                 
         "WHERE user_id LIKE %s "
         "ORDER BY place_id DESC LIMIT 10")
        value = (user_id,)
        mycursor.execute(query, value)

        results = mycursor.fetchall()
  
        if results == []:   
            bot.send_message(message.chat.id, 'Place_List is empty!')
        else:
            bot.send_message(message.chat.id, 'Your Place_List:')
            counter = 1
            for (name, lon, lat, photo_res) in results:

                photo_b = photo_res.encode('utf-8')
                photo = base64.b64decode(photo_b)
                bot.send_message(message.chat.id, '{}. {}'.format(counter, name))
                bot.send_photo(message.chat.id, photo)

                coordinates = '{},{}'.format(lon, lat)
                if get_adress_by_coordinates(coordinates):
                    bot.send_message(message.chat.id, '{}: {}'.format('Adress', get_adress_by_coordinates(coordinates)))
                
                bot.send_location(message.chat.id, lat, lon)
                counter += 1

            bot.send_message(message.chat.id, 'Done!')

    except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        bot.reply_to(message, type(e).__name__)


@bot.message_handler(commands=['reset'])
def delete_placelist(message):
    try:
        user_id = message.from_user.id

        query = ("DELETE FROM place "                 
         "WHERE user_id LIKE %s ")
        value = (user_id,)
        mycursor.execute(query, value)
        mydb.commit()

        bot.send_message(message.chat.id, 'Your Place_List has been deleted!')
    except Exception as e:
        template = "An exception of type {} occured. Arguments:\n{!r}"
        mes = template.format(type(e).__name__, e.args)
        print(mes)
        bot.reply_to(message, type(e).__name__)


@bot.message_handler()
def handler_message(message):
  print(message.text)
  bot.send_message(message.chat.id, text='This BestBot will help you with your Place_List.')
   
# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)                                                               

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()                                                                    

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            template = "An exception of type {} occured. Arguments:\n{!r}"
            mes = template.format(type(e).__name__, e.args)
            print(mes)
            time.sleep(15)                                                           
