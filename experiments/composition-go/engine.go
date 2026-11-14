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

const (
	Schema             = "model-mechanisms.composition-fixture.v1"
	Namespace          = "toy_only"
	MaxConditionNumber = 1e7
)

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
 Namespace string `json:"namespace"`
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

// conditionNumber2x2 computes the scale-invariant L2 condition number (sigma_1 / sigma_2)
// of a 2x2 matrix without overflow or underflow.
func conditionNumber2x2(m Mat) (float64, bool) {
	a, b := m[0][0], m[0][1]
	c, d := m[1][0], m[1][1]
	scale := math.Max(math.Max(math.Abs(a), math.Abs(b)), math.Max(math.Abs(c), math.Abs(d)))
	if !finite(scale) || scale == 0 {
		return math.Inf(1), false
	}
	a, b, c, d = a/scale, b/scale, c/scale, d/scale
	p := a*a + c*c
	q := b*b + d*d
	r := a*b + c*d
	t := p + q
	disc := math.Sqrt(math.Max(0, (p-q)*(p-q)+4*r*r))
	s1Sq := 0.5 * (t + disc)
	s2Sq := 0.5 * math.Max(0, t-disc)
	if s2Sq <= 0 || !finite(s1Sq) || !finite(s2Sq) {
		return math.Inf(1), false
	}
	cond := math.Sqrt(s1Sq / s2Sq)
	return cond, finite(cond)
}

func (e Episode) Validate() error {
 if e.ID == "" || e.Seed < 0 || e.TargetFeature < 0 || e.TargetFeature > 1 || e.ProtectedFeature < 0 || e.ProtectedFeature > 1 || e.TargetFeature == e.ProtectedFeature { return errors.New("INVALID_EPISODE_ID_OR_FEATURE") }
 if !finite(e.TargetValue) || !finite(e.MaxAbsDelta) || e.MaxAbsDelta <= 0 || e.MaxAbsDelta > 10 { return errors.New("INVALID_TARGET_OR_DELTA_BUDGET") }
 for _, v := range e.Base { if !finite(v) { return errors.New("NONFINITE_BASE") } }
 for _, row := range e.Forward { for _, v := range row { if !finite(v) { return errors.New("NONFINITE_FORWARD") } } }
 cond, ok := conditionNumber2x2(e.Forward)
 if !ok || cond > MaxConditionNumber { return errors.New("ILL_CONDITIONED_SYNTHETIC_FORWARD") }
 return nil
}
func (e Episode) Observe(x Vec) Vec {
 return Vec{e.Forward[0][0]*x[0]+e.Forward[0][1]*x[1], e.Forward[1][0]*x[0]+e.Forward[1][1]*x[1]}
}

func Propose(e Episode, treatment string)(Vec,error) {
 if err:=e.Validate();err!=nil { return Vec{},err }
 y:=e.Observe(e.Base)
 for _,v:=range y { if !finite(v) { return Vec{},errors.New("NONFINITE_OBSERVATION") } }
 errTarget:=e.TargetValue-y[e.TargetFeature]
 i,j:=e.TargetFeature,e.ProtectedFeature
 if !finite(errTarget) { return Vec{},errors.New("NONFINITE_TARGET_ERROR") }
 scale := math.Max(math.Max(math.Abs(e.Forward[0][0]), math.Abs(e.Forward[0][1])), math.Max(math.Abs(e.Forward[1][0]), math.Abs(e.Forward[1][1])))
 switch treatment {
 case "T0-untreated": return Vec{},nil
 case "T1-direct":
   slope:=e.Forward[i][i];if math.Abs(slope)<=1e-12*scale{return Vec{},errors.New("ZERO_DIRECT_SLOPE")}
   var d Vec;d[i]=errTarget/slope;return d,nil
 case "T2-constrained":
   // Satisfy target while preserving the independent protected observable.
   // Solve 2x2 system M*d=[desired target correction, 0] in measured space (scale-normalized).
   a,b:=e.Forward[i][i]/scale,e.Forward[i][j]/scale
   c,d:=e.Forward[j][i]/scale,e.Forward[j][j]/scale
   det:=a*d-b*c
   if !finite(det) || math.Abs(det)==0{return Vec{},errors.New("ZERO_SUBSYSTEM_DETERMINANT")}
   rhs := errTarget / scale
   var v Vec;v[i]=rhs*d/det;v[j]=-rhs*c/det;return v,nil
 case "Tneg-equal-norm-shuffle":
   slope:=e.Forward[i][i];if math.Abs(slope)<=1e-12*scale{return Vec{},errors.New("ZERO_DIRECT_SLOPE")}
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
 for _,v:=range before{if !finite(v){return zero,errors.New("NONFINITE_BEFORE_OBSERVATION")}}
 for _,v:=range after{if !finite(v){return zero,errors.New("NONFINITE_OBSERVATION")}}
 targetErr:=math.Abs(after[e.TargetFeature]-e.TargetValue)
 protDrift:=math.Abs(after[e.ProtectedFeature]-before[e.ProtectedFeature])
 if !finite(targetErr)||!finite(protDrift){return zero,errors.New("NONFINITE_RECEIPT_METRIC")}
 return Receipt{Schema:Schema,Namespace:Namespace,EpisodeID:e.ID,Seed:e.Seed,Treatment:treatment,EpisodeSHA256:hex.EncodeToString(sum[:]),Delta:d,Before:before,After:after,TargetAbsError:targetErr,ProtectedAbsDrift:protDrift,Claim:"SYNTHETIC_LINEAR_ORACLE_ONLY_NOT_A_LEARNED_MODEL"},nil
}

// ToB1DOECell adapts a toy_only synthetic Receipt into a B1 schema_version=1 DOE cell record.
func ToB1DOECell(e Episode, r Receipt, cellID, hypothesisID, sourceRevision string) map[string]any {
	tKind := "deterministic-generator"
	if r.Treatment == "T0-untreated" {
		tKind = "none"
	}
	return map[string]any{
		"schema_version":  1,
		"campaign_id":     "comp001-toy-composition-smoke",
		"design_id":       "comp001-2x2-linear-oracle",
		"cell_id":         cellID,
		"rep_id":          e.Seed,
		"phase":           "smoke",
		"hypothesis_id":   hypothesisID,
		"primary_outcome": "target_abs_error_and_protected_abs_drift",
		"method": map[string]any{
			"family":          "other",
			"implementation":  "toy_only_composition_linear_oracle",
			"source_revision": sourceRevision,
		},
		"treatment": map[string]any{
			"kind": tKind,
			"factors": map[string]any{
				"treatment":           r.Treatment,
				"namespace":           r.Namespace,
				"claim":               r.Claim,
				"max_abs_delta":       e.MaxAbsDelta,
				"target_abs_error":    r.TargetAbsError,
				"protected_abs_drift": r.ProtectedAbsDrift,
			},
			"intervention_ref": r.Treatment,
		},
		"control": map[string]any{
			"comparator_cell_id": "cell-t0-untreated",
			"compute_match_basis": "matched-2x2-episode-sha256",
		},
		"workload": map[string]any{
			"suite":       "toy-only-2x2-linear-oracle",
			"split":       "synthetic",
			"dataset_ref": "sha256:" + r.EpisodeSHA256,
		},
		"execution": map[string]any{
			"seed":            e.Seed,
			"environment_ref": "go-1.24-cpu",
			"resource_class":  "cpu",
		},
		"provenance": map[string]any{
			"repository":      "SemperSupra/model-mechanisms",
			"source_revision": sourceRevision,
		},
	}
}
