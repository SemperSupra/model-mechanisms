// Package admission checks the syntactic compatibility of a proposed model-on-
// model correction. It never executes a model or grants rights/compute admission.
package admission

import (
  "bytes"
  "crypto/sha256"
  "encoding/hex"
  "encoding/json"
  "errors"
  "fmt"
  "io"
  "math"
  "strings"
)

const (
 Schema = "model-mechanisms.operator-manifest.v1"
 CandidateSchema = "model-mechanisms.candidate-ref.v1"
 ReceiptSchema = "model-mechanisms.compatibility-receipt.v1"
 MaxJSONBytes = 1 << 20
)

type ModelRef struct {
 Backend string `json:"backend"`
 Revision string `json:"revision"`
 WeightsSHA256 string `json:"weights_sha256"`
 ArchitectureSHA256 string `json:"architecture_sha256,omitempty"`
}

type Representation struct {
 Kind string `json:"kind"`
 ParameterSpace string `json:"parameter_space,omitempty"`
 Dimension int `json:"dimension,omitempty"`
 TopologySHA256 string `json:"topology_sha256,omitempty"`
 RigSHA256 string `json:"rig_sha256,omitempty"`
 Units string `json:"units"`
 Frame string `json:"frame"`
 Timebase string `json:"timebase,omitempty"`
}

type Resources struct {
 MaxWallSeconds int `json:"max_wall_seconds"`
 MaxMemoryMiB int `json:"max_memory_mib"`
 MaxGPUMiB int `json:"max_gpu_mib"`
 AllowNetwork bool `json:"allow_network"`
 AllowPaid bool `json:"allow_paid"`
}

type Manifest struct {
 Schema string `json:"schema"`
 OperatorID string `json:"operator_id"`
 Revision string `json:"revision"`
 Kind string `json:"kind"`
 Model ModelRef `json:"model"`
 Input Representation `json:"input"`
 AllowedScopes []string `json:"allowed_scopes"`
 ProtectedFields []string `json:"protected_fields"`
 DeltaUnit string `json:"delta_unit"`
 MaxAbsDelta float64 `json:"max_abs_delta"`
 SourceClass string `json:"source_class"`
 SourceAdmissionID string `json:"source_admission_id"`
 Resources Resources `json:"resources"`
}

type Candidate struct {
 Schema string `json:"schema"`
 CandidateID string `json:"candidate_id"`
 Model ModelRef `json:"model"`
 State Representation `json:"state"`
 SourceClass string `json:"source_class"`
 SourceAdmissionID string `json:"source_admission_id"`
}

type Receipt struct {
 Schema string `json:"schema"`
 ManifestSHA256 string `json:"manifest_sha256"`
 CandidateSHA256 string `json:"candidate_sha256"`
 OperatorID string `json:"operator_id"`
 CandidateID string `json:"candidate_id"`
 Status string `json:"status"`
 Reasons []string `json:"reasons"`
 Claim string `json:"claim"`
}

func validSHA(s string) bool {
 if len(s)!=64 {return false}
 _,err:=hex.DecodeString(s)
 return err==nil && strings.ToLower(s)==s
}

func validModel(m ModelRef) error {
 if m.Backend=="" || m.Revision=="" || !validSHA(m.WeightsSHA256) {return errors.New("INVALID_EXACT_MODEL_REF")}
 if m.ArchitectureSHA256!=""&&!validSHA(m.ArchitectureSHA256){return errors.New("INVALID_ARCHITECTURE_HASH")}
 return nil
}

func validSource(class,id string)error {
 if class!="public_synthetic" && class!="private_admitted"{return errors.New("UNKNOWN_SOURCE_CLASS")}
 if strings.TrimSpace(id)=="" {return errors.New("MISSING_SOURCE_ADMISSION_REF")}
 return nil
}

