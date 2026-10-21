import argparse,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sticker_media import assemble


class DeltaGifTests(unittest.TestCase):
    def test_decode_preserves_static_body_and_clears_old_hand(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);frames=root/'frames';frames.mkdir()
            for i,x in enumerate((15,20,25,20)):
                im=Image.new('RGBA',(100,100));d=ImageDraw.Draw(im)
                d.rectangle((50,20,80,80),fill='blue')
                d.rectangle((x,15,x+8,30),fill='red');im.save(frames/f'{i}.png')
            r=assemble(argparse.Namespace(frames=frames,output=root/'test.gif',frame_ms=50,durations=None,colors=32,delta=True))
            self.assertEqual(r['frames'],5);self.assertEqual(r['duration_ms'],200)
            with Image.open(root/'test.gif') as im:
                im.seek(3);rgba=im.convert('RGBA')
                self.assertEqual(rgba.getpixel((15,20))[3],0)
                self.assertGreaterEqual(rgba.getpixel((60,40))[2],245)
                self.assertEqual(rgba.getpixel((60,40))[3],255)
                self.assertGreaterEqual(rgba.getpixel((28,20))[0],245)


if __name__=='__main__':unittest.main()
