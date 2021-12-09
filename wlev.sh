#!/bin/zsh

IFS=$'\n'
readonly CMD_NAME="${0##*/}"
readonly TMP_DIR="/tmp/${CMD_NAME%.*}_"$$
trap 'rm -r "${TMP_DIR}" && exit' 0 1 2 3 15 && mkdir -p "${TMP_DIR}"

if [ $# -ne 2 ]; then
    echo "${CMD_NAME}: Please specify 2 args." 1>&2
    exit
fi
    
wav_path="$1"
dest_path="$2"

if [ -d "${wav_path}" ]; then
    echo "${CMD_NAME}: Input is file only." 1>&2
    exit
fi

if [ "${dest_path##*.}" != "wav" ]; then
    echo "${CMD_NAME}: Output is wav only." 1>&2
    exit
fi

if [ "${wav_path##*.}" = "mov" ]; then
    wav_path="${TMP_DIR}/a.wav"
    ffmpeg -i "$1" -vn "${wav_path}"
    echo "Separated audio files from video." 1>&2
fi

ffmpeg-normalize "${wav_path}" -o "${wav_path}" -f -ar 48000 # マジックナンバー

echo "Loudness normalisation completed." 1>&2

ffmpeg -i "${wav_path}" -af dynaudnorm "${dest_path}"

echo "Dynamic Audio Normalizer completed." 1>&2
