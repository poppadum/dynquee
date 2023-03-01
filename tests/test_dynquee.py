#!/usr/bin/env python3

# Unit tests for dynquee module

import unittest, os, logging, time, random, queue, threading
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

#@unittest.skip('temp skip')
class TestMQTTSubscriber(unittest.TestCase):
    '''unit tests for MQTTSubscriber'''

    def setUp(self):
        '''create a MQTTSubscriber instance'''
        self.ms = MockMQTTSubscriber()

    def tearDown(self):
        '''delete MQTTSubscriber instance'''
        del(self.ms)

    
    def testConfigLoaded(self):
        self.assertEqual(config.get('recalbox', 'host'), 'localhost')
        self.assertEqual(config.getint('recalbox', 'port'), 1883)
        self.assertEqual(config.getint('recalbox', 'keepalive'), 600)
        self.assertEqual(config.get('recalbox', 'es_state_local_file'), 'tests/es_state.inf')
        self.assertEqual(config.get('recalbox', 'es_state_remote_url'), 'http://localhost/get?option=readFile&params=file=/tmp/es_state.inf')

    
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


#@unittest.skip('temp skip')
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
        self.assertEqual(self.mm._getPrecedenceRule('default'), ['generic'])
        self.assertEqual(self.mm._getPrecedenceRule('__NOT_FOUND'), ['generic'])
        self.assertEqual(self.mm._getPrecedenceRule('gamelistbrowsing'), ['system', 'generic'])

    
    def test_getMedia(self):
        # test getting ROM-specific media
        precedence = 'rom scraped publisher system genre generic'
        config.set(self.mm._CONFIG_SECTION, 'rungame', precedence)
        
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'}
            ),
            ['tests/media/mame/chasehq.png']
        )
        # publisher media
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId': 'mame', 'GamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'Publisher': 'Taito'}
            ),
            ['tests/media/publisher/taito.png']
        )
        # publisher media containing space
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId': 'mame', 'GamePath': '/recalbox/share_init/roms/mame/UNKNOWN.zip', 'Publisher': 'Data East'}
            ),
            ['tests/media/publisher/data east.png']
        )
        # scraped game image: should return imagePath
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'ImagePath': '/path/to/scraped_image'}
            ),
            ['/path/to/scraped_image']
        )
        # genre image:
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId': 'UNKNOWN', 'GamePath': '/recalbox/share_init/roms/_/UNKNOWN.zip', 'Genre': 'Shooter'}
            ),
            ['tests/media/genre/shooter.png']
        )
        # generic
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId': 'UNKNOWN'}
            ),
            ['tests/media/generic/10sCountdown.mp4', 'tests/media/generic/1MinCountdown.mp4']
        )
        # test ROM it won't know: should return generic media file
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'gamelistbrowsing', 'SystemId': 'UNKNOWN', 'GamePath': 'XXXX'}
            ),
            ['tests/media/generic/10sCountdown.mp4', 'tests/media/generic/1MinCountdown.mp4']
        )

        # test complex rule chunk
        config.set(self.mm._CONFIG_SECTION, 'rungame', 'rom+publisher+system scraped')
        self.assertEqual(
            self.mm.getMedia(
                {'Action': 'rungame', 'SystemId':'mame', 'GamePath':'/recalbox/share_init/roms/mame/chasehq.zip', 'Publisher':'Taito'}
            ),
            ['tests/media/mame/chasehq.png', 'tests/media/publisher/taito.png']
        )

    
    def test_getStartupMedia(self):
        startupMedia = self.mm.getStartupMedia()
        self.assertEqual(startupMedia, ['tests/media/startup/startup01.png', 'tests/media/startup/welcome.mp4'])



