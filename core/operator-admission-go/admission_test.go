package admission

import (
 "encoding/json"
 "math"
 "reflect"
 "strings"
 "testing"
)

func a64()string{return strings.Repeat("a",64)}
func b64()string{return strings.Repeat("b",64)}
func model()ModelRef{return ModelRef{Backend:"synthetic-mhr-like",Revision:"v1",WeightsSHA256:a64(),ArchitectureSHA256:b64()}}
func m0()Manifest{return Manifest{Schema:Schema,OperatorID:"synthetic-control-v1",Revision:"r1",Kind:"parameter_delta",Model:model(),Input:Representation{Kind:"latent_vector",ParameterSpace:"synthetic-2d",Dimension:2,Units:"unitless",Frame:"model-local"},AllowedScopes:[]string{"morphology"},ProtectedFields:[]string{"canonical_authority","source_provenance","persistent_identity","rights"},DeltaUnit:"normalized",MaxAbsDelta:1,SourceClass:"public_synthetic",SourceAdmissionID:"public-fixture-0001",Resources:Resources{MaxWallSeconds:30,MaxMemoryMiB:256,MaxGPUMiB:0}}}
func c0()Candidate{m:=m0();return Candidate{Schema:CandidateSchema,CandidateID:"synthetic-base-v1",Model:m.Model,State:m.Input,SourceClass:m.SourceClass,SourceAdmissionID:m.SourceAdmissionID}}

