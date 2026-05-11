"""
💍 Wedding Photo Ranker — Windows + DSLR Edition
==================================================
Works on Windows 10 / 11.
Hard disk can be any drive letter: D:\  E:\  F:\  etc.

Supports ALL major DSLR RAW formats + JPEG/PNG/HEIC:
  Canon    → .CR2  .CR3
  Nikon    → .NEF  .NRW
  Sony     → .ARW  .SRF  .SR2
  Fuji     → .RAF
  Olympus  → .ORF
  Panasonic→ .RW2  .RAW
  Pentax   → .PEF  .PTX
  Samsung  → .SRW
  Leica    → .DNG  .RWL
  Standard → .JPG  .JPEG .PNG .TIFF .HEIC

What it does:
  1. Scans every sub-folder on your hard disk
  2. Reads RAW + JPEG + PNG + HEIC files
  3. Scores each photo (sharpness, exposure, faces, color, contrast)
  4. Removes near-duplicate / burst shots automatically
  5. Copies ALL photos ranked to Desktop\\Wedding_Best_Photos_Ranked\\
       Rank_001_Score98_DSC_0012.CR2   (best photo first)
  6. Opens a visual gallery in your browser automatically
"""

import os, sys, shutil, warnings, platform
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────
#  Auto-install all required packages
# ─────────────────────────────────────────────────────────
def pip_install(pkg, import_as=None):
    import importlib, subprocess
    try:
        importlib.import_module(import_as or pkg)
    except ImportError:
        print(f"  Installing {pkg} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

print("\n Checking required packages ...")
pip_install("opencv-python",  "cv2")
pip_install("Pillow",         "PIL")
pip_install("imagehash")
pip_install("numpy")
pip_install("tqdm")
pip_install("rawpy")

# HEIC support (iPhone photos mixed in)
try:
    pip_install("pillow-heif", "pillow_heif")
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_OK = True
except Exception:
    HEIC_OK = False

# ─────────────────────────────────────────────────────────
#  Imports
# ─────────────────────────────────────────────────────────
import cv2
import numpy as np
import rawpy
import imagehash
from PIL import Image
from tqdm import tqdm
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────
#  Supported file extensions
# ─────────────────────────────────────────────────────────
RAW_EXTS = {
    ".cr2", ".cr3",          # Canon
    ".nef", ".nrw",          # Nikon
    ".arw", ".srf", ".sr2",  # Sony
    ".raf",                  # Fujifilm
    ".orf",                  # Olympus
    ".rw2", ".raw",          # Panasonic
    ".pef", ".ptx",          # Pentax
    ".srw",                  # Samsung
    ".rwl", ".dng",          # Leica / Universal
}

STD_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
if HEIC_OK:
    STD_EXTS.update({".heic", ".heif"})

ALL_EXTS = RAW_EXTS | STD_EXTS

# ─────────────────────────────────────────────────────────
#  Welcome banner
# ─────────────────────────────────────────────────────────
os.system("cls")  # clear Windows console
print("=" * 60)
print("   WEDDING PHOTO RANKER  -  DSLR Edition  (Windows)")
print("=" * 60)
print()
print("  RAW formats  :", "  ".join(sorted(RAW_EXTS)).upper())
print("  JPEG/PNG etc :", "  ".join(sorted(STD_EXTS)).upper())
print()

# ─────────────────────────────────────────────────────────
#  Ask user for the hard disk / folder path
# ─────────────────────────────────────────────────────────
print("  Where are your wedding photos stored?")
print()
print("  Examples:")
print("    D:\\                          (whole hard disk drive D)")
print("    E:\\WeddingPhotos             (a specific folder on drive E)")
print("    F:\\DCIM                      (camera memory card)")
print("    C:\\Users\\YourName\\Pictures  (local Pictures folder)")
print()

while True:
    raw_input = input("  Paste the path here and press Enter: ").strip().strip('"').strip("'")
    source = Path(raw_input)
    if source.exists() and source.is_dir():
        print(f"\n  OK! Scanning: {source}\n")
        break
    print(f"\n  NOT FOUND: {raw_input}")
    print("  Please check the path and try again.\n")

# Output folder on Windows Desktop
OUTPUT_DIR = Path.home() / "Desktop" / "Wedding_Best_Photos_Ranked"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"  Results will be saved to:\n  {OUTPUT_DIR}\n")

# ─────────────────────────────────────────────────────────
#  Load image  →  BGR numpy array
#  Handles both RAW (rawpy) and standard (PIL)
# ─────────────────────────────────────────────────────────
def load_image(path: Path):
    ext = path.suffix.lower()
    if ext in RAW_EXTS:
        try:
            with rawpy.imread(str(path)) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=True,        # faster; still fine for scoring
                    no_auto_bright=False,
                    output_bps=8,
                )
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            pil = Image.fromarray(rgb)
            return bgr, pil
        except Exception:
            return None, None
    else:
        try:
            pil = Image.open(path).convert("RGB")
            bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            return bgr, pil
        except Exception:
            return None, None

