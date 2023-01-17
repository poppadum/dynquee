#!/usr/bin/python

import subprocess, signal, logging

# Logging setup
logging.basicConfig(
    format = '%(asctime)-15s %(levelname)-7s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    level = logging.DEBUG
)
log = logging.getLogger(__name__)


# MQTT subscriber
class RecalboxMQTTSubscriber:
    '''MQTT subscriber: handles connection to mosquitto_sub'''

    _pipe = None
    "pipe to mosquitto_sub subprocess"

    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)


    def start(self):
        '''Start the mosquitto_sub subprocess and open a pipe to it'''
        self._pipe = subprocess.Popen(
            [
                './announce_time.sh'
                # 'mosquitto_sub',
                # '-h', '127.0.0.1',
                # '-p', '1883',
                # '-q', '0',
                # '-t', 'Recalbox/EmulationStation/Event'
            ],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            bufsize = 4096
        )
        log.debug("launched mosquitto_sub pid=%d", self._pipe.pid)

    def getEvent(self):
        '''Read an event from the MQTT server (blocks until data is received)'''
        line = self._pipe.stdout.readline()
        return line


    def _shutdown(self, *args):
        '''Terminate the mosquitto_sub subprocess and close the pipe'''
        log.debug("RecalboxMQTTSubscriber.shutdown(%d) requested", args[0])
        self._pipe.terminate()


# Test harness
if __name__ == '__main__':
    subscriber = RecalboxMQTTSubscriber()
    subscriber.start()
    while True:
        event = subscriber.getEvent()
        if not event:
            break
        log.info("received event: %s", event)

log.info("end of program")
