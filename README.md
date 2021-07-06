# これは何
音・信号処理に関する小ツール群（予定）

## [wav_conversion.py](wav_conversion.py)

- SciPyが読み込めないwavファイルをSciPyが読み込めるように変換するツール
- [wavファイルの周波数信号をプロットさせるプログラムでエラーが消えない](https://teratail.com/questions/319432) のエラー `WavFileWarning: Chunk (non-data) not understood, skipping it.` を解決する
- SciPyの実装を見てないからわからないが一応解決する
 - このエラーはおそらく[BWF](https://ja.wikipedia.org/wiki/Broadcast_Wave_Format)フォーマットが原因
   - BWFフォーマットに記録された時間情報と実際のデータの長さのズレによる（多分）
   - このツールによりBWFのメタデータは失われる

## [wcut.py](wcut.py)

- wavファイルを切り出すツール
- オプション引数で切り出し方を指定できる
