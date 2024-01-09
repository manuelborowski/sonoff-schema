import paho.mqtt.client as mqtt
from threading import Lock
import time, json, random, string, copy


class Tasmota:
    HB_COUNTER_RESET = 5

    def __init__(self, app, log):
        self.app = app
        self.log = log
        self.wait_on_connect = True
        self.switch_hb_dict = {}
        self.switch_status_dict = {}
        self.switch_ip_dict = {}
        self.switch_lock = Lock()
        self.message_queue = {}

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info('MQTT client connected')
            self.wait_on_connect = False

    def on_message(self, client, userdata, message):
        try:
            # self.log.info(f'on_message, {message.topic}  <>  {message.payload}')
            if message.topic.find('RESULT') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'POWER' in payload:
                    # self.log.info(f'on_message, {message.topic}  <>  {message.payload}')
                    status = True if payload['POWER'] == 'ON' else False
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    self.push_message_on_queue({"type": "state", "id": switch, "data": status})
                # On sonoff/tasmota console: setoption73 1
                # This will decouple the button from the relay and pushing the button sends the mqtt message below
                if 'Button1' in payload:
                    # self.log.info(f'on_message, {message.topic}  <>  {message.payload}')
                    action = payload["Button1"]["Action"]
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    self.push_message_on_queue({"type": "action", "id": switch, "data": action})
            if message.topic.find('STATUS5') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'StatusNET' in payload:
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    self.push_message_on_queue({"type": "ip", "id": switch, "data": payload['StatusNET']['IPAddress']})
        except Exception as e:
            self.log.info('error : {}'.format(e))


    def push_message_on_queue(self, message):
        try:

            self.switch_lock.acquire()
            if message["type"] == "state":
                print(message)
            message_key = "-".join([message["id"], message["type"]])
            self.message_queue[message_key] = message
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()


    def get_message_queue(self):
        out = []
        try:
            self.switch_lock.acquire()
            for _, q in self.message_queue.items():
                out.append(q)
            self.message_queue = {}
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
            return out


    def start(self):
        self.log.info('Start MQTT client')
        self.client = mqtt.Client(f'sonoff-{"".join(random.choices(string.ascii_uppercase + string.digits, k=10))}')
        self.client.on_connect=self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.app.config['MQTT_SERVER'])
        #Wait until client is connected, this takes less than a millisecond
        self.client.loop_start()
        while self.wait_on_connect:
            time.sleep(1)

    def stop(self):
        self.log.info('Stop MQTT client')
        self.client.loop_stop()

    def subscribe_to_switch(self, switch):
        # self.log.info(f'MQTT : subscribing to switch, {switch}')
        self.client.subscribe(f'stat/{switch}/RESULT')
        self.client.subscribe(f'stat/{switch}/STATUS5')

    def unsubscribe_from_switch(self, switch):
        # self.log.info(f'MQTT : unsubscribing to switch, {switch}')
        self.client.unsubscribe(f'stat/{switch}/RESULT')
        self.client.unsubscribe(f'stat/{switch}/STATUS5')


    def set_switch_state(self, switch, state):
        self.log.info("MQTT TX : switch {} to state {}".format(switch, state))
        message = "ON" if state else "OFF"
        self.client.publish(f'cmnd/{switch}/power', message, retain=True)


    def request_status(self, switch):
        try:
            # self.log.info(f"MQTT request state : switch {switch}")
            self.client.publish(f'cmnd/{switch}/status', 5, retain=False)
            if switch in self.switch_hb_dict:
                self.switch_hb_dict[switch] -= 1
                if self.switch_hb_dict[switch] < 1:
                    del(self.switch_hb_dict[switch])
                    self.push_message_on_queue({"type": "ip", "id": switch, "data": "0.0.0.0"})
            else:
                self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
        except Exception as e:
            self.log.info('error : {}'.format(e))

