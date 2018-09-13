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
import nlopt
from itertools import combinations
from itertools import product
import math
import PyNomad


class SlotHeights:
    def __init__(self, hs, invs, alpha, L, M):
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

    
    def solve(self, alg = "recursive_heights"):

        # Alg can be [exhaustive, nomad, recursive_heights, 
        #                recursive_heights_hybrid]
        
        def format_solution(prob, x):
            
            def format_heights(x, H):
                x = np.asarray(x, dtype=int)
                heights = np.array(np.ceil(x/2)*2, dtype=int)
                return np.append(heights, H)
            
            heights = format_heights(x, prob.H)
            prob_qty = SlotQuantities(prob.hs, prob.invs, prob.alpha, heights, prob.M)
            quants, fval, serv = prob_qty.solve()
            return {'fval': fval, 'heights': [heights], 'quants': [quants], 'serv': serv}
    
        def choose_range(prob, ini=None, end=None):
            
            if ini is None:
                ini, end = prob.ini, prob.end
                
            # include only points where there are at least one pallet within the range
            #bounds are inclusive 
            sol_range = np.arange(ini, end+2, 2)
            counts, _ = np.histogram(prob.hs+0.001, bins=np.append(0, sol_range))
            sol_range = sol_range[counts > 0]
            return sol_range
    
        def exhaustive(prob):      
            sol_range = choose_range(prob)
            sol_space = combinations(sol_range, r=prob.n)
            func = lambda x: prob.fitness(x)[0]
            min_x = af.min_map(func, sol_space)
            return min_x
        
        def extend_level_exhaustive(prob, x):
            
            def feasible_solspace(prob, x, lb, ub):
                ranges = []
                ranges.append(choose_range(prob, math.floor(lb/2)*2,x[0]))
                for i in range(len(x)-1):
                    ranges.append(choose_range(prob, x[i],x[i+1]))
                ranges.append(choose_range(prob, x[-1],math.ceil(ub/2)*2))
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
            sol = exhaustive(prob)
            fvals.append(prob.fitness(sol)[0])

            # extend one level at the time based on previous solution
            for i in range(L-2):
                prob.n = i + 2
                sol = extend_level_exhaustive(prob, sol)
                fvals.append(prob.fitness(sol)[0])

            return sol, fvals
       
        def nomad(prob, x0=None):
            def ini_sol(prob):
                if prob.n>0:
                    x0=np.linspace(prob.ini, prob.end, prob.n+2)
                    x0=x0[1:-1]
                    x0=list(np.ceil(x0/2)*2)
                    return x0
                else:     
                    hs_u = np.unique(prob.hs)
                    return hs_u[-1]
                
            if x0 is None:
                x0 = ini_sol(prob) 
                
            def bb(x,prob):
                fun = lambda x: prob.fitness(x)
                dim = x.get_n()
                y=[x.get_coord(i) for i in range(dim)]
                f = fun(y)
                for i in range(len(f)):
                    x.set_bb_output(i, float(f[i]))
                return 1 # 1: success 0: failed evaluation
            
            ff = lambda x: bb(x,prob)   # objective function 
            lb, ub = prob.get_bounds()  # bounds
    
            #contraint string parameter for nomad
            if prob.n==1:
                out = 'BB_OUTPUT_TYPE OBJ'
            else:    
                out = 'BB_OUTPUT_TYPE OBJ ' + (prob.n-1)*'EB '
            params = [out,'MAX_TIME 1000', 'EPSILON 1E-14', 'INITIAL_POLL_SIZE 20'] 
            
            # execute solver
            sol = PyNomad.optimize(ff,x0,lb,ub,params)
            
            return sol[0] 
            
        def extend_level_nomad(prob, x):
            prob.lb = np.append(prob.ini, x)
            prob.ub = np.append(x, prob.end)
            sol = nomad(prob)
            prob.initial_bounds()
            return sol
        
        def recursive_heights_hybrid(prob):

            L = prob.n + 1    
            lim = 3
            if L <= lim:
                return recursive_heights(prob)    
            else:
                prob.n = lim - 1 
                sol, fvals = recursive_heights(prob)
                for i in range(L-lim):
                    prob.n = i + lim
                    sol = extend_level_nomad(prob, sol)
                    fvals.append(prob.fitness(sol)[0])
                return sol, fvals

        if self.n == 0:
            _, sol, _ = af.one_slot(self.hs, self.invs, self.alpha, self.M)
        else:
            fvals = []
            if alg == "exhaustive":
                sol = exhaustive(self)
            elif alg == "recursive_heights":
                sol, fvals = recursive_heights(self)
            elif alg == "nomad":
                sol = nomad(self)
            elif alg == "recursive_heights_hybrid": 
                sol, fvals = recursive_heights_hybrid(self)

        return format_solution(self, sol), fvals
        

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
        return af.find_equal_thetas_solutions(self.rho, self.alpha)*np.ones(self.L)
    
    def get_nic(self):
        return 1

    def coeff_obj(self):
        b = np.insert(self.heights, 0, 0)
        co = np.diff(b)
        d = (self.sigmas * co)
        d = d / LA.norm(d)
        return d

    def solve(self, alg = "nlopt"):
        # There two solution methods
        # nlopt, pygmo
        
        
        def format_solution(prob, zs):
            quants = np.array(np.ceil(af.calc_pallet_positions(prob.mus, prob.sigmas, zs)/prob.M), dtype=int)
            fval = np.dot(prob.heights, quants)
            serv = af.mvncdf(zs, prob.rho)
            return quants, fval, serv
    
        def solve_nlop_direct(prob):
            
            def myfunc(x, grad, d):
                if grad.size > 0:
                    grad = d
                return np.dot(d, x)
        
            def myconstraint(x, grad, rho, alpha):
                l=len(x)
                if grad.size > 0:
                    grad = - af.mvngradient(x,rho)
                p=(alpha+0.0005*(1+2*(l**2)/10))-af.mvncdf(x,rho)
                return p
        
            # get parameters
            lb, ub = prob.get_bounds()
            d = prob.coeff
            x0 = prob.ini_sol()
            
            #set nlopt solver
            opt = nlopt.opt(nlopt.LN_COBYLA, prob.L)
            opt.set_lower_bounds(lb)
            opt.set_upper_bounds(ub)
            opt.set_min_objective(lambda x, grad: myfunc(x, grad, d))
            opt.add_inequality_constraint(lambda x,grad: myconstraint(x,grad,prob.rho,prob.alpha), 1e-4)
            opt.set_xtol_rel(1e-4)
            opt.set_maxtime(5)
            
            #execute solver
            x = opt.optimize(x0)
            return x

        """ 
        def solve_pygmo(prob):
            prob = pg.problem(prob)
            nl = pg.nlopt('cobyla')
            algo = pg.algorithm(nl)
            pop = pg.population(prob,10)
            x0 = prob.ini_sol() 
            pop.set_x(0, x0)
            pop = algo.evolve(pop)
            return pop.champion_x """
            
        if alg == "nlopt":
            x = solve_nlop_direct(self)
        """ elif alg == "pg":
            x = solve_pygmo(self) """
        
        return format_solution(self, x)
            

