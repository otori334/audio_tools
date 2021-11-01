# wav の音量を自動で調節する
import os
import sys
import wave as wave
import numpy as np
import scipy.signal as sp
import argparse
#import matplotlib.pyplot as plt
#import time
#s_time = time.time()# 開始時間

# 位置引数
parser = argparse.ArgumentParser(description='Script to automatically adjust the volume of wav.')
parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]')
parser.add_argument('-d', '--db', type=int, default=50, choices=range(30,71), help='[target db]')
args = parser.parse_args()#wav は 90db まで表現できる
input = os.path.abspath(args.arg1)
output = os.path.abspath(args.arg2)
target_db = args.db

# 入力の絶対パスを解析
if os.path.isfile(input) == False:
    print("The first argument should be an existing file.")
    sys.exit()
input_splitext = os.path.splitext(input)[1]
if input_splitext != '.wav' and input_splitext != '.WAV':
    print("The extension of the first argument must be \'.wav\' or \'.WAV\'.")
    sys.exit()

#https://tips-memo.com/python-db
def to_db(data, N, t):
    pad = np.zeros(N//2)
    pad_data = np.concatenate([pad, data, pad])
    rms = np.array([np.sqrt((1/N) * ((np.sum(pad_data[i:i+N]))**2)) for i in t*framerate])
    a = 1e-7
    rms[rms < a] = a
    return 20 * np.log10(rms)

#https://deepage.net/features/numpy-convolve.html
def smoothing(array, a):
    v = np.ones(a)/a
    array = np.concatenate([np.repeat(array[:a//2], 2), array[a//2:-a//2], np.repeat(array[-a//2:], 2)])
    x = np.convolve(array, v, mode='valid')[:-1]
    return x

# 分離した音声ファイルをwaveモジュールで読み込む
with wave.open(input) as wav:
    samplewidth = wav.getsampwidth()
    nchannels = wav.getnchannels()
    framerate = wav.getframerate()
    nframes = wav.getnframes()
    if samplewidth == 2:
        wav_type = np.int16
    elif samplewidth == 4:
        wav_type = np.int32
    else:
        # https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()
    data = np.frombuffer(wav.readframes(nframes), dtype=wav_type).copy()

T = round(nframes/framerate) + 1 #sec
t=np.array(range(T))#デシベル変換とグラフに用いる時間の配列
dest = np.empty(nchannels * nframes)#配列 data と分けないと音質が劣化する

for whichchannel in range(nchannels):
    #デシベル変換
    db = to_db(data[whichchannel::nchannels], 1024, t)
    #stftで直流バイアスを得る
    f, stft_t, stft_data = sp.stft(db, fs = 1, window = "hann", nperseg = 256)
    db = np.repeat(np.real(stft_data[0,:]), stft_t[1] - stft_t[0])[:T]
    db = smoothing(db, 256)
    mag = np.repeat(np.power(10, (target_db - db)/20), framerate)[:nframes]
    dest[whichchannel::nchannels] = data[whichchannel::nchannels] * mag#data と dest 分けないとここで劣化

# マキシマイズと型変換
dest[dest > np.iinfo(wav_type).max] = np.iinfo(wav_type).max
dest[dest < np.iinfo(wav_type).min] = np.iinfo(wav_type).min
dest = dest.astype(wav_type)

# 加工した音声データを書き出す
with wave.open(output, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(dest)

"""
db1 = smoothing(db, 60);db1 = smoothing(db1, 30)
db2 = to_db(data, 1024, t);db2 = smoothing(db2, 60);db2 = smoothing(db2, 30)
db3 = np.ones(T)*50
e_time = time.time() - s_time; print(f'{e_time}秒かかりました！') # 実行時間 = 終了時間 - 開始時間
plt.xlabel("Time [sec]");plt.ylabel("db")
plt.plot(t,db)
plt.plot(t,db3,'y')
plt.plot(t,db1,'b')
plt.plot(t,db2,'r')
plt.show()
"""