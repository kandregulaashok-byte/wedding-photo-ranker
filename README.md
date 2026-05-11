# 💍 Wedding Photo Ranker — DSLR Edition

Automatically scan, score, and rank **all your wedding photos** from a hard disk.
Works with every DSLR RAW format + JPEG/PNG/HEIC. Runs **100% locally on Windows** — nothing uploaded anywhere.

---

## ✨ What It Does

1. Scans every sub-folder on your hard disk automatically
2. Reads **RAW + JPEG + PNG + HEIC** files
3. Scores each photo on **sharpness, exposure, faces, color & contrast**
4. Removes near-duplicate / burst shots automatically
5. Copies **ALL photos ranked** to `Desktop\Wedding_Best_Photos_Ranked\`
6. Opens a **visual gallery** in your browser

**Output looks like:**
```
Rank_0001_Score98_DSC_0234.CR2   ← best photo
Rank_0002_Score95_DSC_0891.NEF
Rank_0003_Score93_IMG_4521.JPG
...all photos ranked best → worst
RANKING_REPORT.txt
gallery.html
```

---

## 📷 Supported Formats

| Brand | Formats |
|---|---|
| Canon | `.CR2` `.CR3` |
| Nikon | `.NEF` `.NRW` |
| Sony | `.ARW` `.SRF` `.SR2` |
| Fujifilm | `.RAF` |
| Olympus | `.ORF` |
| Panasonic | `.RW2` `.RAW` |
| Pentax | `.PEF` `.PTX` |
| Samsung | `.SRW` |
| Leica / Universal | `.DNG` `.RWL` |
| iPhone | `.HEIC` |
| Standard | `.JPG` `.JPEG` `.PNG` `.TIFF` |

---

## 🖥️ How to Run on Windows

### Step 1 — Install Python (once only)
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download and install Python
3. ⚠️ **Tick "Add Python to PATH"** during install!

### Step 2 — Plug in your Hard Disk
- Connect via USB → open File Explorer → note the drive letter (e.g. `D:\`)

### Step 3 — Double-click `DOUBLE_CLICK_TO_RUN.bat`
- A black window opens
- Installs all required packages automatically (first time ~2 min)
- Asks for your drive path → type e.g. `D:\` → press Enter
- Wait for it to finish → results appear on Desktop!

---

## ⭐ Scoring Weights

| Metric | Weight | What it checks |
|---|---|---|
| Sharpness | 30% | Is the photo in focus? |
| Faces | 25% | Are people clearly visible? |
| Exposure | 20% | Well-lit, not too dark/bright? |
| Color | 15% | Vibrant warm tones? |
| Contrast | 10% | Rich tonal range? |

---

## ⏱️ Time Estimates

| Photos | Time |
|---|---|
| ~500 | 3–5 minutes |
| ~2,000 | 10–15 minutes |
| ~5,000 | 30–40 minutes |

---

## 🔒 Privacy

100% local. No internet needed after first setup. Your photos never leave your computer.

---

## 📁 Files

| File | Description |
|---|---|
| `wedding_photo_ranker.py` | Main Python script |
| `DOUBLE_CLICK_TO_RUN.bat` | Windows one-click launcher |
| `HOW_TO_USE.txt` | Plain English instructions |