func validRepresentation(s Representation)error {
 if s.Frame=="" {return errors.New("MISSING_COORDINATE_FRAME")}
 switch s.Units {case "m","rad","unitless":default:return errors.New("UNKNOWN_UNIT")}
 switch s.Kind {
 case "latent_vector","activation":
  if s.ParameterSpace==""||s.Dimension<=0||s.Dimension>1000000 {return errors.New("INVALID_VECTOR_SPACE")}
  if s.TopologySHA256!=""||s.RigSHA256!=""||s.Timebase!="" {return errors.New("UNEXPECTED_VECTOR_GEOMETRY_FIELDS")}
 case "mesh":
  if !validSHA(s.TopologySHA256)||s.Units!="m" {return errors.New("INVALID_MESH_TOPOLOGY_OR_UNIT")}
  if s.Dimension!=0||s.ParameterSpace!=""||s.Timebase!="" {return errors.New("INVALID_MESH_EXTRA_FIELDS")}
 case "pose_stream":
  if !validSHA(s.RigSHA256)||s.Timebase==""||s.Units!="rad" {return errors.New("INVALID_RIG_TIMEBASE_OR_ANGLE_UNIT")}
  if s.ParameterSpace!=""||s.Dimension!=0||s.TopologySHA256!=""{return errors.New("INVALID_POSE_EXTRA_FIELDS")}
 case "weights":
  if s.ParameterSpace==""||s.Dimension<=0||s.Dimension>1000000 {return errors.New("INVALID_WEIGHT_SPACE")}
  if s.TopologySHA256!=""||s.RigSHA256!=""||s.Timebase!=""{return errors.New("INVALID_WEIGHT_GEOMETRY_FIELDS")}
 default: return errors.New("UNKNOWN_REPRESENTATION")
 }
 return nil
}

func uniqueScopes(values []string)error {
 if len(values)==0{return errors.New("MISSING_SCOPES")}
 seen:=map[string]bool{}
 for _,x:=range values {if x==""||seen[x] {return errors.New("BLANK_OR_DUPLICATE_SCOPE")};seen[x]=true}
 return nil
}

func (m Manifest) Validate()error {
 if m.Schema!=Schema||m.OperatorID==""||m.Revision==""{return errors.New("INVALID_MANIFEST_HEADER")}
 if err:=validModel(m.Model);err!=nil{return err}
 if err:=validRepresentation(m.Input);err!=nil{return err}
 if err:=validSource(m.SourceClass,m.SourceAdmissionID);err!=nil{return err}
 if err:=uniqueScopes(m.AllowedScopes);err!=nil{return err}
 if err:=uniqueScopes(m.ProtectedFields);err!=nil{return err}
 protected:=map[string]bool{}
 for _,p:=range m.ProtectedFields{protected[p]=true}
 for _,p:=range []string{"canonical_authority","source_provenance","persistent_identity"}{if !protected[p]{return fmt.Errorf("UNPROTECTED_INVARIANT:%s",p)}}
 for _,s:=range m.AllowedScopes{if protected[s]{return errors.New("SCOPE_PROTECTION_CONFLICT")}}
 if m.DeltaUnit==""||!isDeltaUnit(m.DeltaUnit)||math.IsNaN(m.MaxAbsDelta)||math.IsInf(m.MaxAbsDelta,0)||m.MaxAbsDelta<=0||m.MaxAbsDelta>100{return errors.New("INVALID_DELTA_BUDGET")}
 r:=m.Resources
 if r.MaxWallSeconds<=0||r.MaxWallSeconds>3600||r.MaxMemoryMiB<64||r.MaxMemoryMiB>262144||r.MaxGPUMiB<0||r.MaxGPUMiB>262144||r.AllowNetwork||r.AllowPaid{return errors.New("RESOURCE_POLICY_REJECTED")}
 allowedKind:=map[string]string{"parameter_delta":"latent_vector","geometry_residual":"mesh","motion_corrector":"pose_stream","activation_bridge":"activation","weight_adapter":"weights"}
 kind,ok:=allowedKind[m.Kind];if !ok||m.Input.Kind!=kind{return errors.New("OPERATOR_REPRESENTATION_MISMATCH")}
 if (m.Kind=="weight_adapter"||m.Kind=="activation_bridge")&&m.Model.ArchitectureSHA256=="" {return errors.New("MISSING_COMPATIBLE_ARCHITECTURE_DIGEST")}
 if m.Kind=="geometry_residual"&&m.DeltaUnit!="m"{return errors.New("MESH_DELTA_NOT_METRES")}
 if m.Kind=="motion_corrector"&&m.DeltaUnit!="rad"{return errors.New("MOTION_DELTA_NOT_RADIANS")}
 return nil
}

