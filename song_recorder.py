import pyaudio
import wave
import threading
import logging
import os
from pydub import AudioSegment


class SongRecorder(threading.Thread):# {{{{{{
    def __init__(self,# {{{
            song,
            chunk_size=1024,
            wave_format=pyaudio.paInt16,
            channels=2,
            rate=44100):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger('SpotifyRecorder')

        self.song_tags = self.get_song_tags(song)
        self.chunk_size = chunk_size
        self.wave_format = wave_format
        self.channels = channels
        self.rate = rate

        self.shutdown_flag = threading.Event()

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
                format=self.wave_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                start=False,
                frames_per_buffer=chunk_size)# }}}

    def get_song_tags(self, song):# {{{
        song_tags = {}

        song_tags['title'] = song['title'].decode('utf-8')
        song_tags['artist'] = song['artist'].decode('utf-8')
        song_tags['album'] = song['album'].decode('utf-8')
        song_tags['trackNumber'] = song['trackNumber']

        return song_tags# }}}

    def run(self):# {{{
        self.record_song_to_file()
        self.convert_wav_to_mp3()
        os.remove(self.song_tags['title'] + '.wav')# }}}

    def record_song_to_file(self):# {{{
        frames = []
        self.stream.start_stream()
        try:
            while not self.shutdown_flag.is_set():
                data = self.stream.read(self.chunk_size)
                frames.append(data)
        except KeyboardInterrupt:
            pass

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        waveFile = wave.open(self.song_tags['title'] + '.wav', 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.wave_format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        self.logger.info('Wrote song to ' + self.song_tags['title'] + '.wav')# }}}

    def convert_wav_to_mp3(self):# {{{
        AudioSegment.from_wav(self.song_tags['title'] + '.wav').export(
                self.song_tags['title'] + ".mp3",
                format = "mp3",
                tags = self.return_mp3_tags_as_dict())# }}}

    def return_mp3_tags_as_dict(self):# {{{
        tags = {
                'title': self.song_tags['title'],
                'artist': self.song_tags['artist'],
                'album': self.song_tags['album'],
                'track': self.song_tags['trackNumber']
                }
        return tags# }}}

