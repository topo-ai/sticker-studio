"""Render an authored local cutout joint; static art is reused without regeneration."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def pose(t, low, high, cycles=1):
    return low+(high-low)*(.5-.5*math.cos(2*math.pi*cycles*t))


def render(config, out):
    if out.exists(): raise ValueError('choose a new output version')
    canvas=config.get('canvas',512)
    count=config.get('frames',40)
    if count<4:raise ValueError('at least four frames required')
    base=Image.open(config['base']).convert('RGBA')
    part=Image.open(config['part']).convert('RGBA')
    if base.size!=(canvas,canvas):raise ValueError('base must be registered to canvas')
    target=config['joint'];pivot=config['pivot'];low,high=config['angles']
    scale=config.get('scale',1)
    if scale<=0:raise ValueError('positive part scale required')
    caption=Image.new('RGBA',base.size)
    text=config.get('caption','')
    if text:
        font=ImageFont.truetype(config['font'],config.get('font_size',58))
        ImageDraw.Draw(caption).text((canvas/2,config.get('caption_y',418)),text,
            font=font,anchor='mt',fill=config.get('text_color','#291d24'),
            stroke_width=config.get('stroke',6),stroke_fill='white')
    frames=[];records=[]
    for i in range(count):
        # Sample a periodic curve without duplicating endpoint/hold frame.
        t=i/count;angle=pose(t,low,high,config.get('cycles',1))
        r=math.radians(angle);c=math.cos(r)/scale;s=math.sin(r)/scale
        # Inverse affine maps canvas coordinates to source part coordinates.
        coeff=(c,-s,pivot[0]-c*target[0]+s*target[1],
               s,c,pivot[1]-s*target[0]-c*target[1])
        layer=part.transform(base.size,Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC)
        b=layer.getchannel('A').point(lambda a:255 if a>=16 else 0).getbbox()
        if not b or b[0]<=0 or b[1]<=0 or b[2]>=canvas or b[3]>=canvas:
            raise ValueError('moving part touches canvas boundary')
        frame=base.copy();frame.alpha_composite(layer);frame.alpha_composite(caption)
        frames.append(frame);records.append({'frame':i+1,'angle_degrees':angle,'joint':target})
    protected=[]
    for roi in config.get('protected_rois',[]):
        hashes={hashlib.sha256(f.crop(tuple(roi)).tobytes()).hexdigest() for f in frames}
        protected.append({'roi':roi,'unique_pixel_hashes':len(hashes)})
        if len(hashes)!=1:raise ValueError('moving part occludes protected stationary ROI')
    out.mkdir(parents=True)
    for i,f in enumerate(frames):f.save(out/f'{i+1:03}.png')
    caption.save(out.parent/(out.name+'-caption.png'))
    report={'method':'local rigid cutout joint, analytic periodic easing',
            'frames':records,'frame_ms':config.get('frame_ms',50),
            'protected_regions':protected,'static_source_sha256':hashlib.sha256(base.tobytes()).hexdigest(),
            'caption_sha256':hashlib.sha256(caption.tobytes()).hexdigest(),
            'visual_review':'pending','generative_interpolation':False,
            'unique_frames':len({f.tobytes() for f in frames})}
    (out.parent/(out.name+'-render.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:print(json.dumps(render(json.loads(a.config.read_text(encoding='utf-8')),a.out),indent=2))
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
