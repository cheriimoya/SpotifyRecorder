# SpotifyRecorder
**NOTE:** do not use this tool, this is just a proof of concept. It should never be executed.

_This tool is just for educational purposes_

---

This tool could be used to record spotify songs to mp3 files with the mp3 tags set correctly.

For this to work, you would have to listen to the songs in real-time and the tool would record the output of your sound card.

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
### TL;DR
- stop all spotify processes if there are any running
- start spotify\_recorder.py with `python3 spotify_recorder.py`
- start spotify
- start listening to a playlist or whatever
- skip the first song, as recording starts immediately `TODO`: fix this
- when you want to exit, stop spotify and give the tool some time to gracefully shut down
*If it doesn't work, you might have to reconfigure your default alsa input device!*
---

### In detail
This tool connects to the D-Bus on your system. It will then wait for spotify to broadcast on D-Bus.

After spotify announces itself, the main script will parse the D-Bus message for the currently playing track.

Immediately after this parsing, it will spawn a child process that in turn records the default ALSA input device.

This might need to be configured with e.g. `pavucontrol`. After spawning this recording thread, the main thread will continue listening for new D-Bus messages.

As soon as the main thread receives a 'spotify song changed' notification from D-Bus, it will tell the old recording thread to shutdown and it will immediately spawn a new recording thread which records the new song.

The old recorder thread will, after it received the shutdown signal, write the audio frames it recorded to memory to a Waveform Audio file.

After the contents are written to the WAVE file, it will convert the WAVE file to a mp3 file and tag it while doing so.
