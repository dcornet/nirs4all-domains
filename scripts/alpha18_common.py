"""Current campaign accounting over the existing cache, keys and shared journal."""
from pathlib import Path
import shutil

from alpha17_common import Context as HistoricalContext,read
from nirs4all_domains.privacy import protect_directory
from nirs4all_domains.storage import StageStore,digest,tree_bytes,atomic_json


class Context:
    def __init__(self):
        old=HistoricalContext();self.old=old;self.cfg=old.cfg;self.store=old.store
        self.root=protect_directory(self.store.root/'alpha18',Path.cwd())
        self.policy=read('configs/bank/storage-policy-alpha18.json')
        self.base_files=sorted(set(old.files)|set(old.load('candidate-inputs.json'))|set(old.load('incident-inputs.json')))
        self.inputs_path=self.root/'participating-inputs.json'
        self.inputs=self.load(self.inputs_path.name) if self.inputs_path.exists() else []
        self.scheduler=StageStore('results/alpha9-perten-keyed/state',
            protect_directory(self.root/'scratch',Path.cwd()),protect_directory(self.root/'stages',Path.cwd()),self.root,self.policy)
        # StageStore accounts each task's controlled output region and the same
        # cumulative journal. guard() remains the authoritative WHOLE-workspace
        # check, including every participating original, before each source and
        # conservative batch. Avoid rescanning the entire Rust/cache tree for
        # every tiny target result. No input, ceiling, or reservation is omitted.
        self.approval={'owner_approved':True,'date':'2026-10-19',
            'owner_instruction':'No further budget approval when the increase is at most 5 Go per alpha; report the increase.',
            'interpretation':'Conservative SI cap; combined ceiling +4,000,000,000 bytes and reservation ceiling +1,000,000,000 bytes sum to 5,000,000,000.',
            'previous_workspace_ceiling':16289597121,'workspace_ceiling_increase':4000000000,
            'previous_campaign_ceiling':805306368,'campaign_ceiling_increase':1000000000,
            'campaign_baseline_reserved_bytes':804650450,'raw_source_acquisition':False,
            'scope':'Existing authorized bank: inventory, missing X, aligned quantitative reference and supported stress tasks; frozen progressive protocol, no TabPFN or upstream edits.'}
        path=self.root/'owner-standing-budget-authorization.json'
        if path.exists():assert self.load(path.name)==self.approval
        else:self.save(path.name,self.approval)
        assert self.policy['workspace_max_bytes']==20289597121 and self.policy['campaign_bytes']==1805306368
        preservation=self.root/'baseline-preservation.json'
        if not preservation.exists():
            self.save(preservation.name,{'files':{str(p.relative_to(self.store.root)):digest(p) for p in self.store.root.rglob('*') if p.is_file() and not p.is_relative_to(self.root)},
                'journal':read(self.scheduler.root/'journal.json')})

    def save(self,name,value):return atomic_json(self.root/name,{'value':value,'authentication':self.store.authenticate(value)})
    def load(self,name):return self.old.auth(self.root/name)

    def guard(self,extra=0,paths=()):
        used=tree_bytes([Path.cwd(),self.store.root,*self.base_files,*self.inputs,*paths])
        assert used+extra<=self.policy['workspace_max_bytes'],'ALPHA18_COMBINED_STORAGE_CAP'
        assert all(shutil.disk_usage(p).free>=extra+self.policy['reserve_free_bytes'] for p in ['C:/','D:/']),'FREE_VOLUME_RESERVE'
        ledger=read(self.scheduler.root/'journal.json')
        assert self.approval['campaign_baseline_reserved_bytes']<=ledger['reserved_campaign_bytes']<=self.policy['campaign_bytes'],'ALPHA18_SHARED_RESERVATION_CAP'
        return {'combined_bytes':used,'campaign_reserved_bytes':ledger['reserved_campaign_bytes'],
            'campaign_remaining_bytes':self.policy['campaign_bytes']-ledger['reserved_campaign_bytes']}

    def participate(self,paths):
        self.guard(paths=paths);self.inputs=sorted(set(self.inputs)|set(map(str,paths)))
        self.save(self.inputs_path.name,self.inputs)

    def preservation(self):
        b=self.load('baseline-preservation.json')
        assert all(digest(self.store.root/p)==sha for p,sha in b['files'].items()),'HISTORICAL_PRIVATE_ARTIFACT_CHANGED'
        j=read(self.scheduler.root/'journal.json')
        assert all(j['runs'][k]==v for k,v in b['journal']['runs'].items()),'HISTORICAL_JOURNAL_ENTRY_CHANGED'
        assert all(j['task_reserved_bytes'][k]>=v for k,v in b['journal']['task_reserved_bytes'].items())
        return self.guard()
