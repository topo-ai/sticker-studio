"""Project initialization, prompt compilation, delivery verification and safe packaging."""
import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, features

from sticker_media import inspect

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ("identity", "anatomy", "caption", "motion", "loop", "edges")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(project, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("project artifact must use a relative path")
    path = (project / relative).resolve()
    if not path.is_relative_to(project.resolve()):
        raise ValueError("artifact path escapes project")
    return path


def load(project):
    config, pack = read(project/"project.json"), read(project/"pack.json")
    if config.get("schema_version") != 2 or pack.get("schema_version") != 2:
        raise ValueError("schema_version 2 required; migrate v1 manually")
    items = pack["items"]
    if config["mode"] not in ("static", "animated"):
        raise ValueError("unknown project mode")
    if not isinstance(config["count"], int) or config["count"] < 1 or len(items) != config["count"]:
        raise ValueError("item count differs from declared project count")
    ids = [x["id"] for x in items]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", x) for x in ids):
        raise ValueError("item ids must be unique safe names")
    allowed = {"gif", "webp"} if config["mode"] == "animated" else {"png"}
    style=config.get("style","")
    if not re.fullmatch(r"[a-z][a-z0-9-]*",style) or not (ROOT/f"references/styles/presets/{style}.md").is_file():
        raise ValueError("unknown or unsafe style preset")
    formats = config["required_formats"]
    if not formats or len(set(formats)) != len(formats) or not set(formats) <= allowed:
        raise ValueError("invalid required formats for project mode")
    for item in items:
        for relative in item.get("files", {}).values():
            inside(project, relative)
    return config, pack


def init(args):
    if args.project.exists():
        raise ValueError("project path exists; use a new project/version")
    if args.count < 1:
        raise ValueError("count must be positive")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.name):
        raise ValueError("name must be a lowercase project slug")
    if not (ROOT/f"references/styles/presets/{args.style}.md").is_file():
        raise ValueError("unknown style preset")
    args.project.mkdir(parents=True)
    for filename in ("project.json", "character.json", "pack.json", "visual-review.json", "profile-generic.json"):
        write(args.project/filename, read(ROOT/"assets/templates"/filename))
    config = read(args.project/"project.json")
    config.update(name=args.name, theme=args.theme, mode=args.mode, count=args.count, style=args.style)
    config["required_formats"] = ["gif", "webp"] if args.mode == "animated" else ["png"]
    write(args.project/"project.json", config)
    pack = read(args.project/"pack.json")
    pack["items"] = [{"id": f"{i:02}", "intent": "", "caption": "", "action": "",
                       "motion_key": "", "frame_beats": [], "durations_ms": [],
                       "state": "planned", "files": {}} for i in range(1,args.count+1)]
    write(args.project/"pack.json", pack)
    return {"project": str(args.project.resolve()), "state": "planned", "generated_images": 0}


def compile_prompts(project):
    config, pack = load(project)
    character = read(project/"character.json")
    master = character.get("master_path")
    if not master or not Path(master).is_file() or not character.get("invariants"):
        raise ValueError("inspect and select a real character master and invariants first")
    style_path = ROOT/f"references/styles/presets/{config['style']}.md"
    style = style_path.read_text(encoding="utf-8")
    jobs = []
    for item in pack["items"]:
        if not item.get("intent") or not item.get("action"):
            raise ValueError(f"{item['id']}: missing intent or action")
        beats, durations = item.get("frame_beats", []), item.get("durations_ms", [])
        cols, rows = pack["grid"]
        if config["mode"] == "animated":
            if min(cols,rows) < 1 or len(beats) != cols*rows or len(beats) != len(durations):
                raise ValueError(f"{item['id']}: beats/grid/duration count mismatch")
            if any(not isinstance(d,int) or d <= 0 or d % 10 for d in durations):
                raise ValueError("durations must be positive multiples of 10 ms")
        template = "frame-sequence" if config["mode"] == "animated" else "static-sticker"
        source = (ROOT/f"references/prompts/{template}.md").read_text(encoding="utf-8")
        caption = item.get("caption", "")
        values = {"master_path": master, "invariants": "; ".join(character["invariants"]),
                  "style": style, "intent": item["intent"], "action": item["action"],
                  "caption": caption or "NO TEXT", "cols": cols, "rows": rows, "count": len(beats),
                  "frame_beats": "\n".join(f"{i+1}. {b}" for i,b in enumerate(beats)),
                  "caption_instruction": f'Exact same caption "{caption}" in each cell, fixed location.' if caption else "NO TEXT"}
        for key, value in values.items():
            source = source.replace("{"+key+"}", str(value))
        jobs.append((item["id"], source))
    # Refuse overwrite; new prompt version invalidates old output only when selected.
    parent = project/"prompts"
    index = 1
    while (parent/f"v{index:03}").exists():
        index += 1
    destination = parent/f"v{index:03}"
    destination.mkdir(parents=True)
    for name, text in jobs:
        (destination/f"{name}.md").write_text(text,encoding="utf-8")
    return {"directory": str(destination), "prompts": len(jobs), "generation_executed": False}


