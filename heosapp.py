from inspect import currentframe
import asyncio
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

SOURCE_ID = 5 # Deezer
pytheos.set_log_level(0)
elem = None


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

async def connect():
    services = await pytheos.discover(5)
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

async def updateAfterConnect():
    heos.subscribe('event/player_state_changed', _on_player_state_changed)
    heos.subscribe('event/player_now_playing_changed',
                   _on_now_playing_changed)
    heos.subscribe('event/player_queue_changed', _on_queue_changed)
    heos.subscribe('event/player_volume_changed', _on_volume_changed)
    players = await heos.get_players()
    global player
    player = players[0]
    sources = await getSources()
    print(sources)
    window.set_title(f'HEOS App ({player.name})')
    window['-SEARCH-'].update(value='3 ', move_cursor_to="end")
    window['-SEARCH-'].SetFocus()
    await updateQueue()
    volume = await player.get_volume()
    window['-VOLUME-'].update(value=volume)
    window['-VOLUME-'].set_tooltip(f'Volume: {volume}')

async def getSources():
    sources = await heos.get_sources()
    return [(source.id, source.name) for source in sources.values()]

async def updateQueue():
    if heos.connected == True:
        sg.PopupAnimated(loading_animation)
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
        window['-SRESULT-'].SetFocus(True)
        sg.PopupAnimated(None)

async def playFromQueue(d: dict):
    if len(d['-QUEUE-']) == 1 and heos.connected == True:
        sg.PopupAnimated(loading_animation)
        index = d['-QUEUE-'][0]+1
        await heos.api.player.play_queue(player.id, index)
        sg.PopupAnimated(None)


async def playNext():
    if heos.connected == True:
        sg.PopupAnimated(loading_animation)
        await player.next()
        sg.PopupAnimated(None)


async def playPrevious():
    if heos.connected == True:
        sg.PopupAnimated(loading_animation)
        await player.previous()
        sg.PopupAnimated(None)


async def playPause():
    if heos.connected == True:
        try:
            sg.PopupAnimated(loading_animation)
            state = await heos.api.player.get_play_state(player.id)
            if state.value == 'stop' or state.value == 'pause':
                await heos.api.player.set_play_state(player.id, PlayState('play'))
            else:
                await heos.api.player.set_play_state(player.id, PlayState('pause'))
        finally:
            print('error occurred.')
            sg.PopupAnimated(None)


async def setVolume(volume: int):
    if heos.connected == True:
        sg.PopupAnimated(loading_animation)
        #window['-VOLUME-'].update(value=volume)
        await heos.api.player.set_volume(player.id, volume)
        sg.PopupAnimated(None)

async def deleteFromQueue(d: dict):
    if len(d['-QUEUE-']) > 0 and heos.connected == True:
        sg.PopupAnimated(loading_animation)
        ids = [id+1 for id in d['-QUEUE-']]
        await heos.api.player.remove_from_queue(player.id, ids)
        sg.PopupAnimated(None)

async def handleNavigation(d: dict, queueType:int=3, open:bool=True):
    # AddToQueueType:
    # PlayNow = 1
    # PlayNext = 2
    # AddToEnd = 3
    # ReplaceAndPlay = 4
    if len(d['-SRESULT-']) > 0 and heos.connected == True:
        sg.PopupAnimated(loading_animation)
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
                media.source_id = SOURCE_ID
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
                    result = await heos.api.browse.browse_source_container(source_id=SOURCE_ID, container_id=media.container_id)
                    for m in result:
                        await heos.api.browse.add_to_queue(
                            player_id=player.id,
                            source_id=m.source_id,
                            container_id=m.container_id,
                            add_type=queueType
                        )
            makeArrowKeysWork(window['-SRESULT-'])
            window['-SRESULT-'].SetFocus(True)
        sg.PopupAnimated(None)

async def getContainer(d: dict):
    if len(d['-SRESULT-']) > 0 and heos.connected == True:
        #sg.PopupAnimated(loading_animation)
        media = window['-SRESULT-'].metadata[d['-SRESULT-'][0]]
        result = await heos.api.browse.browse_source_container(source_id=SOURCE_ID, container_id=media.container_id)
        updateSeachTable(result)
        global undoRedo, lastCall
        undoRedo.add(lastCall)
        lastCall = result

