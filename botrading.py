import ccxt
import time
import pandas as pd
import numpy as np
import tensorflow as tf
from telegram.ext import Updater, CommandHandler

# initialize exchange API keys
exchange_name = 'binance'
api_key = 'qJfeLi4TB9pGShfzZM3vbw1m3NXUeNYPHb4v3Gw4F2jwqA083iEw83AgmwcoNkNk'
api_secret = 'Z4qSbusC1oVbuF2ki4oMpBPBm0OG6erqR7Zv5vxbQoZKBohbz1DWYj5y90TzbWWN'

# instantiate exchange API
exchange = getattr(ccxt, exchange_name)({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True
})

# set up trading parameters
symbol = 'BTC/USDT'
amount = 0.01
buy_price = 0
sell_price = 0

# load AI model
model = tf.keras.models.load_model('my_model')

# start Telegram bot
updater = Updater(token='<6195200394:AAEXl_oEf5C7k-gXAQ2sHHeJnsqEOXXUe3E>', use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, I'm your bot!")
    
def buy(update, context):
    global buy_price
    buy_price = float(context.args[0])
    context.bot.send_message(chat_id=update.effective_chat.id, text="Buy signal set at {}".format(buy_price))

def sell(update, context):
    global sell_price
    sell_price = float(context.args[0])
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sell signal set at {}".format(sell_price))

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

buy_handler = CommandHandler('buy', buy)
dispatcher.add_handler(buy_handler)

sell_handler = CommandHandler('sell', sell)
dispatcher.add_handler(sell_handler)

updater.start_polling()

# enter trading loop
while True:
    # get current market price
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    
    # check if buy signal is triggered
    if current_price < buy_price:
        # execute buy order
        order = exchange.create_order(symbol, 'limit', 'buy', amount, buy_price)
        print('Bought {} BTC at {}'.format(amount, buy_price))
        sell_price = buy_price * 1.1 # set sell price at 10% above buy price
        
        # make predictions on new market data
        new_market_data = pd.DataFrame({'price': [current_price]})
        predictions = model.predict(new_market_data)
        signal = np.argmax(predictions) # convert the predictions to signals (0 for sell, 1 for hold, 2 for buy)
        if signal == 0:
            context.bot.send_message(chat_id='<YOUR_CHAT_ID>', text="Sell signal triggered at {}".format(current_price))
        elif signal == 1:
            context.bot.send_message(chat_id='<YOUR_CHAT_ID>', text="Hold signal triggered at {}".format(current_price))
        else:
            context.bot.send_message(chat_id='<YOUR_CHAT_ID>', text="Buy signal triggered at {}".format(current_price))
        
    # check if sell signal is triggered
    elif current_price > sell_price:
        # execute sell order
        order = exchange.create_order(symbol, 'limit', 'sell', amount, sell_price)
        print('Sold {} BTC at {}'.format(amount, sell_price))
        buy_price = sell_price * 0.9 # set buy price at 10% below sell price
        
# make predictions on new market data
new_market_data = pd.DataFrame({'price': [current_price], 'signal': [0]}) # assuming initial signal is 'sell'
predicted_signal = model.predict(new_market_data)[0]
    
# convert the predicted signal to a string
if predicted_signal == 0:
    signal_str = 'SELL'
elif predicted_signal == 1:
    signal_str = 'HOLD'
else:
    signal_str = 'BUY'
    
# send a message to the Telegram bot with the signal
message = 'Current price: {}\nSignal: {}'.format(current_price, signal_str)
updater.bot.send_message(chat_id='<YOUR_CHAT_ID>', text=message)

# execute trades based on the signal
if predicted_signal == 2:
    # execute buy order
    order = exchange.create_order(symbol, 'limit', 'buy', amount, buy_price)
    print('Bought {} BTC at {}'.format(amount, buy_price))
    sell_price = buy_price * 1.1 # set sell price at 10% above buy price
elif predicted_signal == 0:
    # execute sell order
    order = exchange.create_order(symbol, 'limit', 'sell', amount, sell_price)
    print('Sold {} BTC at {}'.format(amount, sell_price))
    buy_price = sell_price * 0.9 # set buy price at 10% below sell price
    
# wait for 10 seconds before checking price again
time.sleep(10)
