#!/usr/bin/python

# Unit tests for digimarquee module

import unittest, os, logging, threading, time
from digimarquee import MQTTSubscriber, MediaManager, log

# only log warnings and errors when running tests
log.setLevel(logging.WARNING)


class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    
    def setUp(self):
        '''create a MQTTSubscriber instance; set paths for testing'''
        self.ms = MQTTSubscriber()
        self.ms._MQTT_CLIENT = '%s/announce_time.sh' % os.path.dirname(__file__)
        self.ms._MQTT_CLIENT_OPTS = ['-d', '3']
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
        '''test getting events from the mock MQTT client'''
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
        self.assertEqual(count, 6)
        self.assertIsNone(self.ms._childProcess)



    def _killChild(self, delay):
        '''Kill child process after the specified delay in seconds'''
        time.sleep(delay)
        print('killing child process now')
        self.ms._childProcess.kill()



class TestMediaManager(unittest.TestCase):
    '''unit tests for MediaManager'''
    
    def setUp(self):
        '''create a MediaManager instance; set paths for testing'''
        self.mm = MediaManager()
        self.mm._MARQUEE_BASE_PATH = '%s/media' %  os.path.dirname(__file__)
        self.mm._PLAYER = '/usr/bin/cvlc'
        self.mm._PLAYER_OPTS = ['--loop']
        return super(TestMediaManager, self).setUp()


    def test_getMediaMatching(self):
        '''test that glob patterns work as expected'''
        self.assertIsNone(self.mm._getMediaMatching('XXXXXXX'))
        self.assertEqual(self.mm._getMediaMatching('default.*'), 'test/media/default.png')


    def test_getMedia(self):
        # test getting ROM-specific media
        precedence = ['rom', 'scraped', 'publisher', 'system', 'genre', 'generic']
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'systemId':'mame', 'gamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'publisher':'Taito'
                }
            ),
            'test/media/mame/chasehq.png'
        )
        # publisher media
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'systemId': 'mame', 'gamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'publisher': 'Taito'
                }
            ),
            'test/media/publisher/taito.png'
        )
        # scraped game image: should return imagePath
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'imagePath': '/path/to/scraped_image'
                }
            ),
            '/path/to/scraped_image'
        )
        # genre image:
        # TODO: genre-based search not implemented yet
        # self.assertEqual(
        #     self.mm.getMedia(action='gamelistbrowsing', systemId='UNKNOWN', gamePath='/recalbox/share_init/roms/_/UNKNOWN.zip', genre='Shooter'),
        #     '/test/media/genre/shooter.png'
        # )
        # generic
        self.assertEqual(
            self.mm.getMedia(
                precedence=precedence,
                params = {'systemId': 'UNKNOWN'}
            ),
            'test/media/generic/generic01.mp4'
        )


    def test_showOnMarquee(self):
        '''Test we can show the default image on screen: checks player process pid is non-zero.
        '''
        self.mm.showOnMarquee('./media/default.png')
        time.sleep(2)
        self.assertNotEqual(self.mm._childProcess.pid, 0)
        time.sleep(1)
        self.mm.clearMarquee()
