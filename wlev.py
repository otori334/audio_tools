# wav の音量を自動で調節する
import os
import sys
import subprocess as sb
import wave as wave
import tempfile
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
parser.add_argument('-d', '--db', type=int, default=50, choices=range(30,71), help='[target db]')#https://achapi2718.blogspot.com/2011/12/dbbit.html
parser.add_argument('-w', '--window', type=int, default=64, help='[Width of the window function]')
parser.add_argument('-n', '--n', type=int, default=1024, help='[samplesize of to_db]')
args = parser.parse_args()
input = os.path.abspath(args.arg1)
output = os.path.abspath(args.arg2)
target_db = args.db
W = args.window# 小さくすると無音からの立ち上がりへの応答が速くなるが，音量の強弱を失っていく
N = args.n#to_db のサンプルサイズ # 調整する意味はあまりないと思う

# 入力の絶対パスを解析
if os.path.isfile(input) == False:
    print("The first argument should be an existing file.")
    sys.exit()
input_splitext = os.path.splitext(input)[1]
if input_splitext in ['.wav', '.WAV']:
    processing = input
elif input_splitext in ['.mov', '.MOV', '.mp4', '.MP4', '.webm', '.WEBM']:
    fp = tempfile.NamedTemporaryFile(mode='w+b', suffix='.wav', delete=True)
    processing = fp.name
    print("Separating audio file from video...")
    command = "ffmpeg -y -i '"+input+"' -loglevel quiet -vn '"+processing+"'"
    sb.call(command, shell=True)
else:
    print("The extension of the first argument must be one of \'.wav\', \'.WAV\', \'.mp4\', \'.MP4\', \'.webm\', \'.WEBM\', \'.mov\' or \'.MOV\'.")
    sys.exit()
if os.path.isfile(output) == True:
    print("Output file already exists.")
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
with wave.open(processing) as wav:
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
        print("wlev.py: Sample width is ", samplewidth)
        sys.exit()
    data = np.frombuffer(wav.readframes(nframes), dtype=wav_type).copy()

if processing != input:
    fp.close()

T = round(nframes/framerate) + 1 #sec
t=np.array(range(T))#デシベル変換とグラフに用いる時間の配列
extended_T = T + W * 2
extended_t = np.array(range(extended_T))
dest = np.empty(nchannels * nframes)#配列 data と分けないと音質が劣化する
mag = np.empty(nchannels * nframes)
tmp_db = np.empty(extended_T)
bias_db = np.empty(nchannels * T)
stft_duration = W//2 + W%2

if W > T:
    print(f"wlev.py: The wav file is too short. The duration of the wav file must be longer than {W} seconds.")
    sys.exit()

if N > framerate:
    N = framerate
    print(f"wlev.py: Too-large samplesize of to_db \'{N}\' are limited to frameratesize \'{framerate}\'.")

for whichchannel in range(nchannels):
    #端をケア
    extended_data = np.concatenate([-data[whichchannel:W*framerate*nchannels+whichchannel:nchannels][::-1], data[whichchannel::nchannels], -data[-W*framerate*nchannels+whichchannel::nchannels][::-1]])
    #デシベル変換
    extended_db = to_db(extended_data, N, extended_t)
    #stftで直流バイアスを得る
    f, stft_t, stft_data = sp.stft(extended_db, fs = 1, window = "hann", nperseg = W)
    tmp_db = np.repeat(np.real(stft_data[0,:]), stft_duration)
    bias_db[whichchannel::nchannels] = smoothing(tmp_db, W)[stft_duration * 2:stft_duration * 2 + T]
    mag[whichchannel::nchannels] = np.repeat(np.power(10, (target_db - bias_db[whichchannel::nchannels])/20 ), framerate)[:nframes]

dest = data * mag#data と dest 分けないとここで劣化

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
e_time = time.time() - s_time; print(f'{e_time}秒かかりました！') # 実行時間 = 終了時間 - 開始時間
for whichchannel in range(nchannels):
    line = np.ones(T)*target_db;plt.plot(t,line,'y')
    db_ori = to_db(data[whichchannel::nchannels], N, t);db_ori = smoothing(db_ori, 60);db_ori = smoothing(db_ori, 30);plt.plot(t,db_ori,'b')
    plt.plot(t,bias_db[whichchannel::nchannels])
    db3 = to_db(dest[whichchannel::nchannels], N, t);db3 = smoothing(db3, 60);db3 = smoothing(db3, 30);plt.plot(t,db3,'r')
    plt.xlabel("Time [sec]");plt.ylabel("db")
    plt.show()
"""