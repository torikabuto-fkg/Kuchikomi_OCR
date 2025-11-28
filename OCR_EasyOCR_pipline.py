import os
import sys
import glob
import subprocess
from datetime import datetime

from natsort import natsorted
from PIL import Image


# ========= 設定 =========

# 画像が入っているフォルダ
IMAGE_DIR = "./hokuto_scrapes/さいたま赤十字"

# 出力先
OUTPUT_DIR = "./output_easyocr"
INPUT_PDF = "./output_easyocr/input_combined.pdf"
OUTPUT_PDF = "./output_easyocr/さいたま赤十字_easyocr_searchable.pdf"

# ========= ユーティリティ =========


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def collect_images(image_dir: str):
    """対象フォルダから画像を自然順で集める"""
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff"]
    paths = []
    for pat in patterns:
        paths.extend(glob.glob(os.path.join(image_dir, pat)))

    if not paths:
        raise FileNotFoundError(f"画像が見つかりません: {image_dir}")

    return natsorted(paths)


def create_pdf_from_images(img_paths, output_pdf: str):
    """
    Pillowを使って画像を結合してPDFを作成
    """
    log(f"[1/2] PDF作成開始: {len(img_paths)} 枚 -> {output_pdf}")
    
    images = []
    for img_path in img_paths:
        img = Image.open(img_path)
        # PDFはRGB推奨
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)
    
    if not images:
        raise RuntimeError("PDF変換する画像がありません")
    
    # 最初の画像をベースに、残りを追加
    first_img = images[0]
    rest_imgs = images[1:] if len(images) > 1 else []
    
    first_img.save(output_pdf, save_all=True, append_images=rest_imgs)
    log(f"PDF作成完了: {output_pdf}")


def run_ocrmypdf_with_easyocr(input_pdf: str, output_pdf: str):
    """
    ocrmypdf + EasyOCRプラグインで検索可能PDFを作成
    """
    log(f"[2/2] ocrmypdf + EasyOCR実行中...")
    log(f"入力PDF: {input_pdf}")
    log(f"出力PDF: {output_pdf}")
    
    cmd = [
        "ocrmypdf",
        "--plugin", "easyocr",
        "--pdf-renderer", "sandwich",
        "--easyocr-batch-size", "4",
        "--jobs", "1",
        "-l", "jpn+eng",
        input_pdf,
        output_pdf
    ]
    
    log(f"実行コマンド: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        log("✅ OCR処理完了")
    except subprocess.CalledProcessError as e:
        log(f"❌ ocrmypdfエラー (exit code: {e.returncode})")
        if e.stderr:
            print("エラー出力:")
            print(e.stderr)
        raise


# ========= メイン処理 =========


def main():
    log("=== 画像 → PDF → EasyOCR(ocrmypdf) パイプライン開始 ===")

    # 画像フォルダ存在チェック
    if not os.path.isdir(IMAGE_DIR):
        log(f"❌ 画像フォルダが存在しません: {IMAGE_DIR}")
        sys.exit(1)

    ensure_output_dir(OUTPUT_DIR)

    # 1. 画像を集める
    try:
        img_paths = collect_images(IMAGE_DIR)
    except FileNotFoundError as e:
        log(f"❌ エラー: {e}")
        sys.exit(1)

    log(f"対象画像枚数: {len(img_paths)} 枚")

    # 2. 画像を結合してPDFを作成
    try:
        create_pdf_from_images(img_paths, INPUT_PDF)
    except Exception as e:
        log(f"❌ PDF作成エラー: {e}")
        sys.exit(1)

    # 3. ocrmypdf + EasyOCRで検索可能PDFを作成
    try:
        run_ocrmypdf_with_easyocr(INPUT_PDF, OUTPUT_PDF)
    except Exception as e:
        log(f"❌ OCR処理エラー: {e}")
        sys.exit(1)

    log("=== 全処理完了 ===")
    log(f"入力画像フォルダ: {os.path.abspath(IMAGE_DIR)}")
    log(f"中間PDF:         {os.path.abspath(INPUT_PDF)}")
    log(f"検索可能PDF:     {os.path.abspath(OUTPUT_PDF)}")


if __name__ == "__main__":
    main()
