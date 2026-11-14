// Package composition provides a strictly synthetic, method-neutral
// correction-operator contract. No neural model or physical human is loaded.
package composition

import (
 "crypto/sha256"
 "encoding/hex"
 "encoding/json"
 "errors"
 "fmt"
 "math"
)

const Schema = "model-mechanisms.composition-fixture.v1"

type Vec [2]float64
type Mat [2][2]float64

type Episode struct {
 ID string `json:"id"`
 Seed int `json:"seed"`
 Base Vec `json:"base"`
 Forward Mat `json:"forward"`
 TargetFeature int `json:"target_feature"`
 ProtectedFeature int `json:"protected_feature"`
 TargetValue float64 `json:"target_value"`
 MaxAbsDelta float64 `json:"max_abs_delta"`
}

type Receipt struct {
 Schema string `json:"schema"`
 EpisodeID string `json:"episode_id"`
 Seed int `json:"seed"`
 Treatment string `json:"treatment"`
 EpisodeSHA256 string `json:"episode_sha256"`
 Delta Vec `json:"delta"`
 Before Vec `json:"before"`
 After Vec `json:"after"`
 TargetAbsError float64 `json:"target_abs_error"`
 ProtectedAbsDrift float64 `json:"protected_abs_drift"`
 Claim string `json:"claim"`
}

func finite(x float64) bool { return !math.IsNaN(x) && !math.IsInf(x, 0) }
func (e Episode) Validate() error {
 if e.ID == "" || e.Seed < 0 || e.TargetFeature < 0 || e.TargetFeature > 1 || e.ProtectedFeature < 0 || e.ProtectedFeature > 1 || e.TargetFeature == e.ProtectedFeature { return errors.New("INVALID_EPISODE_ID_OR_FEATURE") }
 if !finite(e.TargetValue) || !finite(e.MaxAbsDelta) || e.MaxAbsDelta <= 0 || e.MaxAbsDelta > 10 { return errors.New("INVALID_TARGET_OR_DELTA_BUDGET") }
 for _, v := range e.Base { if !finite(v) { return errors.New("NONFINITE_BASE") } }
 for _, row := range e.Forward { for _, v := range row { if !finite(v) { return errors.New("NONFINITE_FORWARD") } } }
 determinant := e.Forward[0][0]*e.Forward[1][1] - e.Forward[0][1]*e.Forward[1][0]
 if !finite(determinant) || math.Abs(determinant) < 1e-7 { return errors.New("ILL_CONDITIONED_SYNTHETIC_FORWARD") }
 return nil
}
func (e Episode) Observe(x Vec) Vec {
 return Vec{e.Forward[0][0]*x[0]+e.Forward[0][1]*x[1], e.Forward[1][0]*x[0]+e.Forward[1][1]*x[1]}
}

func Propose(e Episode, treatment string)(Vec,error) {
 if err:=e.Validate();err!=nil { return Vec{},err }
 y:=e.Observe(e.Base)
 errTarget:=e.TargetValue-y[e.TargetFeature]
 i,j:=e.TargetFeature,e.ProtectedFeature
 if !finite(errTarget) { return Vec{},errors.New("NONFINITE_TARGET_ERROR") }
 switch treatment {
 case "T0-untreated": return Vec{},nil
 case "T1-direct":
   slope:=e.Forward[i][i];if math.Abs(slope)<1e-9{return Vec{},errors.New("ZERO_DIRECT_SLOPE")}
   var d Vec;d[i]=errTarget/slope;return d,nil
 case "T2-constrained":
   // Satisfy target while preserving the independent protected observable.
   // Solve 2x2 system M*d=[desired target correction, 0] in measured space.
   a,b:=e.Forward[i][i],e.Forward[i][j]
   c,d:=e.Forward[j][i],e.Forward[j][j]
   det:=a*d-b*c
   if math.Abs(det)<1e-7{return Vec{},errors.New("ZERO_SUBSYSTEM_DETERMINANT")}
   var v Vec;v[i]=errTarget*d/det;v[j]=-errTarget*c/det;return v,nil
 case "Tneg-equal-norm-shuffle":
   slope:=e.Forward[i][i];if math.Abs(slope)<1e-9{return Vec{},errors.New("ZERO_DIRECT_SLOPE")}
   var d Vec;d[j]=errTarget/slope;return d,nil
 default: return Vec{},fmt.Errorf("UNSUPPORTED_TREATMENT:%s",treatment)
 }
}
func Execute(e Episode,treatment string)(Receipt,error) {
 var zero Receipt
 d,err:=Propose(e,treatment);if err!=nil{return zero,err}
 for _,v:=range d {if !finite(v) || math.Abs(v)>e.MaxAbsDelta{return zero,errors.New("DELTA_EXCEEDS_BUDGET")}}
 epBytes,_:=json.Marshal(e);sum:=sha256.Sum256(epBytes)
 next:=e.Base
 for k:=range next {next[k]+=d[k];if !finite(next[k]){return zero,errors.New("NONFINITE_CORRECTION")}}
 before,after:=e.Observe(e.Base),e.Observe(next)
 for _,v:=range after{if !finite(v){return zero,errors.New("NONFINITE_OBSERVATION")}}
 return Receipt{Schema:Schema,EpisodeID:e.ID,Seed:e.Seed,Treatment:treatment,EpisodeSHA256:hex.EncodeToString(sum[:]),Delta:d,Before:before,After:after,TargetAbsError:math.Abs(after[e.TargetFeature]-e.TargetValue),ProtectedAbsDrift:math.Abs(after[e.ProtectedFeature]-before[e.ProtectedFeature]),Claim:"SYNTHETIC_LINEAR_ORACLE_ONLY_NOT_A_LEARNED_MODEL"},nil
}
