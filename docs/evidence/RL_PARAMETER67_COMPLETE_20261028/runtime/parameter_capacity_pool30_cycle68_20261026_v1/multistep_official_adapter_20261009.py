"""Use upstream SimbaV2's existing n-step critic; keep its optimizer unchanged.

Construct from a separately copied pinned adapter. No edits to an existing
runtime or checkpoint. Generated parameter wrappers fix n_step in their source,
so the ordinary evaluation constructor restores the identical configuration.
"""
import importlib.util
from pathlib import Path


def make_adapter(base_path,n_step):
    assert isinstance(n_step,int) and n_step>=1
    base_path=Path(base_path).resolve(strict=True)
    spec=importlib.util.spec_from_file_location('_sii_official_multistep_base',base_path)
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

    class OfficialParameterAgent(base.OfficialParameterAgent):
        def __init__(self,*args,**kwargs):
            original=base.official_config
            def config(*args,**kwargs):
                return dict(original(*args,**kwargs),n_step=n_step)
            base.official_config=config
            try:super().__init__(*args,**kwargs)
            finally:base.official_config=original
            assert self.config['n_step']==n_step and self.raw_agent._cfg.n_step==n_step
    return OfficialParameterAgent
