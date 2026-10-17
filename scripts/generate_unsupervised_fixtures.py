"""Controlled X generation only; these generators are not a numerical backend."""
import math
import random

MECHANISMS = (
    'separated', 'gradient', 'overlapping', 'density_imbalance', 'satellites',
    'exact_repeats_unknown', 'close_independent', 'known_acquisitions',
    'scatter', 'chemical_continuum', 'thin_manifold', 'high_dimensional_noise',
    'wavelength_scaling', 'snv_erased', 'snv_enhanced', 'fragmentation',
)


def scenario(name, n=120, p=24):
    if name not in MECHANISMS:
        raise ValueError('UNKNOWN_FROZEN_MECHANISM')
    if name == 'high_dimensional_noise':
        p = 80
    rng = random.Random(12041)
    x, truth, units = [], [], {}
    for i in range(n):
        group = min(2, 3*i//n)
        noise = [rng.gauss(0, .04) for _ in range(p)]
        shape = [math.sin((j+1)*.31)+.1*math.cos((j+1)*.73+i*.11) for j in range(p)]
        if name == 'separated':
            row = [50*group+v for v in noise]
        elif name in ('gradient', 'fragmentation'):
            row = [j*.1+(i/(n-1))*(j+1)/p+v*.03 for j,v in enumerate(noise)]
        elif name == 'overlapping':
            row = [rng.gauss(.2*group,1) for _ in range(p)]
        elif name == 'density_imbalance':
            group = 0 if i < .8*n else 1
            row = [10*group+v*(1 if group == 0 else 15) for v in noise]
        elif name == 'satellites':
            group = 0 if i < .85*n else 1+(i%2)
            row = [30*group+v for v in noise]
        elif name in ('scatter', 'snv_erased'):
            row = [100*group+(group+1)*v for v in shape]
        elif name == 'snv_enhanced':
            row = [100*(i%17)+(1+i%7)*(v+.5*math.sin(j*.3+group*2)) for j,v in enumerate(shape)]
        elif name == 'chemical_continuum':
            row = [v+(i/n)*math.cos(j*.17)+noise[j]*.01 for j,v in enumerate(shape)]
        elif name == 'thin_manifold':
            row = [math.sin(i/n*4+j*.2)+.01*noise[j] for j in range(p)]
        elif name in ('high_dimensional_noise','wavelength_scaling'):
            row = [rng.gauss(0,1)*(1000 if name=='wavelength_scaling' and j==0 else 1) for j in range(p)]
        else:
            base = i//4 if name in ('exact_repeats_unknown','known_acquisitions') else i//2
            row = [math.sin(base*.3+j*.4)+base*.1 for j in range(p)]
            if name == 'close_independent':
                row = [v+(i%2)*1e-11 for v in row]
        x.append(row); truth.append(group)
        units[f'o:{i}'] = f'acquisition-component:{i//4}' if name == 'known_acquisitions' else f'object:{i}'
    identity = 'verified_physical_identity' if name in ('known_acquisitions','close_independent') else 'observation_identity_only'
    return {'spectral':{'source_id':'controlled:'+name,'observation_ids':[f'o:{i}' for i in range(n)],
        'identity_evidence':identity,'axis':[1000+5*j for j in range(p)],'axis_unit':'nm','spectra':x},
        'components':units,'generating_x_labels':truth,'mechanism':name,
        'interpretation':'Known simulated X mechanism; no Y or predictive experiment.'}
