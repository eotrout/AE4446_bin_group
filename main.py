# %% import labraries
import pickle
from gurobipy import *
import pandas as pd
import numpy as np


# %% Open pickle files
with open('data/R.pickle', 'rb') as handle:
    R_pickle = pickle.load(handle)

with open('data/B.pickle', 'rb') as handle:
    B_pickle = pickle.load(handle)


# %% Set model name
model = Model('2D Bin Packing Optimization')
b   
# %% ---- Sets ----
I = list(range(len(R_pickle)))
B = list(range(len(B_pickle)))


# %% ---- Parameters ----
nominal_length = [value[0] for key, value in R_pickle.items()]
nominal_width = [value[1] for key, value in R_pickle.items()]
rotatable = [value[2] for key, value in R_pickle.items()]
fragile = [value[3] for key, value in R_pickle.items()]
perishable = [value[4] for key, value in R_pickle.items()] 
radioactive = [value[5] for key, value in R_pickle.items()]

bin_type = [value[0] for key, value in B_pickle.items()]
bin_length = [value[1][0] for key, value in B_pickle.items()]
bin_height = [value[1][1] for key, value in B_pickle.items()]
bin_available = [value[1][2] for key, value in B_pickle.items()]
bin_cost = [value[1][3] for key, value in B_pickle.items()]
bin_slope = [value[1][4] for key, value in B_pickle.items()]
bin_intercept = [value[1][5] for key, value in B_pickle.items()]


# %% ---- Variables ----
x = {}
for i in N:
    for j in N:
        x[i,j] = model.addVar (vtype = GRB.BINARY, name = 'x[' + str(i) + ',' + str(j) + ']' )

t = {}
for n in N:
    t[n] = model.addVar (vtype = GRB.CONTINUOUS, name = 't[' + str(n) + ']')

l = {}
for j in N:
    l[j] = model.addVar (lb = 0,  vtype = GRB.CONTINUOUS, name = 'j[' + str(j) + ']')

u = {}
for i in N:
        u[i] = model.addVar (lb = 0, vtype = GRB.INTEGER, name = 'u[' + str(i) + ']' ) 


# %% ---- Integrate new variables ----
model.update()

# %% ---- Objective Function ----
model.setObjective (quicksum(c[i][j] * x[i,j] for i in N for j in N))
model.modelSense = GRB.MINIMIZE
model.update ()

# %% Constraints
# Constraint 1: Departure time node 1
con1 = {}
con1[0] = model.addConstr(t[0] == 0, 'con1[' + str(0) + ']-'    )



