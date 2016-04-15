#!/usr/bin/python

# interpolate scalar gradient onto nedelec space
from dolfin import *

import petsc4py
import sys

petsc4py.init(sys.argv)

from petsc4py import PETSc
Print = PETSc.Sys.Print
# from MatrixOperations import *
import numpy as np
import matplotlib.pylab as plt
import PETScIO as IO
import common
import scipy
import scipy.io
import time as t

import BiLinear as forms
import DirectOperations as Iter
import MatrixOperations as MO
import CheckPetsc4py as CP
import ExactSol

m = 3
IterType = 'CD'

errL2u =np.zeros((m-1,1))
errH1u =np.zeros((m-1,1))
errL2p =np.zeros((m-1,1))
errL2b =np.zeros((m-1,1))
errCurlb =np.zeros((m-1,1))
errL2r =np.zeros((m-1,1))
errH1r =np.zeros((m-1,1))



l2uorder =  np.zeros((m-1,1))
H1uorder =np.zeros((m-1,1))
l2porder =  np.zeros((m-1,1))
l2border =  np.zeros((m-1,1))
Curlborder =np.zeros((m-1,1))
l2rorder =  np.zeros((m-1,1))
H1rorder = np.zeros((m-1,1))

NN = np.zeros((m-1,1))
DoF = np.zeros((m-1,1))
Velocitydim = np.zeros((m-1,1))
Magneticdim = np.zeros((m-1,1))
Pressuredim = np.zeros((m-1,1))
Lagrangedim = np.zeros((m-1,1))
Wdim = np.zeros((m-1,1))
iterations = np.zeros((m-1,1))
SolTime = np.zeros((m-1,1))
udiv = np.zeros((m-1,1))
MU = np.zeros((m-1,1))
level = np.zeros((m-1,1))

nn = 2
mm = 1
MUsave = np.zeros((mm,1))
MUit = np.zeros((m-1,mm))
print MUit[0,0]

dim = 2
ShowResultPlots = 'yes'
split = 'Linear'

