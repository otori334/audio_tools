# wavを切り出すやつ

import os
import sys
import wave as wave
import numpy as np
import argparse
import decimal

parser = argparse.ArgumentParser(description='Tool for extracting from wav files. [arg4] can be specified as an optional argument and the option can be omitted.')

# 位置引数
parser.add_argument('arg1', help='[inputfile]')
parser.add_argument('arg2', help='[outputfile]', nargs='?',default=None)
parser.add_argument('arg3', help='[ss]', nargs='?',default=None)
parser.add_argument('arg4', help="[to]", nargs='?',default=None)

# 第四引数をオプションで指定可能にする
parser.add_argument('-t', '--to', help='[arg4]')
parser.add_argument('-b', '--behind', help='[arg4]')
parser.add_argument('-d', '--dulation', help='[arg4]')

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
if args.arg2 == None or args.arg3 == None:
    with wave.open(input_wav_name) as wav:
        framerate = wav.getframerate()
        nframes = wav.getnframes()
    print('Playback time : '+str(nframes/framerate)+' sec')
    sys.exit()

# オプション引数の数・省略されているかを確認
i = 0
argsCount = 0
which_opt = 0
for opt_arg in [args.to, args.behind, args.dulation]:
    if not opt_arg is None:
        arg4 = opt_arg
        which_opt = i
        argsCount += 1
    i += 1
if argsCount > 1 or (argsCount == 1 and args.to != None):
    # オプション引数が多すぎる
    print("The fourth argument, including optional arguments, must be one.")
    sys.exit()
elif argsCount == 0:
    # オプション引数が指定されない場合，素直に第四引数を定める
    arg4 = args.arg4
    which_opt = 0 # to

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
    len_data = nframes * nchannels
    if samplewidth == 2:
        data = np.frombuffer(wav.readframes(nframes), dtype='int16').copy()
    elif samplewidth == 4:
        data = np.frombuffer(wav.readframes(nframes), dtype='int32').copy()
    else:
        # https://qiita.com/Dsuke-K/items/2ad4945a81644db1e9ff
        print("Sample width : ", samplewidth)
        sys.exit()

# 開始する時間を秒数で指定
time_1 = round(framerate_nchannels * float(args.arg3) )    

# 終了する時間を秒数で指定
if which_opt == 0: # to
    if arg4 == None:
        time_2 = len_data
    else:
        time_2 = round(framerate_nchannels * float(arg4) )
elif which_opt == 1: # behind
    time_2 = round(len_data - framerate_nchannels * float(arg4) )
elif which_opt == 2: # dulation
    time_2 = time_1 + round(framerate_nchannels * float(arg4) )

decimal.getcontext().prec = 3
print('Playback time : '+str(nframes/framerate)+' sec -> '+str((time_2 - time_1)/framerate_nchannels)+' sec : '+str(+decimal.Decimal((time_2 - time_1)/len_data*100))+'%')

# 加工した音声データを書き出す
with wave.open(dest_wav_name, 'w') as wav:
    wav.setsampwidth(samplewidth)
    wav.setframerate(framerate)
    wav.setnchannels(nchannels)
    wav.writeframes(data[time_1:time_2])
