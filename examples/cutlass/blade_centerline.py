# Plain Python (numpy): centre line of the curved blade from draft/raster.npz -> draft/blade_center.npy.
# Run from the repo root: python examples/cutlass/blade_centerline.py
import os
P = os.path.join(os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()), "projects", "cutlass") + "/"
import numpy as np
d=np.load(P + 'draft/raster.npz'); yf,yb,xs,zs=d['yf'],d['yb'],d['xs'],d['zs']; T=yf-yb
def at(q):
    j=int(round((q[0]-xs[0])/0.002)); i=int(round((q[1]-zs[0])/0.002))
    return T[i,j] if 0<=i<len(zs) and 0<=j<len(xs) else np.nan
def span(p,n,r=0.2):
    s=np.arange(-r,r,0.002); t=np.array([at(p+n*k) for k in s]); m=np.isfinite(t)
    # contiguous run that holds the point closest to p
    idx=np.where(m)[0]
    if len(idx)==0: return None
    c=idx[np.argmin(abs(s[idx]))]; lo=c; hi=c
    while lo-1>=0 and m[lo-1]: lo-=1
    while hi+1<len(s) and m[hi+1]: hi+=1
    return s[lo],s[hi],s,t
tip=np.array([-0.45,0.885]); guard=np.array([0.075,0.245])    # rough guess read off a plot of raster.npz
a=(tip-guard)/np.linalg.norm(tip-guard); n=np.array([-a[1],a[0]])
L=np.linalg.norm(tip-guard); C=[]
for f in np.linspace(0.02,0.97,40):
    p=guard+a*L*f; r=span(p,n)
    if r: C.append(p+n*(r[0]+r[1])/2)
C=np.array(C)
# the last station stops short of the tip: append the silhouette point farthest along the blade
I, J = np.where(np.isfinite(T)); pts = np.c_[xs[J], zs[I]]
a = C[-1] - C[-5]; a /= np.linalg.norm(a)
np.save(P + 'draft/blade_center.npy', np.vstack([C, pts[np.argmax(pts @ a)]]))
