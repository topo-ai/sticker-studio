import sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recover_grid import recover
from stabilize_frames import stabilize


class GridRecoveryTests(unittest.TestCase):
    def test_adjust_cut_without_recentering_the_pose(self):
        im=Image.new('RGBA',(128,128));d=ImageDraw.Draw(im)
        for x in (10,85):
            d.rectangle((x,10,x+20,65),fill='red')
            d.rectangle((x,76,x+20,115),fill='blue')
        fixed,r=recover(im,2,2)
        pad=r['padding'];cw,ch=r['cell_size']
        self.assertGreater(r['y_cuts'][1],64)
        self.assertEqual(fixed.getpixel((10+pad,65+pad)),(255,0,0,255))
        self.assertEqual(fixed.getpixel((10+pad,ch+76-64+pad)),(0,0,255,255))
        self.assertEqual(r['scaling'],'none')

    def test_overlapping_cells_are_rejected(self):
        im=Image.new('RGBA',(128,128));ImageDraw.Draw(im).rectangle((10,10,115,115),fill='red')
        with self.assertRaises(ValueError):recover(im,2,2)

    def test_true_outer_clip_is_not_hidden_by_padding(self):
        im=Image.new('RGBA',(128,128));ImageDraw.Draw(im).rectangle((10,10,30,127),fill='red')
        with self.assertRaises(ValueError):recover(im,2,2)

    def test_relative_cap_avoids_vertical_slice_scale_false_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'frames';src.mkdir()
            for i,dy in enumerate((0,20)):
                im=Image.new('RGBA',(128,128));ImageDraw.Draw(im).ellipse((20,20+dy,100,100+dy),fill='black');im.save(src/f'{i}.png')
            with self.assertRaises(ValueError):stabilize(src,root/'fixed-window',(5,5,120,60))
            r=stabilize(src,root/'relative',(5,5,120,60),cap_depth=30)
            self.assertEqual(r['frames'][1]['translation'],(0,-20))


if __name__=='__main__':unittest.main()
