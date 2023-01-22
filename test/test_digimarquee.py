#!/usr/bin/python

# Unit tests for digimarquee module

import unittest, os, logging, threading, time
from digimarquee import MQTTSubscriber, log

# only log warnings and errors when running tests
log.setLevel(logging.WARNING)


class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    
    def setUp(self):
        '''create a MQTTSubscriber instance; set paths for testing'''
        self.ms = MQTTSubscriber()
        self.ms._MQTT_CLIENT = '%s/announce_time.sh' % os.path.dirname(__file__)
        self.ms._MQTT_CLIENT_OPTS = ['-d', '5']
        self.ms._ES_STATE_FILE = '%s/es_state.inf' % os.path.dirname(__file__)
        return super(TestMQTTSubscriber, self).setUp()
    

    def test_getEventParams(self):
        '''test reading event params from mock ES state file'''
        params = self.ms.getEventParams()
        self.assertDictEqual(params, {
            'Version': '2.0',
            'Action': 'gamelistbrowsing',
            'ActionData': '/recalbox/share/roms/mame/1942.zip',
            'System': 'Mame',
            'SystemId': 'mame',
            'Game': '1942 (Revision B)',
            'GamePath': '/recalbox/share/roms/mame/1942.zip',
            'ImagePath': '',
            'IsFolder': '0',
            'ThumbnailPath': '',
            'VideoPath': '',
            'Developer': '',
            'Publisher': '',
            'Players': '1',
            'Region': '',
            'Genre': '',
            'GenreId': '0',
            'Favorite': '0',
            'Hidden': '0',
            'Adult': '0',
            'Emulator': 'libretro',
            'Core': 'mame2003_plus',
            'DefaultEmulator': 'libretro',
            'DefaultCore': 'mame2003_plus',
            'State': 'selected',
            'TestKey': 'a long = string',
        })


    def test_getEvent(self):
        '''test getting events from the mock MQTT server'''
        # start MQTT client
        self.ms.start()
        # read 3 events
        for i in range(1, 3):
            event = self.ms.getEvent()
            if not event:
                break
            self.assertTrue(event.startswith('the time is'))
        # stop client
        self.ms.stop()



    def test_childKilled(self):
        '''test that getEvent() exits cleanly if subscriber process is unexpectedly terminates'''
        # thread to kill subscriber process after 17s
        killer = threading.Thread(target = self._killChild, args=(17,))
        self.ms.start()
        killer.start()
        # read events until child exits
        count = 0
        while True:
            event = self.ms.getEvent()
            if not event:
                break
            count += 1
            print('event received: %s' % event)
            self.assertTrue(event.startswith('the time is'))
        self.assertEqual(count, 4)
        self.assertIsNone(self.ms._childProcess)



    def _killChild(self, delay):
        '''Kill child process after the specified delay in seconds'''
        time.sleep(delay)
        print('killing child process now')
        self.ms._childProcess.kill()