# wav の音量を自動で調節する
import os
import sys
import subprocess as sb
import wave as wave
import tempfile
import numpy as np
import scipy.signal as sp
import argparse
import matplotlib.pyplot as plt
import time
s_time = time.time()# 開始時間

#https://cortyuming.hateblo.jp/entry/2015/12/26/085736
def yes_no_input():
    while True:
        choice = input().lower()
        if choice in ['y', 'ye', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        print("wlev.py: Please respond with 'yes' or 'no' [y/N]: ")

# 位置引数
parser = argparse.ArgumentParser(description='Script to automatically adjust the volume of wav.')
parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]')
parser.add_argument('-d', '--db', type=int, default=50, choices=range(30,71), help='[target db]')#https://achapi2718.blogspot.com/2011/12/dbbit.html
parser.add_argument('-w', '--window', type=int, default=64, help='[Width of the window function]')
parser.add_argument('-n', '--n', type=int, default=1024, help='[samplesize of to_db]')
parser.add_argument('-p', '--plot', action='store_true')
parser.add_argument('-c', '--comp', action='store_true')
parser.add_argument('-l', '--limit', action='store_true')
args = parser.parse_args()
input_file = os.path.abspath(args.arg1)
output_file = os.path.abspath(args.arg2)
target_db = args.db
W = args.window# 小さくすると無音からの立ち上がりへの応答が速くなるが，音量の強弱を失っていく
N = args.n#to_db のサンプルサイズ # 調整する意味はあまりないと思う

# 入力の絶対パスを解析
if os.path.isfile(input_file) == False:
    print("wlev.py: The first argument should be an existing file.")
    sys.exit()
if os.path.isfile(output_file) == True:
    print("wlev.py: Output file already exists. Overwrite? [y/N]: ")
    if yes_no_input():
        print('wlev.py: OK!')
    else:
        sys.exit()

input_splitext = os.path.splitext(input_file)[1]
if input_splitext.lower() == '.wav':
    processing_file = input_file
elif input_splitext.lower() in ['.mov', '.mp4', '.webm']:
    fp = tempfile.NamedTemporaryFile(mode='w+b', suffix='.wav', delete=True)
    processing_file = fp.name
    command = "ffmpeg -y -i '"+input_file+"' -loglevel quiet -vn '"+processing_file+"'"
    sb.call(command, shell=True)
    print("wlev.py: Separated audio file from video.")
else:
    print("wlev.py: The extension of the first argument must be one of \'.wav\', \'.mp4\', \'.webm\' or \'.mov\'.")
    sys.exit()

