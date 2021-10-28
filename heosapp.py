from tkinter.constants import LEFT, X
from tkinter.ttk import Combobox
from PySimpleGUI.PySimpleGUI import T, Combo
import asyncio
import os
import sys
import PySimpleGUI as sg
import pytheos
from pytheos.controllers.player import Player
from pytheos.models.player import PlayState
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
    window['-TEXT-'].update(f"Status: Connected to {player.name}")
    #window['-TABLE-'].expand(True, True)


async def updateQueue(heos: pytheos):
    queue = await heos.api.player.get_queue(player.id)
    #print(queue)
    cleanedQueue = [[item.song, item.album, item.artist] for item in queue]
    #list = await pyheos.api.player.play_queue(player.id,1)
    window['-TABLE-'].update(values=cleanedQueue)


async def _on_now_playing_changed(event: HEOSEvent):
    """ Handles event/player_now_playing_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Now Playing Changed Event: {event}')


async def _on_player_state_changed(event: HEOSEvent):
    """ Handles event/player_state_changed events from HEOS.

    :param event: Event object
    :return: None
    """
    print(f'Player State Changed Event: {event}')


async def playFromQueue(index: int):
    if heos.connected == True:
        await heos.api.player.play_queue(player.id, index)


async def playNext():
    if heos.connected == True:
        await heos.api.player.play_next(player.id)


async def playPrevious():
    if heos.connected == True:
        await heos.api.player.play_previous(player.id)


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

layout = [
    [sg.Text("Status: Disconnected", key='-TEXT-')],     # Part 2 - The Layout
    [sg.Table(values=[['', '', '']], headings=['Song', 'Album', 'Artist'], key='-TABLE-',
              justification=LEFT, size=(100, 50), def_col_width=30,
              bind_return_key=True,
              auto_size_columns=False, display_row_numbers=True)],
    [sg.Button("OK")],
    [sg.Combo(values=[], size=(100, 100), key='-COMBO-')]
]

# Create the window
window = sg.Window("HEOS Player", layout, finalize=True)
loop = True
heos = Pytheos
player = Player


async def main():
    services = await pytheos.discover(3)
    if not services:
        print("No HEOS services detected!")
        return

    print("Connecting to first device found...")
    global heos
    heos = await pytheos.connect(services[0])  # '192.168.178.25'
    await heos.sign_in(username='nils.beckmann@gmail.com', password='7Rqok3qk8GZDQ4jB')
    print(f"Connected to {heos.server}!")
    players = await heos.get_players()
    global player
    player = players[0]
    window['-TEXT-'].update(f"Status: Connected to {player.name}")
    heos.subscribe('event/player_state_changed', _on_player_state_changed)
    heos.subscribe('event/player_now_playing_changed',
                   _on_now_playing_changed)
    await updateQueue(heos)
    while True:
        # timeout in window.read() are needed to not make the event
        # listener hang up himself
        event, values = window.read(timeout=100)
        if event != '__TIMEOUT__':
            print(f"event: {event}")
            print(f"values: {values}")

        # End program if user closes window
        if event == sg.WIN_CLOSED:
            break

        # React on Table double click / enter
        if event == '-TABLE-':
            d = dict(values)
            # Only start a song if not multiple items were selected
            if '-COMBO-' in d.keys() and len(d['-TABLE-']) == 1:
                row_num_clicked = d['-TABLE-'][0]+1
                #print(row_num_clicked)
                await playFromQueue(row_num_clicked)
                #await playPause()
                await setVolume(12)

    window.close()

if __name__ == '__main__':
    asyncio.run(main())
