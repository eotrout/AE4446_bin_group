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

# per_i,b variable, mark bin b as perishable as soon as perisbale item is in the bin
per = {}
for b in B:
    per[b] = model.addVar(vtype = GRB.BINARY, name = 'per[' + str(b) + ']' )

# rad_i,b variable, mark bin b as radioactive as soon as radioactive item is in the bin
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

# s i,j variable, non empty intersection
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
#model.setObjective (quicksum(y[i] for i in I))
model.modelSense = GRB.MINIMIZE
model.update ()

# constraint 0: determine link x and x2
con0 = {}
for i in I:
    con0[i] = model.addConstr(x2[i] == x[i] + item_length[i] * r[i] + item_height[i] * (1-r[i]) )
     
con01 = {}
for i in I:
    con01[i] = model.addConstr(y2[i] == y[i] + item_height[i] * r[i] + item_length[i] * (1-r[i]) )

# Constraint 2: Ensures that there is a value for the l and u constraints if two items are in the same box 
con2 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con2[i,j,b] = model.addConstr(l[i,j] + l[j,i] + u[i,j] + u[j,i] >= (p[i,b] + p[j,b] -1), 'con2[' + str(i) + ', ' + str(j) + ', ' + str(b) + ']-')     

# Constraint 3: Mutual positioning along the x axis 1
con3 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con3[i,j,b] = model.addConstr(x[j] >= x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) - M * (1- l[i,j]), 'con3[' + str(i) + ', ' + str(j) + ', ' + str(b) + ']-')   

# Constraint 4: Mutual positioning along the x axis 2
con4 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con4[i,j,b] = model.addConstr(x[j] <= x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) + M * l[i,j], 'con4[' + str(i) + ', ' + str(j) + ', ' + str(b) + ']-')   

                   
# Constraint 5: Mutual positioning along the y axis 1
con5 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con5[i,j,b] = model.addConstr(y[j] >= y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] - M * (1- u[i,j]), 'con5[' + str(i) + ', ' + str(j) + ', ' + str(b) + ']-')   

# Constraint 6: Mutual positioning along the y axis 2
con6 = {}
for i in I:
     for j in I:
          for b in B:
               if i != j:
                    con6[i,j,b] = model.addConstr(y[j] <= y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] + M * u[i,j], 'con6[' + str(i) + ', ' + str(j) + ', ' + str(b) + ']-')   

# Constraint 7: Ensure that the lower-right vertex of item i is contained within bin b.
con7 = {}
for i in I:
     for b in B:
          con7[i,b] = model.addConstr(x[i] + item_length[i] * r[i] + item_height[i] * (1- r[i]) <= quicksum(bin_length[b] * p[i,b] for b in B), 'con7[' + str(i) + ', ' + str(b) + ']-')  

# Constraint 8: Ensure that the upper-right vertex of item i is contained within bin b.
con8 = {}
for i in I:
     for b in B:
          con8[i,b] = model.addConstr(y[i] + item_length[i] * (1- r[i]) + item_height[i] * r[i] <= quicksum(bin_height[b] * p[i,b] for b in B), 'con8[' + str(i) + ', ' + str(b) + ']-')  

# Constraint 11: item assignment to bin
con11 = {}
for i in I:
    con11[i] = model.addConstr(quicksum(p[i,b] for b in B )  == 1, 'con11[' + str(i) + ']-'    )

# Constraint 12: bin flagged as used
con12 = {}
for i in I:
     for b in B:
         con12[i,b] = model.addConstr(z[b] >= p[i,b], 'con12[' + str(i) + ', ' + str(b) + ']-'    )     

# Constraint 13: Incompatible combination constraint


# Constraint 14: Support constraint
con14 = {}
for i in I:
     con14[i] = model.addConstr(quicksum(b1[i,j] for j in I if i != j) + quicksum(b2[i,j] for j in I if i != j) + 2*g[i] == 2, 'con14[' + str(i) + ']-'    )

con141 = {}
for i in I:
    con141[i] = model.addConstr(quicksum(b1[i,j] for j in I if j != i) == quicksum(b2[i,j] for j in I if j != i)  )


# Constraint 15: Gravity constraint 1
con15 = {}
for i in I:
     con15[i] = model.addConstr(y[i] <= M * (1- g[i]),  'con15[' + str(i) + ']-'     )

con151 = {}
for i in I:
     con151[i] = model.addConstr((1 -g[i]) <= y[i] ,  'con151[' + str(i) + ']-'     )


# constraint 16: n1
con16 = {}
for i in I:
    for j in I:
        if i !=j:
            con16[i,j] = model.addConstr(x[j] >= x[i] - M * (1- n1[i,j])  )

con161 = {}
for i in I:
    for j in I:
        if i !=j:
            con161[i,j] = model.addConstr(x[j] <= x[i] + M * (n1[i,j])  )

