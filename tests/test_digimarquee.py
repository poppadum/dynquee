#!/usr/bin/python3

# Unit tests for digimarquee module

import unittest, os, logging, threading, time, random
from digimarquee import MQTTSubscriber, MediaManager, EventHandler, Slideshow, log, config

# uncomment for debug output
# log.setLevel(logging.DEBUG)


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
        self.assertEqual(config.get('recalbox', 'ES_STATE_FILE'), 'tests/es_state.inf')

    
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
        self.assertEqual(config.get('media', 'BASE_PATH'), 'tests/media')
        self.assertEqual(config.get('media', 'default_image'), 'default.png')

    
    def test_getMediaMatching(self):
        '''test that glob patterns work as expected'''
        self.assertEqual(self.mm._getMediaMatching('XXXXXXX'), [])
        self.assertEqual(self.mm._getMediaMatching('default.*'), ['tests/media/default.png'])

    
    def test_getPrecedence(self):
        self.assertEqual(self.mm._getPrecedence('default'), ['generic'])
        self.assertEqual(self.mm._getPrecedence('__NOT_FOUND'), ['generic'])
        self.assertEqual(self.mm._getPrecedence('gamelistbrowsing'), ['system', 'generic'])

    
    def test_getMedia(self):
        # test getting ROM-specific media
        precedence = 'rom scraped publisher system genre generic'
        config.set(self.mm._CONFIG_SECTION, 'rungame', precedence)
        
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'
                }
            ),
            ['tests/media/mame/chasehq.png']
        )
        # publisher media
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'SystemId': 'mame', 'GamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'Publisher': 'Taito'
                }
            ),
            ['tests/media/publisher/taito.png']
        )
        # scraped game image: should return imagePath
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'ImagePath': '/path/to/scraped_image'
                }
            ),
            ['/path/to/scraped_image']
        )
        # genre image:
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'SystemId': 'UNKNOWN', 'GamePath': '/recalbox/share_init/roms/_/UNKNOWN.zip', 'Genre': 'Shooter'
                }
            ),
            ['tests/media/genre/shooter.png']
        )
        # generic
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {'SystemId': 'UNKNOWN'}
            ),
            ['tests/media/generic/generic01.mp4']
        )
        # test ROM it won't know: should return generic media file
        self.assertEqual(
            self.mm.getMedia(
                action = 'gamelistbrowsing',
                evParams = {'SystemId': 'UNKNOWN', 'GamePath': 'XXXX'}
            ),
            ['tests/media/generic/generic01.mp4']
        )

        # test complex rule chunk
        config.set(self.mm._CONFIG_SECTION, 'rungame', 'rom+publisher+system scraped')
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'
                }
            ),
            ['tests/media/mame/chasehq.png', 'tests/media/publisher/taito.png']
        )

    
    def test_getStartupMedia(self):
        startupMedia = self.mm.getStartupMedia()
        self.assertEqual(startupMedia, ['tests/media/startup/startup01.png', 'tests/media/startup/welcome.mp4'])



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
        (changeOn, noChangeOn) = self.eh._getStateChangeRules()
        self.assertFalse(self.eh._hasStateChanged('myaction', self._INIT_EV_PARAMS, changeOn, noChangeOn))
        self.assertTrue(self.eh._hasStateChanged('myaction', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))

    
    def test_stateChangeAlways(self):
        (changeOn, noChangeOn) = ("always", 'endgame wakeup')
        self.assertTrue(self.eh._hasStateChanged('myaction', self._INIT_EV_PARAMS, changeOn, noChangeOn))
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        # check no change of details still causes state change
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different actions
        self.assertTrue(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertTrue(self.eh._hasStateChanged('rungame', self._NEW_EV_PARAMS, changeOn, noChangeOn))


    def test_stateChangeNever(self):
        (changeOn, noChangeOn) = ("never", 'endgame wakeup')
        # check no change of details causes no state change
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different action
        self.assertFalse(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different system or game
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', {'SystemId':'snes','GamePath':''}, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', {'SystemId':'mame','GamePath':'asteroid.zip'}, changeOn, noChangeOn))


    def test_stateChangeOnAction(self):
        (changeOn, noChangeOn) = ("action", 'endgame wakeup')
        # check with same action & different system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._INIT_EV_PARAMS, changeOn, noChangeOn))
        # check with different action & game system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check sleep action & no params
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('sleep', self._INIT_EV_PARAMS, changeOn, noChangeOn))

    
    def test_stateChangeOnSystem(self):
        (changeOn, noChangeOn) = ("system", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with new action, same system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with same action & game, new system
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', {'SystemId':'snes','GamePath':''}, changeOn, noChangeOn))

    
    def test_stateChangeOnGame(self):
        (changeOn, noChangeOn) = ("game", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with new action, same system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with same action & system, new game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', {'SystemId':'mame','GamePath':'asteroid.zip'}, changeOn, noChangeOn))
    

    def test_stateChangeOnSystemOrGame(self):
        (changeOn, noChangeOn) = ("system/game", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('systembrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with new action, same system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged('gamelistbrowsing', self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with same action & game, new system
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', {'SystemId':'snes','GamePath':''}, changeOn, noChangeOn))
        # check with same action & system, new game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', {'SystemId':'mame','GamePath':'asteroid.zip'}, changeOn, noChangeOn))
        # check with same action, new system & game
        self.eh._updateState('systembrowsing', self._NEW_EV_PARAMS)
        self.assertTrue(self.eh._hasStateChanged('systembrowsing', {'SystemId':'megadrive','GamePath':'sonic.zip'}, changeOn, noChangeOn))
        

    def test_getStateChangeRules(self):
        (changeOn, noChangeOn) = self.eh._getStateChangeRules()
        self.assertEqual(changeOn, 'system/game')
        self.assertEqual(noChangeOn, 'endgame wakeup')



    @unittest.skip('method not suitable for unit testing; TODO: refactor into 2 or more methods')
    def test_handleEvent(self):
        #test systembrowsing
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'systembrowsing',
                evParams = {
                    'SystemId':'mame', 'GamePath':''
                }
            )
        print(f"\n{cm.output}\n")
        self.assertEqual(cm.output, ["INFO:digimarquee:EmulationStation state changed: action=systembrowsing system=mame game=", "INFO:digimarquee:new slideshow media=['tests/media/generic/generic01.mp4']"])


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
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=gamelistbrowsing system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow media=['tests/media/generic/generic01.mp4']"])

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
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:digimarquee:new slideshow media=['tests/media/mame/chasehq.png']"])

        # test rungame with only publisher image available
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/bublbobl.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:digimarquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/bublbobl.zip', "INFO:digimarquee:new slideshow media=['tests/media/publisher/taito.png']"])
