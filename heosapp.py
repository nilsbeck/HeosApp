from inspect import currentframe
import asyncio
from os import wait
from typing import Any
import pytheos
from pytheos.controllers.player import Player
from pytheos.models.browse import AddToQueueType, SearchCriteria, ServiceOption
from pytheos.models.player import PlayState
from pytheos.models.source import Source
from pytheos.pytheos import Pytheos, connect
from pytheos.models.heos import HEOSEvent
from undoredo import Undoredo
from utils import *
from popup import *
from layout import *

# source_id 5 = DEEZER
sources = {}
pytheos.set_log_level(0)
elem = None
# unsupported soruces do not return any search criteria, so I can't use them...
unsupportedSources = [13, 1024, 1025, 1026, 1027, 1028]


async def _on_now_playing_changed(event: HEOSEvent):
    """ Handles event/player_now_playing_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Now Playing Changed Event: {event}')


async def _on_volume_changed(event: HEOSEvent):
    """ Handles event/player_volume_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    d = event.message.split('&')
    volume = d[1].split('=')[1]
    window['-VOLUME-'].update(value=volume)
    #print(f'Volume Changed Event: {level}')


async def _on_queue_changed(event: HEOSEvent):
    """ Handles event/player_queue_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    await updateQueue()
    if elem != None:
        elem.set_focus(True)


async def _on_player_state_changed(event: HEOSEvent):
    """ Handles event/player_state_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Player State Changed Event: {event}')


def updateStatusText(error:str=''):
    status = ''
    if heos.connected == True:
        status = f'Connected to: {player.name} '
    else:
        status = 'Disconnected '
    source = sg.user_settings_get_entry('source_id', 5)
    status += f'| Source: {sources[source][0]} '
    if error != '':
        status += f'| error occurred while {error}'
    window['-STATUS-'].update(value=status)
    global resetCounter
    resetCounter = 0

async def execCommand(fun, info:str, selectResults:bool=False, **kwargs) -> Any:
    sg.PopupAnimated(loading_animation)
    res = None
    try:
        if heos.connected == False:
            await connect()
        res = await fun(**kwargs)
    except:
        updateStatusText(info)
    finally:
        sg.PopupAnimated(None)
        if selectResults:
            makeArrowKeysWork(window['-SRESULT-'])
        elif not selectResults:
            makeArrowKeysWork(window['-QUEUE-'])
        return res

async def connect():
    services = await pytheos.discover(5)
    err = ''
    if services:
        #[service. for service in services]
        window['-COMBO-'].update(values=services, set_to_index=0)
        print("Connecting to first device found...")
        global heos
        heos = await pytheos.connect(services[0])
        print(f"Connected to {heos.server}!")
        await updateAfterConnect()
    else:
        window.set_title(f'HEOS App (DISCONNECTED)')
        makeArrowKeysWork(window['-QUEUE-'])
        err = 'on connecting to HEOS'
    updateStatusText(err)

async def updateAfterConnect():
    heos.subscribe('event/player_state_changed', _on_player_state_changed)
    heos.subscribe('event/player_now_playing_changed',
                   _on_now_playing_changed)
    heos.subscribe('event/player_queue_changed', _on_queue_changed)
    heos.subscribe('event/player_volume_changed', _on_volume_changed)
    players = await heos.get_players()
    global player
    player = players[0]
    global sources
    sources = await execCommand(getSources, 'getting sources')
    source = sg.user_settings_get_entry('source_id', 5)
    if not source in sources:
        sg.user_settings_set_entry('source_id', list(sources.keys())[0])
    window.set_title(f'HEOS App ({player.name})')
    window['-SEARCH-'].update(value='3 ', move_cursor_to="end")
    window['-SEARCH-'].SetFocus(True)
    await updateQueue()
    volume = await player.get_volume()
    window['-VOLUME-'].update(value=volume)
    window['-VOLUME-'].set_tooltip(f'Volume: {volume}')

async def getSources():
    sources = await heos.get_sources()
    return {source.id : [source.name] for source in sources.values()}

