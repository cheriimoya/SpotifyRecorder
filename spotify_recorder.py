#!/usr/bin/env python3

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import threading
import time
import gobject
import logging
from queue import Queue

import song_recorder

#not usesd
class MediaKeysHandler():# {{{
    def __init__(self, session_bus):
        print("Finding Spotify...")
        spotify_bus = session_bus.get_object(
                "org.mpris.MediaPlayer2.spotify",
                "/org/mpris/MediaPlayer2")
        self.spotify = dbus.Interface(spotify_bus,
                "org.mpris.MediaPlayer2.Player")

        print("Connect to MediaKeys...")
        bus = session_bus.get_object(
                "org.gnome.SettingsDaemon",
                "/org/gnome/SettingsDaemon/MediaKeys")
        bus.connect_to_signal("MediaPlayerKeyPressed",
                self.key_pressed)
        self.mediakeys = dbus.Interface(bus,
                "org.gnome.SettingsDaemon.MediaKeys")
        self.mediakeys.GrabMediaPlayerKeys("Spotify", time.time())

    def shutdown(self):
        self.mediakeys.ReleaseMediaPlayerKeys("Spotify")

    def key_pressed(self, *keys):
        print("Received MediaPlayerKeyPressed:")
        print("  " + repr(keys))

        if self.spotify:
            for key in keys:
                if key == "":
                    pass

                elif key == "Play":
                    self.spotify.PlayPause()

                elif key == "Pause":
                    self.spotify.PlayPause()

                elif key == "Stop":
                    self.spotify.Stop()

                elif key == "Next":
                    self.spotify.Next()

                elif key == "Previous":
                    self.spotify.Previous()# }}}


class RecordingHandler(object):# {{{
    def __init__(self, session_bus):# {{{
        self.logger = logging.getLogger('RecordingHandlerLogger')
        self.logger.setLevel(logging.INFO)

        self.current_song = {'trackId':'None'}

        self.thread_queue = Queue()

        print("Waiting for song to be changed...")
        bus = session_bus.get_object(
                "org.mpris.MediaPlayer2.spotify",
                "/org/mpris/MediaPlayer2")

        bus.connect_to_signal(
                "PropertiesChanged",
                self.properties_changed)# }}}

    def properties_changed(self,# {{{
            interface_name,
            changed_properties,
            invalid_properties):
        self.logger.info('Properties have changed')

        if 'Metadata' not in changed_properties:
            self.logger.info('Metadata not found in changed properties')
            return

        try:
            if self.current_song['trackId'] == changed_properties['Metadata']['mpris:trackid'].encode('utf-8'):
                return
            self.current_song['trackId'] = changed_properties['Metadata']['mpris:trackid'].encode('utf-8')
            self.current_song['artist'] = changed_properties['Metadata']['xesam:artist'][0].encode('utf-8')
            self.current_song['album'] = changed_properties['Metadata']['xesam:album'].encode('utf-8')
            self.current_song['title'] = changed_properties['Metadata']['xesam:title'].encode('utf-8')
            self.current_song['albumArt'] = changed_properties['Metadata']['mpris:artUrl'].encode('utf-8')
            self.current_song['trackNumber'] = changed_properties['Metadata']['xesam:trackNumber']
            self.current_song['playback_status'] = changed_properties['PlaybackStatus']
        except KeyError:
            logger.warning('There was an error getting the Metadata')

        self.current_song_changed()# }}}

    def current_song_changed(self):# {{{
        self.logger.info('Current song has changed')

        while not self.thread_queue.empty():
            thread = self.thread_queue.get()
            thread.shutdown_flag.set()

        self.logger.debug("Starting song recorder...")
        song_recorder_thread = song_recorder.SongRecorder(self.current_song)
        song_recorder_thread.start()
        self.thread_queue.put(song_recorder_thread)
        self.logger.debug('Recording new song:', str(self.current_song['title']))# }}}

    def shutdown(self):# {{{
        while not self.thread_queue.empty():
            thread = self.thread_queue.get()
            thread.shutdown_flag.set()# }}}}}}


class SpotifyRecorder(object):# {{{
    def __init__(self):# {{{
        print("Setting up DBus...")
        bus_loop = DBusGMainLoop(set_as_default=True)
        self.session_bus = dbus.SessionBus(mainloop=bus_loop)

        bus = self.session_bus.get_object(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus")

        bus.connect_to_signal(
                "NameOwnerChanged",
                self.spotify_started,
                arg0="org.mpris.MediaPlayer2.spotify")

        print("Waiting for spotify to be started...")

        try:
            self.loop = gobject.MainLoop()
            gobject.threads_init()
            self.loop.run()
        finally:
            print("Spotify got shut down, stopping recorder...")# }}}

    def spotify_started(self, name, before, after):# {{{
        print("Found spotify on dbus!")
        if name != "org.mpris.MediaPlayer2.spotify":
            return

        if after:
            self.handler = RecordingHandler(self.session_bus)
        else:
            print("Lost spotify on dbus, shutting down")
            # FIXME
            if self.handler:
                self.handler.shutdown()
            self.loop.quit()
            print("Finished shutting down")# }}}}}}


if __name__ == "__main__":# {{{
    SpotifyRecorder()# }}}
