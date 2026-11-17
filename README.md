# Amazon (Music) mediathek
Unofficial Kodi addon for Amazon Prime Music and Amazon Unlimited Music to search and play Music.
An Amazon account is necessary to use the service.

> [!IMPORTANT]
> Amazon licenses its catalogue in full quality only to a player with a Widevine Verified Media Path. Kodi has one
> on Android alone.
> - **Android (e.g. Fire TV):** playback in high quality, as before. Not tried again with 2.3.0 yet.
> - **Linux (Kodi 21 or newer):** songs of the catalogue play in the one quality Amazon licenses without a
>   Verified Media Path (Opus, about 53 or 165 kbit/s), as in Amazon's web player on a Linux desktop.
>   Kodi 20 crashes with a current Widevine library and is refused with an old one.
> - **Windows:** Amazon refuses the licence for songs of the catalogue in every quality (`VMP_VALIDATION_FAILED`).
> - **Everywhere:** songs you own (purchases and uploads) play in full quality without DRM; browsing and searching work.

## Origin
Versions 2.0.0 to 2.2.3 were developed by Kai Sommerfeld in the fork
[plugin.audio.amazonmedia.ksooo](https://github.com/ksooo/plugin.audio.amazonmedia.ksooo), after development had
stopped here. 2.3.0 takes that work over under the original add-on id `plugin.audio.amazonmedia`.

## Installation
Install [my repo](https://github.com/spacys/mediathek) to receive updates automatically, or choose the latest
zip file for a manual installation.

## Motivation
An easy-to-use way to listen to Amazon Music through Kodi.

## Features
This addon provides an easy access to the Amazon Music world with your own Amazon account. It is possible to search for Playlists, Albums, Songs and Artists; to see the Amazon recommendations, the popular Playlists/Albums and the purchased Albums/Songs.

To play the songs it is necessary to install as well InputStream Adaptive.

## Supported Domains
Only the German domain is tested. The other domains are prepared and their Amazon sign-in pages answer, but nobody has signed in and played a track there yet. Reports are welcome.

| Country | Domain | URL | Comment |
|--|--|--|--|
| Germany | DE | https://music.amazon.de | Tested |
| France | FR | https://music.amazon.fr | Untested |
| Great Britain | UK | https://music.amazon.co.uk | Untested |
| Italy | IT | https://music.amazon.it | Untested |
| Spain | ES | https://music.amazon.es | Untested |

## Languages
The add-on is translated into German, French and Italian. The language follows Kodi's own language setting, not the domain. For any other language Kodi falls back to English. The French and Italian translations have not been reviewed by native speakers yet; corrections are welcome.