class TestSlideshow(unittest.TestCase):
    def setUp(self):
        self.sl = Slideshow()

    def tearDown(self):
        self.sl.stop()

    def test_init(self):
        self.assertIsInstance(self.sl._queue, queue.SimpleQueue)
        self.assertTrue(self.sl._queue.empty())
        self.assertEqual(self.sl._currentMedia, [])
        self.assertFalse(self.sl._mediaChange.is_set())
        self.assertFalse(self.sl._exitSignalled.is_set())
        self.assertIsNone(self.sl._slideshowThread)
        self.assertIsInstance(self.sl._queueReaderThread, threading.Thread)

    def test_getCmdList(self):
        cmd = "echo"
        vars = {
            'file': 'a filename with spaces.txt',
            'num': 123,
        }
        self.assertEqual(self.sl._getCmdList(cmd, "{file}", file="normal.png"), ['echo', 'normal.png'])
        self.assertEqual(self.sl._getCmdList(cmd, "{file} {num}", **vars), ['echo', 'a filename with spaces.txt', '123'])
        self.assertEqual(self.sl._getCmdList(cmd, "{file}", **vars), ['echo', 'a filename with spaces.txt'])
        self.assertEqual(self.sl._getCmdList(cmd, "{file}", file="a 'funny name"), ['echo', 'a \'funny name'])
        self.assertEqual(self.sl._getCmdList(cmd, 'this is "a test" {file} xxx-yyy .b_', **vars), ['echo', 'this', 'is', 'a test', 'a filename with spaces.txt', 'xxx-yyy', '.b_'])
        self.assertEqual(self.sl._getCmdList(cmd, 'abc de"f', **vars), ['echo', 'abc', 'de"f'])


class MockEventHandler(EventHandler):
    def __init__(self):
        self._ms: MQTTSubscriber = MockMQTTSubscriber()
        self._mm: MediaManager = MediaManager()
        self._sl: Slideshow = Slideshow()
        # record current state of EmulationStation
        self._currentState = self.ESState()

