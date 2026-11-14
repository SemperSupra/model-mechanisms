package main
import (
 "encoding/json"
 "log"
 "os"
 composition "github.com/SemperSupra/model-mechanisms/experiments/composition-go"
)
func main(){e:=composition.Episode{ID:"public-synthetic-fixture",Seed:17,Base:composition.Vec{0,0},Forward:composition.Mat{{1,.25},{.2,1}},TargetFeature:0,ProtectedFeature:1,TargetValue:1,MaxAbsDelta:2};out:=struct{Status string `json:"status"`;Receipts []composition.Receipt `json:"receipts"`}{Status:"SYNTHETIC_CONTRACT_SMOKE_ONLY",Receipts:[]composition.Receipt{}};for _,m:=range []string{"T0-untreated","T1-direct","T2-constrained","Tneg-equal-norm-shuffle"}{r,err:=composition.Execute(e,m);if err!=nil{log.Fatal(err)};out.Receipts=append(out.Receipts,r)};enc:=json.NewEncoder(os.Stdout);enc.SetIndent("","  ");if err:=enc.Encode(out);err!=nil{log.Fatal(err)}}
