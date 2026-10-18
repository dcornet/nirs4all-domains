"""Additive alpha.14 schemas; historical schema generators remain unchanged."""
import json
from pathlib import Path
from nirs4all_domains.privacy import PROTOCOL as PRIVATE, STATES, RIGHTS
from nirs4all_domains.disclosure import PROTOCOL as PUBLIC, INDICATORS, STATISTICS, REASONS, LIMITATIONS


def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def main():
    opaque={'type':'string','pattern':'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'}
    permission=obj({'status':{'enum':sorted(STATES)},'evidence_receipt':{'anyOf':[opaque,{'type':'null'}]}})
    permission['allOf']=[{'if':{'properties':{'status':{'const':'allowed'}}},'then':{'properties':{'evidence_receipt':opaque}}}]
    private=obj({'protocol':{'const':PRIVATE},'visibility':{'enum':['public','local_private']},'receipt_id':opaque,
        'permissions':obj({k:permission for k in sorted(RIGHTS)}),'sensitive_handling':permission,
        'participation_public':{'type':'boolean'},'source_scope':{'type':'string','minLength':1}})
    cell=obj({'indicator':{'enum':sorted(INDICATORS)},'statistic':{'enum':sorted(STATISTICS)},
        'status':{'enum':['computed','unavailable']},'reason':{'enum':[None,*sorted(REASONS)]},'value':{'type':['number','null']}})
    cell['allOf']=[{'if':{'properties':{'status':{'const':'computed'}}},
        'then':{'properties':{'reason':{'type':'null'},'value':{'type':'number'}}},
        'else':{'properties':{'reason':{'enum':sorted(REASONS)},'value':{'type':'null'}}}},
        {'if':{'properties':{'status':{'const':'computed'},'indicator':{'not':{'enum':['relative_skill','matched_skill_difference','partition_agreement','stability_ari']}}}},
         'then':{'properties':{'value':{'minimum':0,'maximum':1}}}},
        {'if':{'properties':{'status':{'const':'computed'},'indicator':{'enum':['partition_agreement','stability_ari']}}},
         'then':{'properties':{'value':{'minimum':-1,'maximum':1}}}}]
    count=obj({'cell':{'type':'integer','minimum':0},'suppressed':{'type':'boolean'},'value':{'type':['integer','null'],'minimum':0}})
    count['allOf']=[{'if':{'properties':{'suppressed':{'const':True}}},'then':{'properties':{'value':{'type':'null'}}},
                    'else':{'properties':{'value':{'type':'integer'}}}}]
    public=obj({'protocol':{'const':PUBLIC},'visibility':{'const':'public'},'receipt_id':opaque,'review_id':opaque,
        'policy_version':{'const':PUBLIC},'decision':{'enum':['approved_for_publication','approved_with_suppression']},
        'indicators':{'type':'array','maxItems':32,'items':cell},'counts':{'type':'array','maxItems':32,'items':count},
        'limitations':{'type':'array','uniqueItems':True,'items':{'enum':sorted(LIMITATIONS)},
            'allOf':[{'contains':{'const':v}} for v in ['NOT_ANONYMITY_GUARANTEE','NOT_DIFFERENTIAL_PRIVACY']]}})
    for name,value in [('private-admission',private),('public-disclosure',public)]:
        schema={'$schema':'https://json-schema.org/draft/2020-12/schema',
            '$id':f'https://dcornet.github.io/nirs4all-domains/schemas/{name}.v1.schema.json',**value}
        data=(json.dumps(schema,sort_keys=True,indent=2)+'\n').encode()
        for root in ['schemas','bridges/python/nirs4all_domains']:
            (Path(root)/(name+'.v1.schema.json')).write_bytes(data)


if __name__=='__main__':main()
