#!/usr/bin/python3

# Unit tests for digimarquee module

import unittest, os, logging, threading, time, random
from digimarquee import MQTTSubscriber, MediaManager, EventHandler, Slideshow, log, config

# only log warnings and errors when running tests
log.setLevel(logging.INFO)

# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_digimarquee.config.txt" % os.path.dirname(__file__)
    config.read(configFile)
    log.info("loaded test config file: %s" % configFile)

setupTestConfig()


class MockMQTTSubscriber(MQTTSubscriber):
    _VALID_ACTIONS = ['systembrowsing','gamelistbrowsing','rungame','endgame']
    def __init__(self):
        super().__init__()
        self._disconnect = False
    def start(self):
        pass
    def stop(self):
        self._disconnect = True
    def getEvent(self) -> str:
        if self._disconnect: return None
        time.sleep(1)
        action:str = random.choice(self._VALID_ACTIONS)
        log.info(f"generate action {action}")
        return action


class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    def setUp(self):
        '''create a MQTTSubscriber instance'''
        self.ms = MockMQTTSubscriber()

    def tearDown(self):
        '''delete MQTTSubscriber instance'''
        del(self.ms)

    
    def testConfigLoaded(self):
        self.assertEqual(config.get('recalbox', 'host'), '127.0.0.1')
        self.assertEqual(config.getint('recalbox', 'port'), 1883)
        self.assertEqual(config.getint('recalbox', 'keepalive'), 60)
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
            self.assertIn(event, self.ms._VALID_ACTIONS)
        # stop client
        self.ms.stop()
        time.sleep(2)


    

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


class MockEventHandler(EventHandler):
    def __init__(self):
        self._ms: MQTTSubscriber = MockMQTTSubscriber()
        self._mm: MediaManager = MediaManager()
        self._sl: Slideshow = Slideshow(timeout=7.0)
        # record current state of EmulationStation
        self._currentAction = None
        self._currentSystem = None
        self._currentGame = None



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
        self.eh = MockEventHandler()

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
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=systembrowsing system=mame game=', "INFO:digimarquee:new slideshow media=['test/media/generic/generic01.mp4']"])

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
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=gamelistbrowsing system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow media=['test/media/generic/generic01.mp4']"])

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
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow media=['test/media/mame/chasehq.png']"])

        # test rungame with only publisher image available
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/bublbobl.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/bublbobl.zip', "INFO:digimarquee:new slideshow media=['test/media/publisher/taito.png']"])