#@unittest.skip('temp skip')
class TestEventHandler(unittest.TestCase):
    '''unit tests for TestHandler'''

    _INIT_EV_PARAMS = {
        'Action': '',
        'SystemId': '',
        'GamePath': '',
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
        self._changeRules: EventHandler.ChangeRuleSet = {
            'systembrowsing': 'action',
            'gamelistbrowsing': 'system/game',
            'rungame': 'action',
            'endgame': 'never',
            'sleep': 'always',
        }


    def tearDown(self):
        self.eh._sl.stop()
        del(self.eh)

    
    def test_updateState(self):
        self.assertEqual(self.eh._currentState.action, '')
        self.assertEqual(self.eh._currentState.system, '')
        self.assertEqual(self.eh._currentState.game, '')
        self.assertFalse(self.eh._currentState.isFolder)
        evParams = self._NEW_EV_PARAMS.copy()
        evParams['GamePath'] = 'path/to/agame.zip'
        evParams['IsFolder'] = '1'
        self.eh._updateState(evParams)
        self.assertEqual(self.eh._currentState.action, 'systembrowsing')
        self.assertEqual(self.eh._currentState.system, 'mame')
        self.assertEqual(self.eh._currentState.game, 'path/to/agame.zip')
        self.assertTrue(self.eh._currentState.isFolder)


    def test_hasStateChanged(self):
        # (changeOn, noChangeOn) = ('action', 'endgame wakeup')
        self._newEvParams['Action'] = 'myaction'
        self._changeRules['myaction'] = 'action'
        # initial blank state: expect no state change
        self.assertFalse(self.eh._hasStateChanged(self._INIT_EV_PARAMS, self._changeRules))
        # new state: expect state change
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # update event handler with new state
        self.eh._updateState(self._newEvParams)
        # compare to newState: expect no state change
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))


    def test_stateChangeAlways(self):
        self._initEvParams['Action'] = 'myaction'
        self._changeRules['myaction'] = 'always'
        self._changeRules['systembrowsing'] = 'always'
        self._changeRules['gamelistbrowsing'] = 'always'
        self._changeRules['rungame'] = 'always'
        self.assertTrue(self.eh._hasStateChanged(self._initEvParams, self._changeRules))
        self.eh._updateState(self._NEW_EV_PARAMS)
        # check no change of details still causes state change
        self.assertTrue(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        self.assertTrue(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        # check with different actions
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        self._newEvParams['Action'] = 'rungame'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))


    def test_stateChangeNever(self):
        # check no change of details causes no state change
        self._newEvParams['Action'] = 'systembrowsing'
        self._changeRules['systembrowsing'] = 'never'
        self.eh._updateState(self._NEW_EV_PARAMS)
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        # check with different action
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._NEW_EV_PARAMS, self._changeRules))
        # check with different system or game
        self.assertFalse(self.eh._hasStateChanged({'Action':'systembrowsing','SystemId':'snes','GamePath':''}, self._changeRules))
        self.assertFalse(self.eh._hasStateChanged({'Action':'systembrowsing','SystemId':'mame','GamePath':'asteroid.zip'}, self._changeRules))


    def test_stateChangeOnAction(self):
        self._changeRules['gamelistbrowsing'] = 'action'
        # check with same action & different system & game
        self.eh._updateState(self._NEW_EV_PARAMS)
        self._newEvParams['Action'] = 'systembrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with different action & game system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check sleep action & no params: expect state change
        self.eh._updateState(self._newEvParams)
        self._newEvParams['Action'] = 'sleep'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))


    def test_stateChangeOnSystem(self):
        self._changeRules['systembrowsing'] = 'system'
        self._changeRules['gamelistbrowsing'] = 'system'
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with same action & game, new system
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'snes'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))


    def test_stateChangeOnGame(self):
        self._changeRules['systembrowsing'] = 'game'
        self._changeRules['gamelistbrowsing'] = 'game'
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with same action & system, new game
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'mame'
        self._newEvParams['GamePath'] = 'asteroid.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
    

    def test_stateChangeOnSystemOrGame(self):
        self._changeRules['systembrowsing'] = 'system/game'
        # check with same action, system & game
        self.eh._updateState(self._newEvParams)
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with new action, same system & game
        self._newEvParams['Action'] = 'gamelistbrowsing'
        self.assertFalse(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with same action & game, new system
        self._newEvParams['Action'] = 'systembrowsing'
        self._newEvParams['SystemId'] = 'snes'
        self._newEvParams['GamePath'] = ''
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with same action & system, new game
        self._newEvParams['GamePath'] = 'asteroid.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))
        # check with same action, new system & game
        self._newEvParams['SystemId'] = 'megadrive'
        self._newEvParams['GamePath'] = 'sonic.zip'
        self.assertTrue(self.eh._hasStateChanged(self._newEvParams, self._changeRules))


    def test_stateChangeOnInvalidSearchTerm(self):
        self._changeRules['systembrowsing'] = 'XXXX'
        # check invalid search term causes error
        with self.assertLogs(log, logging.ERROR):
            self.eh._hasStateChanged(self._newEvParams, self._changeRules)


    def test_recordStateBeforeSleep(self):
        evParams = self._newEvParams.copy()
        evParamsBeforeSleep = evParams.copy()
        self.eh._updateState(evParams)
        evParams['Action'] = 'sleep'
        evParams['GamePath'] = '/path/to/mygame.zip'
        evParams['IsFolder'] = '1'
        self.eh._updateState(evParams)
        # check state before sleep recorded
        self.assertEqual(self.eh._stateBeforeSleep.action, 'systembrowsing')
        self.assertEqual(self.eh._stateBeforeSleep.system, 'mame')
        self.assertEqual(self.eh._stateBeforeSleep.game, '')
        self.assertFalse(self.eh._stateBeforeSleep.isFolder)
        # check new state recorded
        self.assertEqual(self.eh._currentState.action, 'sleep')
        self.assertEqual(self.eh._currentState.system, 'mame')
        self.assertEqual(self.eh._currentState.game, '/path/to/mygame.zip')
        self.assertTrue(self.eh._currentState.isFolder)
        # check previous state restored on wakeup
        evParams['Action'] = 'wakeup'
        evParams = self.eh._updateState(evParams)
        self.assertEqual(self.eh._currentState.action, 'systembrowsing')
        self.assertEqual(self.eh._currentState.system, 'mame')
        self.assertEqual(self.eh._currentState.game, '')
        self.assertFalse(self.eh._stateBeforeSleep.isFolder)
        # check evParams changed on _updateState wakeup
        self.assertEqual(evParams, evParamsBeforeSleep)

    def test_getStateChangeRules(self):
        stateChangeRules = self.eh._getStateChangeRules()
        print(stateChangeRules)
        self.assertEqual(stateChangeRules, {
            'systembrowsing': 'action',
            'gamelistbrowsing': 'system/game',
            'rungame': 'always',
            'endgame': 'never',
            'runkodi': 'always',
            'sleep': 'always',
        })


#@unittest.skip('temp skip')
class TestESState(unittest.TestCase):

    def testInit(self):
        # test constructor with no args
        state = EventHandler.ESState()
        self.assertEqual(state.action, '')
        self.assertEqual(state.system, '')
        self.assertEqual(state.game, '')
        self.assertFalse(state.isFolder)
        # test constructor with kw args
        state = EventHandler.ESState(
            action='ABC123',
            game='DEF456',
            isFolder=True
        )
        self.assertEqual(state.action, 'ABC123')
        self.assertEqual(state.system, '')
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
