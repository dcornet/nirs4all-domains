"""Private StageStore adapter: existing serial/cumulative budget, native science.

Full source contracts and numerical evidence stay in the protected root. The
shared historical journal receives an opaque HMAC task and accounting metadata.
No old ledger is reset, forked or relabeled. Callers must freeze admission and
source selection before using this adapter.
"""
from __future__ import annotations

import json
from pathlib import Path

from .adaptive import spectral_request
from .privacy import (PrivateStore, ScopedIdentities, authorize, acquire_private,
                      fail, opaque_id, PrivacyError, _no_reparse)
from .storage import StageStore, atomic_json, digest, fingerprint, tree_bytes
from .unsupervised import (query_design, represent, compact_profile,
                          neighborhood_agreement, compare_partition)
from .native_profile_stream import NativeProfileStream


class PrivateBatch:
    def __init__(self, store, *, state_root, workspace, policy, approval, binary, library, controller_sha256=None):
        self.store=store; self.workspace=Path(workspace); self.policy=policy
        self.approval=approval
        if approval.get('workspace_ceiling')!=policy.get('workspace_max_bytes') or \
                approval.get('campaign_ceiling')!=policy.get('campaign_bytes') or approval.get('owner_approved') is not True:
            fail('ALPHA14_REVIEWED_RESOURCE_APPROVAL_REQUIRED')
        self.binary=Path(binary).resolve();self.library=Path(library).resolve()
        self.runtime={'binary_sha256':digest(self.binary),'library_sha256':digest(self.library),
            'geometry_bridge_sha256':digest(Path(__file__).with_name('unsupervised.py')),
            'stream_bridge_sha256':digest(Path(__file__).with_name('native_profile_stream.py')),
            'privacy_bridge_sha256':digest(Path(__file__).with_name('privacy.py')),
            'csv_transport_sha256':digest(Path(__file__).with_name('adaptive.py')),
            'private_batch_sha256':digest(__file__),
            'controller_sha256':controller_sha256 or digest(__file__)}
        self.scheduler=StageStore(state_root,store.root/'stages-scratch',store.root/'stages',workspace,policy)

    def profile(self, source):
        """Source is a LOCAL frozen contract, never a public task/fixture."""
        spec=source['admission'];authorize(spec)
        _no_reparse(Path(source['matrix']).absolute())
        path=Path(source['matrix']).resolve()
        allowed=Path(source['authorized_cache_root']).resolve()
        if not isinstance(source['source_id'],str) or not source['source_id'].startswith('X') or \
                not source['source_id'].replace('_','').isalnum() or path.name!=source['source_id']+'.csv':
            fail('PRIVATE_SPECTRAL_MATRIX_PATH_REQUIRED')
        if not path.is_relative_to(allowed) or path.is_symlink():
            fail('PRIVATE_SOURCE_OUTSIDE_AUTHORIZED_CACHE')
        if source['identity_evidence']!='observation_identity_only':
            fail('PRIVATE_VERIFIED_COMPONENTS_REQUIRE_SEPARATE_CONTRACT')
        # Permission gate precedes source integrity reads and every fit.
        def source_digest():return digest(path)
        actual=acquire_private(spec,source_digest)
        if actual!=source['source_sha256']:
            fail('PRIVATE_SOURCE_CONTENT_CHANGED')
        # Count the entire protected root as well as the workspace/cache input.
        used=tree_bytes([self.workspace,self.store.root,path,*source.get('other_participating_files',[])])
        if used+source['evidence_upper_bytes']+source['scratch_upper_bytes']>self.policy['workspace_max_bytes']:
            fail('PRIVATE_COMBINED_STORAGE_LIMIT')
        private_contract={'protocol':'domains.private_x_profile.v0.1','source':source,'runtime':self.runtime}
        token=self.store.authenticate(private_contract)
        opaque_task=self.store.authenticate(['private-profile-task',source['source_receipt_id']])
        # These identifiers cannot reveal source content without the private key.
        contract={'task':{'task_id':opaque_task},'private_contract_receipt':token,
                  'visibility':'local_private','protocol':'domains.private_x_profile.v0.1'}
        evidence_receipt=source['evidence_receipt_id']
        evidence_path=self.store.evidence/(evidence_receipt+'.json')
        if evidence_path.exists():
            old=self.store.get(evidence_receipt)
            if old['payload']['contract']!=private_contract:
                fail('PRIVATE_EXECUTION_CONTRACT_CHANGED')
        plan={'inputs':[{'path':str(path),'sha256':actual,'bytes':path.stat().st_size}],
            'scratch_bytes':source['scratch_upper_bytes'], 'evidence_bytes':source['evidence_upper_bytes'],
            'expected_fits':6,'expected_permutations':0,
            'uncertainty':'Two complete-population native PCA fits, four HDBSCAN attempts; raw/SNV, no Y, no public export.'}
        journal=self.scheduler.root/'journal.json'
        ledger=json.loads(journal.read_text()) if journal.exists() else {'runs':{},'reserved_campaign_bytes':0}
        old=ledger['runs'].get(fingerprint(contract)+':P2')
        if not (old and old['status']=='computed') and \
                ledger['reserved_campaign_bytes']-self.approval.get('previous_campaign_reserved',0)+plan['scratch_bytes']+plan['evidence_bytes']>self.approval.get('new_reservation_envelope',self.policy['campaign_bytes']):
            fail('PRIVATE_NEW_RESERVATION_ENVELOPE_EXCEEDED')

        def compute(folder):
            try:
                if evidence_path.exists():
                    saved=self.store.get(evidence_receipt)
                    if saved['payload']['contract']!=private_contract:
                        fail('PRIVATE_EXECUTION_CONTRACT_CHANGED')
                    # Fit completed but accounting/publication may have failed.
                    # Recover the immutable evidence; never repeat its fits.
                    return {'visibility':'local_private','receipt_id':evidence_receipt,
                            'status':'computed','reason':None,'public_export_created':False}
                before=tree_bytes([self.store.root])
                raw=acquire_private(spec,lambda:spectral_request(path,source['source_id'],'observation_identity_only'))
                raw['axis_unit']=source['axis_unit']
                if (len(raw['observation_ids']),len(raw['axis']))!=tuple(source['shape']):
                    fail('PRIVATE_COMPLETE_SOURCE_SHAPE_CHANGED')
                identities=ScopedIdentities(self.store)
                mapped=identities.map_view(source['study_scope'],source['population_scope'],raw['observation_ids'],
                    {s:s for s in raw['observation_ids']},{s:'descriptive' for s in raw['observation_ids']},
                    view_scope=source['source_receipt_id'])
                raw['observation_ids']=mapped['observation_ids'];raw['source_id']=source['source_receipt_id']
                design=query_design(raw['observation_ids'],len(raw['axis']))
                profiles={}
                with NativeProfileStream(self.binary,self.library) as stream:
                    for rep in ['raw','snv']:
                        profile=stream.profile(represent(raw,rep),rep,design=design)
                        profiles[rep]=compact_profile(profile,design)
                ids=raw['observation_ids']
                agreements=[]
                for i in range(2):
                    a,b=[profiles[rep]['cluster_settings'][i] for rep in ['raw','snv']]
                    agreements.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels'])
                        if a['status']==b['status']=='computed' else
                        {'status':'unavailable','reason':'PARTITION_UNAVAILABLE','value':None})
                result={'contract':private_contract,'representations':profiles,
                    'representation_agreement':{'partitions':agreements,
                        'full_axis_neighbors':neighborhood_agreement(profiles['raw']['neighborhoods']['value']['full_axis'],profiles['snv']['neighborhoods']['value']['full_axis'])},
                    'identity_scope':'observation_conditional_not_biological_independence',
                    'original_axis_qualification':source['original_axis_qualification'],
                    'metadata_agreement':{'status':'unavailable','reason':'NO_AUTHORIZED_KEYED_FACTOR_CONTRACT','value':None},
                    'test_target_accessed':False,'new_pca_fits':2,'hdbscan_attempts':4,'supervised_fits':0}
                # Local private scientific report, no public export side effect.
                from .storage import encoded
                mapping_growth=tree_bytes([self.store.root])-before
                if len(encoded(result))+mapping_growth+8192>source['evidence_upper_bytes']:
                    fail('PRIVATE_EVIDENCE_ESTIMATE_REQUIRES_REVIEW')
                self.store.put(spec,result,evidence_receipt)
                atomic_json(folder/'local-receipt.json',{'receipt_id':evidence_receipt,'visibility':'local_private'})
                return {'visibility':'local_private','receipt_id':evidence_receipt,
                        'status':'computed','reason':None,'public_export_created':False}
            except PrivacyError:raise
            except Exception:fail('PRIVATE_NATIVE_PROFILE_FAILED')

        receipt,value=self.scheduler.run(contract,'P2',plan,compute)
        if value is None:fail('PRIVATE_STAGE_NOT_COMPUTED')
        private=self.store.get(value['receipt_id'])
        if private['payload']['contract']!=private_contract:
            fail('PRIVATE_EXECUTION_CONTRACT_CHANGED')
        if tree_bytes([self.workspace,self.store.root,path,*source.get('other_participating_files',[])])>self.policy['workspace_max_bytes']:
            fail('PRIVATE_POSTFIT_STORAGE_LIMIT_RESULT_RETAINED')
        # A private record can survive a post-fit accounting/export failure. No
        # retry may refit it silently; the deterministic receipt above is checked.
        return {'visibility':'local_private','receipt_id':value['receipt_id'],'cache_hit':receipt['cache_hit']}
