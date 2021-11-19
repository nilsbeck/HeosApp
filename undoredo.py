from stack import Stack

class Undoredo:

    def __init__(self, size):
        self.undoStack = Stack(size)
        self.redoStack = Stack(size)

    def undo(self):
        if not self.undoStack.empty:
            undo = self.undoStack.get()
            self.redoStack.put(undo)
            return undo

    def redo(self):
        if not self.redoStack.empty:
            redo = self.redoStack.get()
            self.undoStack.put(redo)
            return redo
    
    def add(self, item):
        self.undoStack.put(item)
