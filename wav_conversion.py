# SciPy が読み込めない wav ファイル ( BWF ？) を SciPy が読み込める純粋な wav に変換するツール
# https://teratail.com/questions/319432
# WavFileWarning: Chunk (non-data) not understood, skipping it.
# ↑の問題を解決する

import os
import sys
import wave as wave
import numpy as np

# コマンドラインの数を確認
if len(sys.argv) != 3:
    print("python3 wav_conversion.py [inputfile] [outputfile]")
    sys.exit()

# 入力の絶対パスを指定
input_wav_name = os.path.abspath(sys.argv[1])

# 出力のmovファイルを指定
dest_wav_name = os.path.abspath(sys.argv[2])

# 分離した音声ファイルをwaveモジュールで読み込む
with wave.open(input_wav_name) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy()
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32').copy()
    else:
        # https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()

# 加工した音声データを書き出す
with wave.open(dest_wav_name, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(data)
