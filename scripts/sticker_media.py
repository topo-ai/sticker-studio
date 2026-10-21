"""Encode aligned PNG frames and inspect files; no platform rules are assumed."""
import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, GifImagePlugin


def save_delta_gif(frames, output, durations):
    """Persist the first canvas; clear/redraw only the union of changing pixels."""
    boxes=[ImageChops.difference(frames[0],f).getbbox() for f in frames[1:]]
    boxes=[b for b in boxes if b]
    if not boxes:raise ValueError('no changing GIF pixels')
    roi=(min(b[0] for b in boxes),min(b[1] for b in boxes),
         max(b[2] for b in boxes),max(b[3] for b in boxes))
    # Pillow's low-level writer preserves exact ROI offsets and mixed disposals.
    # Normal save_all may expand disposal=2 frames back to the full foreground.
    if durations[0]<40:raise ValueError('delta encoding needs first hold >=40ms to prime and clear ROI without a flash')
    with output.open('wb') as fp:
        for block in GifImagePlugin._get_global_header(frames[0],{'loop':0,'transparency':255}):fp.write(block)
        GifImagePlugin._write_frame_data(fp,frames[0],(0,0),{'duration':20,'disposal':1,'transparency':255})
        # Display the SAME first pose while priming the dynamic disposal rectangle.
        # Split its existing hold, so no blank initialization or added pause appears.
        GifImagePlugin._write_frame_data(fp,frames[0].crop(roi),roi[:2],
            {'duration':durations[0]-20,'disposal':2,'transparency':255})
        for frame,duration in zip(frames[1:],durations[1:]):
            GifImagePlugin._write_frame_data(fp,frame.crop(roi),roi[:2],
                {'duration':duration,'disposal':2,'transparency':255})
        fp.write(b';')
    # Decode every frame and compare against the palette-normalized full frames.
    # This catches stale hands, lost static art and incorrect disposal semantics.
    with Image.open(output) as decoded:
        references=[frames[0]]+frames
        if decoded.n_frames!=len(references):raise ValueError('delta frame count mismatch')
        for i,expected in enumerate(references):
            decoded.seek(i)
            actual=decoded.convert('RGBA')
            reference=expected.copy();reference.info['transparency']=255
            want=reference.convert('RGBA')
            bg=Image.new('RGBA',actual.size,(93,117,149,255))
            if Image.alpha_composite(bg,actual).tobytes()!=Image.alpha_composite(bg,want).tobytes():
                raise ValueError(f'delta GIF roundtrip mismatch at frame {i+1}')
    return roi


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def natural_key(path):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", path.name)]


def inspect(path, args=None):
    durations, transparent_frames = [], 0
    with Image.open(path) as im:
        fmt, size = im.format, list(im.size)
        loop = im.info.get("loop")
        frames = getattr(im, "n_frames", 1)
        for i in range(frames):
            im.seek(i)
            im.load()
            durations.append(im.info.get("duration", 0))
            if im.convert("RGBA").getchannel("A").getextrema()[0] < 255:
                transparent_frames += 1
    errors = []
    total_bytes = path.stat().st_size
    if args:
        if args.animated and frames < 2:
            errors.append("expected at least two encoded frames")
        if args.loop and (frames < 2 or loop != 0):
            errors.append("expected infinite animation loop")
        if args.transparent and transparent_frames != frames:
            errors.append("expected transparent pixels in every frame")
        if args.size and size != [int(x) for x in args.size.split("x")]:
            errors.append("canvas size differs from requested size")
        if args.max_kb and total_bytes > args.max_kb * 1024:
            errors.append("file exceeds requested byte budget")
    return {
        "path": str(path.resolve()), "format": fmt, "size": size,
        "bytes": total_bytes, "frames": frames, "durations_ms": durations,
        "duration_ms": sum(durations), "loop": loop,
        "transparent_frames": transparent_frames, "errors": errors,
        "file_checks": "FAIL" if errors else "PASS",
        "visual_review": "not_performed", "platform_compliance": "not_evaluated",
    }


