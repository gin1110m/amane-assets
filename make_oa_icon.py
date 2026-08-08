#!/usr/bin/env python3.11
"""
LINE公式アカウント「あまね｜教室の仕組み化」プロフィールアイコン生成（仮版）

ブランド規律（正本: あまねサムネcharter）
- 濃紺 #1F3A5F / 生成り #F4EFE6 / 低彩度セージ #9BAF9A
- 完全な単色ベタ面のみ。グラデーション・発光・グランジ・飾りは一切なし
- LINEアイコンは円形トリム＋小サイズ表示が前提 → 中央 直径88% の安全円内に収める
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
SS = 4  # スーパーサンプリング倍率（アンチエイリアス用）

NAVY = (0x1F, 0x3A, 0x5F)
CREAM = (0xF4, 0xEF, 0xE6)
SAGE = (0x9B, 0xAF, 0x9A)

TEXT = "あまね"
SAFE_RATIO = 0.88          # 円形トリムの安全直径
FIT_MARGIN = 0.94          # 安全円に対する呼吸量。1.0=円に内接（小サイズで詰まって見える）
GAP = 40                   # 文字下端 ↔ ラインの間隔(px, 1024基準)
LINE_H = 8                 # ライン太さ(px)
LINE_W_RATIO = 0.60        # ライン幅 = 文字幅 * 0.60

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_ICON = os.path.join(OUT_DIR, "oa-icon.png")
OUT_PREVIEW = os.path.join(OUT_DIR, "oa-icon-preview.png")

# 太めの日本語ゴシックを優先順に探索
FONT_CANDIDATES = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.otf",
    "/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/Library/Fonts/Microsoft/Meiryo Bold.ttf",
    "/Library/Fonts/MPLUS1-Bold.ttf",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    sys.exit("日本語太字フォントが見つかりません: " + ", ".join(FONT_CANDIDATES))


def render_text(font):
    """テキストを実際にラスタライズし、インクだけに切り詰めたマスクを返す。

    font.getbbox()/textbbox() はサイドベアリング込みの値を返し、このフォントでは
    実レンダリング結果と 15px ほどずれた（左右非対称の原因）。
    ラスタライズ実測を唯一の基準にして、中央配置のズレを構造的に排除する。
    """
    size = font.size
    pad = size
    layer = Image.new("L", (size * (len(TEXT) + 2), size * 3), 0)
    ImageDraw.Draw(layer).text((pad, pad), TEXT, font=font, fill=255)
    bbox = layer.getbbox()
    return layer.crop(bbox)


def fit_font_size(font_path, radius):
    """文字+ライン のグループ矩形が半径 radius の円に内接する最大サイズを二分探索"""
    lo, hi = 40 * SS, 900 * SS
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        tw, th = render_text(ImageFont.truetype(font_path, mid)).size
        gh = th + GAP * SS + LINE_H * SS          # グループ高さ（文字+間隔+ライン）
        if ((tw / 2.0) ** 2 + (gh / 2.0) ** 2) ** 0.5 <= radius:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def main():
    font_path = find_font()
    canvas = SIZE * SS
    radius = canvas * SAFE_RATIO / 2.0

    size = fit_font_size(font_path, radius * FIT_MARGIN)
    font = ImageFont.truetype(font_path, size)
    text_mask = render_text(font)
    tw, th = text_mask.size
    line_w = tw * LINE_W_RATIO
    gh = th + GAP * SS + LINE_H * SS

    img = Image.new("RGB", (canvas, canvas), NAVY)
    d = ImageDraw.Draw(img)

    # 上下中央。ラインは軽い装飾なので視覚的重心＝文字。
    # 幾何中央(=ラインを等価に扱う)と文字だけの中央の中間を取り、光学的に中央へ落とす。
    group_top = int(round((canvas - gh) / 2.0 + (GAP * SS + LINE_H * SS) * 0.25))
    # インク実測マスクをそのまま貼る＝左右中央が構造的に保証される
    img.paste(CREAM, (int(round((canvas - tw) / 2.0)), group_top), text_mask)

    # セージの水平ライン
    line_top = group_top + th + GAP * SS
    d.rectangle(
        [(canvas - line_w) / 2.0, line_top,
         (canvas + line_w) / 2.0, line_top + LINE_H * SS],
        fill=SAGE,
    )

    icon = img.resize((SIZE, SIZE), Image.LANCZOS)
    icon.save(OUT_ICON, "PNG")

    # 円形プレビュー（LINE表示の見え方確認用）
    mask = Image.new("L", (canvas, canvas), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, canvas - 1, canvas - 1], fill=255)
    mask = mask.resize((SIZE, SIZE), Image.LANCZOS)
    preview = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    preview.paste(icon, (0, 0), mask)
    preview.save(OUT_PREVIEW, "PNG")

    scale = 1.0 / SS
    print(f"font           : {font_path}")
    print(f"font size      : {size * scale:.1f}px (1024基準)")
    print(f"text ink w x h : {tw * scale:.1f} x {th * scale:.1f}")
    print(f"group height   : {gh * scale:.1f}")
    print(f"corner radius  : {((tw / 2) ** 2 + (gh / 2) ** 2) ** 0.5 * scale:.1f} / safe {radius * scale:.1f}")
    print(f"line width     : {line_w * scale:.1f}")
    print(f"out            : {OUT_ICON}")
    print(f"preview        : {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
