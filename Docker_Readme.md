# PaddleOCR GPU + Docker で PDF OCR パイプラインを回す

このリポジトリでは、Docker 上で PaddleOCR を GPU 利用しながら実行し、  
画像群から PDF を生成しつつ OCR 結果を TXT / DOCX に出力するパイプラインを提供します。

- 画像 → 1 つの PDF を生成
- 各画像を PaddleOCR (GPU) で OCR
- テキストを TXT / DOCX で保存

メインの処理は `ocr_pipeline.py` に実装されています。

---

## 環境要件

### ハードウェア / OS

- NVIDIA GPU 搭載マシン
- Windows 10/11
  - WSL2 (Ubuntu など) 有効化済み推奨

### ソフトウェア

- Docker Desktop (Windows)
  - WSL2 backend を有効化
- WSL2 上のシェル（例: Ubuntu）  
  → `docker` コマンドが WSL から叩ける状態にしておく

### 動作確認

#### 1. Windows 側で GPU を確認

コマンドプロンプト or PowerShell:

```powershell
nvidia-smi
GPU 情報と CUDA Version が表示されれば OK です。

2. WSL 側で Docker を確認
WSL (Ubuntu) のターミナル:

bash
コードをコピーする
docker --version
バージョン情報が出ていれば OK です。

ディレクトリ構成 (例)
text
コードをコピーする
your-repo/
├── Dockerfile
├── ocr_pipeline.py        # OCR パイプライン本体
├── data/
│   └── images/            # OCR 対象の PNG 画像をここに置く
└── output/                # 出力(PDF/TXT/DOCX)がここに生成される想定
ocr_pipeline.py 内のパス設定は必要に応じて書き換えてください（後述）。

Docker イメージ
PaddleOCR チームが公開している GPU 対応の公式イメージをベースにしています。

Dockerfile
dockerfile
コードをコピーする
# PaddleOCR (GPU) がすでに入っている公式イメージ
FROM paddlecloud/paddleocr:2.6-gpu-cuda10.2-cudnn7-latest

# 作業ディレクトリ
WORKDIR /workspace

# 追加で必要な Python ライブラリをインストール
# - img2pdf: 画像 → PDF 結合
# - python-docx: DOCX 出力
# - natsort: ファイル名の自然順ソート
# - tqdm: 進捗バー表示
RUN pip install --no-cache-dir \
    img2pdf \
    python-docx \
    natsort \
    tqdm
ocr_pipeline.py のパス設定
ocr_pipeline.py 内の先頭付近にある設定を、リポジトリ構成に合わせて修正します。

python
コードをコピーする
# --- 設定エリア ---
# コンテナ内から見たパスで指定する
IMAGE_DIR = "./data/images"        # OCRしたい画像(png)を置くディレクトリ
OUTPUT_DIR = "./output"            # 出力先ディレクトリ
PDF_FILENAME = "reviews.pdf"
DOCX_FILENAME = "reviews.docx"
TXT_FILENAME = "reviews_raw_text.txt"
IMAGE_DIR にある *.png が OCR 対象

OUTPUT_DIR に PDF / TXT / DOCX が生成されます

Docker イメージのビルド
リポジトリ直下で以下を実行：

bash
コードをコピーする
cd your-repo
docker build -t paddleocr-gpu .
Successfully tagged paddleocr-gpu:latest と出れば成功です。

コンテナの起動 & OCR の実行
1. WSL 上でリポジトリのディレクトリに移動
bash
コードをコピーする
cd /mnt/c/Users/あなたのユーザー名/path/to/your-repo
/mnt/c/... は Windows の C:\ ドライブを WSL から見たパスです。

2. OCR 対象の画像を配置
data/images に PNG 画像を入れておきます。

text
コードをコピーする
your-repo/
└── data/
    └── images/
        ├── page_01.png
        ├── page_02.png
        └── ...
3. Docker コンテナでスクリプトを実行
bash
コードをコピーする
docker run --rm -it \
  --gpus all \
  -v "${PWD}:/workspace" \
  paddleocr-gpu \
  python ocr_pipeline.py
--gpus all
コンテナからホストの GPU を利用するためのオプションです。

-v "${PWD}:/workspace"
現在のディレクトリをコンテナ内 /workspace にマウントし、
Dockerfile で指定した WORKDIR /workspace と合わせています。

4. 出力結果
ocr_pipeline.py が正常終了すると、OUTPUT_DIR に以下が生成されます。

text
コードをコピーする
output/
├── reviews.pdf             # 画像を結合した PDF
├── reviews_raw_text.txt    # OCR 生テキスト
└── reviews.docx            # Word 形式で整形されたテキスト
GPU / CPU の自動切り替えについて
ocr_pipeline.py では、PaddlePaddle のデバイス状況を見て
自動的に GPU / CPU を切り替えるようにしています。

python
コードをコピーする
def setup_device():
    if paddle.device.is_compiled_with_cuda():
        try:
            paddle.set_device("gpu")
            print("✅ GPUモードで動作します")
            return True
        except Exception as e:
            print(f"⚠️ GPU設定に失敗したため CPU にフォールバックします: {e}")

    paddle.set_device("cpu")
    print("⚠️ GPUが利用できないため CPUモードで動作します")
    return False
GPU が利用可能な場合: paddle.set_device("gpu") ＋ use_gpu=True

利用できない場合: 自動的に cpu にフォールバック

Docker 実行時に --gpus all を付け忘れると CPU モードで動きます。

トラブルシューティング
docker: 'xxx' is not a docker command / The term 'docker' is not recognized
Docker Desktop がインストールされていないか、起動していません。

もしくは WSL から Docker が見えていない可能性があります。

Docker Desktop 設定で「Use the WSL 2 based engine」を有効化

対象の WSL ディストロとの統合を ON にしてください。

docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
NVIDIA ドライバ / WSL2 の GPU サポート / NVIDIA Container Toolkit の設定が正しくない可能性があります。

Windows 側で nvidia-smi が通るか確認した上で、
Docker Desktop 側の WSL2 + GPU 設定を見直してください。
