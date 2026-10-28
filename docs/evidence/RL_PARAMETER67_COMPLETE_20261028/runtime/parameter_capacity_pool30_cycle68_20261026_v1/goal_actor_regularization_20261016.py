"""Explicit optimizer-preserving migration of the upstream actor loss only."""
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path


def check_actor_regularization_migration(saved, current):
    if saved.get('n_step') != 25 or saved.get('actor_bc_alpha') != 0. or current.get('actor_bc_alpha') != 1.:
        raise ValueError('Only registered n25 actor_bc_alpha0 ->1 migration is allowed')
    if {k:v for k,v in saved.items() if k!='actor_bc_alpha'} != {
            k:v for k,v in current.items() if k!='actor_bc_alpha'}:
        raise ValueError('Actor regularization migration must preserve every other configuration field')


def make_actor_regularized_adapter(base_path, migration_checkpoint, checkpoint_hashes):
    spec=importlib.util.spec_from_file_location('_sii_actor_regularization_base',Path(base_path).resolve(strict=True))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    allowed=Path(migration_checkpoint).resolve()

    class RegularizedAgent(module.OfficialParameterAgent):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            assert self.config['n_step']==25 and self.config['actor_bc_alpha']==0.
            self.config=dict(self.config,actor_bc_alpha=1.)
            self.raw_agent._cfg=replace(self.raw_agent._cfg,actor_bc_alpha=1.)

        def load(self,path):
            path=Path(path).resolve()
            saved=json.loads((path/'official_agent_state.json').read_text())['config']
            if saved==self.config:
                return super().load(path)
            if path!=allowed:
                raise ValueError('Unregistered actor regularization migration checkpoint')
            check_actor_regularization_migration(saved,self.config)
            if not checkpoint_hashes:
                raise ValueError('Migration requires exact source hashes')
            for name,expected in checkpoint_hashes.items():
                with (path/name).open('rb') as stream:
                    if hashlib.file_digest(stream,'sha256').hexdigest()!=expected:
                        raise ValueError('Migration checkpoint changed')
            current=self.config
            # Strict base loader restores weights, moments, counters, stats and
            # RNG. The upstream loss coefficient lives in _cfg, outside these.
            self.config=saved
            try:
                super().load(path)
            finally:
                self.config=current
            assert self.raw_agent._cfg.actor_bc_alpha==self.config['actor_bc_alpha']==1.
    return RegularizedAgent
