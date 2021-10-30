from tkinter.constants import FALSE, LEFT, MOVETO, TRUE, X
from tkinter.ttk import Combobox
from PySimpleGUI.PySimpleGUI import T, Combo, Text
import asyncio
import os
import sys
import PySimpleGUI as sg
import pytheos
from pytheos import api
from pytheos.controllers.player import Player
from pytheos.models.browse import AddToQueueType, SearchCriteria, ServiceOption
from pytheos.models.player import PlayState
from pytheos.models.source import Source
from pytheos.pytheos import Pytheos, connect
from pytheos.models.heos import HEOSEvent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


async def setup(heos: Pytheos):
    # with await pytheos.connect('192.168.178.25') as svc:
    #     heos = svc
    #await heos.connect(enable_event_connection=True, refresh=True)
    await heos.sign_in(username='nils.beckmann@gmail.com', password='7Rqok3qk8GZDQ4jB')
    #print(heos.connected)
    players = await heos.get_players()
    global player
    player = players[0]
    #window['-TEXT-'].update(f"Status: Connected to {player.name}")
    #window['-TABLE-'].expand(True, True)


async def updateQueue():
    queue = await heos.api.player.get_queue(player.id)
    #print(queue)
    cleanedQueue = [[item.song, item.album, item.artist] for item in queue]
    #list = await pyheos.api.player.play_queue(player.id,1)
    window['-QUEUE-'].update(values=cleanedQueue)


async def _on_now_playing_changed(event: HEOSEvent):
    """ Handles event/player_now_playing_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Now Playing Changed Event: {event}')


async def _on_queue_changed(event: HEOSEvent):
    """ Handles event/player_queue_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    await updateQueue()


async def _on_player_state_changed(event: HEOSEvent):
    """ Handles event/player_state_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Player State Changed Event: {event}')


async def playFromQueue(d: dict):
    if len(d['-QUEUE-']) == 1 and heos.connected == True:
        index = d['-QUEUE-'][0]+1
        await heos.api.player.play_queue(player.id, index)


async def playNext():
    if heos.connected == True:
        await player.next()


async def playPrevious():
    if heos.connected == True:
        await player.previous()


async def playPause():
    if heos.connected == True:
        state = await heos.api.player.get_play_state(player.id)
        if state.value == 'stop' or state.value == 'pause':
            await heos.api.player.set_play_state(player.id, PlayState('play'))
        else:
            await heos.api.player.set_play_state(player.id, PlayState('stop'))


async def setVolume(volume: int):
    if heos.connected == True:
        await heos.api.player.set_volume(player.id, volume)
        print('volume 12')

async def addToQueue(d: dict):
    if len(d['-SRESULT-']) == 1 and heos.connected == True:
        index = d['-SRESULT-'][0]
        media = window['-SRESULT-'].metadata[index]
        media.source_id = '5'
        if media.container_id == None:
            media.container_id = ''
        print(media)
        # AddToQueueType:
        # PlayNow = 1
        # PlayNext = 2
        # AddToEnd = 3
        # ReplaceAndPlay = 4
        await heos.api.browse.add_to_queue(player.id, '5', media.container_id, media.media_id, add_type=AddToQueueType.AddToEnd)
        await updateQueue()

async def search(searchString: str):
    if heos.connected == True:
        # deezer source id = 5
        # search_criteria: 1 - artist
        # search_criteria: 2 - album
        # search_criteria: 3 - track
        searchCriteria = 1
        if searchString[0:2] == '/1':
            print('search: artist')
        elif searchString[0:2] == '/2':
            print('search: album')
            searchCriteria = 2
        elif searchString[0:2] == '/3':
            print('search: track')
            searchCriteria = 3
        else:
            return
        searchString = searchString[2:]
        tracks = await heos.api.browse.search(5, searchString, searchCriteria)
        values = [[source.name] for source in tracks]
        window['-SRESULT-'].update(values)
        window['-SRESULT-'].metadata = tracks

col1 = [
    [sg.In(size=(30, 1), justification=LEFT, enable_events=TRUE, key='-SEARCH-', default_text='/1meatallica')],
    [sg.Table(values=[['', '', '']], headings=['Name'], key='-SRESULT-',
              justification=LEFT, size=(90, 50), def_col_width=25,
              bind_return_key=True,
              auto_size_columns=False, display_row_numbers=True)]
]

col2 = [
    [
        sg.Button(button_text='Prev', key='-PREV-'),
        sg.Button(button_text='Play', key='-PLAY-'),
        sg.Button(button_text='Next', key='-NEXT-')
    ],
    [sg.Table(values=[['', '', '']], headings=['Song', 'Album', 'Artist'], key='-QUEUE-',
              justification=LEFT, size=(90, 50), col_widths=[30, 20, 20],
              #bind_return_key=True,
              auto_size_columns=False, display_row_numbers=True)]
]

layout = [
    [sg.Column(col1), sg.Column(col2)]
]

# Create the window
window = sg.Window("HEOS Player", layout, finalize=True, return_keyboard_events=True)
loop = True
heos = Pytheos
player = Player


async def main():
    services = await pytheos.discover(5)
    if not services:
        print("No HEOS services detected!")
        return

    print("Connecting to first device found...")
    global heos
    heos = await pytheos.connect(services[0])  # '192.168.178.25'
    await heos.api.heart_beat()
    await heos.sign_in(username='nils.beckmann@gmail.com', password='7Rqok3qk8GZDQ4jB')
    print(f"Connected to {heos.server}!")
    players = await heos.get_players()
    global player
    player = players[0]
    #window['-TEXT-'].update(f"Status: Connected to {player.name}")
    heos.subscribe('event/player_state_changed', _on_player_state_changed)
    heos.subscribe('event/player_now_playing_changed',
                   _on_now_playing_changed)
    heos.subscribe('event/player_queue_changed', _on_queue_changed)
    window['-SEARCH-'].update(value='/1', move_cursor_to="end")
    await updateQueue()
    test = await heos.get_sources()
    print(test)
    while True:
        # timeout in window.read() are needed to not make the event
        # listener hang up himself
        event, values = window.read(timeout=100)
        if event != '__TIMEOUT__':
            print(f"event: {event}")
            print(f"values: {values}")
            elem = window.find_element_with_focus()
            # End program if user closes window
            if event == sg.WIN_CLOSED:
                break
            
            elif event == '-PLAY-':
                await playPause()
            elif event == '-PREV-':
                await playPrevious()
            elif event == '-NEXT-':
                await playNext()
            # React if return key was pressed
            elif event == 'Return:603979789':
                if elem is not None:
                    # If the search box is in focus, search
                    if elem.Type == sg.ELEM_TYPE_INPUT_TEXT:
                        print(f'input-box-key: {elem.Key}')
                        await search(values['-SEARCH-'])
                    # If queue is in focus, play the selected song
                    elif elem.Key == "-QUEUE-":
                        print('play a song')
                        await playFromQueue(values)
                    # If search results are selected, add them to queue
                    elif elem.Key == '-SRESULT-':
                        await addToQueue(values)
            elif event == '-QUEUE-':
                print('play a song')
                await playFromQueue(values)
            elif event == '-SRESULT-':
                await addToQueue(values)

    window.close()

if __name__ == '__main__':
    asyncio.run(main())
