import base64
import requests
import mysql.connector
import telebot
import json

from PIL import Image
from mysql.connector import errorcode


url = 'https://geocode-maps.yandex.ru/1.x/'

def get_adress_by_coordinates(coordinates):
    params = {
    "apikey":"6c96be79-497b-42ff-b64e-4af057ffac67",
    "format":"json",
    "lang":"ru_RU",
    "kind":"house",
    "geocode": coordinates
    }
    try:

        response = requests.get(url, params=params)

        json_data = response.json()
        address_str = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]["AddressLine"]
    except:
        return "Too far"
    return address_str


try:
  mydb = mysql.connector.connect(
      host="eu-cdbr-west-03.cleardb.net",
      user="bf74cdeb495328",
      password="b1507432",
      port="3306",
      database="heroku_bf58d8bda48c78b"
      )

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

mycursor = mydb.cursor()

token = '1181480337:AAHZBCS4pt2tvAYDt_L1xxQAqssVfAjUnLQ'
bot = telebot.TeleBot(token)

data_place = {}

class Place:
    def __init__(self, user_id):
        self.user_id = user_id
        self.name = ''
        self.lon = None
        self.lat = None
        self.photo = None

commands = ['/add', '/list', '/reset']

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
        bot.reply_to(message, 'Error in the name')


def process_location_step(message):
    try:
        user_id = message.from_user.id
        place = data_place[user_id]

        place.lon = message.location.longitude
        place.lat = message.location.latitude

        msg = bot.send_message(message.chat.id, 'Send a photo of the place, please.')
        bot.register_next_step_handler(msg, process_placephoto_step)

    except Exception as e:
        bot.reply_to(message, 'Error in location')


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
    except Exception as e:
        bot.reply_to(message, 'Wrong Place_photo!')


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
                bot.send_message(message.chat.id, '{}: {}'.format('Adress', get_adress_by_coordinates(coordinates)))
                
                bot.send_location(message.chat.id, lat, lon)
                counter += 1

            bot.send_message(message.chat.id, 'Done!')

    except Exception as e:
        bot.reply_to(message, 'Error in Place_List')


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
        bot.reply_to(message, 'Error in deleting!')


@bot.message_handler()
def handler_message(message):
  print(message.text)
  bot.send_message(message.chat.id, text='This BestBot will help you with your Place_List.')
   
##@bot.message_handler()
##def handler_message(message):
##  print(message.text)
##  bot.send_message(message.chat.id, text='Ask about currency.')
##
##@bot.message_handler(content_types=['location'])  #if we got location, need to do '/add'
##def handler_location(message):
##  print(message.location)
##  bank_adress, bank_lat, bank_long = bank_location(message.location)
##  image = Image.open(r'D:/CVS/Data/TeleBot/nac_bank_logo.jpg')
##  bot.send_photo(message.chat.id, image, caption = 'Нацбанк: {}'.format(bank_adress))                 
##  bot.send_location(message.chat.id, bank_lat, bank_long)


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)                                                                #Need to uncomment

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()                                                                     #Need to uncomment

if __name__ == '__main__':
    bot.polling(none_stop= True)
