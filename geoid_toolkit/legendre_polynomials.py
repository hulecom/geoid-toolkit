#!/usr/bin/env python
u"""
legendre_polynomials.py
Written by Tyler Sutterley (07/2017)

Computes fully normalized Legendre polynomials for an array of x values
	and their first derivative

CALLING SEQUENCE:
	Pl,dPl = legendre_polynomials(lmax, np.cos(theta))

INPUTS:
	lmax: maximum degree of spherical harmonics
	x: cos(theta)
OUTPUT:
	pl: legendre polynomials (geodesy normalization)
	dpl: first derivative of legendre polynomials

OPTIONS:
	ASTYPE: output variable type (e.g. np.float128).  Default is np.float64

NOTES:
	ptemp is a dummy array of length (0:lmax) storing unnormalized pls

PYTHON DEPENDENCIES:
	numpy: Scientific Computing Tools For Python
		http://www.numpy.org
		http://www.scipy.org/NumPy_for_Matlab_Users

REFERENCE:
	Hofmann-Wellenhof and Moritz, "Physical Geodesy" (2005)
		http://www.springerlink.com/content/978-3-211-33544-4

UPDATE HISTORY:
	Updated 07/2017: added first derivative of Legendre polynomials (dpl)
		added option ASTYPE to output as different variable types e.g. np.float
	Written 03/2013
"""
import numpy as np

def legendre_polynomials(lmax,x,ASTYPE=np.float):
	#-- size of the x array
	dimx = np.ndim(x)
	if (dimx > 0):
		nx = np.shape(x)[0]
	else:
		nx = 1
	lmax = np.int(lmax)
	#-- output matrix of normalized legendre polynomials
	pl = np.zeros((lmax+1,nx),dtype=ASTYPE)
	#-- dummy matrix for the recurrence relation
	ptemp = np.zeros((lmax+1,nx),dtype=ASTYPE)

	#-- Initialize the recurrence relation
	ptemp[0,:] = 1.0
	ptemp[1,:] = x
	#-- Normalization is geodesy convention
	pl[0,:] = ptemp[0,:]
	pl[1,:] = np.sqrt(3.0)*ptemp[1,:]
	for l in range(2,lmax+1):
		ptemp[l,:] = (((2.0*l)-1.0)/l)*x*ptemp[l-1,:] - ((l-1.0)/l)*ptemp[l-2,:]
		#-- Normalization is geodesy convention
		pl[l,:] = np.sqrt((2.0*l)+1.0)*ptemp[l,:]

	#-- First derivative of Legendre polynomials
	dpl = np.zeros((lmax+1,nx),dtype=ASTYPE)
	for l in range(1,lmax+1):
		fl = np.sqrt(((l**2.0) * (2.0*l + 1.0)) / (2.0*l - 1.0))
		dpl[l,:] = (1.0/np.sqrt(1.0 - x**2))*(l*x*pl[l,:] - fl*pl[l-1,:])

	#-- return the legendre polynomials and their first derivative
	return (pl, dpl)
