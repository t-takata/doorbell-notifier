#!/usr/bin/env python3

import pyaudio

p = pyaudio.PyAudio()

for host_index in range(0, p.get_host_api_count()):
    print(p. get_host_api_info_by_index(host_index))
    for device_index in range(0, p. get_host_api_info_by_index(host_index)['deviceCount']):
        print(p.get_device_info_by_host_api_device_index(host_index, device_index))