def assemble(args):
    colors=getattr(args,"colors",255)
    if not 2<=colors<=255:
        raise ValueError("palette colors must be between 2 and 255")
    files = sorted((p for p in args.frames.iterdir() if p.suffix.lower() == ".png"), key=natural_key)
    if len(files) < 2:
        raise ValueError("at least two single-frame PNG files are required")
    output = args.output
    if output.exists():
        raise ValueError("output already exists; choose a versioned filename")
    if output.suffix.lower() not in (".gif", ".webp"):
        raise ValueError("output must be .gif or .webp")
    durations = [positive(v.strip()) for v in args.durations.split(",")] if args.durations else [args.frame_ms] * len(files)
    if len(durations) != len(files):
        raise ValueError("duration count must equal PNG count")
    if output.suffix.lower() == ".gif" and any(d % 10 for d in durations):
        raise ValueError("GIF durations must be multiples of 10 ms")
    frames = []
    for file in files:
        with Image.open(file) as im:
            if getattr(im, "n_frames", 1) != 1:
                raise ValueError(f"input must be single-frame PNG: {file.name}")
            frames.append(im.convert("RGBA"))
    if any(im.size != frames[0].size for im in frames):
        raise ValueError("frame canvases must have identical size; align before encoding")
    if all(im.tobytes() == frames[0].tobytes() for im in frames[1:]):
        raise ValueError("all input frames are identical")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".gif":
        encoded = []
        # One shared palette reduces color flicker between adjacent poses.
        palette_sample = Image.new("RGB", (128 * len(frames), 128))
        for i, frame in enumerate(frames):
            palette_sample.paste(frame.convert("RGB").resize((128,128)), (128*i,0))
        shared_palette = palette_sample.quantize(colors=colors)
        for frame in frames:
            # Reserve index 255 for binary transparency; preserve opaque dark pixels.
            pal = frame.convert("RGB").quantize(palette=shared_palette,
                dither=Image.Dither.NONE if colors<255 else Image.Dither.FLOYDSTEINBERG)
            palette = pal.getpalette() or []
            pal.putpalette((palette + [0] * 768)[:765] + [0, 0, 0])
            mask = frame.getchannel("A").point(lambda a: 255 if a < 128 else 0)
            pal.paste(255, mask=mask)
            encoded.append(pal)
        if getattr(args,'delta',False):
            save_delta_gif(encoded,output,durations)
        else:
            encoded[0].save(output, save_all=True, append_images=encoded[1:],
                            duration=durations, loop=0, disposal=2,
                            transparency=255, optimize=False)
    else:
        # Some libwebp builds drop alpha when every RGB pixel is the same.
        # Change only fully invisible RGB values, preserving all visible pixels.
        prepared = []
        for frame in frames:
            normalized = frame.copy()
            extrema = frame.convert("RGB").getextrema()
            hidden_rgb = (255, 0, 255) if extrema == ((255, 255),) * 3 else (255, 255, 255)
            mask = frame.getchannel("A").point(lambda a: 255 if a == 0 else 0)
            normalized.paste((*hidden_rgb, 0), mask=mask)
            prepared.append(normalized)
        prepared[0].save(output, save_all=True, append_images=prepared[1:],
                         duration=durations, loop=0, lossless=True, exact=True)
    result = inspect(output)
    result["input_frames"] = len(files)
    # Encoders may merge identical adjacent frames without losing their hold time.
    if result["frames"] < 2:
        result["errors"].append("encoding collapsed animation to one frame")
        result["file_checks"] = "FAIL"
    if all(f.getchannel("A").getextrema()[0] == 0 for f in frames) and result["transparent_frames"] != result["frames"]:
        result["errors"].append("output lost expected transparent pixels")
        result["file_checks"] = "FAIL"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("assemble")
    build.add_argument("--frames", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--frame-ms", type=positive, default=120)
    build.add_argument("--durations")
    build.add_argument("--colors",type=positive,default=255,help="GIF palette colors, 2..255")
    build.add_argument("--delta",action="store_true",help="GIF changing-region encoding with per-frame decode verification")
    check = commands.add_parser("inspect")
    check.add_argument("path", type=Path)
    check.add_argument("--animated", action="store_true")
    check.add_argument("--loop", action="store_true")
    check.add_argument("--transparent", action="store_true")
    check.add_argument("--size", help="WIDTHxHEIGHT")
    check.add_argument("--max-kb", type=positive)
    args = parser.parse_args()
    try:
        if args.command == "inspect" and args.size and not re.fullmatch(r"[1-9]\d*x[1-9]\d*", args.size):
            raise ValueError("--size must be WIDTHxHEIGHT with positive integers")
        result = assemble(args) if args.command == "assemble" else inspect(args.path, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["errors"] else 0
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
