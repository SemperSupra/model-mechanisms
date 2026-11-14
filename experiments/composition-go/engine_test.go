package composition

import (
 "math"
 "reflect"
 "testing"
)
func fixture()Episode{return Episode{ID:"public-synthetic-adult-independent",Seed:17,Base:Vec{0,0},Forward:Mat{{1,.25},{.2,1}},TargetFeature:0,ProtectedFeature:1,TargetValue:1,MaxAbsDelta:2}}
func TestConstrainedPreservesInvariant(t *testing.T){e:=fixture();direct,err:=Execute(e,"T1-direct");if err!=nil{t.Fatal(err)};correct,err:=Execute(e,"T2-constrained");if err!=nil{t.Fatal(err)};if correct.TargetAbsError>1e-12||correct.ProtectedAbsDrift>1e-12{t.Fatalf("not preserved: %+v",correct)};if direct.ProtectedAbsDrift<.19{t.Fatal("negative control missing expected coupling")}}
func TestNotMutatingAndReplay(t *testing.T){e:=fixture();old:=e;one,err:=Execute(e,"T2-constrained");if err!=nil{t.Fatal(err)};two,_:=Execute(e,"T2-constrained");if !reflect.DeepEqual(one,two)||!reflect.DeepEqual(e,old){t.Fatal("nonreproducible or mutated source")}}
func TestHostileInputs(t *testing.T){cases:=[]func(*Episode){func(e *Episode){e.TargetValue=math.NaN()},func(e *Episode){e.Forward[0][0]=math.Inf(1)},func(e *Episode){e.Forward=Mat{}},func(e *Episode){e.TargetFeature=e.ProtectedFeature},func(e *Episode){e.MaxAbsDelta=0},func(e *Episode){e.Base[0]=math.NaN()}};for i,f:=range cases{e:=fixture();f(&e);if _,err:=Execute(e,"T2-constrained");err==nil{t.Fatalf("case %d admitted",i)}}}
func TestBudgetAndUnknownTreatment(t *testing.T){e:=fixture();e.MaxAbsDelta=.001;if _,err:=Execute(e,"T2-constrained");err==nil{t.Fatal("unbounded delta accepted")};if _,err:=Execute(fixture(),"weight-hypernetwork");err==nil{t.Fatal("unsupported operator accepted")}}
func TestSyntheticCampaignIsFalsifiable(t *testing.T){n:=0;for i:=0;i<16;i++{for seed:=0;seed<3;seed++{e:=fixture();e.ID="synthetic-subject";e.Seed=seed;e.Forward[0][1]+=.005*float64(i);for _,m:=range []string{"T0-untreated","T1-direct","T2-constrained","Tneg-equal-norm-shuffle"}{r,err:=Execute(e,m);if err!=nil{t.Fatal(err)};if r.Schema!=Schema||r.Claim==""||math.IsNaN(r.TargetAbsError){t.Fatal("invalid receipt")};n++}}};if n!=192{t.Fatal(n)}}
