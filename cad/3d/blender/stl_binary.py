"""Rewrites ASCII STL files as binary (about 5 times smaller). Usage: stl_binary.py a.stl b.stl ..."""
import re, struct, sys
import numpy as np
for p in sys.argv[1:]:
    raw = open(p, "rb").read()
    if not raw[:5] == b"solid" or b"facet normal" not in raw[:2000]:
        continue
    v = np.array(re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", raw), dtype=np.float32).reshape(-1, 3, 3)
    n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    with open(p, "wb") as f:
        f.write(b"AR-Mini C086".ljust(80, b" ") + struct.pack("<I", len(v)))
        for i in range(len(v)):
            f.write(struct.pack("<12fH", *n[i], *v[i].ravel(), 0))
    print(p, len(v), "triangles")
