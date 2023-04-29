# %% import labraries
import pickle
from gurobipy import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# %% Open pickle files
with open('data/R.pickle', 'rb') as handle:
    R_pickle = pickle.load(handle)

with open('data/B.pickle', 'rb') as handle:
    B_pickle = pickle.load(handle)


# %% Set model name
model = Model('2D Bin Packing Optimization')

# %% ---- Sets ----
I = list(range(len(R_pickle)))
#I = list(range(12))
B = list(range(len(B_pickle)))
#B = list(range(1))

# %% ---- Parameters ----
item_length = [value[0] for key, value in R_pickle.items()]
item_height = [value[1] for key, value in R_pickle.items()]
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


# big M
M = 100000

# %% ---- Variables ----
# p_{ib} variable, 1 if box i is in container b, 0 otherwise
p = {}
for i in I:
    for b in B:
        p[i,b] = model.addVar (vtype = GRB.BINARY, name = 'p[' + str(i) + ',' + str(b) + ']' )

# z_{b} variable, 1 if container b is used, 0 otherwise
z = {}
for b in B:
    z[b] = model.addVar(vtype = GRB.BINARY, name = 'z[' + str(b) + ']' )

# l_{ij} variable, 1 if item i is to the left of item j, 0 otherwise
l = {}
for i in I:
    for j in I:
        l[i,j] = model.addVar(vtype = GRB.BINARY, name = 'l[' + str(i) + ',' + str(j) + ']' )

# u_{ij} variable, 1 if item i is under item j, 0 otherwise
u = {}
for i in I:
    for j in I:
        u[i,j] = model.addVar(vtype = GRB.BINARY, name = 'u[' + str(i) + ',' + str(j) + ']' )

# r_{i, L^, L} variable, 1 if the original item i is aligned with the length side of the bin
r = {}
for i in I:
    r[i] = model.addVar(vtype = GRB.BINARY, name = 'r[' + str(i) + ']' )

# x_{i} variable, x coordiante of lower_left corner of item i, with respect to origin of bin b
x = {}
for i in I:
    x[i] = model.addVar(vtype = GRB.INTEGER, name = 'x[' + str(i) + ']' )

x2 = {}
for i in I:
    x2[i] = model.addVar(vtype = GRB.INTEGER, name = 'x2[' + str(i) + ']' )

# y_{i} variable, y coordiante of lower_left corner of item i, with respect to origin of bin b
y = {}
for i in I:
    y[i] = model.addVar(vtype = GRB.INTEGER, name = 'y[' + str(i) + ']'  )

y2 = {}
for i in I:
    y2[i] = model.addVar(vtype = GRB.INTEGER, name = 'y2[' + str(i) + ']'  )


# g_{i} variable, 1 if item i lies on the ground of the bin it is assigned to
g = {}
for i in I:
    g[i] = model.addVar(vtype = GRB.BINARY, name = 'g[' + str(i) + ']')

# per_i variable, mark bin b as perishable as soon as perisbale item is in the bin
per = {}
for b in B:
    per[b] = model.addVar(vtype = GRB.BINARY, name = 'per[' + str(b) + ']' )

# rad_i variable, mark bin b as radioactive as soon as radioactive item is in the bin
rad = {}
for b in B:
    rad[ b] = model.addVar(vtype = GRB.BINARY, name = 'rad[' + str(b) + ']' )

# h i,j variable, if j has a suitable height to support i
h = {}
for i in I:
    for j in I:
        h[i,j] = model.addVar(vtype = GRB.BINARY,  name = 'h[' + str(i) + ',' + str(j) + ']' )

# o i,j variable, non empty intersection
o = {}
for i in I:
    for j in I:
        o[i,j] = model.addVar(vtype = GRB.BINARY,  name = 'o[' + str(i) + ',' + str(j) + ']' )

# s i,j 
s = {}
for i in I:
    for j in I:
        s[i,j] = model.addVar(vtype = GRB.BINARY,  name = 's[' + str(i) + ',' + str(j) + ']' )          

# n1 i,j variable xj smaller than xi
n1 = {}
for i in I:
    for j in I:
        n1[i,j] = model.addVar(vtype = GRB.BINARY,  name = 'n1[' + str(i) + ',' + str(j) + ']' )        

# n2 i,j variable xj smaller than xi
n2 = {}
for i in I:
    for j in I:
        n2[i,j] = model.addVar(vtype = GRB.BINARY,  name = 'n2[' + str(i) + ',' + str(j) + ']' )        