func TestPositiveCompatibleContract(t *testing.T){
 m,c:=m0(),c0();originalM,originalC:=m,c
 r,err:=Plan(m,c);if err!=nil{t.Fatal(err)}
 if r.Status!="COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"||len(r.Reasons)!=0||len(r.ManifestSHA256)!=64||len(r.CandidateSHA256)!=64{t.Fatalf("bad receipt %+v",r)}
 again,_:=Plan(m,c)
 if !reflect.DeepEqual(r,again)||!reflect.DeepEqual(m,originalM)||!reflect.DeepEqual(c,originalC){t.Fatal("non-deterministic or mutating plan")}
 if strings.Contains(r.Claim,"EXECUTED"){t.Fatal("false execution claim")}
}
func TestModelAndRepresentationMismatch(t *testing.T){
 cases:=map[string]func(*Candidate){
 "model_weights":func(c *Candidate){c.Model.WeightsSHA256=b64()},
 "backend":func(c *Candidate){c.Model.Backend="other"},
 "revision":func(c *Candidate){c.Model.Revision="new"},
 "architecture":func(c *Candidate){c.Model.ArchitectureSHA256=a64()},
 "latent_dimension":func(c *Candidate){c.State.Dimension=45},
 "parameter_space":func(c *Candidate){c.State.ParameterSpace="different"},
 "frame":func(c *Candidate){c.State.Frame="gltf-y-up"},
 "unit":func(c *Candidate){c.State.Units="m"},
 "source":func(c *Candidate){c.SourceAdmissionID="other-fixture"},
 "class":func(c *Candidate){c.SourceClass="private_admitted"},
 }
 for name,f:=range cases{t.Run(name,func(t *testing.T){c:=c0();f(&c);r,err:=Plan(m0(),c);if err!=nil{t.Fatal(err)};if r.Status!="REJECTED"||len(r.Reasons)==0{t.Fatalf("fail-open %+v",r)}})}
}
func TestKindSpecificRepresentationAndHardGates(t *testing.T){
 cases:=map[string]func(*Manifest){
 "wrong_kind":func(m *Manifest){m.Kind="geometry_residual"},
 "unsupported_kind":func(m *Manifest){m.Kind="auto_run"},
 "unprotected_identity":func(m *Manifest){m.ProtectedFields=[]string{"canonical_authority","source_provenance"}},
 "scope_conflict":func(m *Manifest){m.AllowedScopes=[]string{"persistent_identity"}},
 "missing_scope":func(m *Manifest){m.AllowedScopes=nil},
 "unknown_source":func(m *Manifest){m.SourceClass="licensed_supposedly"},
 "network":func(m *Manifest){m.Resources.AllowNetwork=true},
 "paid":func(m *Manifest){m.Resources.AllowPaid=true},
 "walltime":func(m *Manifest){m.Resources.MaxWallSeconds=86400},
 "memory":func(m *Manifest){m.Resources.MaxMemoryMiB=0},
 "negative_budget":func(m *Manifest){m.MaxAbsDelta=-1},
 "nan_budget":func(m *Manifest){m.MaxAbsDelta=math.NaN()},
 "inf_budget":func(m *Manifest){m.MaxAbsDelta=math.Inf(1)},
 "invalid_hash":func(m *Manifest){m.Model.WeightsSHA256="bad"},
 "zero_vector":func(m *Manifest){m.Input.Dimension=0},
 "missing_frame":func(m *Manifest){m.Input.Frame=""},
 "unrecognized_frame":func(m *Manifest){m.Input.Frame="unknown-up"},
 "unknown_scope":func(m *Manifest){m.AllowedScopes=[]string{"new-right"}},
 }
 for name,f:=range cases{t.Run(name,func(t *testing.T){m:=m0();f(&m);if _,err:=Plan(m,c0());err==nil{t.Fatal("invalid manifest admitted")}})}
}
func TestGeometryRigMotionAndWeightSpecializations(t *testing.T){
 geo:=m0();geo.Kind="geometry_residual";geo.Input=Representation{Kind:"mesh",TopologySHA256:a64(),Units:"m",Frame:"blender-z-up"};geo.AllowedScopes=[]string{"tissue"};geo.DeltaUnit="m"
 c:=c0();c.State=geo.Input
 if r,err:=Plan(geo,c);err!=nil||r.Status!="COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"{t.Fatalf("geometry rejected %v %+v",err,r)}
 c.State.TopologySHA256=b64()
 if r,err:=Plan(geo,c);err!=nil||r.Status!="REJECTED"{t.Fatalf("wrong topology accepted %v %+v",err,r)}
 motion:=m0();motion.Kind="motion_corrector";motion.Input=Representation{Kind:"pose_stream",RigSHA256:a64(),Timebase:"24/1",Units:"rad",Frame:"model-local"};motion.DeltaUnit="rad";motion.AllowedScopes=[]string{"motion"}
 c=c0();c.State=motion.Input
 if r,err:=Plan(motion,c);err!=nil||r.Status!="COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"{t.Fatalf("motion rejected %v %+v",err,r)}
 c.State.Timebase="25/1";if r,err:=Plan(motion,c);err!=nil||r.Status!="REJECTED"{t.Fatalf("wrong fps accepted %v %+v",err,r)}
 motion.Input.Timebase="0/1";if _,err:=Plan(motion,c0());err==nil{t.Fatal("zero numerator fps admitted")}
 motion.Input.Timebase="24/0";if _,err:=Plan(motion,c0());err==nil{t.Fatal("zero denominator fps admitted")}
 motion.Input.Timebase="justwords";if _,err:=Plan(motion,c0());err==nil{t.Fatal("non rational fps admitted")}
 weight:=m0();weight.Kind="weight_adapter";weight.Input=Representation{Kind:"weights",ParameterSpace:"exact-arch-layer-A",Dimension:128,Units:"unitless",Frame:"model-local"};weight.AllowedScopes=[]string{"weights"}
 c=c0();c.State=weight.Input
 if r,err:=Plan(weight,c);err!=nil||r.Status!="COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"{t.Fatalf("weights rejected %v %+v",err,r)}
 weight.Model.ArchitectureSHA256="";if _,err:=Plan(weight,c);err==nil{t.Fatal("architecture unpinned")}
}
func TestStrictJSONRejectsAmbiguity(t *testing.T){
 raw,_:=json.Marshal(m0())
 cases:=map[string]string{
  "duplicate_root":strings.Replace(string(raw),`"schema":`,`"schema":"forged","schema":`,1),
  "duplicate_nested":strings.Replace(string(raw),`"backend":`,`"backend":"fake","backend":`,1),
  "unknown":strings.Replace(string(raw),`"revision":"r1"`,`"revision":"r1","new_unsafe":true`,1),
  "trailing":string(raw)+` {"schema":"forged"}`,
  "oversized":string(raw)+strings.Repeat(" ",MaxJSONBytes),
  "unknown_first":`{"other":true}`,
  "deep":strings.Repeat("[",80)+`0`+strings.Repeat("]",80),
 }
 for name,data:=range cases{t.Run(name,func(t *testing.T){var m Manifest;if err:=DecodeStrict(strings.NewReader(data),&m);err==nil{t.Fatalf("bad JSON admitted: %s",name)}})}
 var m Manifest;if err:=DecodeStrict(strings.NewReader(string(raw)),&m);err!=nil{t.Fatal(err)}
}
