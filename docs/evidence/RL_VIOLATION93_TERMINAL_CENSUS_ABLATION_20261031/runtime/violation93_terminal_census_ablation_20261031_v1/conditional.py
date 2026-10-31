"""Full-mask-stratified conditional expectation of terminal128 batch loss."""
import numpy as np

def mask_codes(masks):
 masks=np.asarray(masks)
 if masks.ndim!=2 or masks.shape[1]!=5 or not np.isin(masks,[0,1]).all():raise ValueError('Expected binary five-critic masks')
 return (masks.astype(np.int64)*np.array([1,2,4,8,16])).sum(1)

def weights(terminal_masks,batch_masks,dones):
 tm=np.asarray(terminal_masks,dtype=np.float64);bm=np.asarray(batch_masks,dtype=np.float64);dones=np.asarray(dones)
 if dones.shape!=(len(bm),) or not np.isin(dones,[0,1]).all():raise ValueError('Expected aligned binary dones')
 tc=mask_codes(tm);bc=mask_codes(bm);population=np.bincount(tc,minlength=32);counts=np.bincount(bc[dones==1],minlength=32)
 if np.any((counts>0)&(population==0)):raise ValueError('Sampled terminal pattern absent from full terminal population')
 den=(bm*(1+127*dones[:,None])).sum(0)
 if np.any(den<=0):raise ValueError('Native accepted batch requires positive denominators')
 rate=np.divide(counts,population,out=np.zeros(32,dtype=float),where=population>0)
 w=128*rate[tc,None]*tm/den
 np.testing.assert_allclose(w.sum(0),128*bm[dones==1].sum(0)/den,rtol=1e-12,atol=1e-12)
 return w,den,population,counts
