import trimesh, numpy as np, json, time
from OCP.gp import gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.STEPControl import STEPControl_AsIs
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.XCAFDoc import XCAFDoc_ColorSurf
from OCP.Interface import Interface_Static
exec(open('parts.py').read())
pos={k:np.array(v) for k,v in json.load(open('pos.json')).items()}
doc=TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
for n,f,q,card,mat,col,note in P:
    t=time.time()
    m=trimesh.load(f)
    if len(m.faces)>20000: m=m.simplify_quadric_decimation(face_count=2000)
    m.merge_vertices(); m.apply_translation(pos[n])
    V=[gp_Pnt(*map(float,v)) for v in m.vertices]
    sew=BRepBuilderAPI_Sewing(1e-3)
    for a,b,c in m.faces:
        poly=BRepBuilderAPI_MakePolygon(V[a],V[b],V[c],True)
        if not poly.IsDone(): continue
        fc=BRepBuilderAPI_MakeFace(poly.Wire(),True)
        if fc.IsDone(): sew.Add(fc.Face())
    sew.Perform(); sh=sew.SewedShape()
    ex=TopExp_Explorer(sh,TopAbs_SHELL)
    mk=BRepBuilderAPI_MakeSolid()
    while ex.More(): mk.Add(TopoDS.Shell(ex.Current())); ex.Next()
    solid=mk.Solid()
    from OCP.ShapeFix import ShapeFix_Solid
    fx=ShapeFix_Solid(solid); fx.Perform(); solid=fx.Solid()
    u=ShapeUpgrade_UnifySameDomain(solid,True,True,True); u.Build(); s2=u.Shape()
    from OCP.TopAbs import TopAbs_FACE
    nf=0; e2=TopExp_Explorer(s2,TopAbs_FACE)
    while e2.More(): nf+=1; e2.Next()
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g=GProp_GProps(); BRepGProp.VolumeProperties_s(s2,g); ok=BRepCheck_Analyzer(s2).IsValid()
    print('  check',n,round(g.Mass()/1000,1),round(m.volume/1000,1),ok)
    if not ok or abs(g.Mass()-m.volume)>0.03*m.volume: print('  SKIP',n); continue
    lab=st.AddShape(s2,False)
    TDataStd_Name.Set_s(lab,TCollection_ExtendedString(f'{n} x{q}'))
    h=col.lstrip('#'); r,g,b=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    ct.SetColor(lab,Quantity_Color(r,g,b,Quantity_TOC_RGB),XCAFDoc_ColorSurf)
    print(n,len(m.faces),'->',nf,'faces',round(time.time()-t,1),'s',flush=True)
Interface_Static.SetCVal_s('write.step.schema','AP214'); Interface_Static.SetIVal_s('write.surfacecurve.mode',0)
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); Interface_Static.SetIVal_s('write.surfacecurve.mode',0); Interface_Static.SetCVal_s('write.step.schema','AP214')
w.Transfer(doc,STEPControl_AsIs); w.Write('out/AR-Mini_printed_parts.step')
