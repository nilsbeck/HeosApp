from tkinter.constants import HORIZONTAL, LEFT
import PySimpleGUI as sg
from tkinter.constants import FALSE, FLAT, HORIZONTAL, LEFT, MOVETO, TRUE, VERTICAL, X
from tkinter.ttk import Combobox
from PySimpleGUI.PySimpleGUI import MENU_RIGHT_CLICK_DISABLED, T, Combo, Element, Text

sg.theme('dark')
loading_animation = sg.DEFAULT_BASE64_LOADING_GIF

col1 = [
    [
        sg.In(size=(30, 1), justification=LEFT,
              enable_events=True, key='-SEARCH-', border_width=0),
        sg.Combo(values=[], enable_events=True, readonly=True,
                 key='-COMBO-', size=(25, 1))
    ],
    [sg.Table(values=[], headings=['*', 'Name', 'Artist', 'Album'], key='-SRESULT-',
              justification=LEFT, size=(60, 40), col_widths=[3, 20, 15, 15], select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
              enable_click_events=True, bind_return_key=True, alternating_row_color='grey28', selected_row_colors=('ghostwhite', 'wheat4'),
              auto_size_columns=False, display_row_numbers=True)]
]

col2 = [
    [
        sg.Slider(range=(0, 100), default_value=10, orientation=HORIZONTAL,
                  enable_events=True, disable_number_display=True, key='-VOLUME-')
        # sg.Button(button_text='Prev', key='-PREV-'),
        # sg.Button(button_text='Play', key='-PLAY-'),
        # sg.Button(button_text='Next', key='-NEXT-')
    ],
    [sg.Table(values=[['No data :(', '', '']], headings=['Song', 'Album', 'Artist'], key='-QUEUE-',
              justification=LEFT, size=(60, 40), col_widths=[20, 15, 15], enable_click_events=True, selected_row_colors=('ghostwhite', 'wheat4'),
              bind_return_key=True, alternating_row_color='grey28', select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
              auto_size_columns=False, display_row_numbers=True)]
]

sg.set_options(margins=(0, 0), border_width=0,
               slider_relief=sg.RELIEF_FLAT, font='Monospace 12', slider_border_width=0)
layout = [
    [sg.Column(col1, key='-col1-'), sg.Column(col2, element_justification='right', key='-col2-')]
]

# Create the window
window = sg.Window("HEOS Player", layout, use_default_focus=False, finalize=True,
                   return_keyboard_events=True, margins=(0, 0))
