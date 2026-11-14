// Package lbsmath contains tiny reference algebra for evaluating source-model
// linear blend skinning of anisotropic Gaussian primitives.
// No HumanGS source, data, checkpoint or third-party code is copied.
package lbsmath

import "math"

type Mat3 [3][3]float64

func Identity() Mat3 { return Mat3{{1,0,0},{0,1,0},{0,0,1}} }

func RotateZ(theta float64) Mat3 {
	c, s := math.Cos(theta), math.Sin(theta)
	return Mat3{{c,-s,0},{s,c,0},{0,0,1}}
}

func BlendRotations(w0 float64, a Mat3, w1 float64, b Mat3) Mat3 {
	var out Mat3
	for i:=0;i<3;i++ {
		for j:=0;j<3;j++ {
			out[i][j]=w0*a[i][j]+w1*b[i][j]
		}
	}
	return out
}

func Transpose(a Mat3) Mat3 {
	var t Mat3
	for i:=0;i<3;i++ {for j:=0;j<3;j++ {t[j][i]=a[i][j]}}
	return t
}

func Mul(a,b Mat3) Mat3 {
	var result Mat3
	for i:=0;i<3;i++ {for j:=0;j<3;j++ {for k:=0;k<3;k++ {result[i][j]+=a[i][k]*b[k][j]}}}
	return result
}

func Determinant(a Mat3) float64 {
	return a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1]) -
		a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0]) +
		a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0])
}

func FrobeniusOrthogonalityError(a Mat3) float64 {
	g:=Mul(Transpose(a),a)
	sum:=0.0
	for i:=0;i<3;i++ {for j:=0;j<3;j++ {
		expect:=0.0
		if i==j {expect=1.0}
		d:=g[i][j]-expect
		sum+=d*d
	}}
	return math.Sqrt(sum)
}

func CovarianceFromAffine(a,cov Mat3) Mat3 {
	return Mul(Mul(a,cov),Transpose(a))
}

func Diagonal(x,y,z float64) Mat3 {
	return Mat3{{x,0,0},{0,y,0},{0,0,z}}
}

func Trace(a Mat3) float64 { return a[0][0]+a[1][1]+a[2][2] }