# b^{1}_{i,j} variable, 1 if vertex 1 of item i is supported by item j
b1 = {}
for i in I:
    for j in I:
        b1[i,j] = model.addVar(vtype = GRB.BINARY, name = 'b1[' + str(i) + ',' + str(j) + ']' ) 

# b^{2}_{i,j} variable, 1 if vertex 1 of item i is supported by item j
b2 = {}
for i in I:
    for j in I:
        b2[i,j] = model.addVar(vtype = GRB.BINARY, name = 'b2[' + str(i) + ',' + str(j) + ']' ) 

# v i,j diff between boxes
v = {}
for i in I:
    for j in I:
        v[i,j] = model.addVar(vtype = GRB.INTEGER, name = 'v[' + str(i) + ',' + str(j) + ']' ) 

# m i,j diff between boxes
m = {}
for i in I:
    for j in I:
        m[i,j] = model.addVar(vtype = GRB.INTEGER, name = 'm[' + str(i) + ',' + str(j) + ']' ) 





# %% ---- Integrate new variables ----
model.update()

# %% ---- Objective Function ----
model.setObjective (quicksum(bin_cost[b] * z[b] for b in B))
model.modelSense = GRB.MINIMIZE
model.update ()

# constraint 2: determine link x and x2
con2 = {}
for i in I:
    con2[i] = model.addConstr(x2[i] == x[i] + item_length[i] * r[i] + item_height[i] * (1-r[i]) )

# constraint 3: determine link y and y2     
con3 = {}
for i in I:
    con3[i] = model.addConstr(y2[i] == y[i] + item_height[i] * r[i] + item_length[i] * (1-r[i]) )

# Constraint 4: Ensures that there is a value for the l and u constraints if two items are in the same box 
con4 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con4[i,j,b] = model.addConstr(l[i,j] + l[j,i] + u[i,j] + u[j,i] >= (p[i,b] + p[j,b] -1))     

# Constraint 5: Mutual positioning along the x axis 1
con5 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con5[i,j,b] = model.addConstr(x[j] >= x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) - M * (1- l[i,j]))   

# Constraint 6: Mutual positioning along the x axis 2
con6 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con6[i,j,b] = model.addConstr(x[j] <= x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) + M * l[i,j])   

                   
# Constraint 7: Mutual positioning along the y axis 1
con7 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con7[i,j,b] = model.addConstr(y[j] >= y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] - M * (1- u[i,j]))   

# Constraint 8: Mutual positioning along the y axis 2
con8 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con8[i,j,b] = model.addConstr(y[j] <= y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] + M * u[i,j])   

# Constraint 9: Ensure that the lower-right vertex of item i is contained within bin b.
con9 = {}
for i in I:
     for b in B:
          con9[i,b] = model.addConstr(x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) <= quicksum(bin_length[b] * p[i,b] for b in B))  

# Constraint 10: Ensure that the upper-right vertex of item i is contained within bin b.
con10 = {}
for i in I:
     for b in B:
          con10[i,b] = model.addConstr(y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] <= quicksum(bin_height[b] * p[i,b] for b in B))  

# Constraint 11: item assignment to bin
con11 = {}
for i in I:
    con11[i] = model.addConstr(quicksum(p[i,b] for b in B )  == 1)

# Constraint 12: bin flagged as used
con12 = {}
for i in I:
     for b in B:
         con12[i,b] = model.addConstr(z[b] >= p[i,b])     

# Constraint 13: Support constraint
con13 = {}
for i in I:
     con13[i] = model.addConstr(quicksum(b1[i,j] for j in I if i != j) + quicksum(b2[i,j] for j in I if i != j) + 2*g[i] == 2)

# Constraint 14: Stability constraint
con14 = {}
for i in I:
    con14[i] = model.addConstr(quicksum(b1[i,j] for j in I if j != i) == quicksum(b2[i,j] for j in I if j != i)  )

# Constraint 15: Gravity constraint
con15 = {}
for i in I:
     con15[i] = model.addConstr(y[i] <= M * (1- g[i]),  'con15[' + str(i) + ']-'     )

# constraint 16: n1 big M part one
con16 = {}
for i in I:
    for j in I:
        if i !=j:
            con16[i,j] = model.addConstr(x[j] >= x[i] - M * (1- n1[i,j])  )

