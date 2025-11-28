import os
import glob
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from paddleocr import PaddleOCR
from natsort import natsorted
from tqdm import tqdm
import logging

# ログ抑制
logging.getLogger("ppocr").setLevel(logging.WARNING)

# --- 設定 ---
IMAGE_DIR = "./hokuto_scrapes/"
OUTPUT_PDF = "./output_data/hokuto_searchable.pdf"

# 【重要】日本語フォントの設定 (WSLからWindowsのフォントを参照)
# これがないとPDFに日本語を書き込めず文字化けします
FONT_PATH = "/mnt/c/Windows/Fonts/msgothic.ttc"  # Windows標準のMSゴシック
FONT_NAME = "MsGothic"

def register_font():
    """日本語フォントをReportLabに登録する"""
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        print(f"✅ フォントをロードしました: {FONT_PATH}")
    except Exception as e:
        print(f"⚠️ フォント読み込みエラー: {e}")
        print("日本語が文字化けする可能性があります。FONT_PATHを確認してください。")
        # フォールバック（英語のみなどになる可能性あり）

def main():
    # 1. 出力先作成
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

    # 2. フォント登録
    register_font()

    # 3. PaddleOCR準備 (回転補正なし・CPU使用)
    print("OCRエンジンを初期化中...")
    ocr = PaddleOCR(use_angle_cls=False, lang='japan', use_gpu=False, show_log=False)

    # 4. 画像リスト取得
    img_paths = natsorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")))
    if not img_paths:
        print("画像が見つかりません")
        return

    print(f"対象画像: {len(img_paths)}枚 -> PDF生成開始")

    # 5. PDF生成開始
    # 最初の画像のサイズに合わせてCanvasを作成（途中でサイズ変更も可能）
    first_img = Image.open(img_paths[0])
    c = canvas.Canvas(OUTPUT_PDF, pagesize=first_img.size)

    for img_path in tqdm(img_paths, desc="Processing"):
        img = Image.open(img_path)
        w, h = img.size
        
        # ページサイズを画像に合わせる
        c.setPageSize((w, h))

        # A. 画像を背面に描画
        c.drawImage(img_path, 0, 0, width=w, height=h)

        # B. OCR実行
        # result = [[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, conf)], ...]
        result = ocr.ocr(img_path, cls=True)

        # C. 透明テキストを重ねる
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                text = line[1][0]
                
                # 座標計算 (PaddleOCRは左上原点、PDFは左下原点)
                # box[0] = 左上(x, y), box[2] = 右下(x, y)
                x_left = box[0][0]
                y_top = box[0][1]
                x_right = box[2][0]
                y_bottom = box[2][1]

                # PDF座標系への変換 (Y軸を反転)
                pdf_x = x_left
                pdf_y = h - y_bottom  # 下からの位置

                # フォントサイズの計算 (高さに合わせる)
                box_height = y_bottom - y_top
                font_size = box_height * 0.9 # 少し小さめにしないとはみ出る場合がある

                # テキスト描画設定
                c.setFont(FONT_NAME, font_size)
                
                # 【ここが魔法】完全透明な白色テキストにする
                # fillOpacity=0で不可視、fillColor='white'で背景に溶け込む
                c.setFillColorRGB(1, 1, 1, alpha=0)  # 白色で完全透明
                
                # 書き込み
                c.drawString(pdf_x, pdf_y, text)
                
                # 次のテキスト用に透明度をリセット
                c.setFillColorRGB(0, 0, 0, alpha=1)

        # ページ確定
        c.showPage()

    # 保存
    c.save()
    print(f"\n✅ 検索可能PDFを作成しました: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
