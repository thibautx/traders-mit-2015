from Queue import Queue
from threading import Lock
from threading import Thread
from json import dumps
from json import loads
from re import match
from time import sleep
from time import time
from zlib import decompress
from zlib import MAX_WBITS

from websocket import create_connection
from websocket import WebSocketTimeoutException
from websocket import WebSocketConnectionClosedException

DEFAULT_DELAY = 1
DEFAULT_POSITION_LIMIT = 100
DEFAULT_ORDER_QUANTITY = 50

EWMA_FACTOR = 0.2
ENTER_THRESHOLD = 0.05

class Options():
    def __init__(self, default=None):
        self.data = default or {}
        self.mu = Lock()

    def get(self, key):
        return self.data.get(key)

    def set(self, key, val):
        if key not in self.data:
            print "Invalid option: %s" % key
        else:
            print "Set %s to %s" % (key, val)
            self.data[key] = val


class BaseBot(object):
    # XXX change me for actual running
    trader_id = 'trader0'
    password = ''

    # Sets up the connection to the server.
    # Please do not change anything here unless
    # you know what's going on
    def __init__(self):
        self.options = Options({
            'delay': DEFAULT_DELAY,
            'position_limit': DEFAULT_POSITION_LIMIT,
            'order_quantity': DEFAULT_ORDER_QUANTITY,
            'ewma_factor': EWMA_FACTOR,
            'enter_threshold': ENTER_THRESHOLD,
        })

        self.ws = create_connection(
            'ws://localhost:10914/%s/%s' % (self.trader_id, self.password),
            timeout=0.5,
        )
        self.outbox = Queue()

        self.started = False
        self.done = False
        self.lastActionTime = time()

        self.topBid = {}
        self.topAsk = {}
        self.lastPrices = {}
        self.positions = {}
        self.priceChange = {}

        register_msg = dumps({
            'message_type': 'REGISTER',
        })
        self.outbox.put(register_msg)


    # You should not have to modify the following three
    # methods.
    
    # Starts and returns the two processes of the bot.
    def makeThreads(self):
        reader_t = Thread(target=self.ws_reader, args=())
        writer_t = Thread(target=self.ws_writer, args=())

        return reader_t, writer_t

    # Reads input from from the server and processes
    # them accordingly
    def ws_reader(self):
        while True:
            try:
                msg = self.ws.recv()
                msg = decompress(msg, 16+MAX_WBITS)
                msg = loads(msg)
            except WebSocketTimeoutException:
                msg = None
            except WebSocketConnectionClosedException:
                self.outbox.put(None)
                return

            output = self.process(msg)
            if output is not None:
                self.outbox.put(output)

    # Sends messages in our outbox to the server
    def ws_writer(self):
        while True:
            msg = self.outbox.get()
            if msg is None:
                break
            else:
                self.ws.send(msg)
        self.ws.close()


    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        # Update internal positions
        if msg.get('trader_state'):
            self.positions = msg['trader_state']['positions']

        # Update internal books for each ticker
        if msg.get('market_states'):
            for ticker, state in msg['market_states'].iteritems():
                if len(state['bids']):
                    self.topBid[ticker] = max(map(float, state['bids'].keys()))
                if len(state['asks']):
                    self.topAsk[ticker] = min(map(float, state['asks'].keys()))
                self.lastPrices[ticker] = state['last_price']
                self.priceChange[ticker] = 0

        # Update internal book for a single ticker
        if msg.get('market_state'):
            state = msg['market_state']
            ticker = state['ticker']

            if len(state['bids']):
                self.topBid[ticker] = max(map(float, state['bids'].keys()))
            if len(state['asks']):
                self.topAsk[ticker] = min(map(float, state['asks'].keys()))

            # We keep track of the exponentially weighted
            # moving average of the price changes.
            # Feel free to change the way you update
            # your internal state.

            lastPrice = self.lastPrices[ticker]
            ewma_factor = self.options.get('ewma_factor')
            self.priceChange[ticker] *= (1-ewma_factor)
            self.priceChange[ticker] += ewma_factor * (state['last_price'] - lastPrice)

            self.lastPrices[ticker] = state['last_price']

        if msg.get('message_type') == 'START':
            self.started = True
        elif msg.get('end_time'):
            if not msg.get('end_time').startswith('0001'):
                self.started = True

    # Processes the messages received from the server.
    # This BaseBot process only updates the bot's state
    # with server updates. To execute your own strategies,
    # modify this method (in either a child class or this one).
    def process(self, msg):
        if msg is not None:
            self.update_state(msg)
        return None


if __name__ == '__main__':
    bot = BaseBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

