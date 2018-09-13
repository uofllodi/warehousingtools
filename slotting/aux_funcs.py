#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 17:38:50 2018

@author: luis2
"""

import scipy.stats.mvn as mvn
import numpy as np
from scipy.stats import norm
import math
from math import ceil
from scipy.optimize import bisect


def mvncdf(z, rho):
    n = len(z)
    low = np.ones(n) * -10
    mu = np.zeros(n)
    p, i = mvn.mvnun(low, z, mu, rho)
    return p


def mvngradient(z, R):
   L = len(z);
   g = np.zeros(L)
   for i in range(0,L):
       R_bar = calc_R_bar(R,i)
       z_bar = calc_z_bar(z, R, i)
       g[i]= mvncdf(z_bar, R_bar)*norm.pdf(z[i])
   return g


def calc_z_bar(z, R, i):
    s= R.shape[0]
    z_bar = np.zeros(s)
    for j in range(0,s):
       if j!=i:
         z_bar[j] = (z[j] - R[j,i]*z[i])/ math.sqrt(1-R[j,i]**2)
      
    z_bar = np.delete(z_bar,i)
    return z_bar


def calc_R_bar(R,i):
    # pdb.set_trace()
    s= R.shape[0]
    R_bar = np.zeros((s, s))

    for j in range(0, s):
      if j!= i:
        for k in range(0, s):
            if k!=i:
                num= (R[j, k] - R[j,i]*R[k,i])
                den= math.sqrt((1-R[j,i]**2) * (1-R[k,i]**2))
                R_bar[j,k] = num/den
                
    R_bar = np.delete(R_bar, i, axis=0)
    R_bar = np.delete(R_bar, i, axis=1)
    return R_bar  


def calc_pallet_positions(mus, sigmas, zs):
    cum_quantities= np.ceil(mus+ zs*sigmas)
    quants=-np.diff(cum_quantities)
    quants=np.append(quants, cum_quantities[-1])
    quants = quants.astype(int).clip(min=0)
    return quants
    

def calc_mvn_params(heights, hs, invs):
    invs_T = group_inventory_signals(heights, hs, invs)
    rho = np.corrcoef(invs_T)
    sigmas = np.array(np.std(invs_T,1)).flatten()
    mus = np.array(np.mean(invs_T,1)).flatten()
    return rho, mus, sigmas


def calc_serv(rho, mus, sigmas, N):
    #rho, mus, sigmas = calc_mvn_params(x, hs, invs)
    cum_quants = np.cumsum(N[::-1])[::-1]
    zs = np.divide(cum_quants - mus, sigmas)
    return mvncdf(zs,rho)


def one_slot(hs, invs, alpha, M):
    invs_T = np.sum(invs,0)
    mu= np.mean(invs_T)
    st= np.std(invs_T)
    z=norm.ppf(alpha)
    quants = ceil((mu+z*st)/M)
    heights= max(hs)
    fval = heights*quants
    return fval, heights, quants       

def penalty(zetha, rho, alpha):
    L=rho.shape[0]
    zethas= np.ones(L)*zetha
    z=mvncdf(zethas, rho) - alpha
    return z

def find_equal_thetas_solutions(rho, alpha):

    fun = lambda x: penalty(x, rho, alpha)
    min_z= norm.ppf(alpha)-0.1
    zetha = bisect(fun, min_z, 4)
    return zetha

def group_inventory_signals(heights, hs, invs):
    L=len(heights)
    invs_T=np.zeros((L,invs.shape[1]))
    invs_T[0,:]=np.sum(invs,0)
    for i in range(1,L):
        invs_T[i,:]=np.sum(invs[hs>heights[i-1],:],0)
    return invs_T

def min_map(func, iterable):
    min_x = []
    min_f = float("inf")
    for sol in iterable:
        f = func(sol)
        if f < min_f:
            min_f = f
            min_x = sol
    return list(min_x)
