"""Controlled input generation only; never a numerical analysis backend."""
import copy
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]


def make(kind):
    base=json.loads((ROOT/"tests/fixtures/structure/separated.json").read_text())
    base["context"]["dataset_id"]="controlled_dependence_"+kind
    base["provenance"]={"purpose":"Frozen alpha.6 A-H scientific controls; synthetic only"}
    base["observations"]=[]
    rng=random.Random(103)
    for i in range(96):
        g=(i//2)%3
        trait=(i//6)%8-3.5+(.25 if i%2 else -.25)
        offsets=[-8.,0.,8.]
        noise=[rng.gauss(0,1) for _ in range(3)]
        y={"group_only":offsets[g],"trait_only":2*trait,"mixed":offsets[g]+2*trait,
           "independent_y":rng.gauss(0,1),"unseen":offsets[g]+2*trait,
           "high_cardinality":offsets[g]+2*trait,"repeats":offsets[g]+2*trait}[kind]
        factor=str(i//2) if kind=="unseen" else (str(i) if kind=="high_cardinality" else str(g))
        row={"observation_id":f"o{i:03}","sample_id":f"p{i:03}","physical_sample_id":f"p{i:03}",
             "independence_group":f"block:{i//2:03}","partition":"train",
             "x":[float(g),float(g==1),trait,*noise],"y":y,"reference_id":f"ref:{i:03}",
             "reference_status":"exact","reference_unit":"test_units","repetition_type":"rescan",
             "metadata":{"instrument":"instrument:0","campaign":"synthetic","factor":factor}}
        base["observations"].append(row)
        if kind=="repeats":
            duplicate=copy.deepcopy(row);duplicate["observation_id"]+="_repeat";base["observations"].append(duplicate)
    held=copy.deepcopy(base["observations"][-1]);held.update(observation_id="held",sample_id="held",physical_sample_id="held",independence_group="held",partition="test",reference_id="held",y=None)
    base["observations"].append(held)
    return base


if __name__=="__main__":
    out=ROOT/"tests/fixtures/dependence";out.mkdir(exist_ok=True)
    for kind in ("group_only","trait_only","mixed","independent_y","unseen","high_cardinality","repeats"):
        (out/(kind+".json")).write_text(json.dumps(make(kind),indent=2,allow_nan=False)+"\n",encoding="utf-8")
