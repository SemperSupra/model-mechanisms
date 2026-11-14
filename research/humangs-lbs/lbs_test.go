package lbsmath

import (
	"encoding/json"
	"fmt"
	"math"
	"testing"
)

func approx(t *testing.T,name string,got,want,tol float64) {
	t.Helper()
	if !isFinite(got)||math.Abs(got-want)>tol {
		t.Fatalf("%s got %.9g expected %.9g ± %.9g",name,got,want,tol)
	}
}
func isFinite(x float64) bool {return !math.IsNaN(x)&&!math.IsInf(x,0)}

func TestSingleJointIsRigid(t *testing.T) {
	a:=BlendRotations(1,Identity(),0,RotateZ(math.Pi/2))
	approx(t,"det",Determinant(a),1,1e-10)
	approx(t,"orthogonality",FrobeniusOrthogonalityError(a),0,1e-10)
}

func TestTwoJointQuarterTurnBlendIsNotSO3(t *testing.T) {
	// Mirrors HumanGS model/lbs.py's R_lbs = sum_j w_ij * R_j.
	// Equal-weight identity/90deg has R_lbs = sqrt(0.5)*R(45deg) in XY.
	a:=BlendRotations(.5,Identity(),.5,RotateZ(math.Pi/2))
	approx(t,"det blended",Determinant(a),0.5,1e-10)
	approx(t,"orthogonality residual",FrobeniusOrthogonalityError(a),math.Sqrt(.5),1e-10)
	// Converting this nonorthogonal affine matrix directly to a unit quaternion
	// cannot encode its 0.7071 in-plane contraction or shear.
	// This is a mathematical falsifier, NOT execution of pytorch3d matrix_to_quaternion.
	if math.Abs(Determinant(a)-1)<0.01 {t.Fatal("false rigid SO3 acceptance")}
}

func TestCovariancePropagationDiffersFromPureRotation(t *testing.T) {
	a:=BlendRotations(.5,Identity(),.5,RotateZ(math.Pi/2))
	cov:=Diagonal(.04,.01,.02)
	affine:=CovarianceFromAffine(a,cov)
	rot45:=RotateZ(math.Pi/4) // Polar rotation of equal 0deg+90deg in XY
	rigid:=CovarianceFromAffine(rot45,cov)
	approx(t,"affine covariance trace",Trace(affine),.045,1e-10)
	approx(t,"polar projected covariance trace",Trace(rigid),.07,1e-10)
	if math.Abs(Trace(affine)-Trace(rigid))<.01 {
		t.Fatal("affine and pure rotation were wrongly identified")
	}
	if Determinant(affine)<=0 {t.Fatal("expected SPD with nonsingular A")}
	value:=map[string]any{
		"source_mathematics":"source HumanGS model/lbs.py weighted LBS 3x3",
		"synthetic":"two-joint 0 and 90 degree rotations, equal weights",
		"det_A":Determinant(a),
		"orthogonality_fro_error":FrobeniusOrthogonalityError(a),
		"trace_cov_affine":Trace(affine),
		"trace_cov_rotation_only":Trace(rigid),
		"conclusion":"Weighted LBS rotation generally not SO(3), so direct quaternion projection may discard affine covariance deformation",
		"limitation":"No trained HumanGS, checkpoint, PyTorch3D or renderer executed",
	}
	j,err:=json.Marshal(value)
	if err!=nil {t.Fatal(err)}
	fmt.Printf("RECEIPT %s\n",j)
}

func TestOpposingJointBlendCanBecomeSingular(t *testing.T) {
	// 50/50 of 0deg and 180deg can collapse XY and lose invertibility.
	a:=BlendRotations(.5,Identity(),.5,RotateZ(math.Pi))
	if math.Abs(Determinant(a))>1e-12 {t.Fatal("expected singular blended affine transform")}
	cov:=CovarianceFromAffine(a,Diagonal(.04,.01,.02))
	if math.Abs(Determinant(cov))>1e-12 {t.Fatal("expected singular covariance")}
}
