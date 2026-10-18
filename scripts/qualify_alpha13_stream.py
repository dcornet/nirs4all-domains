"""Exact executable transport parity; all numeric work remains native."""
import json
from pathlib import Path
import random
import subprocess
import time
from alpha13_common import ROOT,PUBLIC,run,publish
from generate_unsupervised_fixtures import MECHANISMS,scenario
from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import native_profile,represent


def main():
    from n4m._ffi import library_path
    old=Path('target/debug/n4domains.exe').resolve();new=Path('target/qualification/n4domains.exe').resolve();library=Path(library_path()).resolve()
    for name in ['unsupervised.rs','methods.rs']:
        path=Path('crates/nirs4all-domains/src')/name
        assert subprocess.check_output(['git','show','ebb1b9b8a45d01618931d846d059641701cac7da:'+path.as_posix()])==path.read_bytes()
    contract={'task':{'task_id':fingerprint(['alpha13','native-stream-parity'])},'phase':'native-stream-parity',
        'protocol_version':'domains.native_profile_stream.v0.1','old_binary_sha256':digest(old),'new_binary_sha256':digest(new),
        'library_sha256':digest(library),'runner_sha256':digest(__file__),
        'stream_bridge_sha256':digest('bridges/python/nirs4all_domains/native_profile_stream.py'),
        'native_characterization_source_sha256':digest('crates/nirs4all-domains/src/unsupervised.rs'),
        'native_adapter_source_sha256':digest('crates/nirs4all-domains/src/methods.rs')}
    def calculate(folder):
        rows=[];old_seconds=0.;new_seconds=0.;begin=time.perf_counter()
        requests=[(name,rep,represent(scenario(name)['spectral'],rep)) for name in MECHANISMS for rep in ['raw','snv']]
        rng=random.Random(13047);large={'source_id':'controlled:stream-full-rank','observation_ids':[f'large:{i}' for i in range(513)],
            'identity_evidence':'observation_identity_only','axis':[1000+j for j in range(128)],'axis_unit':'nm',
            'spectra':[[rng.gauss(0,1) for _ in range(128)] for _ in range(513)]}
        requests.append(('full_rank_over_500','raw',large))
        with NativeProfileStream(new,library) as stream:
            for name,rep,q in requests:
                start=time.perf_counter();left=native_profile(q,rep,old,library);old_seconds+=time.perf_counter()-start
                start=time.perf_counter();right=stream.profile(q,rep);new_seconds+=time.perf_counter()-start
                assert left==right,(name,rep)
                rows.append({'mechanism':name,'representation':rep,'n_observations':len(q['spectra']),
                    'profile_sha256':fingerprint(left),'scores_partitions_eigenvalues_statuses_exact':True})
            q=scenario('gradient')['spectral'];bad={**q,'Y_test':[999.]*120}
            try:stream.profile(bad,'raw')
            except RuntimeError as error:assert 'unknown field' in str(error)
            else:raise AssertionError('STREAM_ACCEPTED_TARGET')
            assert stream.profile(q,'raw')==native_profile(q,'raw',old,library)
        return {'protocol_version':'domains.native_profile_stream.v0.1','contract':contract,'cases':rows,
            'all_exact':True,'bad_target_rejected_and_following_request_exact':True,'parity_pca_fits':68,'parity_hdbscan_attempts':136,
            'old_request_seconds':old_seconds,'new_request_seconds':new_seconds,'elapsed_seconds':time.perf_counter()-begin,
            'scope':'33 paired cases plus one paired recovery request, engineering qualification separate from controlled scientific fit counts.',
            'target_accessed':False,'real_data_fits':0}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':32768,'expected_fits':204,'expected_permutations':0,
        'uncertainty':'34 paired synthetic requests, exact full profile parity; no real data or stored score matrices.'}
    store,receipt,value=run(contract,'P2',plan,calculate);publish(store,receipt,'native-stream-parity.json');atomic_json(ROOT/'stream-parity-receipt.json',receipt)
    print(json.dumps({'all_exact':value['all_exact'],'old_seconds':value['old_request_seconds'],'stream_seconds':value['new_request_seconds']}))


if __name__=='__main__':main()
