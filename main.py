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
B = list(range(len(B_pickle)))


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
     r[i] = model.addVar(vtype = GRB.BINARY, name = 'r[' + str(b) + ']' )

# x_{i} variable, x coordiante of lower_left corner of item i, with respect to origin of bin b
x = {}
for i in I:
     for b in B:
          x[i,b] = model.addVar(vtype = GRB.INTEGER, name = 'x[' + str(i) + ',' + str(b) + ']'  )

# y_{i} variable, y coordiante of lower_left corner of item i, with respect to origin of bin b
y = {}
for i in I:
     for b in B:
          y[i,b] = model.addVar(vtype = GRB.INTEGER, name = 'y[' + str(i) + ',' + str(b) + ']'  )

# g_{i} variable, 1 if item i lies on the ground of the bin it is assigned to
g = {}
for i in I:
     g[i] = model.addVar(vtype = GRB.BINARY, name = 'g[' + str(i) + ']')

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


# %% ---- Integrate new variables ----
model.update()

# %% ---- Objective Function ----
model.setObjective (quicksum(bin_cost[b] * z[b] for b in B))
model.modelSense = GRB.MINIMIZE
model.update ()

# Constraint 11: item assignment to bin
con11 = {}
for i in I:
    con11[i] = model.addConstr(quicksum(p[i,b] for b in B )  == 1, 'con11[' + str(i) + ']-'    )

# Constraint 12: bin flagged as used
con12 = {}
for i in I:
     for b in B:
         con12[i,b] = model.addConstr(z[b] >= p[i,b], 'con12[' + str(i) + ', ' + str(b) + ']-'    )     
          





# %%  ---- Solve ----
model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file
model.optimize ()

if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Solution found, minimal costs: ' + '%10.3f' % model.objVal + ' euros'  )  
    print ('')
else:
    print ('\nNo feasible solution found')



# %%

if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    # Define a list of colors for the small rectangles
    colors = plt.cm.viridis(np.linspace(0, 1, len(I)))
    for b in B:
        if z[b].x == 1.0:
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
                    # Set the width and height of the item
                    i_length = item_length[i]
                    i_height = item_height[i]

                    # Set x and y coordinates of bottom left corner
                    x_pos = np.random.uniform(0, b_length - i_length) # x[i].x
                    y_pos = np.random.uniform(0, b_height - i_height) # y[i].x

                    # Add a rectangle to the axis
                    rect_item = plt.Rectangle((x_pos, y_pos), i_length, i_height, linewidth=1, edgecolor='black', facecolor=colors[i])
                    ax.add_patch(rect_item)
                    ax.text(x_pos + i_length/2, y_pos + i_height/2, 'i: ' + str(i), ha='center', va='center', color='white')
                  
            # Set the limits of the plot
            ax.set_xlim([-1, b_length + 1])
            ax.set_ylim([-1, b_height + 1])

            # Add a title to the plot
            ax.set_title('Bin ' + str(b))

            # Show the plot
            plt.show()               
                        

# %%
