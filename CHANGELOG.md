# Changelog

## Version 0.4

* Adds back/forward navigation with left/right key for the search window in an
  `Undo`/`Redo` manner.
* Adds volume change with `Shift+Right`/Up and `Shift+Left`/Down
* Adds status bar, that shows also error for a few seconds, if they occur
* Adds changing the source with `CMD+K` or `Shift+K`

## Version 0.3

* Improves again on shortcuts:
  * CTRL/`CMD+P`: Play/Pause music
  * CTRL/`CMD+S`/F: Enter search field
  * CTRL/`CMD+Left/Right`: Prev/Next song
  * SHIFT/CTRL/`CMD+Return`: Add album/song to queue with options
  * CTRL/`CMD+Backspace`/Del: Delete items from queue
  * CTRL/`CMD+R`: Refresh HEOS device search
* Adds navigation through search results
  * Songs/albums can be added to queue
  * Stations can be played directly
* Makes found devices selectable
* Adds volume control
* Improves item selection after adding them to queue
* Improves stability

## Version 0.2.1

* Adds some better shortcuts:
  * CMD+S: Start/Stop
  * CMD+Left/Right: Prev/Next song
  * CMD+P/D: Go to search input
* Known Bugs:
  * Working to fast with the API crashes the system (blocking coroutines)
  * Tabbing and element focus + up/down key navigation does not work as expected

## Version 0.2

* Layout extended to show two tables (search and queue) plus search field and
  playback buttons
* Search field has a prefix to search for:
  * `/1` artist
  * `/2` album
  * `/3` track
  Hitting return executes the search.
* Double click or return in queue plays song
* Double click or return in search appends the song or album to the queue

## Version 0.1

* A first prototype to connect to a device and play a song from queue via double
  click or return key.
