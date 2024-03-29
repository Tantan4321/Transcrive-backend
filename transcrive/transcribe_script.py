#!/usr/bin/env python3

from __future__ import division

import os
import pathlib
import re
import threading
# Audio recording parameters
import time

import boto3
import pyaudio
from google.cloud import speech
from pynput.keyboard import Key, Listener
from six.moves import queue

from transcrive import json_helper


def get_current_time():
    return int(round(time.time() * 1000))


def duration_to_secs(duration):
    return duration.seconds + (duration.nanos / float(1e9))


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk_size):
        self._rate = rate
        self._chunk_size = chunk_size
        self._num_channels = 1
        self._max_replay_secs = 5

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()

        # 2 bytes in 16 bit samples
        self._bytes_per_sample = 2 * self._num_channels
        self._bytes_per_second = self._rate * self._bytes_per_sample

        self._bytes_per_chunk = (self._chunk_size * self._bytes_per_sample)
        self._chunks_per_second = (
                self._bytes_per_second // self._bytes_per_chunk)

    def __enter__(self):
        self.closed = False

        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            if get_current_time() - self.start_time > STREAMING_LIMIT:
                self.start_time = get_current_time()
                break
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


STREAMING_LIMIT = 290000
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms


class Transcrive:
    def __init__(self, presentation_name, jsoned_db: dict):
        self.client = speech.SpeechClient()
        config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code='en-US',
            max_alternatives=1,
            enable_word_time_offsets=True)
        self.streaming_config = speech.types.StreamingRecognitionConfig(
            config=config,
            interim_results=True)

        self.mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)

        self.filename = presentation_name + ".json"
        self.s3 = boto3.resource('s3')
        # self.s3.Bucket('transcrivebucket').put_object(Key="presentations.txt", Body="test.json\ntranscrive.json")

        self.s3.Bucket('transcrivebucket').download_file("presentations.txt", "temp.txt")
        with open("temp.txt", "r+") as myfile:
            for line in myfile:
                if self.filename in line:
                    break
            else:  # not found, we are at the eof
                myfile.write("\n" + self.filename)
        self.s3.Bucket('transcrivebucket').put_object(Key="presentations.txt", Body=open('temp.txt', 'rb'))

        self.db_store = jsoned_db
        self.current_slide = 0
        self.should_close = False

    def listen_print_loop(self, responses, stream):
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.
        """
        responses = (r for r in responses if (
                r.results and r.results[0].alternatives))

        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.
            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            top_alternative = result.alternatives[0]
            transcript = top_alternative.transcript

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result
            overwrite_chars = ' ' * (num_chars_printed - len(transcript))

            ret: str = transcript + overwrite_chars
            ret = ret.strip()

            if not result.is_final:
                print(ret, end='\r', flush=True)

                num_chars_printed = len(transcript)
            else:

                print(ret)
                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                if re.search(r'\b(quit)\b', transcript, re.I):
                    stream.closed = True
                    self._quit()
                    break

                self.db_store["slides"][self.current_slide]["lines"].append(ret)
                self._update_to_log()

                num_chars_printed = 0

    def _quit(self):
        self.db_store["isActive"] = False
        self._update_to_log()
        os._exit(0)

    def _update_to_log(self):
        # parent_dir = str(pathlib.Path(__file__).parent.absolute())
        # json_helper.dict_to_json_file(self.db_store, os.path.join(parent_dir, "output", str(filename)))
        self.s3.Bucket('transcrivebucket').put_object(Key=self.filename, Body=json_helper.dict_to_json(self.db_store))

    def on_press(self, key):
        if key == Key.right:
            if not len(self.db_store["slides"]) - 1 == self.current_slide:
                self.current_slide += 1
                self.db_store["current_slide"] = self.current_slide
        elif key == Key.left:
            if not self.current_slide == 0:
                self.current_slide -= 1
                self.db_store["current_slide"] = self.current_slide
        if key == Key.esc:
            # Exit script
            self._quit()
            return False

    def key_logger(self):
        # Collect events until released
        with Listener(
                on_press=self.on_press) as listener:
            listener.join()

    def run_transcribe(self):

        print('Say "Quit" or press "Esc" to terminate the program.')

        with self.mic_manager as stream:
            while not stream.closed:
                audio_generator = stream.generator()
                requests = (speech.types.StreamingRecognizeRequest(
                    audio_content=content)
                    for content in audio_generator)

                responses = self.client.streaming_recognize(self.streaming_config, requests)

                threading.Thread(name='keypress', target=self.key_logger).start()
                # Now, put the transcription responses to use.
                threading.Thread(name='transcriber', target=self.listen_print_loop(responses, stream)).start()


if __name__ == '__main__':
    print("test")