async def updateQueue():
    await asyncio.sleep(0.5)
    queue = []
    start = 0
    increment = 100
    while True:
        result = await heos.api.player.get_queue(player.id, start, increment)
        if len(result) == 0:
            break
        if len(queue) == 0:
            queue = result
        else: 
            for item in result:
                queue.append(item)
        start += increment
    if len(queue) > 0:
        cleanedQueue = [[item.song, item.album, item.artist] for item in queue]
        window['-QUEUE-'].update(values=cleanedQueue)
    makeArrowKeysWork(window['-SRESULT-'])

async def playFromQueue(d: dict):
    if len(d['-QUEUE-']) == 1:
        index = d['-QUEUE-'][0]+1
        await heos.api.player.play_queue(player.id, index)


async def playNext():
    await player.next()


async def playPrevious():
    await player.previous()


async def playPause():
    state = await heos.api.player.get_play_state(player.id)
    if state.value == 'stop' or state.value == 'pause':
        await heos.api.player.set_play_state(player.id, PlayState('play'))
    else:
        await heos.api.player.set_play_state(player.id, PlayState('pause'))


async def setVolume(volume: int):
    await heos.api.player.set_volume(player.id, volume)

async def deleteFromQueue(d: dict):
    ids = [id+1 for id in d['-QUEUE-']]
    await heos.api.player.remove_from_queue(player.id, ids)

async def handleNavigation(d: dict, queueType:int=3, open:bool=True):
    # AddToQueueType:
    # PlayNow = 1
    # PlayNext = 2
    # AddToEnd = 3
    # ReplaceAndPlay = 4
    if len(d['-SRESULT-']) > 0:
        isPlayable = True
        for index in d['-SRESULT-']:
            media = window['-SRESULT-'].metadata[index]
            if media.playable == 'no' or (media.type.value == 'album' and open==True):
                isPlayable = False
                await getContainer(d)
                break
        if isPlayable == True:
            for index in d['-SRESULT-']:
                media = window['-SRESULT-'].metadata[index]
                media.source_id = sg.user_settings_get_entry('source_id', 5)
                if media.container_id == None:
                    media.container_id = ''
                print(media.type)
                if media.type.value == 'station':
                    await heos.api.browse.play_station(
                        player_id=player.id,
                        source_id=media.source_id,
                        container_id=media.container_id,
                        media_id=media.media_id,
                        name=media.name
                    )
                elif media.type.value == 'song':
                    await heos.api.browse.add_to_queue(
                        player_id=player.id,
                        source_id=media.source_id,
                        container_id=media.container_id,
                        media_id=media.media_id,
                        add_type=queueType
                    )
                # albums cannot be added directly, although all items in it can
                # be added
                elif media.type.value == 'album':
                    source = sg.user_settings_get_entry('source_id', 5)
                    result = await heos.api.browse.browse_source_container(source_id=source, container_id=media.container_id)
                    for m in result:
                        await heos.api.browse.add_to_queue(
                            player_id=player.id,
                            source_id=m.source_id,
                            container_id=m.container_id,
                            add_type=queueType
                        )
            makeArrowKeysWork(window['-SRESULT-'])

async def getContainer(d: dict):
    if len(d['-SRESULT-']) > 0:
        media = window['-SRESULT-'].metadata[d['-SRESULT-'][0]]
        source = sg.user_settings_get_entry('source_id', 5)
        result = await heos.api.browse.browse_source_container(source_id=source, container_id=media.container_id)
        updateSeachTable(result)
        global undoRedo, lastCall
        undoRedo.add(lastCall)
        lastCall = result

def updateSeachTable(result):
    values = [[source.playable, source.name, source.artist, source.album]
                  for source in result]
    window['-SRESULT-'].update(values)
    window['-SRESULT-'].metadata = result
    makeArrowKeysWork(window['-SRESULT-'])
    