# constraint 17: n1 big M part two
con17= {}
for i in I:
    for j in I:
        if i !=j:
            con17[i,j] = model.addConstr(x[j] <= x[i] + M * (n1[i,j])  )

# constraint 18: n2 big M part one
con18 = {}
for i in I:
    for j in I:
        if i !=j:
            con18[i,j] = model.addConstr(x2[i] >= x2[j] - M * (1- n2[i,j])  )

# constraint 19: n2 big M part two
con19 = {}
for i in I:
    for j in I:
        if i !=j:
            con19[i,j] = model.addConstr(x2[i] <= x2[j] + M * (n2[i,j])  )

# absolute level of vij part one
con20 = {}
for i in I:
    for j in I:
        con20[i,j] = model.addConstr(y2[j] - y[i] <= v[i,j]  )

# absolute level of vij part two
con21 = {}
for i in I:
    for j in I:
        con21[i,j] = model.addConstr(y[i] - y2[j] <= v[i,j]  )


# mij big m constraint part one
con22 = {}
for i in I:
    for j in I:
        if i !=j:
            con22[i,j] = model.addConstr(y2[j] >= y[i] - M * (1- m[i,j])  )

# mij big m constraint part two
con23 = {}
for i in I:
    for j in I:
        if i !=j:
            con23[i,j] = model.addConstr(y2[j] <= y[i] + M * (m[i,j])  )

# Determine if iem j has a suitable height for item i part one
con24 = {}
for i in I:
    for j in I:
        if i != j:
            con24[i,j] = model.addConstr(v[i,j] <= y2[j] - y[i] + M*(1-m[i,j]))

# Determine if iem j has a suitable height for item i part two
con25 = {}
for i in I:
    for j in I:
        if i != j:
            con25[i,j] = model.addConstr(v[i,j] <= y[i] - y2[j] + M * m[i,j] )

# Determine if iem j has a suitable height for item i part three
con26 = {}
for i in I:
    for j in I:
        if i != j:
            con26[i,j] = model.addConstr(h[i,j] <= v[i,j] )

# Determine if iem j has a suitable height for item i part four
con27 = {}
for i in I:
    for j in I:
        if i != j:
            con27[i,j] = model.addConstr(v[i,j] <= h[i,j] * M)

# Constraint based on the fact that boxes i and k share a part of their orthogonal projection part one
con28 = {}
for i in I:
    for j in I:
        if i != j:
            con28[i,j] = model.addConstr( o[i,j] == l[i,j] + l[j,i]      )

# If the bottom face of box i is supported by the top face of a box j part one
con29 = {}
for i in I:
    for j in I:
        if i != j:
            con29[i,j] = model.addConstr( (1-s[i,j]) <= h[i,j] + o[i,j]  )

# If the bottom face of box i is supported by the top face of a box j part two
con30 = {}
for i in I:
    for j in I:
        if i != j:
            con30[i,j] = model.addConstr( 2*(1-s[i,j]) >= h[i,j] + o[i,j]  )


# guarentee that stacket items are in the same bin part one
con31 = {}
for i in I:
    for j in I:
        for b in B:
            if i != j:
                con31[i,j,b] = model.addConstr(p[i,b] - p[j,b] <= 1 - s[i,j] )

# guarentee that stacket items are in the same bin part two
con32 = {}
for i in I:
    for j in I:
        for b in B:
            if i != j:
                con32[i,j,b] = model.addConstr(p[j,b] - p[i,b] <= 1 - s[i,j] )


# Constraint certify that a box k support one vertex of the basis of box i only if this one is supported by box k, part one
con33 = {}
for i in I:
    for j in I:
        if i != j:
            con33[i,j] = model.addConstr(b1[i,j] <= s[i,j]   )

# Constraint certify that a box k support one vertex of the basis of box i only if this one is supported by box k, part one
con34 = {}
for i in I:
    for j in I:
        if i != j:
            con34[i,j] = model.addConstr(b2[i,j] <= s[i,j]   )


# fig 9 constraints part one
con35 = {}
for i in I:
    for j in I:
        if i != j:
            con35[i,j] = model.addConstr(n1[i,j] + n2[i,j] <= 2 * (1-b1[i,j])     )

# fig 9 constraints part one
con36 = {}
for i in I:
    for j in I:
        if i != j:
            con36[i,j] = model.addConstr(n1[i,j] + n2[i,j] <= 2 * (1-b2[i,j])     )

