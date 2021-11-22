from heosapp import *

def closeWindow(popup):
    makeArrowKeysWork(window['-SRESULT-'])
    popup.close()


async def optionsPopup(options:dict):
    popup = sg.Window('', finalize=True, no_titlebar=True, modal=True, border_depth=0,
                      margins=(0, 0), element_padding=0, return_keyboard_events=True, font='Monospace 12',
                      layout=[
                          [sg.Table(values=options.values(), headings=['Your options:'], justification='left', row_height=25, key='-LIST-', size=(40, 10), bind_return_key=True, enable_events=True, font='Monospace 14',
                                    select_mode=sg.TABLE_SELECT_MODE_BROWSE, def_col_width=40, auto_size_columns=False, alternating_row_color='grey28', selected_row_colors=('ghostwhite', 'wheat4'))]
                      ])
    popup['-LIST-'].set_focus(True)
    makeArrowKeysWork(popup['-LIST-'])
    value = None
    await asyncio.sleep(0.1)
    while True:
        event, values = popup.read(timeout=300)
        if event != '__TIMEOUT__':
            print(event, values)
            if event == 'Escape:889192475':
                closeWindow(popup)
                break
            elif event == 'Return:603979789' and len(values['-LIST-']) == 1:
                print('return pressed')
                value = list(options)[values['-LIST-'][0]]
                closeWindow(popup)
                break
            elif event in (sg.WIN_CLOSED, 'Exit'):  # always check for closed window
                break
    return value