MU[0]= 1e0
R = 0100.0
for yy in xrange(1,mm+1):

    MU =(R*10**(-yy))
    print "++++++++",MU
    MUsave[yy-1] = MU

    for xx in xrange(1,m):
        print xx
        level[xx-1] = xx+2
        nn = 2**(level[xx-1])


        # Create mesh and define function space
        nn = int(nn)
        NN[xx-1] = nn/2
        parameters["form_compiler"]["quadrature_degree"] = -1
        mesh = UnitSquareMesh(nn,nn)

        order = 2
        parameters['reorder_dofs_serial'] = False
        Velocity = VectorFunctionSpace(mesh, "CG", order)
        Pressure = FunctionSpace(mesh, "CG", order-1)
        Magnetic = FunctionSpace(mesh, "N1curl", order)
        Lagrange = FunctionSpace(mesh, "CG", order)
        W = MixedFunctionSpace([Velocity,Pressure,Magnetic,Lagrange])
        # W = Velocity*Pressure*Magnetic*Lagrange
        Velocitydim[xx-1] = Velocity.dim()
        Pressuredim[xx-1] = Pressure.dim()
        Magneticdim[xx-1] = Magnetic.dim()
        Lagrangedim[xx-1] = Lagrange.dim()
        Wdim[xx-1] = W.dim()
        print "\n\nW:  ",Wdim[xx-1],"Velocity:  ",Velocitydim[xx-1],"Pressure:  ",Pressuredim[xx-1],"Magnetic:  ",Magneticdim[xx-1],"Lagrange:  ",Lagrangedim[xx-1],"\n\n"
        dim = [Velocity.dim(), Pressure.dim(), Magnetic.dim(), Lagrange.dim()]


        def boundary(x, on_boundary):
            return on_boundary

        u0, p0,b0, r0, Laplacian, Advection, gradPres,CurlCurl, gradR, NS_Couple, M_Couple = ExactSol.MHD2D(4,1)
        # plot(interpolate(u0,Velocity))

        p0 = interpolate(p0,Pressure)
        p0.vector()[:] -= np.max(p0.vector().array() )/2
        # plot(interpolate(p0,Pressure))

        bcu = DirichletBC(W.sub(0),u0, boundary)
        bcb = DirichletBC(W.sub(2),b0, boundary)
        bcr = DirichletBC(W.sub(3),r0, boundary)

        # bc = [u0,p0,b0,r0]
        bcs = [bcu,bcb,bcr]
        FSpaces = [Velocity,Pressure,Magnetic,Lagrange]


        (u, p, b, r) = TrialFunctions(W)
        (v, q, c,s ) = TestFunctions(W)
        kappa = 1.0


        Mu_m =1e4
        # MU = 1.0
        print "================================",MU
        F_NS = -MU*Laplacian + Advection + gradPres - kappa*NS_Couple

        F_M = Mu_m*kappa*CurlCurl + gradR - kappa*M_Couple

        params = [kappa,Mu_m,MU]

        u_k,p_k,b_k,r_k = common.InitialGuess(FSpaces,[u0,p0,b0,r0],[F_NS,F_M],params,Neumann=Expression(("0","0")),options ="New")
        # plot(u_k)
        VelPres = Velocitydim[xx-1]+Pressuredim[xx-1]
        # t.sleep(10)
        ones = Function(Pressure)
        ones.vector()[:]=(0*ones.vector().array()+1)
        pConst = -assemble(p_k*dx)/assemble(ones*dx)
        p_k.vector()[:] += pConst
        x = Iter.u_prev(u_k,p_k,b_k,r_k)
        # plot(b_k)


        ns,maxwell,CoupleTerm,Lmaxwell,Lns = forms.MHD2D(mesh, W, F_M, F_NS, u_k, b_k, params, IterType)
        RHSform = forms.PicardRHS(mesh, W, u_k, p_k, b_k, r_k, params)


        bcu = DirichletBC(W.sub(0),Expression(("0.0","0.0")), boundary)
        bcb = DirichletBC(W.sub(2),Expression(("0.0","0.0")), boundary)
        bcr = DirichletBC(W.sub(3),Expression(("0.0")), boundary)
        bcs = [bcu,bcb,bcr]

        eps = 1.0           # error measure ||u-u_k||
        tol = 1.0E-5     # tolerance
        iter = 0            # iteration counter
        maxiter = 40       # max no of iterations allowed
        SolutionTime = 0
        outer = 0
        parameters['linear_algebra_backend'] = 'uBLAS'

        p = forms.Preconditioner(mesh,W,u_k, b_k,params,IterType)

        # PP,Pb = assemble_system(p, Lns,bcs)


        if IterType == "CD":
            AA, bb = assemble_system(maxwell+ns+CoupleTerm, (Lmaxwell + Lns) - RHSform,  bcs)
            A,b,u = Iter.RemoveRowCol(AA,bb,VelPres)


        while eps > tol  and iter < maxiter:
            iter += 1
            if IterType == "CD":
                bb = assemble((Lmaxwell + Lns) - RHSform)
                for bc in bcs:
                    bc.apply(bb)
                A,b,u = Iter.RemoveRowCol(AA,bb,VelPres)
            else:
                AA, bb = assemble_system(maxwell+ns+CoupleTerm, (Lmaxwell + Lns) - RHSform,  bcs)
                A,b,u = Iter.RemoveRowCol(AA,bb,VelPres)

            ksp = PETSc.KSP().create()
            pc = ksp.getPC()#.PC().create()
            # P = MO.shift(A,0.000001)
            ksp.setOperators(A )
            del A
            OptDB = PETSc.Options()

            OptDB["ksp_type"] =  "preonly"
            OptDB["pc_type"] =  "lu"
            OptDB["pc_factor_mat_ordering_type"] = "rcm"
            OptDB["pc_factor_mat_solver_package"] =  "mumps"
            # OptDB["pc_factor_shift_amount"] = 2

            ksp.setFromOptions()

            tic()
            ksp.solve(b, u)

            time = toc()
            print time
            SolutionTime = SolutionTime +time
            del ksp, pc
            u, p, b, r, eps= Iter.PicardToleranceDecouple(u,x,FSpaces,dim,"2",iter)
            p.vector()[:] += - assemble(p*dx)/assemble(ones*dx)
            u_k.assign(u)
            p_k.assign(p)
            b_k.assign(b)
            r_k.assign(r)
            # plot(u_k)
            # plot(p_k)
            uOld= np.concatenate((u_k.vector().array(),p_k.vector().array(),b_k.vector().array(),r_k.vector().array()), axis=0)
            x = Iter.u_prev(u_k,p_k,b_k,r_k)
            if eps > 1e10:
                iter = 0
                break
                        # u_k,b_k,epsu,epsb=Iter.PicardTolerance(x,u_k,b_k,FSpaces,dim,"inf",iter)

        MUit[xx-1,yy-1]= iter
        # SolTime[xx-1] = SolutionTime/iter

        ue =u0
        pe = p0
        be = b0
        re = r0




        ExactSolution = [ue,pe,be,re]
        # errL2u[xx-1], errH1u[xx-1], errL2p[xx-1], errL2b[xx-1], errCurlb[xx-1], errL2r[xx-1], errH1r[xx-1] = Iter.Errors(x,mesh,FSpaces,ExactSolution,order,dim)

        # if xx == 1:
        #     l2uorder[xx-1] = 0
        # else:
        #     l2uorder[xx-1] =  np.abs(np.log2(errL2u[xx-2]/errL2u[xx-1]))
        #     H1uorder[xx-1] =  np.abs(np.log2(errH1u[xx-2]/errH1u[xx-1]))

        #     l2porder[xx-1] =  np.abs(np.log2(errL2p[xx-2]/errL2p[xx-1]))

        #     l2border[xx-1] =  np.abs(np.log2(errL2b[xx-2]/errL2b[xx-1]))
        #     Curlborder[xx-1] =  np.abs(np.log2(errCurlb[xx-2]/errCurlb[xx-1]))

        #     l2rorder[xx-1] =  np.abs(np.log2(errL2r[xx-2]/errL2r[xx-1]))
        #     H1rorder[xx-1] =  np.abs(np.log2(errH1r[xx-2]/errH1r[xx-1]))




