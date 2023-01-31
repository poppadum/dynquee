#!/usr/bin/python3

# Unit tests for digimarquee module

import unittest, os, logging, threading, time
from digimarquee import ProcessManager, MQTTSubscriber, MediaManager, EventHandler, log, config

# only log warnings and errors when running tests
log.setLevel(logging.INFO)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_digimarquee.config.txt" % os.path.dirname(__file__)
    config.read(configFile)
    log.info("loaded test config file: %s" % configFile)

setupTestConfig()



class TestProcessManager(unittest.TestCase):
    '''unit tests for ProcessManager'''

    def testLaunchFailure(self):
        pm = ProcessManager()
        with self.assertLogs(log, logging.ERROR) as cm:
            pm._launch('/invalid/path')
        self.assertTrue('unable to launch' in cm.output[0])
        self.assertIsNone(pm._subprocess)
        time.sleep(1)



class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    def setUp(self):
        '''create a MQTTSubscriber instance'''
        self.ms = MQTTSubscriber()

    def tearDown(self):
        '''delete MQTTSubscriber instance'''
        del(self.ms)

    
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
        for i in range(1, 4):
            event = self.ms.getEvent()
            if not event:
                break
            self.assertTrue(event.startswith('the time is'))
        # stop client
        self.ms.stop()
        time.sleep(2)


    
    def test_childKilled(self):
        '''test that getEvent() exits cleanly if subscriber process unexpectedly terminates'''
        self.ms.start()
        # thread to kill subscriber process after 17s
        killer = threading.Timer(17.0, __killProcess, args=(self.ms._subprocess,))
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
        self.ms.terminate()
        self.assertIsNone(self.ms._subprocess)


# Not sure why name has to be as it is, but that's what the test runner looks for
def _TestMQTTSubscriber__killProcess(process):
    '''Kill process'''
    log.info('killing process pid=%d' % process.pid)
    process.kill()



class TestMediaManager(unittest.TestCase):
    '''unit tests for MediaManager'''
    
    def setUp(self):
        '''create a MediaManager instance'''
        self.mm = MediaManager()

    def tearDown(self):
        del(self.mm)


    def test_configLoaded(self):
        self.assertEqual(config.get('media', 'BASE_PATH'), 'test/media')
        self.assertEqual(config.get('media', 'PLAYER'), '/usr/bin/cvlc')
        self.assertEqual(config.get('media', 'PLAYER_OPTS'), '--loop')


    def test_getMediaMatching(self):
        '''test that glob patterns work as expected'''
        self.assertEqual(self.mm._getMediaMatching('XXXXXXX'), [])
        self.assertEqual(self.mm._getMediaMatching('default.*'), ['test/media/default.png'])


    def test_getMedia(self):
        # test getting ROM-specific media
        precedence = ['rom', 'scraped', 'publisher', 'system', 'genre', 'generic']
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'
                }
            ),
            ['test/media/mame/chasehq.png']
        )
        # publisher media
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'SystemId': 'mame', 'GamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'Publisher': 'Taito'
                }
            ),
            ['test/media/publisher/taito.png']
        )
        # scraped game image: should return imagePath
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'ImagePath': '/path/to/scraped_image'
                }
            ),
            ['/path/to/scraped_image']
        )
        # genre image:
        self.assertEqual(
            self.mm.getMedia(
                precedence = precedence,
                params = {
                    'SystemId': 'UNKNOWN', 'GamePath': '/recalbox/share_init/roms/_/UNKNOWN.zip', 'Genre': 'Shooter'
                }
            ),
            ['test/media/genre/shooter.png']
        )
        # generic
        self.assertEqual(
            self.mm.getMedia(
                precedence=precedence,
                params = {'SystemId': 'UNKNOWN'}
            ),
            ['test/media/generic/generic01.mp4']
        )
        # test ROM it won't know: should return default media file
        self.assertEqual(
            self.mm.getMedia(
                precedence=['rom'],
                params = {'SystemId': 'UNKNOWN', 'GamePath': 'XXXX'}
            ),
            ['test/media/default.png']
        )
        # test unrecognised rule
        self.assertEqual(
            self.mm.getMedia(
                precedence=['XXX'],
                params = {'SystemId': 'UNKNOWN'}
            ),
            ['test/media/default.png']
        )



class TestEventHandler(unittest.TestCase):
    '''unit tests for TestHandler'''

    _INIT_EV_PARAMS = {
        'SystemId': None,
        'GamePath': None
    }

    _NEW_EV_PARAMS = {
        'SystemId': 'mame',
        'GamePath': ''
    }

    def setUp(self):
        self.eh = EventHandler()

    def tearDown(self):
        del(self.eh)

    def test_updateState(self):
        self.assertIsNone(self.eh._currentAction)
        self.assertIsNone(self.eh._currentSystem)
        self.assertIsNone(self.eh._currentGame)
        self.eh._updateState(action = 'systembrowsing', evParams=self._NEW_EV_PARAMS)
        self.assertEqual(self.eh._currentAction, 'systembrowsing')
        self.assertEqual(self.eh._currentSystem, 'mame')
        self.assertEqual(self.eh._currentGame, '')


    def test_hasStateChanged(self):
        self.assertFalse(self.eh._hasStateChanged(None, evParams=self._INIT_EV_PARAMS))
        self.assertTrue(self.eh._hasStateChanged(None, evParams=self._NEW_EV_PARAMS))
        self.eh._updateState(action='systembrowsing', evParams=self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', evParams=self._NEW_EV_PARAMS))
    
    
    def test_getPrecedence(self):
        self.assertEqual(self.eh._getPrecedence('default'), ['generic'])
        self.assertEqual(self.eh._getPrecedence('__NOT_FOUND'), ['generic'])
        self.assertEqual(self.eh._getPrecedence('gamelistbrowsing'), ['system', 'genre', 'generic'])


    def test_handleEvent(self):
        #test systembrowsing
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'systembrowsing',
                evParams = {
                    'SystemId':'mame', 'GamePath':''
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=systembrowsing system=mame game=', "INFO:digimarquee:new slideshow paths=['test/media/generic/generic01.mp4']"])

        #still systembrowsing - should not change slideshow
        self.eh._handleEvent(
            action = 'systembrowsing',
            evParams = {
                'SystemId':'mame', 'GamePath':''
            }
        )

        #now gamelistbrowsing
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'gamelistbrowsing',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=gamelistbrowsing system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow paths=['test/media/generic/generic01.mp4']"])

        #still gamelistbrowsing - should not change slideshow
        self.eh._handleEvent(
            action = 'gamelistbrowsing',
            evParams = {
                'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/asteroid.zip', 'Publisher':'Atari'
            }
        )

        # test rungame
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow paths=['test/media/mame/chasehq.png']"])

        # test rungame with only publisher image available
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/bublbobl.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/bublbobl.zip', "INFO:digimarquee:new slideshow paths=['test/media/publisher/taito.png']"])
