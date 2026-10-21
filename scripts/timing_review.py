"""Validate an explicitly reviewed eye-state timeline, not infer facial quality from pixels."""
import argparse
import json
from pathlib import Path

STATES={'open','half','closed','occluded','not_applicable'}

def validate(timeline, *, loop=True, rationale=''):
    errors=[];warnings=[]
    if len(timeline)<2:return {'complete':False,'errors':['at least two timeline entries required'],'warnings':[]}
    for n,t in enumerate(timeline,1):
        if t.get('eye_state') not in STATES:errors.append(f'frame {n}: unknown eye state')
        duration=t.get('duration_ms')
        if isinstance(duration,bool) or not isinstance(duration,int) or duration<=0:errors.append(f'frame {n}: duration must be a positive integer')
    pairs=list(zip(timeline,timeline[1:]))
    if loop:pairs.append((timeline[-1],timeline[0]))
    for a,b in pairs:
        if {a.get('eye_state'),b.get('eye_state')}=={'open','closed'}:
            errors.append(f"abrupt eye transition {a.get('frame','?')} -> {b.get('frame','?')}: missing half-lid drawing")
    if len({t.get('duration_ms') for t in timeline})==1 and not rationale.strip():
        warnings.append('uniform timing needs an action-specific rationale; a continuous run may legitimately use equal intervals')
    return {'complete':not errors,'errors':errors,'warnings':warnings,
            'duration_ms':sum(t.get('duration_ms',0) for t in timeline if isinstance(t.get('duration_ms'),int)),
            'scope':'declared timeline only; facial drawings and playback require visual review'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('plan',type=Path);args=parser.parse_args()
    data=json.loads(args.plan.read_text(encoding='utf-8'))
    result=validate(data['timeline'],loop=data.get('loop',True),rationale=data.get('rationale',''))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['complete'] else 1)
