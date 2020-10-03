import telebot
import mysql.connector
import json

from mysql.connector import errorcode

try:
  mydb = mysql.connector.connect(
      host="localhost",
      user="root",
      password="777denis",
      port="3306",
      database="telebot"
      )
  print('Db has been connected!')    ####
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print('Error!')                   ####
        print(err)



mycursor = mydb.cursor()

#cursor.execute("CREATE DATABASE telebot")

#cursor.execute("SHOW DATABASES")

#for x in cursor:
#  print(x)

token = '1181480337:AAHZBCS4pt2tvAYDt_L1xxQAqssVfAjUnLQ'

bot = telebot.TeleBot(token)

data_place = {}

class Place:
    def __init__(self, user_id):
        self.user_id = user_id
        self.name = ''
        self.lon = None
        self.lat = None

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
         "WHERE user_id LIKE %s")
        value = (place.user_id,)
        mycursor.execute(query, value)
        for user in mycursor:
            pass
        if user[0] != place.user_id:
            sql = ("INSERT INTO ""user (user_id) ""VALUES (%s) ")                   
            val = (place.user_id,)
            mycursor.execute(sql, val)                                           
            mydb.commit()

        msg = bot.send_message(message.chat.id, 'Send your location, please.')
        
        bot.register_next_step_handler(msg, process_locationname_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')



def process_locationname_step(message):
    try:
        print(data_place[message.from_user.id].user_id)
        user_id = message.from_user.id
        place = data_place[user_id]

        print(message.location)

        place.lon = message.location.longitude
        place.lat = message.location.latitude
        print(place.lon, place.lat)

        sql = "INSERT INTO place (name,lon,lat,user_id) VALUES (%s,%s,%s,%s)"
        val = (place.name, place.lon, place.lat, place.user_id)
        mycursor.execute(sql, val)
        mydb.commit()

        bot.send_message(message.chat.id, 'Place has been saved!')
    except Exception as e:
        bot.reply_to(message, 'oooops')


@bot.message_handler()
def handler_message(message):
  print(message.text)
  bot.send_message(message.chat.id, text='Этот Бот для сохранения мест, в которых вы хотите побывать.')
   
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
####bot.enable_save_next_step_handlers(delay=2)                                                                #Need to uncomment

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
####bot.load_next_step_handlers()                                                                     #Need to uncomment

if __name__ == '__main__':
    bot.polling(none_stop= True)
