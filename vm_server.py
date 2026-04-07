#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║     VM - VIDEO MAKER SERVER       ║
║     Chalao: python bhajan_server.py         ║
║     Phir: VM_Maker.html open karo       ║
╚══════════════════════════════════════════════╝
"""
from flask import Flask, request, jsonify, send_file
import shutil
# Check if ffmpeg available
FFMPEG = shutil.which('ffmpeg') or 'ffmpeg'
import os
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import subprocess, os, json, tempfile, threading, uuid, math, sys, webbrowser

app = Flask(__name__)
CORS(app)
jobs = {}

# ── FONTS ────────────────────────────────────────────────────
def get_fonts(sizes):
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    reg_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    bold = next((p for p in bold_paths if os.path.exists(p)), None)
    reg  = next((p for p in reg_paths  if os.path.exists(p)), None)
    result = {}
    for name, size, is_bold in sizes:
        path = bold if is_bold else reg
        try:
            result[name] = ImageFont.truetype(path, size) if path else ImageFont.load_default()
        except:
            result[name] = ImageFont.load_default()
    return result

# ── UTILS ────────────────────────────────────────────────────
def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3: h = h[0]*2 + h[1]*2 + h[2]*2
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def blend(base, color, alpha):
    return tuple(min(255, int(b + c * alpha)) for b, c in zip(base, color))

# ── FRAME RENDERER ───────────────────────────────────────────
def make_frame(t, dur, god_name, god_symbol, mantra, lyrics, theme, W=1280, H=720):
    img = Image.new("RGB", (W, H), (0,0,0))
    draw = ImageDraw.Draw(img)

    c1   = hex2rgb(theme["c1"])
    c2   = hex2rgb(theme["c2"])
    fire = hex2rgb(theme["fire"])
    gold = hex2rgb(theme["gold"])
    acc  = hex2rgb(theme["acc"])

    # ── Background gradient + glow ──
    for y in range(0, H, 2):
        ratio = y / H
        base = tuple(int(c1[i] + (c2[i]-c1[i])*ratio) for i in range(3))
        cx, cy2 = W//2, H//2
        # radial glow
        glow_a = 0.25 * (0.6 + 0.4*math.sin(t*2))
        draw.rectangle([(0,y),(W,y+1)], fill=blend(base, fire, glow_a * max(0, 1-(y/H))))

    # ── Animated particles ──
    for i in range(22):
        px = int((math.sin(i*7.3 + t*0.5) + 1) / 2 * W)
        py = int((math.cos(i*4.1 + t*0.4) + 1) / 2 * H)
        sz = max(1, int(2 + 2*abs(math.sin(i+t))))
        brt = int(160 + 95*abs(math.sin(i + t*2)))
        draw.ellipse([px-sz, py-sz, px+sz, py+sz],
                     fill=(min(255,brt), int(brt*0.5), 0))

    # ── Fonts ──
    F = get_fonts([
        ("title", 50, True), ("lyric", 52, True),
        ("small", 26, False), ("dim",   32, False)
    ])

    # ── Top decoration line ──
    for x in range(W//5, 4*W//5):
        a = math.sin((x - W//5) / (3*W//5) * math.pi)
        draw.point((x, 85), fill=(int(165*a), int(135*a), 0))

    # ── God name + symbol ──
    gv = int(200 + 55*math.sin(t*2))
    title = f"{god_symbol}  {god_name.upper()}"
    tw = int(draw.textlength(title, font=F["title"]))
    draw.text(((W-tw)//2+2, 18), title, font=F["title"], fill=(50, 20, 0))
    draw.text(((W-tw)//2,   16), title, font=F["title"], fill=(gv, int(gv*0.85), 0))

    # ── Mantra ──
    mw = int(draw.textlength(mantra, font=F["small"]))
    draw.text(((W-mw)//2, 78), mantra, font=F["small"],
              fill=(acc[0]//2, max(0, acc[1]//3), 55))

    # ── Current lyric ──
    ci = -1
    for i, ld in enumerate(lyrics):
        if t >= ld["t"]: ci = i
        else: break

    prev_l = lyrics[ci-1]["l"] if ci > 0          else ""
    cur_l  = lyrics[ci]["l"]   if ci >= 0          else mantra
    next_l = lyrics[ci+1]["l"] if ci < len(lyrics)-1 else ""
    cy = H // 2

    if prev_l:
        pw = int(draw.textlength(prev_l, font=F["dim"]))
        draw.text(((W-pw)//2, cy-110), prev_l, font=F["dim"], fill=(55, 42, 12))

    draw.line([(W//8, cy-55), (7*W//8, cy-55)], fill=(75, 58, 0), width=1)
    draw.line([(W//8, cy+55), (7*W//8, cy+55)], fill=(75, 58, 0), width=1)

    lv = int(220 + 35*math.sin(t*3))
    lw = int(draw.textlength(cur_l, font=F["lyric"]))
    draw.text(((W-lw)//2+2, cy-25), cur_l, font=F["lyric"], fill=(45, 14, 0))
    draw.text(((W-lw)//2,   cy-27), cur_l, font=F["lyric"], fill=(255, lv, 0))

    draw.text((W//12,    cy-27), god_symbol, font=F["dim"], fill=(90, 62, 0))
    draw.text((10*W//12, cy-27), god_symbol, font=F["dim"], fill=(90, 62, 0))

    if next_l:
        nw = int(draw.textlength(next_l, font=F["dim"]))
        draw.text(((W-nw)//2, cy+72), next_l, font=F["dim"], fill=(55, 42, 12))

    # ── Progress bar ──
    by, bx1, bx2 = H-60, W//8, 7*W//8
    draw.rectangle([bx1, by, bx2, by+5], fill=(22, 14, 3))
    prog = min(t / max(dur, 1), 1.0)
    if prog > 0:
        draw.rectangle([bx1, by, bx1+int((bx2-bx1)*prog), by+5], fill=(255, 145, 0))

    mins, secs = int(t)//60, int(t)%60
    dm,   ds   = int(dur)//60, int(dur)%60
    draw.text((bx1, by+9), f"{mins}:{secs:02d}", font=F["small"], fill=(110, 82, 14))
    ds2 = f"{dm}:{ds:02d}"
    dw2 = int(draw.textlength(ds2, font=F["small"]))
    draw.text((bx2-dw2, by+9), ds2, font=F["small"], fill=(110, 82, 14))

    return img

# ── VIDEO GENERATION ─────────────────────────────────────────
def generate_video(job_id, audio_path, lyrics, god_name, god_symbol,
                   mantra, theme, output_path):
    try:
        jobs[job_id].update(status="processing", progress=2,
                            message="Audio duration check kar rahe hain...")

        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True)
        dur = float(r.stdout.strip() or "180")

        FPS   = 12
        total = int(dur * FPS)
        jobs[job_id]["message"] = f"Frames generate ho rahi hain (total {total})..."

        tmpdir    = tempfile.mkdtemp()
        frame_dir = os.path.join(tmpdir, "frames")
        os.makedirs(frame_dir)

        for fi in range(total):
            t = fi / FPS
            frame = make_frame(t, dur, god_name, god_symbol,
                               mantra, lyrics, theme)
            frame.save(os.path.join(frame_dir, f"f{fi:06d}.jpg"), quality=85)
            if fi % 24 == 0:
                pct = int(fi / total * 80)
                jobs[job_id].update(progress=pct,
                    message=f"Frame {fi}/{total} ({pct}%)")

        jobs[job_id].update(progress=83,
            message="FFmpeg se video compile ho rahi hai...")

        cmd = [FFMPEG, "-y",
               "-framerate", str(FPS),
               "-i", os.path.join(frame_dir, "f%06d.jpg"),
               "-i", audio_path,
               "-c:v", "libx264", "-preset", "fast", "-crf", "22",
               "-c:a", "aac", "-b:a", "192k",
               "-pix_fmt", "yuv420p", "-shortest",
               output_path]
        res = subprocess.run(cmd, capture_output=True, text=True)

        import shutil; shutil.rmtree(tmpdir)

        if res.returncode == 0 and os.path.exists(output_path):
            jobs[job_id].update(status="done", progress=100,
                                message="✅ Video ready!")
        else:
            jobs[job_id].update(status="error",
                message="FFmpeg error: " + res.stderr[-300:])

    except Exception as e:
        jobs[job_id].update(status="error", message=str(e))


# ── ROUTES ───────────────────────────────────────────────────
@app.route("/")
def index():
    # Serve the VM_Maker.html if exists
    html_path = os.path.join(os.path.dirname(__file__), "VM_Maker.html")
    if os.path.exists(html_path):
        return send_file(html_path)
    return "<h1>🔱 VM Server Running!</h1><p>Upload VM_Maker.html to same folder</p>"

@app.route("/ping")
def ping():
    return jsonify({"status": "ok",
                    "message": "VM Server chal raha hai! 🔱"})

@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    data    = request.json
    job_id  = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "queued", "progress": 0,
                    "message": "Queue mein hai...", "path": None}

    import base64
    tmpdir     = tempfile.mkdtemp()
    audio_path = os.path.join(tmpdir, "audio.mp3")
    with open(audio_path, "wb") as f:
        f.write(base64.b64decode(data["audio_b64"]))

    output_path = os.path.join(tmpdir, "output.mp4")
    jobs[job_id]["path"] = output_path

    threading.Thread(
        target=generate_video,
        args=(job_id, audio_path, data["lyrics"],
              data["god_name"], data["god_symbol"],
              data["mantra"],   data["theme"], output_path),
        daemon=True
    ).start()

    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job: return jsonify({"status": "not_found"}), 404
    return jsonify(job)

@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return "Not ready", 404
    return send_file(job["path"], as_attachment=True,
                     download_name="VM_Video.mp4",
                     mimetype="video/mp4")

# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("=" * 52)
    print("  🔱  VM - VIDEO MAKER SERVER  🔱")
    print("=" * 52)
    print("  URL : http://localhost:8765")
    print("  Phir: VM_Maker.html open karo")
    print("  Band: Ctrl+C")
    print("=" * 52)
    print()
    port = int(os.environ.get("PORT", 8765))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
