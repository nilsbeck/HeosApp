# HeosApp

The HeosApp will be a small application to control the most important features
in Heos devices via a graphical interface.

## Motivation

I have been using the Heos System for some time now and found an app for Windows
on the Windows store that suited my needs to control my device from a Windows
machine. However, there does not seem to be a (free) app for Mac and
Denon/Marantz decided for unknown reasons to not publish their iOS app for Mac.
But there are indeed quite a few Python APIs on github that, sadly, lack a GUI.
As I always wanted to learn more about Python, this project was born.

## Features

There is no clear definition of what those features are yet but I was hoping to
implement the following:

* Connect to a device
* Show current queue, play song from current queue
* Stop, Play, Pause song
* Change volume
* Search for music from a configured online service (Deezer, Spotify, etc)
* Add music to queue from those services (see above)

## Installation

Using py2applet:
```bash
py2applet --iconfile assets/music.png --make-setup HeosApp.py
py2applet --make-setup HeosApp.py
```

You can run the py script directly or create a bundle using pyinstaller:

```bash
pyinstaller \
    --noconfirm --log-level=WARN \
    --onefile --clean --windowed \
    --disable-windowed-traceback \
    --icon=assets/music.png \
    --name=HeosApp heosapp.py
```

## Contribution

Thanks to the following projects, I believe I'll be able to create the app and
implement the named features:

* [Pytheos](https://github.com/endlesscoil/pytheos)
* [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI)
* Icons made by [Freepik](https://www.freepik.com) from [www.flaticon.com](https://www.flaticon.com/)

## Docs

Some general docs for Heos system communications can be found
[here](https://rn.dmglobal.com/euheos/HEOS_CLI_ProtocolSpecification.pdf)