# ─────────────────────────────────────────────────────────
#  Scoring functions  (each returns 0.0 – 1.0)
# ─────────────────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def score_sharpness(gray):
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(lap / 800.0, 1.0))

def score_exposure(gray):
    mean = float(np.mean(gray))
    return 1.0 - abs(mean - 128.0) / 128.0

def score_faces(bgr):
    small = cv2.resize(bgr, (0, 0), fx=0.5, fy=0.5)
    gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
    )
    n = len(faces)
    if n == 0:
        return 0.2
    return float(min(0.4 + n * 0.15, 1.0))

def score_color(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return float(np.mean(hsv[:, :, 1])) / 255.0

def score_contrast(gray):
    return float(min(gray.std() / 80.0, 1.0))

WEIGHTS = {
    "sharpness": 0.30,
    "exposure" : 0.20,
    "faces"    : 0.25,
    "color"    : 0.15,
    "contrast" : 0.10,
}

def composite(scores):
    return sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)

# ─────────────────────────────────────────────────────────
#  STEP 1 — Find all image files
# ─────────────────────────────────────────────────────────
print("  Scanning all sub-folders for photos ...")
all_files = [
    p for p in source.rglob("*")
    if p.suffix.lower() in ALL_EXTS and p.is_file()
]

raw_count = sum(1 for p in all_files if p.suffix.lower() in RAW_EXTS)
std_count = len(all_files) - raw_count

print(f"  Found {len(all_files):,} photos")
print(f"  ({raw_count:,} RAW files  +  {std_count:,} JPEG/PNG/etc)\n")

if not all_files:
    print("  ERROR: No photos found. Please check the path.")
    input("  Press Enter to close...")
    sys.exit(1)

# ─────────────────────────────────────────────────────────
#  STEP 2 — Score & deduplicate every photo
# ─────────────────────────────────────────────────────────
print("  Scoring photos now ...")
print("  (RAW files take a bit longer — please wait)\n")

records     = []
seen_hashes = {}
errors      = 0

for path in tqdm(all_files, unit="photo", ncols=65, colour="cyan"):
    bgr, pil = load_image(path)
    if bgr is None:
        errors += 1
        continue

    try:
        ph = str(imagehash.phash(pil))
    except Exception:
        ph = path.stem

    gray   = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    scores = {
        "sharpness": score_sharpness(gray),
        "exposure" : score_exposure(gray),
        "faces"    : score_faces(bgr),
        "color"    : score_color(bgr),
        "contrast" : score_contrast(gray),
    }
    total = composite(scores)

    rec = {
        "file"  : path,
        "score" : round(total, 4),
        "ext"   : path.suffix.lower(),
        **{k: round(v, 3) for k, v in scores.items()},
        "phash" : ph,
    }

    if ph in seen_hashes:
        idx = seen_hashes[ph]
        if total > records[idx]["score"]:
            records[idx] = rec
    else:
        seen_hashes[ph] = len(records)
        records.append(rec)

# ─────────────────────────────────────────────────────────
#  STEP 3 — Sort best → worst
# ─────────────────────────────────────────────────────────
records.sort(key=lambda r: r["score"], reverse=True)
unique     = len(records)
dupes_out  = len(all_files) - errors - unique

print(f"\n  Scoring complete!")
print(f"  Total scanned     : {len(all_files):,}")
print(f"  RAW files         : {raw_count:,}")
print(f"  Duplicates removed: {dupes_out:,}")
print(f"  Could not read    : {errors:,}")
print(f"  Unique ranked     : {unique:,}\n")

# ─────────────────────────────────────────────────────────
#  STEP 4 — Copy ranked files to Desktop folder
# ─────────────────────────────────────────────────────────
print(f"  Copying {unique:,} ranked photos to Desktop ...\n")
pad = len(str(unique))

for rank, rec in enumerate(
    tqdm(records, unit="photo", ncols=65, colour="green"), start=1
):
    src  = rec["file"]
    rstr = str(rank).zfill(pad)
    sstr = str(int(rec["score"] * 100)).zfill(3)
    # Windows-safe filename: no special chars
    safe_name = src.name.replace(":", "-").replace("*", "-").replace("?", "-")
    dest = OUTPUT_DIR / f"Rank_{rstr}_Score{sstr}_{safe_name}"
    try:
        shutil.copy2(src, dest)
    except Exception as e:
        tqdm.write(f"  Could not copy {src.name}: {e}")

# ─────────────────────────────────────────────────────────
#  STEP 5 — Text report
# ─────────────────────────────────────────────────────────
report = OUTPUT_DIR / "RANKING_REPORT.txt"
with open(report, "w", encoding="utf-8") as f:
    f.write("WEDDING PHOTO RANKING REPORT\n")
    f.write(f"Generated : {datetime.now():%Y-%m-%d %H:%M}\n")
    f.write(f"Source    : {source}\n")
    f.write(f"Total     : {unique} unique photos ranked\n")
    f.write(f"RAW files : {raw_count}\n")
    f.write(f"Duplicates removed: {dupes_out}\n")
    f.write("=" * 72 + "\n\n")
    f.write(f"{'Rank':<6} {'Score':>6}  {'Sharp':>6} {'Expo':>6} "
            f"{'Faces':>6} {'Color':>6} {'Cont':>6}  {'Ext':>5}  File\n")
    f.write("-" * 72 + "\n")
    for rank, rec in enumerate(records, 1):
        f.write(
            f"{rank:<6} {rec['score']:>6.3f}  "
            f"{rec['sharpness']:>6.2f} {rec['exposure']:>6.2f} "
            f"{rec['faces']:>6.2f} {rec['color']:>6.2f} "
            f"{rec['contrast']:>6.2f}  {rec['ext']:>5}  "
            f"{rec['file'].name}\n"
        )

