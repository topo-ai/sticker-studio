"""Recover transparent grid cuts while preserving nominal cell coordinates and one scale."""
import argparse,json,math
from pathlib import Path
from PIL import Image


def recover(image, cols, rows, search=.12, allow_bottom_viewport=False):
    im=image.convert('RGBA');w,h=im.size
    alpha=im.getchannel('A').point(lambda a:255 if a>=16 else 0)
    box=alpha.getbbox()
    if not box or im.getchannel('A').getextrema()[0]!=0:raise ValueError('nonempty real alpha required')
    if box[0]==0 or box[1]==0 or box[2]==w or (box[3]==h and not allow_bottom_viewport):
        raise ValueError('foreground touches source outer edge; inspect/regenerate clipped content')
    cuts=[]
    for axis,count,extent in [('x',cols,w),('y',rows,h)]:
        empty=[]
        for n in range(extent):
            strip=alpha.crop((n,0,n+1,h) if axis=='x' else (0,n,w,n+1))
            empty.append(strip.getbbox() is None)
        line=[0]
        for k in range(1,count):
            nominal=round(k*extent/count);radius=math.ceil(extent/count*search)
            choices=[n for n in range(max(1,nominal-radius),min(extent-1,nominal+radius)+1)
                     if empty[n-1] and empty[n] and empty[min(n+1,extent-1)]]
            if not choices:raise ValueError(f'no safe transparent {axis} gutter near cut {k}')
            line.append(min(choices,key=lambda n:abs(n-nominal)))
        line.append(extent)
        if sorted(set(line))!=line:raise ValueError('ambiguous/reversed cuts')
        cuts.append(line)
    xs,ys=cuts;pad=math.ceil(max(w/cols,h/rows)*search)+4
    cw,ch=math.ceil(w/cols)+2*pad,math.ceil(h/rows)+2*pad
    sheet=Image.new('RGBA',(cw*cols,ch*rows))
    records=[]
    for row in range(rows):
        for col in range(cols):
            bounds=(xs[col],ys[row],xs[col+1],ys[row+1])
            # Preserve frame coordinates relative to nominal grid origin, NOT its bbox.
            dx=pad+xs[col]-round(col*w/cols);dy=pad+ys[row]-round(row*h/rows)
            cell=Image.new('RGBA',(cw,ch));cell.alpha_composite(im.crop(bounds),(dx,dy))
            sheet.alpha_composite(cell,(col*cw,row*ch))
            records.append({'crop':bounds,'paste':[dx,dy]})
    report={'method':'measured transparent cuts, nominal origins retained','source_size':[w,h],
            'x_cuts':xs,'y_cuts':ys,'cell_size':[cw,ch],'padding':pad,'cells':records,
            'allow_bottom_viewport':allow_bottom_viewport,'visual_review':'pending','scaling':'none'}
    return sheet,report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sheet',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--cols',type=int,required=True);p.add_argument('--rows',type=int,required=True)
    p.add_argument('--allow-bottom-viewport',action='store_true');a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('choose a new output version')
        sheet,report=recover(Image.open(a.sheet),a.cols,a.rows,allow_bottom_viewport=a.allow_bottom_viewport)
        sheet.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
