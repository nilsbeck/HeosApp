# Changelog

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
