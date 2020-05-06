#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 ft=python fileencoding=utf-8

import sys
import logging
import pyaudio
import re
import numpy as np
import wave
from datetime import datetime
import pprint
import getopt
import subprocess

class DoorbellNotifier:
    DEFAULT_CHANNELS = 1
    DEFAULT_CHUNK_SIZE = 1024 * 8
    DEFAULT_RATE = 8000
    DEFAULT_TARGET_LEVEL = 10 ** 7
    DEFAULT_SUPPRESS_INTERVAL_SEC = 60

    previous_detected_time = None

    def execute_command(self, options):
        subprocess.Popen(options["command"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    def doorbell_detected(self, options):
        suppress_interval_sec = options["suppress_interval_sec"]

        this_time = datetime.now()
        if self.previous_detected_time is not None:
            delta = this_time - self.previous_detected_time
            if delta.seconds < suppress_interval_sec:
                logging.info("SUPPRESSED: The bell is ringing!")
                self.previous_detected_time = this_time
                return

        self.previous_detected_time = this_time
        logging.info("FIRED: The bell is ringing!")
        if options["command"] is not None:
            self.execute_command(options)
        return

    def detect_loop(self, audio, stream, options):
        target_level = options["target_level"]

        sampling_rate = options["sampling_rate"]
        chunk_size = options["chunk_size"]

        freqList = np.fft.fftfreq(int(1.5 * sampling_rate / chunk_size) * chunk_size * 2, d = 1.0 / sampling_rate)
        sound_count = 0
        data1 = []
        data2 = []
        try:
            while stream.is_active():
                for i in range(int(1.5 * sampling_rate / chunk_size)):
                    buf = stream.read(chunk_size)
                    d = np.frombuffer(buf, dtype='int16')
                    if sound_count == 0:
                        data1.append(d)

                    else:
                        data1.append(d)
                        data2.append(d)

                if sound_count >= 1:
                    if sound_count % 2 == 1:
                        data = np.asarray(data1).flatten()
                        fft_data = np.fft.fft(data)
                        data1 = []

                    else:
                        data = np.asarray(data2).flatten()
                        fft_data = np.fft.fft(data)
                        data2 = []

                    fft_abs = np.abs(fft_data)

                    data0 = fft_abs[np.where((freqList < 850) & (freqList > 800))]
                    if (data0.max() > 0.5 * target_level):
                        self.doorbell_detected(options)
                        data1 = []
                        data2 = []
                        sound_count = 0

                sound_count += 1

        except KeyboardInterrupt:
            stream.stop_stream()
            stream.close()
            audio.terminate()


    def open_stream(self, audio, options):
        chunk_size = options["chunk_size"]
        device_index = options["device_index"]
        channels = options["channels"]
        sampling_rate = options["sampling_rate"]

        stream = audio.open(format = pyaudio.paInt16,
                        channels = channels,
                        input_device_index = device_index,
                        rate = sampling_rate,
                        frames_per_buffer = chunk_size,
                        input = True,
                        output = False)
        return stream

    def find_input_device(self, audio, devname_regex):
        for host_index in range(0, audio.get_host_api_count()):
            for device_index in range(0, audio. get_host_api_info_by_index(host_index)['deviceCount']):
                devinfo = audio.get_device_info_by_host_api_device_index(host_index, device_index)
                if re.match(devname_regex, devinfo["name"]):
                    return device_index
        return None


    def parse_options(self, options, command_args=[]):
        opts, args = getopt.getopt(command_args[1:], "hd:i:s:c:", ["help", "device=", "devidx=", "suppress-interval=", "command="])
    
        for o, a in opts:
            if o in ("-h", "--help"):
                return False
            elif o in ("-d", "--device"):
                options["device_regex"] = a
            elif o in ("-i", "--devidx"):
                options["device_index"] = int(a)
            elif o in ("-s", "--suppress-interval"):
                options["suppress_interval_sec"] = int(a)
            elif o in ("-c", "--command"):
                options["command"] = a
    
        return True


    def main(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
        options = {
            "target_level": self.DEFAULT_TARGET_LEVEL,
            "chunk_size": self.DEFAULT_CHUNK_SIZE,
            "sampling_rate": self.DEFAULT_RATE,
            "channels": self.DEFAULT_CHANNELS,
            "device_index": 0,
            "device_regex": None,
            "suppress_interval_sec": self.DEFAULT_SUPPRESS_INTERVAL_SEC,
            "command": None,
        }

        try:
            if not self.parse_options(options, sys.argv):
                self.usage()
                sys.exit()
        except getopt.GetoptError as err:
            print(str(err))
            self.usage()
            sys.exit(2)

        audio = pyaudio.PyAudio()
        if options["device_regex"] is not None:
            options["device_index"] = self.find_input_device(audio, options["device_regex"])

        stream = self.open_stream(audio, options)
        self.detect_loop(audio, stream, options)


if __name__ == "__main__":
    DoorbellNotifier().main()