def verify(project, require_visual=False):
    config, pack = load(project)
    profile = read(project/"profile-generic.json")
    review = read(project/"visual-review.json").get("items", {})
    errors, records = [], []
    seen_paths = set()
    for item in pack["items"]:
        for fmt in config["required_formats"]:
            relative = item.get("files", {}).get(fmt)
            if not relative:
                errors.append(f"{item['id']}: missing declared {fmt} file")
                continue
            path = inside(project, relative)
            if path in seen_paths:
                errors.append(f"{item['id']}: duplicate artifact reference")
                continue
            seen_paths.add(path)
            if not path.is_file():
                errors.append(f"missing file: {relative}")
                continue
            try:
                report = inspect(path)
                with Image.open(path) as im:
                    visible, signatures = [], set()
                    for n in range(getattr(im,"n_frames",1)):
                        im.seek(n)
                        rgba=im.convert("RGBA")
                        visible.append(rgba.getchannel("A").getextrema()[1] > 0)
                        flattened=Image.alpha_composite(Image.new("RGBA",rgba.size,(127,127,127,255)),rgba)
                        signatures.add(flattened.tobytes()+rgba.getchannel("A").tobytes())
                if report["format"].lower() != fmt:
                    errors.append(f"{relative}: actual format mismatch")
                if not all(visible):
                    errors.append(f"{relative}: empty foreground frame")
                if profile.get("size") and report["size"] != profile["size"]:
                    errors.append(f"{relative}: wrong canvas")
                if profile.get("max_bytes") is not None and report["bytes"] > profile["max_bytes"]:
                    errors.append(f"{relative}: exceeds byte budget")
                if profile.get("transparent") and report["transparent_frames"] != report["frames"]:
                    errors.append(f"{relative}: missing real transparent pixels")
                if config["mode"] == "animated":
                    if report["frames"] < 2 or len(signatures) < 2:
                        errors.append(f"{relative}: no encoded animation")
                    if profile.get("loop") and report["loop"] != 0:
                        errors.append(f"{relative}: not infinite loop")
                    if any(d<=0 for d in report["durations_ms"]):
                        errors.append(f"{relative}: invalid animation timing")
                current_hash=sha(path)
                if require_visual:
                    entry=review.get(item["id"],{})
                    if entry.get("file_hashes",{}).get(relative)!=current_hash:
                        errors.append(f"{relative}: visual review missing/stale")
                    if not all(entry.get("checks",{}).get(k)=="pass" for k in CHECKS):
                        errors.append(f"{item['id']}: visual checks incomplete")
                    if not entry.get("method") or not entry.get("evidence"):
                        errors.append(f"{item['id']}: visual evidence missing")
                    elif not inside(project,entry["evidence"]).is_file():
                        errors.append(f"{item['id']}: local visual evidence file missing")
                report["path"]=relative
                records.append({"id":item["id"],"path":relative,"sha256":current_hash,"media":report})
            except (OSError,ValueError) as exc:
                errors.append(f"{relative}: {exc}")
    return {"schema_version":2,"project":config["name"],"complete":not errors,
            "checked_at":datetime.now(timezone.utc).isoformat(),"errors":errors,"files":records,
            "visual_review_required":require_visual,"platform_compliance":"not_evaluated"}


def package(project, output):
    if output.exists():
        raise ValueError("archive exists; choose a new version")
    report=verify(project,require_visual=True)
    if not report["complete"]:
        raise ValueError("delivery rejected: "+"; ".join(report["errors"]))
    metadata=("project.json","character.json","pack.json","visual-review.json","profile-generic.json")
    all_files=[inside(project,f["path"]) for f in report["files"]]+[project/n for n in metadata]
    if any(p.resolve()==output.resolve() for p in all_files):
        raise ValueError("archive cannot replace a source artifact")
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        with zipfile.ZipFile(output,"x",zipfile.ZIP_DEFLATED) as archive:
            for path in all_files:
                archive.write(path,path.relative_to(project).as_posix())
            archive.writestr("delivery-manifest.json",json.dumps(report,ensure_ascii=False,indent=2))
    except Exception:
        if output.exists():
            output.unlink()
        raise
    return {"archive":str(output.resolve()),"sha256":sha(output),"files":len(report["files"]),
            "platform_compliance":"not_evaluated","published":False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest="command",required=True)
    subs.add_parser("doctor")
    for name in ("init","compile","verify","package"):
        sub=subs.add_parser(name)
        sub.add_argument("--project",type=Path,required=True)
        if name=="init":
            sub.add_argument("--name",required=True)
            sub.add_argument("--theme",required=True)
            sub.add_argument("--mode",choices=("static","animated"),required=True)
            sub.add_argument("--count",type=int,default=6)
            sub.add_argument("--style",default="chibi-ink")
        if name=="verify":
            sub.add_argument("--require-visual",action="store_true")
            sub.add_argument("--report",type=Path)
        if name=="package":
            sub.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        if a.command=="doctor":
            result={"python":sys.version.split()[0],"pillow":Image.__version__,"webp":features.check("webp"),
                    "ffmpeg":shutil.which("ffmpeg"),"ffprobe":shutil.which("ffprobe"),
                    "image_video_publish_tools":"discover in agent tool inventory; not tested here"}
        elif a.command=="init":result=init(a)
        elif a.command=="compile":result=compile_prompts(a.project)
        elif a.command=="verify":
            result=verify(a.project,a.require_visual)
            if a.report:
                if a.report.exists():raise ValueError("report exists; choose a new report path")
                write(a.report,result)
        else:result=package(a.project,a.output)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get("complete") is False else 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({"error":str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
