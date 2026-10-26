"""Scheduling-only candidate for30 parameter samplers sharing12 physical CPUs.

Not deployed by importing this module. A subsequent complete-cycle registration,
full-state resume check and online startup audit are required for deployment.
"""
FIRST_CPU = {'impedance': 13, 'admittance': 26, 'vmc': 39}


def sampler_affinity(controller, cpus, slot):
    first = FIRST_CPU[controller]
    if cpus != list(range(first, first + 13)) or not 0 <= slot < 30:
        raise ValueError('Expected original parameter CPU allocation and slot0..29')
    return ','.join(str(cpu) for cpu in cpus[1:])


def validate_pool(protocol, args, cpus):
    first = FIRST_CPU[args.controller]
    expected = dict(kind='shared_physical_cpu_set', workers=30,
                    learner_cpu=first, physical_cpus=list(range(first + 1, first + 13)))
    if (protocol.get('sampler_pool') != expected or args.workers != 30
            or cpus != list(range(first, first + 13))
            or len(protocol['conditions']) != 30
            or len({row['id'] for row in protocol['conditions']}) != 30):
        raise ValueError('Expected30 unique conditions and registered shared sampler pool')


def transform_trainer(source):
    guard = """    if len(set(cpus)) != len(cpus) or args.workers > len(cpus)-1:
        raise ValueError('Reserve one distinct learner CPU plus one per sampler')"""
    affinity = 'str(cpus[slot+1])'
    if source.count(guard) != 1 or source.count(affinity) != 1:
        raise ValueError('Frozen trainer scheduling seam changed')
    return source.replace(guard, '    _validate_parameter_sampler_pool(protocol, args, cpus)').replace(
        affinity, 'str(_parameter_sampler_affinity(args.controller, cpus, slot))')
