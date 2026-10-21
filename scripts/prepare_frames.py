"""Recover explicit grid cells, preserve shared geometry, and emit an auditable frame contract."""
import argparse
import hashlib
import json
import math
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remove_screen(image, rgb, tolerance=16):
    """Remove only screen-colored pixels connected to an outer border."""
    image = image.convert("RGBA")
    w, h = image.size
    pixels = image.load()
    matches = lambda x, y: max(abs(pixels[x, y][c] - rgb[c]) for c in range(3)) <= tolerance
    border = [(x, y) for x in range(w) for y in (0, h - 1)]
    border += [(x, y) for y in range(h) for x in (0, w - 1)]
    if sum(matches(x, y) for x, y in border) / len(border) < .98:
        raise ValueError("screen background is not uniform at the outer edge")
    seen = bytearray(w * h)
    queue = deque()
    for x, y in border:
        if matches(x, y) and not seen[y * w + x]:
            seen[y * w + x] = 1
            queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        for xx, yy in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if 0 <= xx < w and 0 <= yy < h and not seen[yy*w+xx] and matches(xx, yy):
                seen[yy*w+xx] = 1
                queue.append((xx, yy))
    return image


def prepare(sheet, cols, rows, size, out, screen=None, margin=.1):
    if min(cols, rows, size) <= 0 or not 0 <= margin < .4:
        raise ValueError("positive dimensions and margin in [0,0.4) required")
    if out.exists():
        raise ValueError("output path exists; choose a new version")
    with Image.open(sheet) as im:
        image = im.convert("RGBA")
    if cols>image.width or rows>image.height:
        raise ValueError("grid has more cells than source pixels")
    warnings=[]
    if image.width % cols or image.height % rows:
        warnings.append("fractional grid boundaries rounded; inspect contact sheet gutters")
    if screen is not None:
        image = remove_screen(image, screen)
    if image.getchannel("A").getextrema()[0] != 0:
        raise ValueError("real transparent background required; opaque/checkerboard source rejected")
    cw, ch = math.ceil(image.width / cols), math.ceil(image.height / rows)
    cells, boxes = [], []
    for row in range(rows):
        for col in range(cols):
            # Round shared boundaries once; pad at most one pixel without scaling cells.
            bounds=(round(col*image.width/cols),round(row*image.height/rows),
                    round((col+1)*image.width/cols),round((row+1)*image.height/rows))
            crop=image.crop(bounds)
            cell=Image.new("RGBA",(cw,ch))
            cell.alpha_composite(crop,(0,0))
            # Ignore nearly invisible alpha noise when measuring foreground geometry.
            # Preserve source alpha inside the shared crop; this is not character matting.
            box = cell.getchannel("A").point(lambda a:255 if a>=16 else 0).getbbox()
            if not box:
                raise ValueError(f"empty cell {row*cols+col+1}")
            if box[0] <= 0 or box[1] <= 0 or box[2] >= crop.width or box[3] >= crop.height:
                raise ValueError(f"cell {row*cols+col+1} touches boundary; inspect clipping/gutters")
            cells.append(cell)
            boxes.append(box)
    # One union crop and one scale: retain authored pose displacement.
    union = (min(b[0] for b in boxes), min(b[1] for b in boxes),
             max(b[2] for b in boxes), max(b[3] for b in boxes))
    uw, uh = union[2]-union[0], union[3]-union[1]
    scale = min(size*(1-2*margin)/uw, size*(1-2*margin)/uh)
    target = (max(1, round(uw*scale)), max(1, round(uh*scale)))
    offset = ((size-target[0])//2, (size-target[1])//2)
    normalized = []
    for cell in cells:
        pose = cell.crop(union).resize(target, Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", (size, size))
        frame.alpha_composite(pose, offset)
        normalized.append(frame)
    out.mkdir(parents=True)
    frame_dir = out / "frames"
    frame_dir.mkdir()
    records = []
    for i, frame in enumerate(normalized):
        path = frame_dir/f"{i+1:03}.png"
        frame.save(path)
        records.append({"path": str(path.relative_to(out)), "sha256": digest(path)})
    thumb = min(size, 192)
    for label, bg in (("light", (250,250,247,255)), ("dark", (36,37,40,255))):
        preview = Image.new("RGBA", (cols*thumb, rows*(thumb+22)), bg)
        draw = ImageDraw.Draw(preview)
        for i, frame in enumerate(normalized):
            x, y = i % cols * thumb, i // cols * (thumb+22)
            preview.alpha_composite(frame.resize((thumb,thumb),Image.Resampling.LANCZOS),(x,y))
            draw.text((x+6,y+thumb+3),str(i+1),fill="gray")
        preview.convert("RGB").save(out/f"contact-{label}.jpg",quality=93)
    result = {"schema_version": 2, "source_sha256": digest(sheet),
              "grid": [cols, rows], "canvas": [size,size], "count": len(cells),
              "shared_crop": union, "shared_scale": scale, "frames": records,
              "unique_frames": len({f.tobytes() for f in normalized}),
              "geometry_alpha_threshold":16,"warnings":warnings,"visual_review": "pending", "interpolation": "none"}
    (out/"frames.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sheet",type=Path,required=True)
    p.add_argument("--cols",type=int,required=True)
    p.add_argument("--rows",type=int,required=True)
    p.add_argument("--size",type=int,default=512)
    p.add_argument("--margin",type=float,default=.1)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--screen",help="optional explicit RRGGBB screen; never auto-guessed")
    a=p.parse_args()
    try:
        if a.screen and (len(a.screen)!=6 or any(c not in "0123456789abcdefABCDEF" for c in a.screen)):
            raise ValueError("screen must be six hex digits")
        rgb=tuple(int(a.screen[i:i+2],16) for i in (0,2,4)) if a.screen else None
        print(json.dumps(prepare(a.sheet,a.cols,a.rows,a.size,a.out,rgb,a.margin),indent=2))
    except (ValueError,OSError) as exc:
        p.exit(2,f"{exc}\n")


if __name__=="__main__":
    main()
