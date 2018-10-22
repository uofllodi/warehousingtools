#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 23 12:22:58 2018

@author: luis2


class slot heights problem
class slot quantities problem

"""


from . import aux_funcs as af
from scipy.stats import norm
from numpy import linalg as LA
import numpy as np
from itertools import combinations
from itertools import product
import math
from scipy.optimize import minimize


class SlotHeights:
    def __init__(self, hs, invs, alpha, L, M):
        #heights must be sorted
        self.hs = hs
        self.invs = invs
        self.alpha = alpha
        self.n = L-1
        self.H = int(np.ceil(self.hs[-1]/2)*2)
        self.initial_bounds()
        self.ini = self.lb[0]
        self.end = self.ub[0]
        self.M = M

    def fitness(self, x):   
        # objective
        prob_qty = SlotQuantities(self.hs, self.invs, self.alpha, np.append(x, self.H), self.M)
        _, fval, _ = prob_qty.solve()
        f = [fval]
    
        #inequality constraints 
        for i in range(self.n-1):
            f.append(x[i] - x[i+1])
        return f
    
    def get_bounds(self):
        return self.lb, self.ub
    
    def initial_bounds(self):
        hs_u = np.ceil(self.hs/2)*2
        hs_u = np.unique(hs_u)
        ini = int(hs_u[1])
        end = int(hs_u[-2])
        self.lb = [ini]*(self.n)
        self.ub = [end]*(self.n)

    def get_nic(self):
        return self.n-1

    # Solution methods 
    def choose_range(self, ini=None, end=None):

        if ini is None:
            ini, end = self.ini, self.end

        # include only points where there are at least one pallet within the range
        # bounds are inclusive
        sol_range = np.arange(ini, end + 2, 2)
        counts, _ = np.histogram(self.hs + 0.001, bins=np.append(0, sol_range))
        sol_range = sol_range[counts > 0]
        return sol_range

    def exhaustive(self):
        sol_range = self.choose_range()
        sol_space = combinations(sol_range, r=self.n)
        func = lambda x: self.fitness(x)[0]

        min_x = []
        min_f = float("inf")
        for sol in sol_space:
            f = func(sol)
            if f < min_f:
                min_f = f
                min_x = sol
        return list(min_x)

    def format_solution(self, x):

        def format_heights(x, H):
            x = np.asarray(x, dtype=int)
            heights = np.array(np.ceil(x / 2) * 2, dtype=int)
            return np.append(heights, H)

        heights = format_heights(x, self.H)
        prob_qty = SlotQuantities(self.hs, self.invs, self.alpha, heights, self.M)
        quants, fval, serv = prob_qty.solve()
        return {'fval': fval, 'heights': [heights], 'quants': [quants], 'serv': serv}
    
    def solve(self, alg = "recursive_heights"):

        # Alg can be [exhaustive, nomad, recursive_heights, 
        #                recursive_heights_hybrid]

        def extend_level_exhaustive(prob, x):
            
            def feasible_solspace(prob, x, lb, ub):
                ranges = []
                ranges.append(prob.choose_range(math.floor(lb/2)*2,x[0]))
                for i in range(len(x)-1):
                    ranges.append(prob.choose_range(x[i],x[i+1]))
                ranges.append(prob.choose_range(x[-1],math.ceil(ub/2)*2))
                return ranges 
            
            # create solution space
            ranges = feasible_solspace(prob, x, prob.ini, prob.end)
        
            # find minimum element
            func = lambda x: prob.fitness(x)[0]
            min_x = af.min_map(func, product(*ranges))
            
            return min_x  
    
        def recursive_heights(prob):

            # initialize recursive fvals
            fval, _, _ = af.one_slot(prob.hs, prob.invs, prob.alpha, prob.M)
            fvals = [fval]

            L = prob.n + 1
            # solve for 2 slot heights problem
            prob.n = 1
            sol = prob.exhaustive()
            fvals.append(prob.fitness(sol)[0])

            # extend one level at the time based on previous solution
            for i in range(L-2):
                prob.n = i + 2
                sol = extend_level_exhaustive(prob, sol)
                fvals.append(prob.fitness(sol)[0])

            return sol, fvals
            

        if self.n == 0:
            _, sol, _ = af.one_slot(self.hs, self.invs, self.alpha, self.M)
        else:
            fvals = []
            if alg == "exhaustive":
                sol = self.exhaustive(self)
            elif alg == "recursive_heights":
                sol, fvals = recursive_heights(self)

        return self.format_solution(sol), fvals
        

# class slot quantities problem

class SlotQuantities:
    def __init__(self, hs, invs, alpha, heights, M):
        """ 
        inputs
            hs: 1D np-array (skus), pallet heights. It has to be sorted.
            invs: 2D np-array (skus, dates),  Inventory levels.
            alpha: scalar, desired service level
            heights: slot heights. It includes H.
            
        var: the z-vector to achieve alpha
          
        """ 
             
        self.hs = hs
        self.invs = invs
        self.alpha = alpha
        self.heights = heights
        self.L = len(heights)
        self.rho, self.mus, self.sigmas = af.calc_mvn_params(heights, hs,invs)
        self.coeff = self.coeff_obj()
        self.M = M
    
    def fitness(self, x):

        #obj
        d = self.coeff
        f = [np.dot(d, x)]

        # get number of pallet positions
        x = np.array(x)*self.M

        # inequality constraint - service level
        p = self.alpha - af.mvncdf(x, self.rho)
        f.append(p)
    
        return np.asarray(f)        
        
    def get_bounds(self):
        lb= norm.ppf(self.alpha)*np.ones(self.L)
        ub= 6*np.ones(self.L)
        return lb, ub
      
    def ini_sol(self):
        return np.ones(self.L)
    
    def get_nic(self):
        return 1

    def coeff_obj(self):
        b = np.insert(self.heights, 0, 0)
        co = np.diff(b)
        d = (self.sigmas * co)
        d = d / LA.norm(d)
        return d

    def solve(self, alg = "scipy"):
        # There two solution methods
        
        def format_solution(prob, zs):
            quants = np.array(np.ceil(af.calc_pallet_positions(prob.mus, prob.sigmas, zs)/prob.M), dtype=int)
            fval = np.dot(prob.heights, quants)
            serv = af.mvncdf(zs, prob.rho)
            return quants, fval, serv
            
        def solve_scipy(prob):
            x0 = prob.ini_sol()
            obj = lambda x: np.dot(prob.coeff, x) 
            
            def serv(x, rho, alpha):
                l=len(x)
                p=(alpha+0.0005*(1+2*(l**2)/10))-af.mvncdf(x,rho)
                return p

            cons_f = lambda x: - serv(x, prob.rho, prob.alpha)
            cons_j = lambda x: af.mvngradient(x,prob.rho)
            ineq_cons = {'type': 'ineq', 'fun': cons_f, 'jac': cons_j}
            res = minimize(obj, x0, method='COBYLA', constraints= [ineq_cons])
            return res.x
           
        if alg == "scipy":
            x = solve_scipy(self)
        
        return format_solution(self, x)
            

