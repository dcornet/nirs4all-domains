"""Additional alpha.7 inputs only; old fixtures are never rewritten."""
import copy
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]


def generate(kind):
    template="trait_only" if kind in ("size_only","extrapolation") else "mixed"
    data=json.loads((ROOT/"tests/fixtures/dependence"/(template+".json")).read_text())
    data=copy.deepcopy(data);data["context"]["dataset_id"]="controlled_split_stress_"+kind
    data["provenance"]={"purpose":"Frozen alpha.7 controlled input; no source dataset or prior fixture modified"}
    rng=random.Random(241)
    for i,row in enumerate(r for r in data["observations"] if r["partition"]=="train"):
        if kind=="size_only":row["y"]+=rng.gauss(0,.5)
        elif kind=="extrapolation":
            t=i/20;row["x"][2]=t;row["y"]=t*t+2*t
        elif kind=="mixed_composition":row["metadata"]["factor"]=str(((i//2)%3+i%2)%3)
        elif kind=="power_failure":row["metadata"]["factor"]=row["physical_sample_id"]
        else:raise ValueError(kind)
    return data


if __name__=="__main__":
    destination=ROOT/"tests/fixtures/split_stress";destination.mkdir(exist_ok=True)
    for kind in ("size_only","extrapolation","mixed_composition","power_failure"):
        (destination/(kind+".json")).write_text(json.dumps(generate(kind),indent=2,allow_nan=False)+"\n",encoding="utf-8")
