"""Translation-only stabilization using an explicitly approved stationary silhouette ROI."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def stabilize(source, out, roi, max_shift=48, extent_tolerance=.08, cap_depth=None):
    if out.exists():
        raise ValueError('choose a new output version')
    paths=sorted(source.glob('*.png'))
    if len(paths)<2:
        raise ValueError('at least two PNG frames required')
    frames=[Image.open(p).convert('RGBA') for p in paths]
    size=frames[0].size
    x0,y0,x1,y1=roi
    if not (0<=x0<x1<=size[0] and 0<=y0<y1<=size[1]):
        raise ValueError('ROI outside canvas')
    anchors=[]
    for im in frames:
        if im.size!=size:
            raise ValueError('canvas mismatch')
        b=im.crop(roi).getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        if not b or b[0]==0 or b[1]==0 or b[2]==x1-x0:
            raise ValueError('anchor empty or clipped by ROI; choose an isolated stationary feature')
        # An upper silhouette cap may continue below ROI (e.g. head into neck).
        # Only horizontal extent and top edge are used, never its clipped bottom.
        top=y0+b[1]
        if cap_depth is not None:
            if cap_depth<=0 or top+cap_depth>size[1]:raise ValueError('invalid relative cap depth')
            cap=im.crop((x0,top,x1,top+cap_depth)).getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            if not cap or cap[0]==0 or cap[2]==x1-x0:raise ValueError('relative cap clipped/empty')
            anchors.append((x0+(cap[0]+cap[2])/2,top,cap[2]-cap[0],1))
        else:
            anchors.append((x0+(b[0]+b[2])/2,top,b[2]-b[0],1))
    ref=anchors[0]
    shifts=[]
    for a in anchors:
        if any(abs(a[k]/ref[k]-1)>extent_tolerance for k in (2,3)):
            raise ValueError('anchor shape/scale changed; regenerate instead of stretching')
        shift=(round(ref[0]-a[0]),round(ref[1]-a[1]))
        if max(map(abs,shift))>max_shift:
            raise ValueError('translation exceeds approved limit')
        shifts.append(shift)
    results=[]
    for im,(dx,dy) in zip(frames,shifts):
        b=im.getchannel('A').point(lambda a:255 if a>=16 else 0).getbbox()
        if not b or b[0]+dx<0 or b[1]+dy<0 or b[2]+dx>size[0] or b[3]+dy>size[1]:
            raise ValueError('translation would clip foreground')
        target=Image.new('RGBA',size)
        target.alpha_composite(im,(dx,dy))
        results.append(target)
    out.mkdir(parents=True)
    records=[]
    for p,im,s,a in zip(paths,results,shifts,anchors):
        dest=out/p.name;im.save(dest)
        records.append({'file':p.name,'translation':s,'anchor_before':a[:2],
                        'anchor_after':[a[0]+s[0],a[1]+s[1]],
                        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    report={'method':'explicit stationary silhouette ROI, translation only',
            'roi':roi,'reference':paths[0].name,'extent_tolerance':extent_tolerance,'relative_cap_depth':cap_depth,
            'frames':records,'visual_review':'pending','interpolation':'none'}
    (out.parent/(out.name+'-stability.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frames',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--roi',type=int,nargs=4,required=True)
    p.add_argument('--max-shift',type=int,default=48)
    p.add_argument('--cap-depth',type=int,help='measure fixed depth below each detected top, avoiding vertical slice bias')
    a=p.parse_args()
    try: print(json.dumps(stabilize(a.frames,a.out,a.roi,a.max_shift,cap_depth=a.cap_depth),indent=2))
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
