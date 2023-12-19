import paho.mqtt.client as mqtt
from threading import Lock
import time, datetime,json, random, string


class Tasmota:
    HB_COUNTER_RESET = 5

    def __init__(self, app, log, state_cb=None, ip_cb=None):
        self.app = app
        self.log = log
        self.state_cb = state_cb
        self.ip_cb=ip_cb
        self.wait_on_connect = True
        self.switch_hb_dict = {}
        self.switch_status_dict = {}
        self.switch_ip_dict = {}
        self.switch_lock = Lock()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info('MQTT client connected')
            self.wait_on_connect = False

    def on_message(self, client, userdata, message):
        try:
            self.switch_lock.acquire()
            if message.topic.find('RESULT') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'POWER' in payload:
                    status = True if payload['POWER'] == 'ON' else False
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    if self.state_cb:
                        self.state_cb(switch, status)
            if message.topic.find('STATUS5') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'StatusNET' in payload:
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    if self.ip_cb:
                        self.ip_cb(switch, payload['StatusNET']['IPAddress'])
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()

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
        self.log.info(f'MQTT : subscribing to switch, {switch}')
        self.client.subscribe(f'stat/{switch}/RESULT')
        self.client.subscribe(f'stat/{switch}/STATUS5')

    def unsubscribe_from_switch(self, switch):
        self.log.info(f'MQTT : unsubscribing to switch, {switch}')
        self.client.unsubscribe(f'stat/{switch}/RESULT')
        self.client.unsubscribe(f'stat/{switch}/STATUS5')

    # warning : no protection with lock!
    def set_switch_state(self, switch, state):
        # self.log.info("MQTT TX : switch {} to state {}".format(switch, state))
        message = "ON" if state else "OFF"
        self.client.publish(f'cmnd/{switch}/power', message, retain=True)

    def request_status(self, switch):
        try:
            self.switch_lock.acquire()
            # self.log.info(f"MQTT request state : switch {switch}")
            self.client.publish(f'cmnd/{switch}/status', 5, retain=False)
            if switch in self.switch_hb_dict:
                self.switch_hb_dict[switch] -= 1
                if self.switch_hb_dict[switch] < 1:
                    del(self.switch_hb_dict[switch])
                    if self.ip_cb:
                        self.ip_cb(switch, "0.0.0.0")
            else:
                self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()

