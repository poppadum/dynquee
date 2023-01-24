#!/usr/bin/python

# Unit tests for digimarquee module

import unittest, os, logging, threading, time
from digimarquee import MQTTSubscriber, MediaManager, EventHandler, log, config

# only log warnings and errors when running tests
log.setLevel(logging.WARNING)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_digimarquee.config.txt" % os.path.dirname(__file__)
    print("loading test config file: %s" % configFile)
    config.read(configFile)

setupTestConfig()



class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    def setUp(self):
        '''create a MQTTSubscriber instance'''
        self.ms = MQTTSubscriber()


    def testConfigLoaded(self):
        self.assertEqual(config.get('recalbox', 'MQTT_CLIENT'), 'test/announce_time.sh')
        self.assertEqual(config.get('recalbox', 'MQTT_CLIENT_OPTS'), '-d 3')
        self.assertEqual(config.get('recalbox', 'ES_STATE_FILE'), 'test/es_state.inf')


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
        self.ms.start()
        # thread to kill subscriber process after 17s
        killer = threading.Timer(17.0, __killProcess, args=(self.ms._childProcess,))
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


# Not sure why name has to be as it is, but that's what the test runner looks for
def _TestMQTTSubscriber__killProcess(process):
    '''Kill process'''
    print('killing child process now')
    process.kill()



class TestMediaManager(unittest.TestCase):
    '''unit tests for MediaManager'''
    
    def setUp(self):
        '''create a MediaManager instance'''
        self.mm = MediaManager()


    def test_configLoaded(self):
        self.assertEqual(config.get('media', 'BASE_PATH'), 'test/media')
        self.assertEqual(config.get('media', 'PLAYER'), '/usr/bin/cvlc')
        self.assertEqual(config.get('media', 'PLAYER_OPTS'), '--loop')


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
            Also test clearing image
        '''
        self.mm.showOnMarquee('./media/default.png')
        time.sleep(2)
        self.assertEqual(self.mm._currentMedia, './media/default.png')
        self.assertNotEqual(self.mm._childProcess.pid, 0)
        self.mm.clearMarquee()
        time.sleep(1)
        self.assertIsNone(self.mm._currentMedia)
        self.assertIsNone(self.mm._childProcess)



class TestEventHandler(unittest.TestCase):
    '''unit tests for TestHandler'''

    def setUp(self):
        self.eh = EventHandler()


    def test_getPrecedence(self):
        self.assertEqual(self.eh._getPrecedence('default'), ['generic'])
        self.assertEqual(self.eh._getPrecedence('__NOT_FOUND'), ['generic'])
        self.assertEqual(self.eh._getPrecedence('gamelistbrowsing'), ['system', 'genre', 'generic'])

    
    def test_handleEvent(self):
        self.eh._handleEvent(
            event = 'rungame',
            params = {
                'systemId':'mame', 'gamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'publisher':'Taito'
            }
        )
        self.assertEqual(self.eh._mm._currentMedia, 'test/media/mame/chasehq.png')
        time.sleep(1)
