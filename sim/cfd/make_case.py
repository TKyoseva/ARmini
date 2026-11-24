#!/usr/bin/env python3
"""AR-Mini C085 · write one OpenFOAM (v1912) double-body case for the hull.

  python3 make_case.py <case dir> <single|pair> <base cell, m> <speed, m/s>

single: half of one hull, symmetry on the hull centreline (y = 0).
pair:   one whole hull, symmetry on the catamaran centreline (y = +0.175 m = half of gap 250 + hull 100).
The waterline (z = 0) is a symmetry plane in both: no waves (double-body model).
"""
import os
import sys

case, mode, h, U = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
NU, RHO = 1.0e-6, 998.2            # fresh water 20 °C
L, T = 0.610, 0.023
X0, X1, Z0 = -1.0, 2.6, -0.6
Y0, Y1 = (0.0, 0.8) if mode == "single" else (-0.8, 0.175)
nx, ny, nz = round((X1 - X0) / h), round((Y1 - Y0) / h), round(-Z0 / h)
ymin_patch = "symmetry" if mode == "single" else "patch"
k = 1.5 * (0.01 * U) ** 2          # 1 % turbulence intensity
omega = k ** 0.5 / (0.09 ** 0.25 * 0.07 * L)

F = {}
HDR = 'FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'
F["system/blockMeshDict"] = HDR.format(cls="dictionary", obj="blockMeshDict") + f"""
vertices (({X0} {Y0} {Z0}) ({X1} {Y0} {Z0}) ({X1} {Y1} {Z0}) ({X0} {Y1} {Z0})
          ({X0} {Y0} 0) ({X1} {Y0} 0) ({X1} {Y1} 0) ({X0} {Y1} 0));
blocks (hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1));
edges ();
boundary (
  inlet  {{ type patch; faces ((0 4 7 3)); }}
  outlet {{ type patch; faces ((1 2 6 5)); }}
  ymin   {{ type {ymin_patch}; faces ((0 1 5 4)); }}
  ymax   {{ type {'patch' if mode == 'single' else 'symmetry'}; faces ((3 7 6 2)); }}
  bottom {{ type patch; faces ((0 3 2 1)); }}
  waterline {{ type symmetry; faces ((4 5 6 7)); }}
);
"""
F["system/snappyHexMeshDict"] = HDR.format(cls="dictionary", obj="snappyHexMeshDict") + f"""
castellatedMesh true; snap true; addLayers true;
geometry {{
  hull_wet.stl {{ type triSurfaceMesh; name hull; }}
  wake  {{ type searchableBox; min (-0.15 -0.20 -0.12); max (1.5 0.20 0.01); }}
  near  {{ type searchableBox; min (-0.06 -0.10 -0.06); max (0.95 0.10 0.01); }}
}}
castellatedMeshControls {{
  maxLocalCells 4000000; maxGlobalCells 8000000; minRefinementCells 10; nCellsBetweenLevels 3;
  features ( {{ file "hull_wet.eMesh"; level 3; }} );
  refinementSurfaces {{ hull {{ level (3 3); patchInfo {{ type wall; }} }} }}
  resolveFeatureAngle 30;
  refinementRegions {{ wake {{ mode inside; levels ((1e15 1)); }} near {{ mode inside; levels ((1e15 2)); }} }}
  locationInMesh ({X0 + 0.1013} {Y1 - 0.0517} {Z0 + 0.0519});
  allowFreeStandingZoneFaces true;
}}
snapControls {{ nSmoothPatch 3; tolerance 2.0; nSolveIter 50; nRelaxIter 5; nFeatureSnapIter 10;
  implicitFeatureSnap false; explicitFeatureSnap true; multiRegionFeatureSnap false; }}
addLayersControls {{ relativeSizes true; layers {{ hull {{ nSurfaceLayers 3; }} }}
  expansionRatio 1.3; finalLayerThickness 0.5; minThickness 0.1; nGrow 0; featureAngle 100;
  nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5;
  maxThicknessToMedialRatio 0.3; minMedianAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50; nRelaxedIter 20; }}
meshQualityControls {{ maxNonOrtho 65; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-13;
  minTetQuality 1e-15; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.05; minVolRatio 0.01;
  minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75; relaxed {{ maxNonOrtho 75; }} }}
mergeTolerance 1e-6;
"""
F["system/surfaceFeatureExtractDict"] = HDR.format(cls="dictionary", obj="surfaceFeatureExtractDict") + """
hull_wet.stl { extractionMethod extractFromSurface; includedAngle 150; writeObj no; }
"""
F["system/controlDict"] = HDR.format(cls="dictionary", obj="controlDict") + f"""
application simpleFoam; startFrom latestTime; startTime 0; stopAt endTime; endTime 1200; deltaT 1;
writeControl timeStep; writeInterval 1200; purgeWrite 1; writeFormat ascii; writePrecision 8;
timePrecision 6; runTimeModifiable false;
"""
F["system/fvSchemes"] = HDR.format(cls="dictionary", obj="fvSchemes") + """
ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind;
  div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
"""
F["system/fvSolution"] = HDR.format(cls="dictionary", obj="fvSolution") + """
solvers {
  p { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.05; }
  "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.1; }
}
SIMPLE { nNonOrthogonalCorrectors 1; consistent yes; residualControl { p 1e-5; U 1e-6; "(k|omega)" 1e-6; } }
relaxationFactors { equations { U 0.9; k 0.7; omega 0.7; } fields { p 1; } }
"""
F["system/decomposeParDict"] = HDR.format(cls="dictionary", obj="decomposeParDict") + "numberOfSubdomains 4; method simple; coeffs { n (4 1 1); }\n"
F["constant/transportProperties"] = HDR.format(cls="dictionary", obj="transportProperties") + f"transportModel Newtonian; nu {NU};\n"
F["constant/turbulenceProperties"] = HDR.format(cls="dictionary", obj="turbulenceProperties") + \
    "simulationType RAS;\nRAS\n{\n    RASModel kOmegaSST;\n    turbulence on;\n    printCoeffs off;\n}\n"


