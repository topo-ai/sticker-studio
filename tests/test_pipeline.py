"""Offline behavior regression tests. All review approvals here are synthetic fixtures."""
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPTS=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
import studio
from prepare_frames import prepare, remove_screen
from sticker_media import assemble, inspect


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="sticker-v2-test-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def sheet(self, blank=False, boundary=False, opaque=False):
        im=Image.new("RGBA",(128,64),(255,255,255,255) if opaque else (0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rectangle((0 if boundary else 12,16,30,44),fill=(20,20,20,255))
        if not blank:d.rectangle((84,16,108,44),fill=(20,20,20,255))
        p=self.root/"sheet.png";im.save(p);return p

    def frames(self):
        root=self.root/"frames";root.mkdir()
        for i,x in enumerate((8,18,28,8)):
            im=Image.new("RGBA",(64,64),(0,0,0,0))
            ImageDraw.Draw(im).rectangle((x,20,x+12,40),fill=(0,0,0,255))
            im.save(root/f"{i:03}.png")
        return root

    def encode(self, folder, output):
        return assemble(argparse.Namespace(frames=folder,output=output,frame_ms=120,durations="100,120,200,100"))

    def project(self, mode="animated"):
        project=self.root/"project"
        studio.init(argparse.Namespace(project=project,name="fixture",theme="test",mode=mode,count=1,style="chibi-ink"))
        profile=studio.read(project/"profile-generic.json");profile["size"]=[64,64]
        studio.write(project/"profile-generic.json",profile)
        return project

    def ready(self, mode="animated"):
        project=self.project(mode)
        folder=self.frames()
        pack=studio.read(project/"pack.json")
        formats=["gif","webp"] if mode=="animated" else ["png"]
        for fmt in formats:
            target=project/f"exports/01.{fmt}";target.parent.mkdir(parents=True,exist_ok=True)
            if fmt=="png":Image.open(folder/"000.png").save(target)
            else:self.encode(folder,target)
            pack["items"][0]["files"][fmt]=target.relative_to(project).as_posix()
        studio.write(project/"pack.json",pack)
        return project

    def approve_fixture(self, project):
        pack=studio.read(project/"pack.json")
        evidence=project/"previews/fixture.txt";evidence.parent.mkdir();evidence.write_text("SYNTHETIC FIXTURE",encoding="utf-8")
        entry={"file_hashes":{p:studio.sha(project/p) for p in pack["items"][0]["files"].values()},
               "checks":{k:"pass" for k in studio.CHECKS},"method":"synthetic test fixture, not visual QA",
               "evidence":"previews/fixture.txt"}
        studio.write(project/"visual-review.json",{"schema_version":2,"items":{"01":entry}})

    def test_prepare_shared_scale_retains_displacement(self):
        result=prepare(self.sheet(),2,1,64,self.root/"prepared")
        self.assertEqual(result["count"],2)
        first=Image.open(self.root/"prepared/frames/001.png").getchannel("A").getbbox()
        second=Image.open(self.root/"prepared/frames/002.png").getchannel("A").getbbox()
        self.assertGreater(second[0],first[0])
        self.assertTrue((self.root/"prepared/contact-dark.jpg").is_file())

    def test_prepare_rejects_empty_cell(self):
        with self.assertRaisesRegex(ValueError,"empty cell"):prepare(self.sheet(blank=True),2,1,64,self.root/"out")

    def test_nearly_invisible_alpha_noise_does_not_define_geometry(self):
        path=self.sheet()
        im=Image.open(path).convert('RGBA');im.putpixel((0,0),(255,0,0,3));im.save(path)
        result=prepare(path,2,1,64,self.root/'out')
        self.assertEqual(result['geometry_alpha_threshold'],16)
        self.assertEqual(result['count'],2)

    def test_compact_palette_retains_animation_and_black(self):
        frames=self.frames();output=self.root/'compact.gif'
        result=assemble(argparse.Namespace(frames=frames,output=output,frame_ms=120,durations='100,120,200,100',colors=32))
        self.assertEqual(result['frames'],4)
        self.assertEqual(result['duration_ms'],520)
        with Image.open(output) as im:self.assertEqual(im.convert('RGBA').getpixel((10,25)),(0,0,0,255))

    def test_prepare_rejects_boundary_contact(self):
        with self.assertRaisesRegex(ValueError,"boundary"):prepare(self.sheet(boundary=True),2,1,64,self.root/"out")

    def test_prepare_rejects_false_alpha(self):
        with self.assertRaisesRegex(ValueError,"transparent"):prepare(self.sheet(opaque=True),2,1,64,self.root/"out")

    def test_prepare_rejects_bad_grid(self):
        with self.assertRaises(ValueError):prepare(self.sheet(),3,1,64,self.root/"out")

    def test_fractional_grid_rounding_preserves_all_cells(self):
        im=Image.new("RGBA",(129,65));d=ImageDraw.Draw(im)
        d.rectangle((12,16,30,44),fill="red");d.rectangle((84,16,108,44),fill="red")
        path=self.root/"odd.png";im.save(path)
        result=prepare(path,2,1,64,self.root/"out")
        self.assertEqual(result["count"],2)
        self.assertTrue(result["warnings"])

    def test_screen_preserves_enclosed_matching_pixels(self):
        image=Image.new("RGB",(64,64),(0,255,0));d=ImageDraw.Draw(image)
        d.rectangle((12,12,52,52),fill=(200,0,0));d.rectangle((24,24,40,40),fill=(0,255,0))
        out=remove_screen(image,(0,255,0))
        self.assertEqual(out.getpixel((0,0))[3],0)
        self.assertEqual(out.getpixel((30,30))[3],255)

    def test_screen_rejects_checkerboard(self):
        image=Image.new("RGB",(64,64),(220,220,220));d=ImageDraw.Draw(image)
        for y in range(0,64,8):
            for x in range(0,64,8):
                if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(180,180,180))
        with self.assertRaisesRegex(ValueError,"uniform"):remove_screen(image,(220,220,220))

    def test_gif_and_webp_timing_and_transparency(self):
        frames=self.frames()
        for fmt in ("gif","webp"):
            target=self.root/f"test.{fmt}";result=self.encode(frames,target)
            self.assertEqual(result["frames"],4)
            self.assertEqual(result["duration_ms"],520)
            self.assertEqual(result["loop"],0)
            self.assertEqual(result["transparent_frames"],4)
            with Image.open(target) as im:
                self.assertEqual(im.convert("RGBA").getpixel((10,25)),(0,0,0,255))

    def test_static_cannot_satisfy_animation(self):
        project=self.ready()
        im=Image.new("RGBA",(64,64));ImageDraw.Draw(im).ellipse((10,10,50,50),fill="red")
        im.save(project/"exports/01.gif")
        result=studio.verify(project)
        self.assertFalse(result["complete"])
        self.assertTrue(any("animation" in e for e in result["errors"]))

    def test_invisible_animation_rejected(self):
        project=self.ready();Image.new("RGBA",(64,64)).save(project/"exports/01.gif")
        self.assertTrue(any("empty foreground" in e for e in studio.verify(project)["errors"]))

    def test_missing_file_rejected(self):
        project=self.ready();(project/"exports/01.webp").unlink()
        self.assertFalse(studio.verify(project)["complete"])

    def test_format_and_size_rejected(self):
        project=self.ready();Image.new("RGBA",(32,32),"red").save(project/"exports/01.gif",format="PNG")
        errors=studio.verify(project)["errors"]
        self.assertTrue(any("format mismatch" in e for e in errors))
        self.assertTrue(any("wrong canvas" in e for e in errors))

    def test_path_escape_rejected(self):
        project=self.project();pack=studio.read(project/"pack.json")
        pack["items"][0]["files"]={"gif":"../outside.gif"};studio.write(project/"pack.json",pack)
        with self.assertRaisesRegex(ValueError,"escapes"):studio.verify(project)

    def test_duplicate_artifact_rejected(self):
        project=self.ready();pack=studio.read(project/"pack.json")
        pack["items"][0]["files"]["webp"]=pack["items"][0]["files"]["gif"];studio.write(project/"pack.json",pack)
        self.assertTrue(any("duplicate" in e for e in studio.verify(project)["errors"]))

    def test_archive_requires_actual_review(self):
        project=self.ready()
        with self.assertRaisesRegex(ValueError,"review"):studio.package(project,self.root/"no.zip")
        self.assertFalse((self.root/"no.zip").exists())

    def test_stale_review_rejected(self):
        project=self.ready();self.approve_fixture(project)
        path=project/"exports/01.gif";path.write_bytes(path.read_bytes()+b"trailing metadata")
        with self.assertRaisesRegex(ValueError,"stale"):studio.package(project,self.root/"no.zip")

    def test_valid_archive_has_relative_allowlist(self):
        project=self.ready();self.approve_fixture(project)
        (project/"secret.env").write_text("not included",encoding="utf-8")
        output=self.root/"delivery.zip";studio.package(project,output)
        with zipfile.ZipFile(output) as z:
            self.assertIn("exports/01.gif",z.namelist())
            self.assertIn("delivery-manifest.json",z.namelist())
            self.assertNotIn("secret.env",z.namelist())
            self.assertTrue(all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in z.namelist()))
        with self.assertRaisesRegex(ValueError,"exists"):studio.package(project,output)

    def test_static_project_valid(self):
        project=self.ready("static");self.approve_fixture(project)
        self.assertTrue(studio.verify(project,True)["complete"])

    def test_prompt_compile_requires_complete_plan(self):
        project=self.project()
        with self.assertRaisesRegex(ValueError,"master"):studio.compile_prompts(project)
        master=self.root/"master.png";Image.new("RGBA",(64,64),"red").save(master)
        studio.write(project/"character.json",{"master_path":str(master),"invariants":["round glasses"]})
        pack=studio.read(project/"pack.json");item=pack["items"][0]
        item.update(intent="acknowledge",action="salute",frame_beats=[str(i) for i in range(8)],durations_ms=[120]*8)
        studio.write(project/"pack.json",pack)
        result=studio.compile_prompts(project)
        self.assertEqual(result["prompts"],1)
        content=(Path(result["directory"])/"01.md").read_text(encoding="utf-8")
        self.assertIn("round glasses",content)
        second=studio.compile_prompts(project)
        self.assertNotEqual(result["directory"],second["directory"])

    def test_count_mismatch_rejected(self):
        project=self.project();config=studio.read(project/"project.json");config["count"]=2
        studio.write(project/"project.json",config)
        with self.assertRaisesRegex(ValueError,"count"):studio.verify(project)

    def test_video_extraction_offline(self):
        if not studio.shutil.which("ffmpeg"):self.skipTest("FFmpeg unavailable")
        video=self.root/"fixture.mp4"
        subprocess.run(["ffmpeg","-v","error","-nostdin","-f","lavfi","-i","testsrc=size=64x64:rate=10",
                        "-t","1","-pix_fmt","yuv420p",str(video)],check=True,capture_output=True)
        result=subprocess.run([sys.executable,str(SCRIPTS/"extract_video.py"),"--video",str(video),
                               "--duration","0.5","--fps","10","--out",str(self.root/"video-frames")],
                              capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(list((self.root/"video-frames").glob("*.png"))),5)


if __name__=="__main__":unittest.main()