func isDeltaUnit(u string)bool{return u=="normalized"||u=="m"||u=="rad"}

func (c Candidate) Validate()error {
 if c.Schema!=CandidateSchema||c.CandidateID==""{return errors.New("INVALID_CANDIDATE_HEADER")}
 if err:=validModel(c.Model);err!=nil{return err}
 if err:=validRepresentation(c.State);err!=nil{return err}
 return validSource(c.SourceClass,c.SourceAdmissionID)
}

func Plan(m Manifest,c Candidate)(Receipt,error) {
 receipt:=Receipt{Schema:ReceiptSchema,OperatorID:m.OperatorID,CandidateID:c.CandidateID,Status:"REJECTED",Reasons:[]string{},Claim:"COMPATIBILITY_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"}
 if err:=m.Validate();err!=nil{return receipt,fmt.Errorf("INVALID_MANIFEST: %w",err)}
 if err:=c.Validate();err!=nil{return receipt,fmt.Errorf("INVALID_CANDIDATE: %w",err)}
 mb,_:=json.Marshal(m);cb,_:=json.Marshal(c);mh,ch:=sha256.Sum256(mb),sha256.Sum256(cb)
 receipt.ManifestSHA256=hex.EncodeToString(mh[:]);receipt.CandidateSHA256=hex.EncodeToString(ch[:])
 reason:=func(ok bool,msg string){if !ok{receipt.Reasons=append(receipt.Reasons,msg)}}
 reason(m.Model==c.Model,"MODEL_OR_ARCHITECTURE_MISMATCH")
 reason(m.Input==c.State,"REPRESENTATION_RIG_TOPOLOGY_UNITS_OR_TIMEBASE_MISMATCH")
 reason(m.SourceClass==c.SourceClass && m.SourceAdmissionID==c.SourceAdmissionID,"SOURCE_ADMISSION_SCOPE_MISMATCH")
 if len(receipt.Reasons)==0{receipt.Status="COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION"}
 return receipt,nil
}

// scanValue reads one JSON value recursively and rejects duplicate object keys.
// The depth limit bounds adversarial nesting without relying on json.Unmarshal.
func scanValue(d *json.Decoder, depth int)error {
 if depth>64{return errors.New("JSON_MAX_DEPTH_EXCEEDED")}
 token,err:=d.Token();if err!=nil{return err}
 delim,ok:=token.(json.Delim)
 if !ok{return nil}
 switch delim{
 case '{':
  keys:=map[string]bool{}
  for d.More(){
   k,err:=d.Token();if err!=nil{return err}
   s,ok:=k.(string);if !ok{return errors.New("JSON_OBJECT_KEY_REQUIRED")}
   if keys[s]{return fmt.Errorf("DUPLICATE_JSON_KEY:%s",s)}
   keys[s]=true
   if err:=scanValue(d,depth+1);err!=nil{return err}
  }
  end,err:=d.Token();if err!=nil{return err};if end!=json.Delim('}') {return errors.New("JSON_OBJECT_NOT_CLOSED")}
 case '[':
  for d.More(){if err:=scanValue(d,depth+1);err!=nil{return err}}
  end,err:=d.Token();if err!=nil{return err};if end!=json.Delim(']'){return errors.New("JSON_ARRAY_NOT_CLOSED")}
 default: return errors.New("UNEXPECTED_JSON_DELIMITER")
 }
 return nil
}

func DecodeStrict(r io.Reader,v any)error {
 b,err:=io.ReadAll(io.LimitReader(r,MaxJSONBytes+1));if err!=nil{return err}
 if len(b)>MaxJSONBytes{return errors.New("JSON_TOO_LARGE")}
 d:=json.NewDecoder(bytes.NewReader(b));if err:=scanValue(d,0);err!=nil{return err}
 var trailing any
 if err:=d.Decode(&trailing);err!=io.EOF{
  if err==nil{return errors.New("TRAILING_JSON_VALUE")}
  return fmt.Errorf("TRAILING_JSON_DATA:%w",err)
 }
 d=json.NewDecoder(bytes.NewReader(b));d.DisallowUnknownFields()
 if err:=d.Decode(v);err!=nil{return err}
 return nil
}
