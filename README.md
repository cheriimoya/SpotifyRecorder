# SpotifyRecorder
**NOTE:** do not use this tool, this is just a proof of concept. It should never be executed.

_This tool is just for educational purposes_

---

This tool could be used to record spotify songs to mp3 files with the mp3 tags set correctly.

For this to work, you would have to listen to the songs in realtime and the tool would record the output of your soundcard.

## Requirements
In general:
- Linux
- ALSA
- spotify
- ffmpeg
- python 3.6

python dependencies:
- pyaudio
- pydub
- dbus-python
- pygobject

## How it works
TL;DR
- stop all spotify processes if there are any running
- start spotify\_recorder.py with `python3 spotify_recorder.py`
- start listening to a playlist or whatever
- skip the first song, as recording starts immediately `TODO`: fix this
- when you want to exit, stop spotify and give the tool some time to gracefully shut down
---

In detail
`TODO`