#デシベル変換だけでなく修飾もする
#https://tips-memo.com/python-db
def to_db(data, N, t, target_db):
    pad = np.zeros(N//2)
    pad_data = np.concatenate([pad, data, pad])
    rms = np.array([np.sqrt((1/N) * ((np.sum(pad_data[i:i+N]))**2)) for i in t*framerate])
    bool_list = rms < 1e-7#発散しないよう適当な数字で抑える
    rms[bool_list] = 10
    db_list = 20 * np.log10(rms)#デシベル変換
    db_list[bool_list] = target_db#倍率を1にするため
    return db_list

#https://deepage.net/features/numpy-convolve.html
def smoothing(array, a):
    v = np.ones(a)/a
    array = np.concatenate([np.repeat(array[:a//2], 2), array[a//2:-a//2], np.repeat(array[-a//2:], 2)])
    x = np.convolve(array, v, mode='valid')[:-1]
    return x

def comp(dest_db, th, ratio, target_db, data_db, bias_db):
    if th > 0:
        bool_list = data_db - bias_db > th
    else:
        bool_list = th > data_db - bias_db
    ratio = abs(data_db - bias_db)[bool_list] * ratio
    dest_db[bool_list] = (data_db[bool_list] - th) * (1/ratio - 1) - bias_db[bool_list]/ratio + target_db
    return dest_db

def limit(dest_db, th, target_db, data_db):
    if th > 0:
        bool_list = data_db > target_db + th
    else:
        bool_list = target_db + th > data_db
    dest_db[bool_list] = dest_db[bool_list] + (target_db + th) - data_db[bool_list]
    return dest_db

# 分離した音声ファイルをwaveモジュールで読み込む
with wave.open(processing_file) as wav:
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

if processing_file != input_file:
    fp.close()

T = round(nframes/framerate) + 1 #sec
t=np.array(range(T))#デシベル変換とグラフに用いる時間の配列
extended_T = T + W * 2
extended_t = np.array(range(extended_T))
data_db = np.empty(nchannels * T)
smooth_db = np.empty(nchannels * T)
bias_db = np.empty(nchannels * T)
tmp_db = np.empty(extended_T)
mag = np.empty(nchannels * nframes)
stft_duration = W//2 + W%2
dest = np.empty(nchannels * nframes)#配列 data と分けないと音質が劣化する

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
    extended_db = to_db(extended_data, N, extended_t, target_db)
    data_db[whichchannel::nchannels] = extended_db[W:W + T]
    smooth_db[whichchannel::nchannels] = smoothing(smoothing(extended_db, 60), 30)[W:W + T]
    #stftで直流バイアスを得る
    f, stft_t, stft_data = sp.stft(extended_db, fs = 1, window = "hann", nperseg = W)
    tmp_db = np.repeat(np.real(stft_data[0,:]), stft_duration)[:extended_T]
    bias_db[whichchannel::nchannels] = smoothing(tmp_db, W)[stft_duration * 2:stft_duration * 2 + T]

tmp_db = target_db - bias_db
#near_dest_db = smooth_db + tmp_db

#コンプレッサー 
if args.comp == True:
    tmp_db = comp(tmp_db, 5, 2, target_db, data_db, bias_db)
    tmp_db = comp(tmp_db, -5, 2, target_db, data_db, bias_db)

#リミッター 
if args.limit == True:
    tmp_db = limit(tmp_db, 5, target_db, smooth_db + tmp_db)
    tmp_db = limit(tmp_db, -5, target_db, smooth_db + tmp_db)

for whichchannel in range(nchannels):
    if args.comp == True:
        #適当な秒数でスムージングする
        tmp_db[whichchannel::nchannels] = smoothing(tmp_db[whichchannel::nchannels], 8)
    mag[whichchannel::nchannels] = np.repeat(np.power(10, (tmp_db[whichchannel::nchannels])/20 ), framerate)[:nframes]

dest = data * mag#data と dest 分けないとここで劣化

#リミッターと型変換
dest[dest > np.iinfo(wav_type).max] = np.iinfo(wav_type).max
dest[dest < np.iinfo(wav_type).min] = np.iinfo(wav_type).min
dest = dest.astype(wav_type)

# 加工した音声データを書き出す
with wave.open(output_file, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(dest)

if args.plot == True:
    e_time = time.time() - s_time; print(f'wlev.py: {e_time}秒かかりました！')# 実行時間 = 終了時間 - 開始時間
    for whichchannel in range(nchannels):
        plt.title(f'Channel {whichchannel+1}')
        if args.comp == True:
            plt.plot(t[:-1],tmp_db[whichchannel::nchannels][:-1],'c',label="cmp_db")
        plt.plot(t[:-1],(target_db - bias_db)[whichchannel::nchannels][:-1],'g',label="tmp_db")
        dest_db = to_db(dest[whichchannel::nchannels], N, t, target_db);dest_db = smoothing(dest_db, 60);dest_db = smoothing(dest_db, 30);plt.plot(t[:-1],dest_db[:-1],'r',label="dest_db")
        #plt.plot(t[:-1],data_db[whichchannel:-nchannels+whichchannel:nchannels],'b',label="data_db")
        plt.plot(t[:-1],smooth_db[whichchannel::nchannels][:-1],'b',label="smooth_db")
        plt.plot(t[:-1],bias_db[whichchannel::nchannels][:-1],label="bias_db")
        plt.axhline(y=target_db,xmin=0,xmax=T-1,color='y',linestyle='dashed',label="target_db")
        plt.legend()
        plt.xlabel("Time [sec]");plt.ylabel("db")
        plt.show()