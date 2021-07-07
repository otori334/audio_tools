# wav音声の先頭に無音を挿入するツール

import os
import sys
import wave as wave
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Tool for inserting silence at the beginning of wav audio.')

parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]')
parser.add_argument('arg3', help='[ss]')

args = parser.parse_args()

input = os.path.abspath(args.arg1)
output = os.path.abspath(args.arg2)

with wave.open(input) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    framerate_nchannels = framerate * nchannels
    time = round(float(args.arg3) * framerate_nchannels)
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy()
        data = np.insert(data, 0, np.zeros(time, dtype = 'int16'))
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32').copy()
        data = np.insert(data, 0, np.zeros(time, dtype = 'int32'))
    else:
        # https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()

# 加工した音声データを書き出す
with wave.open(output, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(data)
