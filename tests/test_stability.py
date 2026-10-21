import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from stabilize_frames import stabilize


class StabilityTests(unittest.TestCase):
    def test_remove_translation_preserve_local_motion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source';src.mkdir()
            for i,(dx,dy) in enumerate(((0,0),(7,3),(-4,2))):
                im=Image.new('RGBA',(100,100));d=ImageDraw.Draw(im)
                d.rectangle((30+dx,20+dy,50+dx,60+dy),fill='black')
                d.rectangle((65+dx,60+dy-i*5,70+dx,65+dy-i*5),fill='red')
                im.save(src/f'{i}.png')
            report=stabilize(src,root/'out',(15,10,60,45))
            self.assertEqual([r['translation'] for r in report['frames']],[(0,0),(-7,-3),(4,-2)])
            for i in range(3):
                with Image.open(root/'out'/f'{i}.png') as im:
                    self.assertEqual(im.getpixel((65,60-i*5)),(255,0,0,255))

    def test_ambiguous_anchor_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source';src.mkdir()
            for i in range(2):Image.new('RGBA',(40,40),'black').save(src/f'{i}.png')
            with self.assertRaises(ValueError):stabilize(src,root/'out',(5,5,30,30))
            self.assertFalse((root/'out').exists())

    def test_changed_scale_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source';src.mkdir()
            for i,width in enumerate((10,20)):
                im=Image.new('RGBA',(100,100));ImageDraw.Draw(im).rectangle((30,20,30+width,60),fill='black');im.save(src/f'{i}.png')
            with self.assertRaises(ValueError):stabilize(src,root/'out',(10,10,80,50))

if __name__=='__main__':unittest.main()
