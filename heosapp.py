from inspect import currentframe
from tkinter.constants import FALSE, LEFT, MOVETO, TRUE, X
from tkinter.ttk import Combobox
from PySimpleGUI.PySimpleGUI import T, Combo, Element, Text
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

sg.theme('dark amber')
loading_animation = sg.DEFAULT_BASE64_LOADING_GIF

def makeArrowKeysWork(elem: Element, row: dict):
    if len(row) == 0:
        row = 0
    else:
        row = row[0]
    table_row = elem.Widget.get_children()[row]
    elem.Widget.selection_set(table_row)  # move selection
    elem.Widget.focus(table_row)  # move focus
    elem.Widget.see(table_row)  # scroll to show it

async def updateQueue():
    await asyncio.sleep(0.5)
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
        sg.PopupAnimated(loading_animation)
        index = d['-QUEUE-'][0]+1
        await heos.api.player.play_queue(player.id, index)
        sg.PopupAnimated(None)


async def playNext():
    if heos.connected == True:
        await player.next()


async def playPrevious():
    if heos.connected == True:
        await player.previous()


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
        await heos.api.player.set_volume(player.id, volume)
        print('volume 12')

async def addToQueue(d: dict):
    if len(d['-SRESULT-']) == 1 and heos.connected == True:
        sg.PopupAnimated(loading_animation)
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
        await heos.api.browse.add_to_queue(player.id, '5', media.container_id, media.media_id, add_type=3)
        await updateQueue()
        sg.PopupAnimated(None)

async def search(searchString: str):
    if heos.connected == True:
        sg.PopupAnimated(loading_animation)
        # deezer source id = 5
        # search_criteria: 1 - artist
        # search_criteria: 2 - album
        # search_criteria: 3 - track
        searchCriteria = 1
        if searchString[0:1] == ('1' or 'b'):
            print('search: artist')
        elif searchString[0:1] == ('2' or 'a'):
            print('search: album')
            searchCriteria = 2
        elif searchString[0:1] == ('3' or 't'):
            print('search: track')
            searchCriteria = 3
        else:
            return
        searchString = searchString[1:].strip()
        tracks = await heos.api.browse.search(5, searchString, searchCriteria)
        values = [[source.name, source.artist, source.album] for source in tracks]
        window['-SRESULT-'].update(values)
        makeArrowKeysWork(window['-SRESULT-'], [0])
        window['-SRESULT-'].SetFocus()
        window['-SRESULT-'].metadata = tracks
        sg.PopupAnimated(None)

col1 = [
    [sg.In(size=(30, 1), justification=LEFT, enable_events=TRUE, key='-SEARCH-')],
    [sg.Table(values=[], headings=['Name', 'Artist', 'Album'], key='-SRESULT-',
              justification=LEFT, size=(60, 40), col_widths=[20, 15, 15], select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
              enable_click_events=True, bind_return_key=True, alternating_row_color='salmon4',
              auto_size_columns=False, display_row_numbers=True)]
]

col2 = [
    [
        sg.Button(button_text='Prev', key='-PREV-'),
        sg.Button(button_text='Play', key='-PLAY-'),
        sg.Button(button_text='Next', key='-NEXT-')
    ],
    [sg.Table(values=[['No data :(', '', '']], headings=['Song', 'Album', 'Artist'], key='-QUEUE-',
              justification=LEFT, size=(60, 40), col_widths=[20, 15, 15], enable_click_events=True,
              bind_return_key=True, alternating_row_color='salmon4', select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
              auto_size_columns=False, display_row_numbers=True)]
]

layout = [
    [sg.Column(col1), sg.Column(col2)]
]

# Create the window
window = sg.Window("HEOS Player", layout, use_default_focus=False, finalize=True,
                   font='Monospace 12', return_keyboard_events=True, margins=(0, 0))
# used for start/stop
window.bind("<Command-p>", "Control + p")
window.bind("<Control-p>", "Control + p")
# search -> search + future command palette
window.bind("<Command-k>", "key_search")
window.bind("<Control-k>", "key_search")
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
window.bind("<Return>", "return")
#window.bind("<Tab>", "tab")

heos = Pytheos
player = Player


async def main():
    sg.PopupAnimated(loading_animation)
    services = await pytheos.discover(5)
    if not services:
        print("No HEOS services detected!")
        return

    print("Connecting to first device found...")
    global heos
    heos = await pytheos.connect(services[0])
    print(f"Connected to {heos.server}!")
    players = await heos.get_players()
    global player
    player = players[0]
    window.set_title(f'HEOS App ({player.name})')
    heos.subscribe('event/player_state_changed', _on_player_state_changed)
    heos.subscribe('event/player_now_playing_changed',
                   _on_now_playing_changed)
    heos.subscribe('event/player_queue_changed', _on_queue_changed)
    window['-SEARCH-'].update(value='3 ', move_cursor_to="end")
    window['-SEARCH-'].SetFocus()
    await updateQueue()
    elem = window.find_element_with_focus()

    sg.PopupAnimated(None)

    while True:
        # timeout in window.read() are needed to not make the event
        # listener hang up himself
        event, values = window.read(timeout=10)
        if event != '__TIMEOUT__':
            print(f"event: {event}")
            print(f"values: {values}")
            #elem = 
            # End program if user closes window
            if event == sg.WIN_CLOSED:
                break
            # used window.bind previously to create key combos
            elif event == 'key_search':
                window['-SEARCH-'].set_focus()
            elif event == 'Control + return':
                print('feature not yet implemented')
                # TODO: add options function
            elif event == '-PLAY-'or event == 'Control + p':
                await playPause()
            elif event == '-PREV-' or event == 'Control + left':
                await playPrevious()
            elif event == '-NEXT-' or event == 'Control + right':
                await playNext()
            elif event == '-QUEUE-':
                print('play a song')
                await playFromQueue(values)
            elif event == '-SRESULT-':
                await addToQueue(values)
            elif event == 'Tab:805306377':
                if elem is not None and elem.Key == '-QUEUE-' and len(window['-SRESULT-'].Widget.get_children()) > 0:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-SRESULT-'], values['-SRESULT-'])
                    window['-SRESULT-'].set_focus(True)
                else:
                    # Workaround: otherwise arrow keys do not work after set_focus()
                    makeArrowKeysWork(window['-QUEUE-'], values['-QUEUE-'])
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
                        await addToQueue(values)
            elem = window.find_element_with_focus()

    window.close()

if __name__ == '__main__':
    asyncio.run(main())
