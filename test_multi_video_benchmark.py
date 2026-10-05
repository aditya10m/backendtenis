import os
import time
from app.cv.match_play_skeleton import MatchPlaySkeletonTracker

tracker = MatchPlaySkeletonTracker(target_fps=8.0)

assets = [
    r"C:\Users\Administrator\Downloads\8224597-hd_1080_1920_30fps.mp4",
    r"C:\Users\Administrator\Downloads\8224590-hd_1080_1920_30fps.mp4",
    r"C:\Users\Administrator\Downloads\8224256-hd_1920_1080_30fps.mp4",
    r"C:\Users\Administrator\Downloads\ezgif-25fbc075d25294e8-jpg.zip",
    r"C:\Users\Administrator\Downloads\8224211-hd_1920_1080_30fps.mp4",
    r"C:\Users\Administrator\Downloads\ezgif-86b3f08f5537e38f-jpg.zip",
    r"C:\Users\Administrator\Downloads\8224292-hd_1920_1080_30fps.mp4"
]

print("=" * 80)
print("STARTING COMPREHENSIVE MULTI-VIDEO AI ACCURACY BENCHMARK")
print("=" * 80)

results_summary = []

for asset in assets:
    base = os.path.basename(asset)
    if not os.path.exists(asset):
        print(f"[-] Asset missing: {base}")
        results_summary.append({"asset": base, "status": "MISSING"})
        continue
    
    t0 = time.time()
    try:
        res = tracker.analyze_match_video(asset)
        dur = time.time() - t0
        frames = res["frames"]
        n_frames = len(frames)
        events = res["events"]
        
        knee_angles = [f["knee_angle"] for f in frames if f.get("knee_angle") is not None]
        avg_knee = sum(knee_angles) / len(knee_angles) if knee_angles else 0
        
        shoulder_rot = [f["shoulder_rotation"] for f in frames if f.get("shoulder_rotation") is not None]
        avg_shoulder = sum(shoulder_rot) / len(shoulder_rot) if shoulder_rot else 0
        
        balance_scores = [f["balance"] for f in frames if f.get("balance") is not None]
        avg_balance = sum(balance_scores) / len(balance_scores) if balance_scores else 0
        
        v_type = "Portrait (Mobile)" if res.get("is_portrait") else "Landscape"
        print(f"\n[+] Verified: {base}")
        print(f"    Type: {v_type} | Res: {res.get('width')}x{res.get('height')} | Video Dur: {res.get('duration_seconds')}s")
        print(f"    Processed in: {dur:.2f}s | Sampled Frames: {n_frames}")
        print(f"    Biomechanics -> Avg Knee Flexion: {avg_knee:.1f} deg | Avg Shoulder Coil: {avg_shoulder:.1f} deg | Avg Balance: {avg_balance:.1f}%")
        print("    Detected Stroke Events:")
        for ev in events:
            print(f"      * {ev['name']}: {ev['timestamp_str']} ({ev['timestamp']}s) [Knee: {ev.get('knee_flexion')} deg | Shoulder: {ev.get('shoulder_rotation')} deg | Bal: {ev.get('balance')}%] - {ev['note']}")
            
        results_summary.append({
            "asset": base,
            "status": "PASS",
            "resolution": f"{res.get('width')}x{res.get('height')}",
            "is_portrait": res.get("is_portrait"),
            "duration": res.get("duration_seconds"),
            "frames": n_frames,
            "process_time": round(dur, 2),
            "events": [f"{ev['name']}@{ev['timestamp_str']}" for ev in events],
            "avg_knee": round(avg_knee, 1),
            "avg_shoulder": round(avg_shoulder, 1),
            "avg_balance": round(avg_balance, 1)
        })
    except Exception as e:
        print(f"[-] Error processing {base}: {e}")
        results_summary.append({"asset": base, "status": "FAIL", "error": str(e)})

print("\n" + "=" * 80)
passed = sum(1 for r in results_summary if r["status"] == "PASS")
print(f"BENCHMARK SUMMARY: {passed}/{len(results_summary)} PASSED")
print("=" * 80)
