package composition

import (
 "math"
 "reflect"
 "testing"
)
func fixture()Episode{return Episode{ID:"public-synthetic-adult-independent",Seed:17,Base:Vec{0,0},Forward:Mat{{1,.25},{.2,1}},TargetFeature:0,ProtectedFeature:1,TargetValue:1,MaxAbsDelta:2}}
func TestConstrainedPreservesInvariant(t *testing.T){e:=fixture();direct,err:=Execute(e,"T1-direct");if err!=nil{t.Fatal(err)};correct,err:=Execute(e,"T2-constrained");if err!=nil{t.Fatal(err)};if correct.TargetAbsError>1e-12||correct.ProtectedAbsDrift>1e-12{t.Fatalf("not preserved: %+v",correct)};if direct.ProtectedAbsDrift<.19{t.Fatal("negative control missing expected coupling")}}
func TestNotMutatingAndReplay(t *testing.T){e:=fixture();old:=e;one,err:=Execute(e,"T2-constrained");if err!=nil{t.Fatal(err)};two,_:=Execute(e,"T2-constrained");if !reflect.DeepEqual(one,two)||!reflect.DeepEqual(e,old){t.Fatal("nonreproducible or mutated source")}}
func TestHostileInputs(t *testing.T){
	cases:=[]func(*Episode){
		func(e *Episode){e.TargetValue=math.NaN()},
		func(e *Episode){e.Forward[0][0]=math.Inf(1)},
		func(e *Episode){e.Forward=Mat{}},
		func(e *Episode){e.TargetFeature=e.ProtectedFeature},
		func(e *Episode){e.MaxAbsDelta=0},
		func(e *Episode){e.Base[0]=math.NaN()},
		// High-scale near-rank-deficient matrix (det=1, cond ~ 4e16) must fail closed
		func(e *Episode){e.Forward=Mat{{1e8,1e8},{1e8,1e8+1e-8}}},
		// Overflow in derived TargetAbsError / Observe must fail closed
		func(e *Episode){e.Forward=Mat{{1e308,-1e308},{0,1}};e.Base=Vec{1,-1}},
	}
	for i,f:=range cases{e:=fixture();f(&e);if _,err:=Execute(e,"T2-constrained");err==nil{t.Fatalf("case %d admitted",i)}}
	// Uniformly-scaled well-conditioned matrix (det=9.5e-11, cond ~ 1.54) must be accepted
	scaled:=fixture()
	scaled.Forward=Mat{{1e-5,0.25e-5},{0.2e-5,1e-5}}
	scaled.TargetValue=1e-5
	if r,err:=Execute(scaled,"T2-constrained");err!=nil||r.TargetAbsError>1e-16||r.ProtectedAbsDrift>1e-16{
		t.Fatalf("uniformly-scaled well-conditioned matrix failed: err=%v r=%+v",err,r)
	}
}
func TestBudgetAndUnknownTreatment(t *testing.T){e:=fixture();e.MaxAbsDelta=.001;if _,err:=Execute(e,"T2-constrained");err==nil{t.Fatal("unbounded delta accepted")};if _,err:=Execute(fixture(),"weight-hypernetwork");err==nil{t.Fatal("unsupported operator accepted")}}
func TestSyntheticCampaignIsFalsifiable(t *testing.T){
	n:=0
	for i:=0;i<16;i++{
		for seed:=0;seed<3;seed++{
			e:=fixture()
			e.ID="synthetic-subject"
			e.Seed=seed
			e.Forward[0][1]+=.005*float64(i)
			byTreatment := map[string]Receipt{}
			for _,m:=range []string{"T0-untreated","T1-direct","T2-constrained","Tneg-equal-norm-shuffle"}{
				r,err:=Execute(e,m)
				if err!=nil{t.Fatal(err)}
				if r.Schema!=Schema||r.Namespace!=Namespace||r.Claim==""||math.IsNaN(r.TargetAbsError)||math.IsNaN(r.ProtectedAbsDrift){
					t.Fatalf("invalid receipt: %+v",r)
				}
				byTreatment[m]=r
				n++
			}
			t0,t1,t2,tneg := byTreatment["T0-untreated"], byTreatment["T1-direct"], byTreatment["T2-constrained"], byTreatment["Tneg-equal-norm-shuffle"]
			if t0.ProtectedAbsDrift!=0 || t0.TargetAbsError<0.5 { t.Fatalf("T0 failure: %+v",t0) }
			if t1.TargetAbsError>1e-12 || t1.ProtectedAbsDrift<0.19 { t.Fatalf("T1 negative control failure: %+v",t1) }
			if t2.TargetAbsError>1e-12 || t2.ProtectedAbsDrift>1e-12 { t.Fatalf("T2 constrained failure: %+v",t2) }
			if tneg.TargetAbsError<0.5 || tneg.ProtectedAbsDrift<0.9 { t.Fatalf("Tneg deterioration failure: %+v",tneg) }
			if !(t2.TargetAbsError < t0.TargetAbsError && t2.ProtectedAbsDrift < t1.ProtectedAbsDrift && t2.ProtectedAbsDrift < tneg.ProtectedAbsDrift) {
				t.Fatalf("matched control ordering violated: t0=%+v t1=%+v t2=%+v tneg=%+v",t0,t1,t2,tneg)
			}
			cell := ToB1DOECell(e, t2, "cell-001", "H1", "b886792")
			if cell["schema_version"] != 1 { t.Fatalf("bad B1 schema_version: %+v",cell) }
		}
	}
	if n!=192{t.Fatal(n)}
}
