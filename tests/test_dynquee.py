#!/usr/bin/python3

# Unit tests for dynquee module

import unittest, os, logging, time, random
from dynquee import MQTTSubscriber, MediaManager, EventHandler, Slideshow, log, config
from typing import Optional

# uncomment for debug output
# log.setLevel(logging.DEBUG)


# set up config for test environment
def setupTestConfig():
    '''read test config file'''
    configFile = "%s/test_dynquee.ini" % os.path.dirname(__file__)
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
    def getEvent(self, checkInterval: float = 5.0) -> Optional[str]:
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
        self.assertEqual(config.get('media', 'media_path'), 'tests/media')
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
        # publisher media containing space
        self.assertEqual(
            self.mm.getMedia(
                action = 'rungame',
                evParams = {
                    'SystemId': 'mame', 'GamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'Publisher': 'Data East'
                }
            ),
            ['tests/media/publisher/data east.png']
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
        self._currentState = self.ESState()


class TestEventHandler(unittest.TestCase):
    '''unit tests for TestHandler'''

    _INIT_EV_PARAMS = {
        'Action': None,
        'SystemId': None,
        'GamePath': None,
        'IsFolder': '0'
    }

    _NEW_EV_PARAMS = {
        'Action': 'systembrowsing',
        'SystemId': 'mame',
        'GamePath': '',
        'IsFolder': '0'        
    }

    @classmethod
    def getInitState(cls, action, evParams={}):
        return EventHandler.ESState(
            action = action,
            system = evParams.get('SystemId', cls._INIT_EV_PARAMS['SystemId']),
            game = evParams.get('GamePath', cls._INIT_EV_PARAMS['GamePath']),
            isFolder = evParams.get('IsFolder', cls._INIT_EV_PARAMS['IsFolder'])
        )

    @classmethod
    def getNewState(cls, action = None, evParams={}):
        return EventHandler.ESState(
            action = action or cls._NEW_EV_PARAMS['Action'],
            system = evParams.get('SystemId', cls._NEW_EV_PARAMS['SystemId']),
            game = evParams.get('GamePath', cls._NEW_EV_PARAMS['GamePath']),
            isFolder = evParams.get('IsFolder', cls._NEW_EV_PARAMS['IsFolder'])
        )



    def setUp(self):
        self.eh = MockEventHandler()
        self._initEvParams = self._INIT_EV_PARAMS.copy()
        self._newEvParams = self._NEW_EV_PARAMS.copy()


    def tearDown(self):
        del(self.eh)

    
    def test_updateState(self):
        self.assertIsNone(self.eh._currentState.action)
        self.assertIsNone(self.eh._currentState.system)
        self.assertIsNone(self.eh._currentState.game)
        self.assertFalse(self.eh._currentState.isFolder)
        self.eh._updateState(self._NEW_EV_PARAMS)
        self.assertEqual(self.eh._currentState.action, 'systembrowsing')
        self.assertEqual(self.eh._currentState.system, 'mame')
        self.assertEqual(self.eh._currentState.game, '')
        self.assertFalse(self.eh._currentState.isFolder)


    def test_hasStateChanged(self):
        (changeOn, noChangeOn) = ('action', 'endgame wakeup')
        self._newEvParams['Action'] = 'myaction'
        # initial blank state: expect no state change
        self.assertFalse(self.eh._hasStateChanged(self._INIT_EV_PARAMS, changeOn, noChangeOn))
        # new state: expect state change
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # update event handler with new state
        self.eh._updateState(self._newEvParams)
        # compare to newState: expect no state change
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))


    def test_stateChangeAlways(self):
        (changeOn, noChangeOn) = ("always", 'endgame wakeup')
        self._initEvParams['Action'] = 'myaction'
        self.assertTrue(self.eh._hasStateChanged(self._initEvParams, changeOn, noChangeOn))
        self.eh._updateState(self._NEW_EV_PARAMS)
        # check no change of details still causes state change
        self.assertTrue(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertTrue(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different actions
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        self._newEvParams['Action'] = 'rungame'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))


    def test_stateChangeNever(self):
        (changeOn, noChangeOn) = ("never", 'endgame wakeup')
        # check no change of details causes no state change
        self._newEvParams['Action'] = 'systembrowsing'
        self.eh._updateState(self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different action
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, changeOn, noChangeOn))
        # check with different system or game
        self.assertFalse(self.eh._hasStateChanged({'Action':'systembrowsing','SystemId':'snes','GamePath':''}, changeOn, noChangeOn))
        self.assertFalse(self.eh._hasStateChanged({'Action':'systembrowsing','SystemId':'mame','GamePath':'asteroid.zip'}, changeOn, noChangeOn))

    
    def test_stateChangeOnAction(self):
        (changeOn, noChangeOn) = ("action", 'endgame wakeup')
        # check with same action & different system & game
        self.eh._updateState(self._NEW_EV_PARAMS)
        self._newEvParams['Action'] = 'systembrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with different action & game system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check sleep action & no params
        self.eh._updateState(self._newEvParams)
        self._newEvParams['Action'] = 'sleep'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))

    
    def test_stateChangeOnSystem(self):
        (changeOn, noChangeOn) = ("system", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with same action & game, new system
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'snes'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))

    
    def test_stateChangeOnGame(self):
        (changeOn, noChangeOn) = ("game", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with same action & system, new game
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'mame'
        self._newEvParams['GamePath'] = 'asteroid.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
    
    
    def test_stateChangeOnSystemOrGame(self):
        (changeOn, noChangeOn) = ("system/game", 'endgame wakeup')
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with same action & game, new system
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'snes'
        self._newEvParams['GamePath'] = ''
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with same action & system, new game
        self._newEvParams['GamePath'] = 'asteroid.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        # check with same action, new system & game
        self._newEvParams['SystemId'] = 'megadrive'
        self._newEvParams['GamePath'] = 'sonic.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn))
        

    def test_stateChangeOnInvalidSearchTerm(self):
        (changeOn, noChangeOn) = ("blah", 'endgame wakeup')
        # check invalid search term causes error
        with self.assertLogs(log, logging.ERROR):
            self.eh._hasStateChanged(self._newEvParams, changeOn, noChangeOn)


    def test_getStateChangeRules(self):
        (changeOn, noChangeOn) = self.eh._getStateChangeRules()
        self.assertEqual(changeOn, 'system/game')
        self.assertEqual(noChangeOn, 'endgame')



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
        self.assertEqual(cm.output, ["INFO:dynquee:EmulationStation state changed: action=systembrowsing system=mame game=", "INFO:dynquee:new slideshow media=['tests/media/generic/generic01.mp4']"])


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
        self.assertEqual(cm.output, ['INFO:dynquee:EmulationStation state changed: action=gamelistbrowsing system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:dynquee:new slideshow media=['tests/media/generic/generic01.mp4']"])

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
        self.assertEqual(cm.output, ['INFO:dynquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/chasehq.zip', "INFO:dynquee:new slideshow media=['tests/media/mame/chasehq.png']"])

        # test rungame with only publisher image available
        with self.assertLogs(log, level=logging.INFO) as cm:
            self.eh._handleEvent(
                action = 'rungame',
                evParams = {
                    'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/bublbobl.zip', 'Publisher':'Taito'
                }
            )
        self.assertEqual(cm.output, ['INFO:dynquee:EmulationStation state changed: action=rungame system=mame game=/recalbox/share_init/roms/mame/bublbobl.zip', "INFO:dynquee:new slideshow media=['tests/media/publisher/taito.png']"])


class TestESState(unittest.TestCase):

    def testInit(self):
        # test constructor with no args
        state = EventHandler.ESState()
        self.assertIsNone(state.action)
        self.assertIsNone(state.system)
        self.assertIsNone(state.game)
        self.assertFalse(state.isFolder)
        # test constructor with kw args
        state = EventHandler.ESState(
            action='ABC123',
            game='DEF456',
            isFolder=True
        )
        self.assertEqual(state.action, 'ABC123')
        self.assertIsNone(state.system)
        self.assertEqual(state.game, 'DEF456')
        self.assertTrue(state.isFolder)


    def testFromEvent(self):
        evParams = {
            'Action': 'XYZ987',
            'SystemId': 'UVW654',
            'IsFolder': '1'
        }
        state = EventHandler.ESState.fromEvent(evParams)
        self.assertEqual(state.action, 'XYZ987')
        self.assertEqual(state.system, 'UVW654')
        self.assertEqual(state.game, '')
        self.assertTrue(state.isFolder)
