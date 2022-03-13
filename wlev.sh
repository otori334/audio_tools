#!/bin/bash
# http://ayageman.blogspot.com/2018/02/mp3-volume.html
# https://nico-lab.net/normalize_audio_with_ffmpeg/

IFS=$'\n'
readonly CMD_NAME="${0##*/}"
# See https://qiita.com/katoy/items/c0d9ff8aff59efa8fcbb
# See http://unix.stackexchange.com/questions/101080/realpath-command-not-found
realpath ()
{
    f=$@;
    if [ -d "$f" ]; then
        base="";
        dir="$f";
    else
        base="/$(basename "$f")";
        dir=$(dirname "$f");
    fi;
    dir=$(mkdir -p "$dir" && cd "$dir" && /bin/pwd);
    echo "$dir$base"
}
src_path=`realpath $1`
dest_path=`realpath $2`
if [ "${src_path}" == "${src_path#/mnt/c}" ]; then
    readonly TMP_DIR="/tmp/${CMD_NAME%.*}_"$$
    readonly _ffmpeg='/usr/local/bin/ffmpeg'
else
    readonly TMP_DIR="/mnt/c/tmp/${CMD_NAME%.*}_"$$
    readonly _ffmpeg='/mnt/c/FFmpeg/bin/ffmpeg.exe'
fi
FFMPEG_PATH="${FFMPEG_PATH:-${3:-${_ffmpeg}}}"
GIT="${GIT}"
trap 'rm -r "${TMP_DIR}" && exit' 0 1 2 3 15 && mkdir -p "${TMP_DIR}"
tmp_path="${TMP_DIR}/tmp.wav"

if [ $# -lt 2 -o $# -gt 3 ]; then
    echo "${CMD_NAME}: Please specify 2 or 3 args." 1>&2
    exit
fi

if [ -d "${src_path}" ]; then
    echo "${CMD_NAME}: Input is file only." 1>&2
    exit
fi

if [ "${dest_path##*.}" != "wav" ]; then
    echo "${CMD_NAME}: Output is wav only." 1>&2
    exit
fi

_oldpwd=`pwd`
cd "${src_path%/*}"
if [ "${src_path##*.}" = "mov" -o "${src_path##*.}" = "mp4" ]; then
    eval \"${FFMPEG_PATH}\" -i \"${src_path#/mnt/c}\" -loglevel error -hide_banner -stats -af dynaudnorm -vn \"${tmp_path#/mnt/c}\"
else
    eval \"${FFMPEG_PATH}\" -i \"${src_path#/mnt/c}\" -loglevel error -hide_banner -stats -af dynaudnorm \"${tmp_path#/mnt/c}\"
fi
cd "${_oldpwd}"

echo "Separated audio files from video." 1>&2
echo "Dynamic Audio Normalizer completed." 1>&2
echo "Loudness normalisation started." 1>&2
unset FFMPEG_PATH
eval \"${GIT}/audio_tools/.venv/bin/ffmpeg-normalize\" \"${tmp_path}\" -o \"${dest_path}\" -f -ar 48000 # マジックナンバー
echo "Loudness normalisation completed." 1>&2