# constraint 17: n2
con17 = {}
for i in I:
    for j in I:
        if i !=j:
            con17[i,j] = model.addConstr(x2[i] >= x2[j] - M * (1- n2[i,j])  )

con171 = {}
for i in I:
    for j in I:
        if i !=j:
            con171[i,j] = model.addConstr(x2[i] <= x2[j] + M * (n2[i,j])  )

# absolute level of vij
con18 = {}
for i in I:
    for j in I:
        con18[i,j] = model.addConstr(y2[j] - y[i] <= v[i,j]  )

# absolute level of vij
con19 = {}
for i in I:
    for j in I:
        con19[i,j] = model.addConstr(y[i] - y2[j] <= v[i,j]  )


# mij
con20 = {}
for i in I:
    for j in I:
        if i !=j:
            con20[i,j] = model.addConstr(y2[j] >= y[i] - M * (1- m[i,j])  )

con201 = {}
for i in I:
    for j in I:
        if i !=j:
            con201[i,j] = model.addConstr(y2[j] <= y[i] + M * (m[i,j])  )

# Determine if iem j has a suitable height for item i
con21 = {}
for i in I:
    for j in I:
        if i != j:
            con21[i,j] = model.addConstr(v[i,j] <= y2[j] - y[i] + 2*M*(1-m[i,j]))

con211 = {}
for i in I:
    for j in I:
        if i != j:
            con211[i,j] = model.addConstr(v[i,j] <= y[i] - y2[j] + 2 * M * m[i,j] )

con212 = {}
for i in I:
    for j in I:
        if i != j:
            con212[i,j] = model.addConstr(h[i,j] <= v[i,j] )

con213 = {}
for i in I:
    for j in I:
        if i != j:
            con213[i,j] = model.addConstr(v[i,j] <= h[i,j] * M)

# Constraint based on the fact that boxes i and k share a part of their orthogonal projection
con22 = {}
for i in I:
    for j in I:
        if i != j:
            con22[i,j] = model.addConstr( o[i,j] <= l[i,j] + l[j,i]      )

con221 = {}
for i in I:
    for j in I:
        if i != j:
            con221[i,j] = model.addConstr(o[i,j] >= l[i,j] + l[j,i]      )

# If the bottom face of box i is supported by the top face of a box j
con23 = {}
for i in I:
    for j in I:
        if i != j:
            con23[i,j] = model.addConstr( (1-s[i,j]) <= h[i,j] + o[i,j]  )

con231 = {}
for i in I:
    for j in I:
        if i != j:
            con231[i,j] = model.addConstr( 2*(1-s[i,j]) >= h[i,j] + o[i,j]  )


# guarentee that stacket items are in the same bin 
con24 = {}
for i in I:
    for j in I:
        for b in B:
            if i != j:
                con24[i,j,b] = model.addConstr(p[i,b] - p[j,b] <= 1 - s[i,j] )

con241 = {}
for i in I:
    for j in I:
        for b in B:
            if i != j:
                con241[i,j,b] = model.addConstr(p[j,b] - p[i,b] <= 1 - s[i,j] )


# Constraint certify that a box k support one vertex of the basis of box i only if this one is supported by box k,
con25 = {}
for i in I:
    for j in I:
        if i != j:
            con25[i,j] = model.addConstr(b1[i,j] <= s[i,j]   )

con251 = {}
for i in I:
    for j in I:
        if i != j:
            con251[i,j] = model.addConstr(b2[i,j] <= s[i,j]   )


# fig 9 constraints
con26 = {}
for i in I:
    for j in I:
        if i != j:
            con26[i,j] = model.addConstr(n1[i,j] + n2[i,j] <= 2 * (1-b1[i,j])     )

con261 = {}
for i in I:
    for j in I:
        if i != j:
            con261[i,j] = model.addConstr(n1[i,j] + n2[i,j] <= 2 * (1-b2[i,j])     )

# Fragile constraint
con27 = {}
for i in I:
    for j in I:
        if i != j:
            con27[i,j] = model.addConstr(s[i,j] <= (1 - fragile[j])    )

# rotation constraint r[i] == 1 means original position
con28 = {}
for i in I:
    con28[i] = model.addConstr(r[i] >= (1 - rotatable[i]) )

# radioactive, perishable contstraint
# mark perishable bin
con29 = {}
for i in I:
    for b in B:
        con29[i,b] = model.addConstr( perishable[i] - M*(1-p[i,b])  <= per[b] )

# mark radioactive bin
con291 = {}
for i in I:
    for b in B:
        con291[i,b] = model.addConstr( radioactive[i] - M*(1-p[i,b])  <= rad[b]  )

# either or constraint
con292 = {}
for b in B:
    con292[b] = model.addConstr( per[b] + rad[b] <= 1   )


if False:
    con99 = {}
    con99[0] = model.addConstr(x[0] == 0)
    con99[0] = model.addConstr(x[1] == 0)
    con99[0] = model.addConstr(y[1] == 0)
    #con99[0] = model.addConstr(y[2] == 0)

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
