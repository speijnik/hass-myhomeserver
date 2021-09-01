# Bticino MyHomeSERVER

The Legrand/Bticino MyHomeSERVER integration for Home Assistant uses the
same HTTP-based API as the MyHome_UP mobile application.

This integration is currently a proof-of-concept and supports lights and
dimmers only.

The integration makes use of the *myhome* Python library, which can be found
at [https://github.com/speijnik/myhome] and contains some additional information
on how the API is being accessed.

If you are looking for a more mature, more sophisticated integration check out [https://github.com/anotherjulien/MyHOME]

## Features

* Automatic discovery of MyHomeSERVER1 devices via UPnP
* Discovery of zones and rooms, providing suggested areas in HomeAssistant (format is hard-coded at "zone name / room name" for now)
* Discovery of lights, including their names as seen in MyHome_UP
* Control of simple switches / lights and dimmers
* Additional light properties as extra state attributes: protocol name and protocol configuration (address)
