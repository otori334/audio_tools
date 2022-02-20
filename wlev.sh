#!/bin/zsh
# http://ayageman.blogspot.com/2018/02/mp3-volume.html
# https://nico-lab.net/normalize_audio_with_ffmpeg/

IFS=$'\n'
readonly CMD_NAME="${0##*/}"
readonly TMP_DIR="/tmp/${CMD_NAME%.*}_"$$
trap 'rm -r "${TMP_DIR}" && exit' 0 1 2 3 15 && mkdir -p "${TMP_DIR}"

if [ $# -ne 2 ]; then
    echo "${CMD_NAME}: Please specify 2 args." 1>&2
    exit
fi
    
src_path="$1"
dest_path="$2"
tmp_path="${TMP_DIR}/a.wav"

if [ -d "${src_path}" ]; then
    echo "${CMD_NAME}: Input is file only." 1>&2
    exit
fi

if [ "${dest_path##*.}" != "wav" ]; then
    echo "${CMD_NAME}: Output is wav only." 1>&2
    exit
fi

if [ "${src_path##*.}" = "mov" -o "${src_path##*.}" = "mp4" ]; then
    ffmpeg -i "${src_path}" -hide_banner -af dynaudnorm -vn "${tmp_path}"
else
    ffmpeg -i "${src_path}" -hide_banner -af dynaudnorm "${tmp_path}"
fi

echo "Separated audio files from video." 1>&2
echo "Dynamic Audio Normalizer completed." 1>&2
echo "Loudness normalisation started." 1>&2
ffmpeg-normalize "${tmp_path}" -o "${dest_path}" -f -ar 48000 # マジックナンバー
echo "Loudness normalisation completed." 1>&2