def field(name, cls, dim, internal, inlet, outlet, wall):
    sym = "{ type symmetry; }"
    far = inlet if name != "p" else "{ type zeroGradient; }"
    side = {"single": ("ymin", sym, "ymax", far), "pair": ("ymin", far, "ymax", sym)}[mode]
    return HDR.format(cls=cls, obj=name) + f"""
dimensions {dim}; internalField uniform {internal};
boundaryField {{
  inlet {inlet}
  outlet {outlet}
  bottom {far}
  {side[0]} {side[1]}
  {side[2]} {side[3]}
  waterline {sym}
  hull {wall}
}}
"""


F["0/U"] = field("U", "volVectorField", "[0 1 -1 0 0 0 0]", f"({U} 0 0)", f"{{ type fixedValue; value uniform ({U} 0 0); }}",
                 f"{{ type inletOutlet; inletValue uniform (0 0 0); value uniform ({U} 0 0); }}", "{ type noSlip; }")
F["0/p"] = field("p", "volScalarField", "[0 2 -2 0 0 0 0]", "0", "{ type zeroGradient; }",
                 "{ type fixedValue; value uniform 0; }", "{ type zeroGradient; }")
F["0/k"] = field("k", "volScalarField", "[0 2 -2 0 0 0 0]", f"{k:.6e}", f"{{ type fixedValue; value uniform {k:.6e}; }}",
                 f"{{ type inletOutlet; inletValue uniform {k:.6e}; value uniform {k:.6e}; }}",
                 f"{{ type kqRWallFunction; value uniform {k:.6e}; }}")
F["0/omega"] = field("omega", "volScalarField", "[0 0 -1 0 0 0 0]", f"{omega:.6e}", f"{{ type fixedValue; value uniform {omega:.6e}; }}",
                     f"{{ type inletOutlet; inletValue uniform {omega:.6e}; value uniform {omega:.6e}; }}",
                     f"{{ type omegaWallFunction; value uniform {omega:.6e}; }}")
F["0/nut"] = field("nut", "volScalarField", "[0 2 -1 0 0 0 0]", "0", "{ type calculated; value uniform 0; }",
                   "{ type calculated; value uniform 0; }", "{ type nutUSpaldingWallFunction; value uniform 0; }")

for path, text in F.items():
    p = os.path.join(case, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text)
os.makedirs(os.path.join(case, "constant", "triSurface"), exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(case, "constant", "triSurface", "hull_wet.stl"), "w").write(open(os.path.join(here, "hull_wet.stl")).read())
print(f"{case}: {mode}, base cell {h} m ({nx} x {ny} x {nz}), U {U} m/s")