import pandas as pd

LatexTitles = ["l","DoF"]
for x in xrange(1,mm+1):
    LatexTitles.append("it")
LatexValues = np.concatenate((level,Wdim,MUit), axis=1)
title = np.concatenate((np.array([[0,0]]),MUsave.T),axis=1)

LatexValues = np.vstack((title,LatexValues))
LatexTable = pd.DataFrame(LatexValues, columns = LatexTitles)

print LatexTable.to_latex()
# LatexTitles = ["l","DoFu","Dofp","V-L2","L2-order","V-H1","H1-order","P-L2","PL2-order"]
# LatexValues = np.concatenate((level,Velocitydim,Pressuredim,errL2u,l2uorder,errH1u,H1uorder,errL2p,l2porder), axis=1)
# LatexTable = pd.DataFrame(LatexValues, columns = LatexTitles)
# pd.set_option('precision',3)
# LatexTable = MO.PandasFormat(LatexTable,"V-L2","%2.4e")
# LatexTable = MO.PandasFormat(LatexTable,'V-H1',"%2.4e")
# LatexTable = MO.PandasFormat(LatexTable,"H1-order","%1.2f")
# LatexTable = MO.PandasFormat(LatexTable,'L2-order',"%1.2f")
# LatexTable = MO.PandasFormat(LatexTable,"P-L2","%2.4e")
# LatexTable = MO.PandasFormat(LatexTable,'PL2-order',"%1.2f")
# print LatexTable.to_latex()


# print "\n\n   Magnetic convergence"
# MagneticTitles = ["l","B DoF","R DoF","B-L2","L2-order","B-Curl","HCurl-order"]
# MagneticValues = np.concatenate((level,Magneticdim,Lagrangedim,errL2b,l2border,errCurlb,Curlborder),axis=1)
# MagneticTable= pd.DataFrame(MagneticValues, columns = MagneticTitles)
# pd.set_option('precision',3)
# MagneticTable = MO.PandasFormat(MagneticTable,"B-Curl","%2.4e")
# MagneticTable = MO.PandasFormat(MagneticTable,'B-L2',"%2.4e")
# MagneticTable = MO.PandasFormat(MagneticTable,"L2-order","%1.2f")
# MagneticTable = MO.PandasFormat(MagneticTable,'HCurl-order',"%1.2f")
# print MagneticTable.to_latex()

# print "\n\n   Lagrange convergence"
# LagrangeTitles = ["l","B DoF","R DoF","R-L2","L2-order","R-H1","H1-order"]
# LagrangeValues = np.concatenate((level,Magneticdim,Lagrangedim,errL2r,l2rorder,errH1r,H1rorder),axis=1)
# LagrangeTable= pd.DataFrame(LagrangeValues, columns = LagrangeTitles)
# pd.set_option('precision',3)
# LagrangeTable = MO.PandasFormat(LagrangeTable,"R-L2","%2.4e")
# LagrangeTable = MO.PandasFormat(LagrangeTable,'R-H1',"%2.4e")
# LagrangeTable = MO.PandasFormat(LagrangeTable,"H1-order","%1.2f")
# LagrangeTable = MO.PandasFormat(LagrangeTable,'L2-order',"%1.2f")
# print LagrangeTable.to_latex()




# # # if (ShowResultPlots == 'yes'):

plot(u_k)
plot(b_k)
plot(r_k)
plot(p_k)


# #     plot(ba)
plot(interpolate(p0,Pressure))

# #     plot(ra)
# plot(interpolate(re,Lagrange))

# interactive()









interactive()