def updateSeachTable(result):
    values = [[source.playable, source.name, source.artist, source.album]
                  for source in result]
    window['-SRESULT-'].update(values)
    makeArrowKeysWork(window['-SRESULT-'])
    window['-SRESULT-'].SetFocus(True)
    window['-SRESULT-'].metadata = result
        #sg.PopupAnimated(None)

async def search(searchString: str):
    if heos.connected == True and len(searchString) > 0:
        sg.PopupAnimated(loading_animation)
        # deezer source id = 5
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
        if searchString != '' and searchCriteria != 4 and searchCriteria != -1: 
            result = await heos.api.browse.search(SOURCE_ID, searchString, searchCriteria)
            updateSeachTable(result)
        elif searchCriteria == 4:
            result = await heos.api.browse.browse_source_container(SOURCE_ID, 'My Playlists')
            updateSeachTable(result)
        else:
            window['-SEARCH-'].SetFocus(True)
        if result != None:
            global undoRedo, lastCall
            undoRedo.add(lastCall)
            lastCall = result
        sg.PopupAnimated(None)

# used for start/stop
window.bind("<Command-p>", "Control + p")
window.bind("<Control-p>", "Control + p")
# search -> search + future command palette
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
window.bind("<Command-R>", "refresh")
window.bind("<Control-R>", "refresh")
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

heos = Pytheos
player = Player
undoRedo = Undoredo(10)
lastCall = None

async def main():
    sg.PopupAnimated(loading_animation)
    await connect()
    global elem
    elem = window.find_element_with_focus()
    sg.PopupAnimated(None)

    while True:
        # sleep is need for the event subscription to work!
        await asyncio.sleep(0.01)
        # timeout in window.read() are needed to not make the event
        # listener hang up himself
        global focus
        event, values = window.read(timeout=400)
        if event != '__TIMEOUT__':
            print(f"event: {event}")
            print(f"values: {values}")
            if elem != None:
                print(f"elem: {elem.Key}")
            # End program if user closes window
            if event == sg.WIN_CLOSED:
                break
            # used window.bind previously to create key combos
            elif event == 'vol_up':
                current = values['-VOLUME-']
                if current < 99:
                    current += 2
                else:
                    current = 100
                await setVolume(current)
            elif event == 'vol_down':
                current = values['-VOLUME-']
                if current > 1:
                    current -= 2
                else:
                    current = 0
                await setVolume(current)
            elif event == 'refresh':
                await connect()
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
            elif event == 'Control + return' and elem != None and elem.Key == '-SRESULT-':
                #BUG: Bug in MacOS with modal windows: https: // github.com/PySimpleGUI/PySimpleGUI/issues/4511
                type = await optionsPopup()
                if type != None:
                    await handleNavigation(values, queueType=type, open=False)
            elif event == 'delete' and elem != None and elem.Key == '-QUEUE-':
                await deleteFromQueue(values)
            elif event == '-PLAY-'or event == 'Control + p':
                await playPause()
            elif event == '-PREV-' or event == 'Control + left':
                await playPrevious()
            elif event == '-NEXT-' or event == 'Control + right':
                await playNext()
            elif event == '-QUEUE-':
                print('play a song')
                await playFromQueue(values)
            elif event == '-VOLUME-':
                print('set volume')
                await setVolume(values['-VOLUME-'])
            elif event == '-COMBO-':
                if values['-COMBO-'] != '':
                    global heos
                    heos = await pytheos.connect(values['-COMBO-'])
                    await updateAfterConnect()
            elif event == '-SRESULT-':
                await handleNavigation(values)
            elif event == 'tab':
                if elem is not None and elem.Key == '-QUEUE-' and len(window['-SRESULT-'].Widget.get_children()) > 0:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-SRESULT-'])
                    window['-SRESULT-'].set_focus(True)
                else:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-QUEUE-'])
                    window['-QUEUE-'].set_focus(True)
            # React if return key was pressed
            elif elem is not None:
                if event == 'return':
                    # If the search box is in focus, search
                    if elem.Type == sg.ELEM_TYPE_INPUT_TEXT:
                        await search(values['-SEARCH-'])
                    # If queue is in focus, play the selected song
                    elif elem.Key == "-QUEUE-":
                        await playFromQueue(values)
                    # If search results are selected, add them to queue
                    elif elem.Key == '-SRESULT-':
                        await handleNavigation(values)
            elem = window.find_element_with_focus()

    window.close()

if __name__ == '__main__':
    asyncio.run(main())

#TODO: add now playing info, add status bar, change search source, add setting
#to set defaults (like source)