async def search(searchString: str):
    if len(searchString) > 0:
        # search_criteria: 1 - artist
        # search_criteria: 2 - album
        # search_criteria: 3 - track
        searchCriteria = -1
        if searchString[0:1] == ('1' or 'b'):
            searchCriteria = 1
            print('search: artist')
        elif searchString[0:1] == ('2' or 'a'):
            print('search: album')
            searchCriteria = 2
        elif searchString[0:1] == ('3' or 't'):
            print('search: track')
            searchCriteria = 3
        elif searchString[0:1] == ('4' or 'p'):
            searchCriteria = 4
        else:
            return
        searchString = searchString[1:].strip()
        result = None
        source = sg.user_settings_get_entry('source_id', 5)
        if source == 3:
            searchCriteria = 4 # for radio only stations are valid
        if searchString != '' and searchCriteria != 4 and searchCriteria != -1: 
            result = await heos.api.browse.search(source, searchString, searchCriteria)
            updateSeachTable(result)
        elif searchCriteria == 4 and source != 3:
            result = await heos.api.browse.browse_source_container(source, 'My Playlists')
            updateSeachTable(result)
        elif searchCriteria == 4 and source == 3:
            result = await heos.api.browse.search(source, searchString, searchCriteria)
            updateSeachTable(result)
        else:
            window['-SEARCH-'].SetFocus(True)
        if result != None:
            global undoRedo, lastCall
            undoRedo.add(lastCall)
            lastCall = result

# used for start/stop
window.bind("<Command-p>", "Control + p")
window.bind("<Control-p>", "Control + p")
# search
window.bind("<Command-f>", "key_search")
window.bind("<Control-f>", "key_search")
window.bind("<Command-s>", "key_search")
window.bind("<Control-s>", "key_search")
# next song
window.bind("<Command-Right>", "Control + right")
window.bind("<Control-Right>", "Control + right")
# prev song
window.bind("<Command-Left>", "Control + left")
window.bind("<Control-Left>", "Control + left")
# options for adding to queue
window.bind("<Command-Return>", "Control + return")
window.bind("<Control-Return>", "Control + return")
window.bind("<Shift-Return>", "Control + return")
# for readability
window.bind("<Return>", "return")
window.bind("<Tab>", "tab")
# deleting queue items
window.bind("<Command-Delete>", "delete")
window.bind("<Control-Delete>", "delete")
window.bind("<Command-BackSpace>", "delete")
window.bind("<Control-BackSpace>", "delete")
#refresh heos service
window.bind("<Command-r>", "refresh")
window.bind("<Control-r>", "refresh")
#check if window has focus
# window.bind('<FocusIn>', 'foucs_in')
# window.bind('<FocusOut>', 'focus_out')
# Navigate through stack
window.bind('<Left>', 'undo')
window.bind('<Right>', 'redo')
# Volume changes
window.bind("<Shift-Left>", "vol_down")
window.bind("<Shift-Down>", "vol_down")
window.bind("<Shift-Right>", "vol_up")
window.bind("<Shift-Up>", "vol_up")
# select sources -> future settings
window.bind("<Command-k>", "Control + k")
window.bind("<Control-k>", "Control + k")

heos = Pytheos
player = Player
undoRedo = Undoredo(10)
lastCall = None
resetCounter = 0