# Fragile constraint
con37 = {}
for i in I:
    for j in I:
        if i != j:
            con37[i,j] = model.addConstr(s[i,j] <= (1 - fragile[j])    )

# rotation constraint r[i] == 1 means original position
con38 = {}
for i in I:
    con38[i] = model.addConstr(r[i] >= (1 - rotatable[i]) )

# radioactive, perishable contstraint
# mark perishable bin
con39 = {}
for i in I:
    for b in B:
        con39[i,b] = model.addConstr( perishable[i] - M*(1-p[i,b])  <= per[b] )

# mark radioactive bin
con40 = {}
for i in I:
    for b in B:
        con40[i,b] = model.addConstr( radioactive[i] - M*(1-p[i,b])  <= rad[b]  )

# either or constraint
con41 = {}
for b in B:
    con41[b] = model.addConstr( per[b] + rad[b] <= 1   )


# %%  ---- Solve ----
model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.setParam('TimeLimit', 300)  # TimeLimit of five minutes
model.write("output.lp")            # print the model in .lp format file
model.optimize ()

if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Optimal olution found, minimal costs: ' + '%10.3f' % model.objVal + ' euros'  )  
    print ('')
elif model.status == GRB.TIME_LIMIT:
    print ('Time Limit solution found, minimal costs: ' + '%10.3f' % model.objVal + ' euros'  )  
    print ('')
else:
    print ('\nNo feasible solution found')


# %%

if model.status == GRB.Status.OPTIMAL or model.status == GRB.Status.TIME_LIMIT: # If solution is found
    # Define a list of colors for the small rectangles
    colors = plt.cm.viridis(np.linspace(0, 1, len(I)))
    for b in B:
        if z[b].x == 1.0:
            # bin label 
            bin_label = ''
            if per[b].x == 1.0:
                bin_label += 'Per.'
            if rad[b].x == 1.0:
                bin_label += 'Rad.'

            # Set the width and height of the bin
            b_length = bin_length[b]
            b_height = bin_height[b]

            # Create a figure and axis object
            fig, ax = plt.subplots()

            # Add a rectangle to the axis
            rect_bin = plt.Rectangle((0, 0), b_length, b_height, linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(rect_bin)

            for i in I:
                if p[i,b].x == 1.0:
                    # set label
                    label = ''
                    if fragile[i] == 1.0:
                        label += '\nFra.'
                    if perishable[i] == 1.0:
                        label += '\nPer.'
                    if radioactive[i] == 1.0:
                        label += '\nRad.'
                    if rotatable[i] == 1.0:
                        label += '\nRot.'

                    # Set the width and height of the item
                    i_length = item_length[i] * r[i].x + item_height[i] * (1- r[i].x)  
                    i_height = item_height[i] * r[i].x + item_length[i] * (1- r[i].x)  

                    # Set x and y coordinates of bottom left corner
                    x_pos = x[i].x
                    y_pos = y[i].x

                    # Add a rectangle to the axis
                    rect_item = plt.Rectangle((x_pos, y_pos), i_length, i_height, linewidth=1, edgecolor='black', facecolor=colors[i])
                    ax.add_patch(rect_item)
                    ax.text(x_pos + i_length/2, y_pos + i_height/2, 'i: ' + str(i) + ' (' + label + ')'   , ha='center', va='center', color='white')
                  
            # Set the limits of the plot
            ax.set_xlim([-1, b_length + 1])
            ax.set_ylim([-1, b_height + 1])

            # Add a title to the plot
            ax.set_title('Bin ' + str(b) + '; ' + bin_label)

            # Show the plot
            plt.show()               
                        
# %%
if False:
     for b in B:
          for i in I:
               for j in I:       
                    if i != j:
                         print(b, i, j)
                         print(l[i,j].x, l[i,j].x)
                         print(u[i,j].x, u[j,i].x)
                         print(p[i,b].x, p[j,b].x)
                         print()

if False:
    for i in [4]:
        for j in I:
            print(i, j, g[i].x,b1[i,j].x, b2[i,j].x, u[i,j].x, y[i].x)

if True:
    for i in [0,1]:
        for j in I:
            print(i, j, g[i].x,b1[i,j].x, b2[i,j].x, s[i,j].x, h[i,j].x, o[i,j].x, n1[i,j].x, n2[i,j].x)


# %%
