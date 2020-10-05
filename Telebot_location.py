import telebot
import mysql.connector
import json
import base64

from mysql.connector import errorcode

try:
  mydb = mysql.connector.connect(
      host="localhost",
      user="root",
      password="777denis",
      port="3306",
      database="telebot"
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
        
        bot.register_next_step_handler(msg, process_location_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')



def process_location_step(message):
    try:
        user_id = message.from_user.id
        place = data_place[user_id]

        print(message.location)

        place.lon = message.location.longitude
        place.lat = message.location.latitude

        #sql = "INSERT INTO place (name,lon,lat,user_id) VALUES (%s,%s,%s,%s)"
        #val = (place.name, place.lon, place.lat, place.user_id)
        #mycursor.execute(sql, val)
        #mydb.commit()

        msg = bot.send_message(message.chat.id, 'Send a photo of the place, please.')
        bot.register_next_step_handler(msg, process_placephoto_step)
        #bot.send_message(message.chat.id, 'Place has been saved!')
    except Exception as e:
        bot.reply_to(message, 'oooops')

@bot.message_handler(content_types=['photo'])
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
        bot.reply_to(message, 'Wrong photo!')


@bot.message_handler(commands=['list'])
def place_list(message):
    try:
        user_id = message.from_user.id
        print('----------------------------------------------------')
        query = ("SELECT name, lon, lat FROM place "                 
         "WHERE user_id LIKE %s "
         "ORDER BY place_id DESC LIMIT 10")
        value = (user_id,)
        mycursor.execute(query, value)

        print(mycursor.rowcount, "record inserted.")
        results = mycursor.fetchall()
  

        print(mycursor.column_names)
        print("Result: ", results)


        if results == []:   
            bot.send_message(message.chat.id, 'Place_List is empty!')
        else:
            for (name, lon, lat) in results:
                print(name, lon, lat)
                bot.send_message(message.chat.id, '{}\n{}, {}.'.format(name, lon, lat))

            bot.send_message(message.chat.id, 'Done!')

        #query = ("SELECT photo FROM place "                 
        # "WHERE user_id LIKE %s "
        # "ORDER BY place_id DESC")
        #value = (user_id,)
        #mycursor.execute(query, value)

        #results = base64.b64decode(mycursor.fetchone())
        #bot.send_photo(message.chat.id, results[0],caption='Done!')
        ###print(type(results[0]))
    except Exception as e:
        bot.reply_to(message, 'Error')


@bot.message_handler(commands=['del'])
def delete_placelist(message):
    try:
        user_id = message.from_user.id

        query = ("DELETE FROM place "                 
         "WHERE user_id LIKE %s ")
        value = (user_id,)
        mycursor.execute(query, value)
        mydb.commit()

        print("Deleted!")
        bot.send_message(message.chat.id, 'Your Place_List has been deleted!')
    except Exception as e:
        bot.reply_to(message, 'Wrong del!')


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