async def main():
    sg.PopupAnimated(loading_animation)
    global elem
    elem = window.find_element_with_focus()
    await execCommand(connect, 'connecting on start')
    sg.PopupAnimated(None)

    while True:
        # sleep is need for the event subscription to work!
        await asyncio.sleep(0.01)
        # timeout in window.read() are needed to not make the event
        # listener hang up himself
        event, values = window.read(timeout=400)
        global resetCounter
        if resetCounter > 20:
            updateStatusText()
            resetCounter = 0
        resetCounter += 1
        if event != '__TIMEOUT__':
            print(f"event: {event}")
            print(f"values: {values}")
            if elem != None:
                print(f"elem: {elem.Key}")
            # End program if user closes window
            if event == sg.WIN_CLOSED:
                break
            # used window.bind previously to create key combos
            elif event == 'Control + k':
                source = await optionsPopup(sources)
                if source != None:
                    if source in unsupportedSources:
                        sg.popup_error('Cannot set Amazon Music because it is not working as other services with HEOS.',
                            title="Error on setting source"
                        )
                    else:
                        sg.user_settings_set_entry('source_id', source)
                        window['-SRESULT-'].update(values=[])
                        window['-SRESULT-'].metadata = None
                        window['-SEARCH-'].SetFocus(True)
            elif event == 'vol_up':
                current = values['-VOLUME-']
                if current < 99:
                    current += 2
                else:
                    current = 100
                kwargs = {'volume': current}
                await execCommand(setVolume, 'setting volume', **kwargs)
            elif event == 'vol_down':
                current = values['-VOLUME-']
                if current > 1:
                    current -= 2
                else:
                    current = 0
                kwargs = {'volume': current}
                await execCommand(setVolume, 'setting volume', **kwargs)
            elif event == 'refresh':
                await execCommand(connect, 'connecting')
            elif event == 'undo':
                result = undoRedo.undo()
                if result != None:
                    updateSeachTable(result)
            elif event == 'redo':
                result = undoRedo.redo()
                if result != None:
                    updateSeachTable(result)
            elif event == 'key_search':
                window['-SEARCH-'].set_focus(True)
            elif event == 'Control + return' and elem != None and elem.Key == '-SRESULT-' and not sg.user_settings_get_entry('source_id', 3):
                #BUG: Bug in MacOS with modal windows: https: // github.com/PySimpleGUI/PySimpleGUI/issues/4511
                # AddToQueueType:
                # PlayNow = 1
                # PlayNext = 2
                # AddToEnd = 3
                # ReplaceAndPlay = 4
                option = {
                    2: ['Play next'],
                    1: ['Play now'],
                    3: ['Add to end'],
                    4: ['Replace and play']
                }
                type = await optionsPopup(option)
                if type != None:
                    kwargs = {'d':values, 'queueType':type, 'open':False}
                    await execCommand(handleNavigation, 'navigation through results', True, **kwargs)
            elif event == 'delete' and elem != None and elem.Key == '-QUEUE-':
                kwargs = {'d': values}
                await execCommand(deleteFromQueue, 'deleting from queue', **kwargs)
            elif event == '-PLAY-'or event == 'Control + p':
                await execCommand(playPause, 'play/pause', None)
            elif event == '-PREV-' or event == 'Control + left':
                await execCommand(playPrevious, 'playing previous song')
            elif event == '-NEXT-' or event == 'Control + right':
                await execCommand(playNext, 'playing next song')
            elif event == '-QUEUE-':
                kwargs = {'d': values}
                await execCommand(playFromQueue, 'playing from queue', **kwargs)
            elif event == '-VOLUME-':
                kwargs = {'volume': values['-VOLUME-']}
                await execCommand(setVolume, 'setting volume', **kwargs)
            elif event == '-COMBO-':
                if values['-COMBO-'] != '':
                    global heos
                    kwargs = {'host': values['-COMBO-']}
                    heos = await execCommand(pytheos.connect, 'conneting to heos', **kwargs)
                    await execCommand(updateAfterConnect, 'updating after heos connection')
            elif event == '-SRESULT-':
                kwargs = {'d': values}
                await execCommand(handleNavigation, 'navigating results', True, **kwargs)
            elif event == 'tab':
                if elem is not None and elem.Key == '-QUEUE-' and len(window['-SRESULT-'].Widget.get_children()) > 0:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-SRESULT-'])
                else:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-QUEUE-'])
            # React if return key was pressed
            elif elem is not None:
                if event == 'return':
                    # If the search box is in focus, search
                    if elem.Type == sg.ELEM_TYPE_INPUT_TEXT:
                        kwargs = {'searchString': values['-SEARCH-']}
                        await execCommand(search, 'searching sources', True, **kwargs)
                    # If queue is in focus, play the selected song
                    elif elem.Key == "-QUEUE-":
                        kwargs = {'d': values}
                        await execCommand(playFromQueue, 'playing from queue', **kwargs)
                    # If search results are selected, add them to queue
                    elif elem.Key == '-SRESULT-':
                        kwargs = {'d': values}
                        await execCommand(handleNavigation, 'navigating results', True, **kwargs)
            elem = window.find_element_with_focus()
            
    window.close()

if __name__ == '__main__':
    asyncio.run(main())

#TODO: add now playing info


