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
parser.add_argument('-c', '--ch', type=int, default=0, choices=range(1,10), help='[select channel]')
args = parser.parse_args()
input = os.path.abspath(args.arg1)
output = os.path.abspath(args.arg2)

# 入力の絶対パスを解析
if os.path.isfile(input) == False:
    print("The first argument should be an existing file.")
    sys.exit()
input_splitext = os.path.splitext(input)[1]
if input_splitext != '.wav' and input_splitext != '.WAV':
    print("The extension of the first argument must be \'.wav\' or \'.WAV\'.")
    sys.exit()

# waveモジュールで読み込む
with wave.open(input) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    if nchannels == 1:
        print("wmono.py: Target is already mono.")
        sys.exit()
    whichchannel = (args.ch - 1) % (nchannels)
    print(f'Channel {whichchannel + 1} has been selected.')
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16')[whichchannel::nchannels].copy()
        #data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy().reshape([nchannels, nframes], order='F').mean(axis=0, dtype = "int16") #移動する人間の声ではうなりが発生する．位置推定に使えそう．
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32')[whichchannel::nchannels].copy()
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