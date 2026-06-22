# file2png

ファイルまたはフォルダを分割ZIPにし、各パートをPNGとして見えるファイルに埋め込むツールです。

## ディレクトリ

- `base/`: 埋め込み先に使うPNG画像
- `outputs/`: `--output-dir` を指定した場合の出力先
- `work/`: 7-Zipの分割ファイルなどの一時作業先
- `file2png.py`: ファイル/フォルダをPNG群に変換
- `png2file.py`: PNG群から元ファイル/フォルダを復元
- `zipaspng.py`: ZIPをPNGに埋め込む低レベル処理

`outputs/` と `work/` の中身はGit管理しません。

## 使い方

PNGに埋め込む:

```powershell
python file2png.py --src <ファイルまたはフォルダ>
```

出力先は、標準では入力ファイルまたはフォルダの隣に作る `<元ファイル名>_png/` です。既に同名の出力フォルダがあり、中身が残っている場合は停止します。置き換えたい場合は `--replace` を付けます。

PNGから取り出す:

```powershell
python png2file.py --src <PNGファイル群>
```

復元先は、選択したPNGがあるフォルダです。既存ファイルは標準では上書きせずスキップします。上書きしたい場合は `--overwrite` を付けます。

## As/r設定

As/rからは、このリポジトリ内のスクリプトを直接呼び出します。
`Run` には、Pythonの実行ファイルをフルパスで指定します。
ユーザー名の直書きを避けるため、OS環境変数 `%USERPROFILE%` を使います。

`C:\Asr\Ubar\ponjorapi\Script\file2png.txt`

```text
CommandLineOption="D:\Dev\06_file2png-split\file2png.py" "--src" ?SelFile?
Run=%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe
```

`C:\Asr\Ubar\ponjorapi\Script\png2file.txt`

```text
CommandLineOption="D:\Dev\06_file2png-split\png2file.py" "--src" ?SelFile?
Run=%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe
```

`C:\Asr\Plugin\External_Script\file2png.py` などのコピーは置かず、As/rからもこのリポジトリ内の実体を直接呼び出す想定です。

## 7-Zip

標準では `C:\Program Files\7-Zip\7z.exe` を使います。別の場所にある場合は環境変数 `FILE2PNG_7ZIP` に実行ファイルのパスを設定してください。

## License

MIT License.

The ZIP-to-PNG embedding logic in `zipaspng.py` is based on
[yoshi389111/zip-as-png-py](https://github.com/yoshi389111/zip-as-png-py),
copyright (c) 2018 sato yoshiyuki, released under the MIT License.
