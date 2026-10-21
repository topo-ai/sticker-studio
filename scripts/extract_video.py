"""Extract a bounded video interval with FFmpeg; never generates or uploads video."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--start",type=float,default=0)
    p.add_argument("--duration",type=float,required=True)
    p.add_argument("--fps",type=int,default=10)
    a=p.parse_args()
    try:
        if not a.video.is_file():raise ValueError("video not found")
        if a.out.exists():raise ValueError("output exists; use a new version")
        if a.start<0 or not 0<a.duration<=30 or not 1<=a.fps<=30:
            raise ValueError("start >= 0, duration in (0,30], fps in [1,30] required")
        ffmpeg=shutil.which("ffmpeg")
        ffprobe=shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:raise ValueError("FFmpeg and FFprobe required")
        metadata=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration",
                                 "-of","json",str(a.video.resolve())],capture_output=True,text=True,check=True,timeout=30)
        length=float(json.loads(metadata.stdout)["format"]["duration"])
        if a.start+a.duration>length+.02:raise ValueError("requested interval exceeds actual video")
        a.out.mkdir(parents=True)
        subprocess.run([ffmpeg,"-v","error","-nostdin","-n","-ss",str(a.start),"-i",str(a.video.resolve()),
                        "-t",str(a.duration),"-vf",f"fps={a.fps}",str(a.out.resolve()/"%04d.png")],
                       capture_output=True,text=True,check=True,timeout=120)
        frames=sorted(a.out.glob("*.png"))
        if len(frames)<2:raise ValueError("interval produced fewer than two frames")
        record={"video":str(a.video.resolve()),"start":a.start,"duration":a.duration,
                "fps":a.fps,"frames":len(frames),"alpha":"inspect source; not automatically matted"}
        (a.out/"extraction.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
        print(json.dumps(record,indent=2))
    except (ValueError,OSError,KeyError,subprocess.SubprocessError) as exc:
        p.exit(2,f"{exc}\n")


if __name__=="__main__":main()