# ─────────────────────────────────────────────────────────
#  STEP 6 — HTML visual gallery
# ─────────────────────────────────────────────────────────
gallery = OUTPUT_DIR / "gallery.html"
top     = records[:200]
cards   = ""

for rank, rec in enumerate(top, 1):
    rstr  = str(rank).zfill(pad)
    sstr  = str(int(rec["score"] * 100)).zfill(3)
    safe_name = rec["file"].name.replace(":", "-").replace("*","-").replace("?","-")
    fname = f"Rank_{rstr}_Score{sstr}_{safe_name}"
    ext   = rec["ext"]
    tag   = "RAW" if ext in RAW_EXTS else "JPG"
    tag_c = "#ffcc02" if tag == "RAW" else "#80cbc4"
    cards += f"""
  <div class="card">
    <div class="rank">#{rank}</div>
    <div class="tag" style="background:{tag_c};color:#111">{ext.upper()}</div>
    <img src="{fname}" alt="rank {rank}" loading="lazy"
         onerror="this.style.display='none';this.nextSibling.style.display='flex'">
    <div class="raw-ph" style="display:none">
      <div>RAW File<br><small>{ext.upper()}</small><br><small>Open with Lightroom</small></div>
    </div>
    <div class="info">
      <span class="score">Score: {rec['score']:.3f}</span>
      <span class="bars">
        <span title="Sharpness">Focus {int(rec['sharpness']*100)}%</span> |
        <span title="Exposure">Light {int(rec['exposure']*100)}%</span> |
        <span title="Faces">Faces {int(rec['faces']*100)}%</span>
      </span>
      <span class="name">{rec['file'].name}</span>
    </div>
  </div>"""

with open(gallery, "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Wedding Photos - Ranked</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Segoe UI,sans-serif;background:#0d0d0d;color:#eee;padding:20px}}
h1{{text-align:center;color:#f9d5e5;font-size:1.8rem;margin-bottom:4px}}
.sub{{text-align:center;color:#888;font-size:.85rem;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px}}
.card{{background:#1a1a1a;border-radius:12px;overflow:hidden;position:relative;transition:transform .15s}}
.card:hover{{transform:translateY(-3px)}}
.rank{{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.8);color:#ffcc02;
       font-weight:800;font-size:.8rem;padding:3px 10px;border-radius:20px;z-index:2}}
.tag{{position:absolute;top:8px;right:8px;font-size:.65rem;font-weight:700;
      padding:2px 8px;border-radius:10px;z-index:2}}
.card img{{width:100%;height:185px;object-fit:cover;display:block}}
.raw-ph{{width:100%;height:185px;background:#1e1e1e;align-items:center;
         justify-content:center;text-align:center;color:#666;font-size:.85rem;line-height:1.8}}
.info{{padding:10px 12px}}
.score{{display:block;font-size:.82rem;color:#c9a0dc;font-weight:700;margin-bottom:4px}}
.bars{{display:block;font-size:.7rem;color:#888;margin-bottom:4px}}
.name{{display:block;font-size:.68rem;color:#555;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
</style>
</head>
<body>
<h1>&#128141; Wedding Photos &mdash; Best {len(top)} of {unique}</h1>
<p class="sub">Ranked by Focus &bull; Lighting &bull; Faces &bull; Color &bull; Contrast
&nbsp;&mdash;&nbsp; RAW files: open with Lightroom / Windows Photos for full preview</p>
<div class="grid">{cards}
</div>
</body>
</html>""")

# ─────────────────────────────────────────────────────────
#  Open gallery in browser
# ─────────────────────────────────────────────────────────
try:
    os.startfile(str(gallery))
except Exception:
    pass

# ─────────────────────────────────────────────────────────
#  Done!
# ─────────────────────────────────────────────────────────
print(f"""
  ALL DONE!
  =========================================================
  Ranked photos  ->  {OUTPUT_DIR}
  Visual gallery ->  gallery.html  (opening in browser...)
  Full report    ->  RANKING_REPORT.txt

  Best photo : {records[0]['file'].name}   (score {records[0]['score']:.3f})
  2nd best   : {records[1]['file'].name if len(records)>1 else 'N/A'}
  3rd best   : {records[2]['file'].name if len(records)>2 else 'N/A'}

  Files are named like:
  Rank_0001_Score98_DSC_0234.CR2   <- best first
  Rank_0002_Score95_DSC_0891.NEF
  ...and so on for all {unique:,} photos
  =========================================================
""")

input("  Press Enter to close this window ...")
