"""Split two generated cutout layers only at a measured transparent vertical gutter."""
import argparse,json
from pathlib import Path
from PIL import Image


def split_layers(image, threshold=32, min_gap=8):
    im=image.convert('RGBA');w,h=im.size
    if im.getchannel('A').getextrema()[0]!=0:raise ValueError('real alpha required')
    alpha=im.getchannel('A').point(lambda a:255 if a>=threshold else 0)
    runs=[];start=None
    for x in range(round(w*.20),round(w*.85)):
        empty=alpha.crop((x,0,x+1,h)).getbbox() is None
        if empty and start is None:start=x
        if not empty and start is not None:runs.append((start,x));start=None
    if start is not None:runs.append((start,round(w*.85)))
    if not runs:raise ValueError('no transparent gutter')
    gap=max(runs,key=lambda r:r[1]-r[0])
    if gap[1]-gap[0]<min_gap:raise ValueError('insufficient transparent gutter')
    split=round(sum(gap)/2);layers=[];bounds=[]
    for i in range(2):
        cell=im.crop((0 if i==0 else split,0,split if i==0 else w,h))
        b=cell.getchannel('A').point(lambda a:255 if a>=threshold else 0).getbbox()
        if not b:raise ValueError('empty layer')
        if b[0]==0 or b[2]==cell.width or b[1]==0 or b[3]==h:
            raise ValueError('layer touches source/cut boundary')
        layers.append(cell.crop(b));bounds.append(b)
    return layers,{'split_x':split,'transparent_gutter':gap,'canvas':im.size,
                   'alpha_threshold':threshold,'local_bounds':bounds,'visual_review':'pending'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sheet',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('choose a new output version')
        layers,report=split_layers(Image.open(a.sheet))
        a.out.mkdir(parents=True)
        for name,im in zip(('body.png','part.png'),layers):im.save(a.out/name)
        (a.out/'split.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
