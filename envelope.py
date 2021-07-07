# ヒルベルト変換から得た包絡線に基づいて簡単にwavを切り出すやつ
# 入力ファイルが1分程度の場合は一瞬で終わる
# 入力ファイルが1時間程度の場合は10分経っても終わらず実用に耐えない．深層学習の方が速い（正確に比べたわけではない）．

import os
import sys
import wave as wave
from scipy import signal
import numpy as np
import argparse
import decimal

parser = argparse.ArgumentParser(description='Tool for easily cutting out wav files using envelopes obtained from Hilbert transforms.')

parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]', nargs='?',default=None)
parser.add_argument('arg3', help='[threshold]', nargs='?',default=None)

parser.add_argument('-n', '--noEnergy', action='store_true')

args = parser.parse_args()

# 入力の絶対パスを解析
input_wav_name = os.path.abspath(args.arg1)
if os.path.isfile(input_wav_name) == False:
    print("The first argument should be an existing file.")
    sys.exit()
input_wav_splitext = os.path.splitext(input_wav_name)[1]
if input_wav_splitext != '.wav' and input_wav_splitext != '.WAV':
    print("The extension of the first argument must be \'.wav\' or \'.WAV\'.")
    sys.exit()

# 位置引数が足りない場合，時間だけ表示する
if args.arg2 == None:
    with wave.open(input_wav_name) as wav:
        framerate = wav.getframerate()
        nframes = wav.getnframes()
    print('Playback time : '+str(nframes/framerate)+' sec')
    sys.exit()

# 出力の絶対パスを指定
dest_wav_name = os.path.abspath(args.arg2)
dest_wav_dirname = os.path.dirname(dest_wav_name)
if os.path.exists(dest_wav_dirname) == False:
    os.makedirs(dest_wav_dirname)

# waveモジュールで読み込む
with wave.open(input_wav_name) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    framerate_nchannels = framerate * nchannels
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy()
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32').copy()
    else:
        # https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()

# ヒルベルト変換と絶対値処理を実行し包絡線を得る
amplitude_envelope = np.abs(signal.hilbert(data))

# 切り出す
if args.arg3 == None:
    threshold = round(np.mean(amplitude_envelope) * 0.4)
else:
    threshold = round(np.mean(amplitude_envelope) * float(args.arg3))
if args.noEnergy:
    bool_list = amplitude_envelope > threshold
else:
    bool_list = amplitude_envelope < threshold
data = np.delete(data, bool_list)

# 加工した音声データを書き出す
with wave.open(dest_wav_name, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(data)
