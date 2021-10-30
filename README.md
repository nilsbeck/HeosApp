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

## Contribution

Thanks to the following projects, I believe I'll be able to create the app and
implement the named features:

* [Pytheos](https://github.com/endlesscoil/pytheos)
* [PySimpleGUI](https://github.com/PySimpleGUI/PySimpleGUI)

## Docs

Some general docs for Heos system communications can be found
[here](https://rn.dmglobal.com/euheos/HEOS_CLI_ProtocolSpecification.pdf)
