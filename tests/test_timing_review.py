import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from timing_review import validate

def entries(states):return [{'frame':n,'eye_state':s,'duration_ms':80} for n,s in enumerate(states,1)]

class TimingReviewTests(unittest.TestCase):
    def test_direct_open_closed_is_rejected(self):
        self.assertFalse(validate(entries(['open','closed','open']))['complete'])
    def test_both_halves_and_loop_rest_pass(self):
        self.assertTrue(validate(entries(['open','half','closed','half','open']))['complete'])
    def test_loop_boundary_is_checked(self):
        self.assertFalse(validate(entries(['open','half','closed']))['complete'])
    def test_uniform_run_is_not_automatically_slowed(self):
        r=validate(entries(['open']*16),rationale='continuous run cycle at 60ms')
        self.assertTrue(r['complete']);self.assertFalse(r['warnings'])
    def test_invalid_durations_are_rejected(self):
        t=entries(['open','half']);t[1]['duration_ms']=0
        self.assertFalse(validate(t)['complete'])

if __name__=='__main__':unittest.main()
