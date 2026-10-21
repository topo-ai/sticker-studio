import json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from render_cutout import render,pose
from prepare_cutout import split_layers


class CutoutTests(unittest.TestCase):
    def test_unequal_panels_use_actual_gutter(self):
        im=Image.new('RGBA',(240,100));d=ImageDraw.Draw(im)
        d.rectangle((10,10,145,90),fill='blue');d.rectangle((180,20,220,80),fill='red')
        layers,r=split_layers(im)
        self.assertGreater(r['split_x'],145)
        self.assertEqual(layers[0].size,(136,81))
        self.assertEqual(layers[1].size,(41,61))

    def test_connected_parts_reject_false_split(self):
        im=Image.new('RGBA',(240,100));ImageDraw.Draw(im).rectangle((10,10,230,90),fill='blue')
        with self.assertRaises(ValueError):split_layers(im)

    def config(self,root):
        base=Image.new('RGBA',(100,100));ImageDraw.Draw(base).rectangle((60,10,90,60),fill='blue');base.save(root/'base.png')
        part=Image.new('RGBA',(20,40));ImageDraw.Draw(part).rectangle((4,4,16,36),fill='red');part.save(root/'part.png')
        return {'canvas':100,'base':str(root/'base.png'),'part':str(root/'part.png'),
                'joint':[40,60],'pivot':[10,35],'angles':[-10,10],'frames':20,
                'protected_rois':[[65,15,85,55]]}

    def test_local_motion_preserves_static_pixels_and_joint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.config(root);r=render(c,root/'frames')
            self.assertEqual(r['protected_regions'][0]['unique_pixel_hashes'],1)
            self.assertGreater(r['unique_frames'],4)
            self.assertEqual(len({tuple(x['joint']) for x in r['frames']}),1)
            self.assertFalse(r['generative_interpolation'])

    def test_invalid_clipping_produces_no_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.config(root);c['joint']=[1,1]
            with self.assertRaises(ValueError):render(c,root/'frames')
            self.assertFalse((root/'frames').exists())

    def test_occlusion_of_protected_region_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c=self.config(root);c['protected_rois']=[[20,20,60,70]]
            with self.assertRaises(ValueError):render(c,root/'frames')

    def test_periodic_position_and_velocity(self):
        self.assertAlmostEqual(pose(0,-8,12),pose(1,-8,12))
        dt=1e-5
        self.assertLess(abs((pose(dt,-8,12)-pose(0,-8,12))/dt),.01)
        self.assertLess(abs((pose(1,-8,12)-pose(1-dt,-8,12))/dt),.01)


if __name__=='__main__':unittest.main()
