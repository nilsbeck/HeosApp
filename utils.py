from PySimpleGUI.PySimpleGUI import Element

def makeArrowKeysWork(elem: Element):
    row = 1
    if len(elem.Widget.get_children()) > 0:
        selection = elem.Widget.selection()
        if len(selection) > 0:
            row = selection[-1]
        try:
            elem.Widget.selection_set(row)  # move selection
            elem.Widget.focus(row)  # move focus
            elem.Widget.see(row)  # scroll to show it
        finally:
            print('could not select items')