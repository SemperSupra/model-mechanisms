package main

import (
  "encoding/json"
  "flag"
  "fmt"
  "os"
  admission "github.com/SemperSupra/model-mechanisms/core/operator-admission-go"
)

func main() {
 manifestPath:=flag.String("manifest","","source-safe operator manifest path")
 candidatePath:=flag.String("candidate","","source-safe candidate reference path")
 flag.Parse()
 if *manifestPath==""||*candidatePath==""{fmt.Fprintln(os.Stderr,"REJECT: manifest and candidate required");os.Exit(2)}
 mf,err:=os.Open(*manifestPath);if err!=nil{fmt.Fprintln(os.Stderr,"REJECT:",err);os.Exit(2)}
 defer mf.Close()
 cf,err:=os.Open(*candidatePath);if err!=nil{fmt.Fprintln(os.Stderr,"REJECT:",err);os.Exit(2)}
 defer cf.Close()
 var m admission.Manifest;var c admission.Candidate
 if err=admission.DecodeStrict(mf,&m);err!=nil{fmt.Fprintln(os.Stderr,"REJECT manifest:",err);os.Exit(2)}
 if err=admission.DecodeStrict(cf,&c);err!=nil{fmt.Fprintln(os.Stderr,"REJECT candidate:",err);os.Exit(2)}
 receipt,err:=admission.Plan(m,c);if err!=nil{fmt.Fprintln(os.Stderr,"REJECT:",err);os.Exit(2)}
 if err=json.NewEncoder(os.Stdout).Encode(receipt);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
 if receipt.Status=="REJECTED"{os.Exit(3)}
}
