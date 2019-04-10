#!/usr/bin/env python3

import dbus
import dbus.service
import threading
import time
import gobject
import logging
from queue import Queue
from dbus.mainloop.glib import DBusGMainLoop

import song_recorder


class RecordingHandler(object):# {{{
    def __init__(self, session_bus):# {{{
        self.logger = logging.getLogger('RecordingHandlerLogger')

        self.current_song = {'trackId':'None'}
        self.thread_queue = Queue()

        bus = session_bus.get_object(
                'org.mpris.MediaPlayer2.spotify',
                '/org/mpris/MediaPlayer2')

        bus.connect_to_signal(
                'PropertiesChanged',
                self.properties_changed)# }}}

    def properties_changed(self,# {{{
            interface_name,
            changed_properties,
            invalid_properties):
        self.logger.info('Properties have changed')

        if 'Metadata' not in changed_properties:
            self.logger.warn('Metadata not found in changed properties')
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
            self.logger.warning('There was an error getting the Metadata')

        self.current_song_changed()# }}}

    def current_song_changed(self):# {{{
        self.logger.debug('Current song has changed')

        while not self.thread_queue.empty():
            thread = self.thread_queue.get()
            thread.shutdown_flag.set()

        self.logger.debug('Starting song recorder...')
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
        self.logger = logging.getLogger('RecordingHandlerLogger')

        self.logger.debug('Setting up DBus...')
        bus_loop = DBusGMainLoop(set_as_default=True)
        self.session_bus = dbus.SessionBus(mainloop=bus_loop)

        bus = self.session_bus.get_object(
                'org.freedesktop.DBus',
                '/org/freedesktop/DBus')

        bus.connect_to_signal(
                'NameOwnerChanged',
                self.spotify_started,
                arg0='org.mpris.MediaPlayer2.spotify')

        self.logger.debug('Waiting for spotify to be started...')

        try:
            self.loop = gobject.MainLoop()
            gobject.threads_init()
            self.loop.run()
        finally:
            self.logger.debug('Spotify got shut down, stopping recorder...')# }}}

    def spotify_started(self, name, before, after):# {{{
        self.logger.debug('Found spotify on dbus!')
        if name != 'org.mpris.MediaPlayer2.spotify':
            return

        if after:
            self.handler = RecordingHandler(self.session_bus)
        else:
            self.logger.debug('Lost spotify on dbus, shutting down')
            # FIXME
            if self.handler:
                self.handler.shutdown()
            self.loop.quit()
            self.logger.debug('Finished shutting down')# }}}}}}


if __name__ == '__main__':# {{{
    logger = logging.getLogger('RecordingHandlerLogger')
    logger.setLevel(logging.INFO)
    SpotifyRecorder()# }}}
