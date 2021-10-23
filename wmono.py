# wavファイルをモノラルにするツール
import os
import sys
import wave as wave
import numpy as np
import argparse

# 位置引数
parser = argparse.ArgumentParser(description='Script to make wav mono.')
parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]')
args = parser.parse_args()
input = os.path.abspath(args.arg1)
output = os.path.abspath(args.arg2)

# waveモジュールで読み込む
with wave.open(input) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    if nchannels == 1:
        print("wmono.py: Target is already mono.")
        sys.exit()
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy().reshape([nchannels, nframes], order='F').mean(axis=0, dtype = "int16")
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32').copy().reshape([nchannels, nframes], order='F').mean(axis=0, dtype = "int32")
    else:
        #https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()

# 加工した音声データを書き出す
with wave.open(output, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(1)
    wav.writeframes(data)