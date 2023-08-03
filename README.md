# Amazon (Music) mediathek
Unofficial Kodi addon for Amazon Prime Music and Amazon Unlimited Music to search and play Music.
An Amazon account is necessary to use the service.

## Installation
Install my [repo](https://github.com/spacys/repoverview) to receive automatically updates or choose the latest [zip-file](https://github.com/spacys/mediathek/tree/master/plugin.audio.amazonmedia) for a manual installation.

## Motivation
I want an easy-to-use way to listen Amazon Music through Kodi. That is why I created this addon for private use only.

## Features
This addon provides an easy access to the Amazon Music world with your own Amazon account. It is possible to search for Playlists, Albums, Songs, Station and Artists; to see the Amazon recommendations, the popular Playlists/Albums and the purchased Albums/Songs.

To play the songs it is necessary to install as well InputStream Adaptive.

## Supported Domains
The following Domains are currently supported:

| Country | Domain | URL | Comment |
|--|--|--|--|
| Germany | DE | https://music.amazon.de | |
| France | FR | https://music.amazon.fr | Translation is maybe partially incorrect |
| Great Britain | UK | https://music.amazon.co.uk | |
| Italy | IT | https://music.amazon.it | Translation is maybe partially incorrect |
| Spain | ES | https://music.amazon.es | Translation is missing |

If you are in a different country located, no worry. Install the addon, add your Top Level Domain to the end of the existing entries in `settings.xml` with the separator `|`. Example: `"DE|FR|UK|IT|ES"`

Do the same in `tools.py` but comma separated. Example: `['de', 'fr', 'co.uk', 'it', 'es']`

Even if the translation is not available Kodi will use the fallback language, which is English. If you are successful, please inform me to add it to the general supported languages/countries and it would be great, if you can provide the translated language file.