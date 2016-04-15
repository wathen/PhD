import petsc4py
import sys

petsc4py.init(sys.argv)

from petsc4py import PETSc
import mshr
from dolfin import *
import sympy as sy
import numpy as np
import ExactSol
import MatrixOperations as MO
import CheckPetsc4py as CP
def Domain(n):

    # defining the L-shaped domain
    # domain = mshr.Rectangle(Point(-1., -1.), Point(1., 1.)) - mshr.Rectangle(Point(0., -1.), Point(1., 0.) )
    # mesh = mshr.generate_mesh(domain, n)
    mesh = RectangleMesh(-1,-1,1,1,n,n, 'crossed')
    cell_f = CellFunction('size_t', mesh, 0)
    for cell in cells(mesh):
        v = cell.get_vertex_coordinates()
        y = v[np.arange(0,6,2)]
        x = v[np.arange(1,6,2)]
        xone = np.ones(3)
        xone[x > 0] = 0
        yone = np.ones(3)
        yone[y < 0] = 0
        if np.sum(xone)+ np.sum(yone)>5.5:
            cell_f[cell] = 1
    mesh = SubMesh(mesh, cell_f, 0)


    # cell_markers = CellFunction("bool", mesh)
    # cell_markers.set_all(False)
    # origin = Point(0., 0.)
    # for cell in cells(mesh):
    #     p = cell.midpoint()
    #     if abs(p.distance(origin)) < 0.6:
    #         cell_markers[cell] = True

    # mesh = refine(mesh, cell_markers)


    # cell_markers = CellFunction("bool", mesh)
    # cell_markers.set_all(False)
    # origin = Point(0., 0.)
    # for cell in cells(mesh):
    #     p = cell.midpoint()
    #     if abs(p.distance(origin)) < 0.4:
    #         cell_markers[cell] = True

    # mesh = refine(mesh, cell_markers)


    # cell_markers = CellFunction("bool", mesh)
    # cell_markers.set_all(False)
    # origin = Point(0., 0.)
    # for cell in cells(mesh):
    #     p = cell.midpoint()
    #     if abs(p.distance(origin)) < 0.2:
    #         cell_markers[cell] = True

    # mesh = refine(mesh, cell_markers)



    # Creating classes that define the boundary of the domain
    class Left(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[0], -1.0)

    class Right(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[0], 1.0)

    class Bottom(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[1], -1.0)

    class Top(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[1], 1.0)

    class CornerTop(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[1], 0.0)

    class CornerLeft(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[0], 0.0)


    left = Left()
    top = Top()
    right = Right()
    bottom = Bottom()
    cleft = CornerLeft()
    ctop = CornerTop()

    # Initialize mesh function for the domain
    domains = CellFunction("size_t", mesh)
    domains.set_all(0)

    # Initialize mesh function for boundary domains
    boundaries = FacetFunction("size_t", mesh)
    boundaries.set_all(0)

    left.mark(boundaries, 1)
    top.mark(boundaries, 1)
    bottom.mark(boundaries, 1)
    cleft.mark(boundaries, 1)
    ctop.mark(boundaries, 1)
    right.mark(boundaries, 2)
    return mesh, boundaries, domains


# functions that perform partial derivatives of x and y with respect to polar coordinates
def polarx(u, rho, phi):
    return sy.cos(phi)*sy.diff(u, rho) - (1./rho)*sy.sin(phi)*sy.diff(u, phi)

def polary(u, rho, phi):
    return sy.sin(phi)*sy.diff(u, rho) + (1./rho)*sy.cos(phi)*sy.diff(u, phi)


def Solution(mesh, params):

    l = 0.54448373678246
    omega = (3./2)*np.pi

    phi = sy.symbols('x[1]')
    rho = sy.symbols('x[0]')
    z = sy.symbols('z')

    # looked at all the exact solutions and they seems to be the same as the paper.....
    psi = (sy.sin((1+l)*phi)*sy.cos(l*omega))/(1+l) - sy.cos((1+l)*phi) - (sy.sin((1-l)*phi)*sy.cos(l*omega))/(1-l) + sy.cos((1-l)*phi)
    psi_prime = sy.diff(psi, phi)
    psi_3prime = sy.diff(psi, phi, phi, phi)

    u = rho**l*((1+l)*sy.sin(phi)*psi + sy.cos(phi)*psi_prime)
    v = rho**l*(-(1+l)*sy.cos(phi)*psi + sy.sin(phi)*psi_prime)

    uu0 = Expression((sy.ccode(u),sy.ccode(v)))

    p = -rho**(l-1)*((1+l)**2*psi_prime + psi_3prime)/(1-l)
    pu0 = Expression(sy.ccode(p))

    f = rho**(2./3)*sy.sin((2./3)*phi)
    # b = sy.diff(f,rho)#
    b = polarx(f, rho, phi)
    # d = (1./rho)*sy.diff(f,phi)#
    d = polary(f, rho, phi)

    bu0 = Expression((sy.ccode(b),sy.ccode(d)))

    r = sy.diff(phi,rho)
    ru0 = Expression(sy.ccode(r))


    # Defining polarx and polary as the x and y derivatives with respect to polar coordinates (rho, phi). Writing the right handside with respect to cartesian coords

    #Laplacian
    L1 = polarx(polarx(u, rho, phi), rho, phi) + polary(polary(u, rho, phi), rho, phi)
    L2 = polarx(polarx(v, rho, phi), rho, phi) + polary(polary(v, rho, phi), rho, phi)

    # Advection
    A1 = u*polarx(u, rho, phi)+v*polary(u, rho, phi)
    A2 = u*polarx(v, rho, phi)+v*polary(v, rho, phi)

    # Pressure gradient
    P1 = polarx(p, rho, phi)
    P2 = polary(p, rho, phi)

    # Curl-curl
    C1 = polarx(polary(d, rho, phi), rho, phi) - polary(polary(b, rho, phi), rho, phi)
    C2 = polarx(polary(b, rho, phi), rho, phi) - polary(polary(d, rho, phi), rho, phi)

    # Multiplier gradient
    R1 = sy.diff(r, rho)
    R2 = sy.diff(r, rho)

    # Coupling term for fluid variables
    NS1 = -d*(polarx(d, rho, phi)-polary(b, rho, phi))
    NS2 = b*(polarx(d, rho, phi)-polary(b, rho, phi))

    # Coupling term for Magnetic variables
    M1 = polary(u*d-v*b, rho, phi)
    M2 = -polarx(u*d-v*b, rho, phi)

    # Using https://en.wikipedia.org/wiki/Del_in_cylindrical_and_spherical_coordinates defintitions of the derivative operators      (sy.diff(u,rho) means partial derivative of u with respect to rho)

    # Laplacian
    L11 = (1./rho)*sy.diff(rho*sy.diff(u,rho),rho) + (1./(rho**2))*sy.diff(sy.diff(u,phi),phi) - (1./rho**2)*u - (2./rho**2)*sy.diff(v, phi)
    L22 = (1./rho)*sy.diff(rho*sy.diff(v,rho),rho) + (1./(rho**2))*sy.diff(sy.diff(v,phi),phi) - (1./rho**2)*v + (2./rho**2)*sy.diff(u, phi)


    # Advection
    A11 = u*sy.diff(u, rho) + (1./rho)*v*sy.diff(u, phi) - u**2/rho
    A22 = u*sy.diff(v, rho) + (1./rho)*v*sy.diff(v, phi) + v*u/rho

    # Pressure gradient
    P11 = sy.diff(p, rho)
    P22 = (1./rho)*sy.diff(p, phi)

    # Curl-curl
    c = (1./rho)*(sy.diff(rho*d, rho) - sy.diff(b, phi))
    C11 = (1./rho)*sy.diff(c, phi)
    C22 = -sy.diff(c, rho)

    # Multiplier gradient
    R11 = sy.diff(r, rho)
    R22 = sy.diff(r, rho)

    # Coupling term for fluid variables
    NS11 = -c*d
    NS22 = c*b

    # Coupling term for Magnetic variables
    c = u*d-v*b
    M11 = (1./rho)*sy.diff(c, phi)
    M22 = -sy.diff(c, rho)
    FF = sy.diff(u, rho) + (1./rho)*sy.diff(v, phi)

    # print "\n\n\nL limits \n\n"
    # print sy.limit(L1, rho,0), sy.limit(sy.limit(L1, phi,0),rho,0)
    # print sy.limit(L11, rho,0), sy.limit(sy.limit(L11, phi,0),rho,0)
    # print "\n", sy.limit(L2, rho,0), sy.limit(sy.limit(L2, phi,0),rho,0)
    # print sy.limit(L22, rho,0), sy.limit(sy.limit(L22, phi,0),rho,0)

    # print "\n\n\nA limits \n\n"
    # print sy.limit(A1, rho,0), sy.limit(sy.limit(A1, phi,0),rho,0)
    # print sy.limit(A11, rho,0), sy.limit(sy.limit(A11, phi,0),rho,0)
    # print "\n", sy.limit(A2, rho,0), sy.limit(sy.limit(A2, phi,0),rho,0)
    # print sy.limit(A22, rho,0), sy.limit(sy.limit(A22, phi,0),rho,0)

    # print "\n\n\nP limits \n\n"
    # print sy.limit(P1, rho,0), sy.limit(sy.limit(P1, phi,0),rho,0)
    # print sy.limit(P11, rho,0), sy.limit(sy.limit(P11, phi,0),rho,0)
    # print "\n", sy.limit(P2, rho,0), sy.limit(sy.limit(P2, phi,0),rho,0)
    # print sy.limit(P22, rho,0), sy.limit(sy.limit(P22, phi,0),rho,0)

    # print "\n\n\nC limits \n\n"
    # print sy.limit(C1, rho,0), sy.limit(sy.limit(C1, phi,0),rho,0)
    # print sy.limit(C11, rho,0), sy.limit(sy.limit(C11, phi,0),rho,0)
    # print "\n", sy.limit(C2, rho,0), sy.limit(sy.limit(C2, phi,0),rho,0)
    # print sy.limit(C22, rho,0), sy.limit(sy.limit(C22, phi,0),rho,0)

    # print "\n\n\nR limits \n\n"
    # print sy.limit(R1, rho,0), sy.limit(sy.limit(R1, phi,0),rho,0)
    # print sy.limit(R11, rho,0), sy.limit(sy.limit(R11, phi,0),rho,0)
    # print "\n", sy.limit(R2, rho,0), sy.limit(sy.limit(R2, phi,0),rho,0)
    # print sy.limit(R22, rho,0), sy.limit(sy.limit(R22, phi,0),rho,0)

    # print "N\n\n\nS limits \n\n"
    # print sy.limit(NS1, rho,0), sy.limit(sy.limit(NS1, phi,0),rho,0)
    # print sy.limit(NS11, rho,0), sy.limit(sy.limit(NS11, phi,0),rho,0)
    # print "\n", sy.limit(NS2, rho,0), sy.limit(sy.limit(NS2, phi,0),rho,0)
    # print sy.limit(NS22, rho,0), sy.limit(sy.limit(NS22, phi,0),rho,0)

    # print "\n\n\nM limits \n\n"
    # print sy.limit(M1, rho,0), sy.limit(sy.limit(M1, phi,0),rho,0)
    # print sy.limit(M11, rho,0), sy.limit(sy.limit(M11, phi,0),rho,0)
    # print "\n", sy.limit(M2, rho,0), sy.limit(sy.limit(M2, phi,0),rho,0)
    # print sy.limit(M22, rho,0), sy.limit(sy.limit(M22, phi,0),rho,0)

    # print "\n\n\Fluid limits \n\n"
    # print sy.limit(u, rho,0), sy.limit(sy.limit(u, phi,0),rho,0)
    # print sy.limit(v, rho,0), sy.limit(sy.limit(v, phi,0),rho,0)
    # print sy.limit(p, rho,0), sy.limit(sy.limit(p, phi,0),rho,0)

    # print "\n\n\nVelocity limits \n\n"
    # print sy.limit(b, rho,0), sy.limit(sy.limit(b, phi,0),rho,0)
    # print sy.limit(d, rho,0), sy.limit(sy.limit(d, phi,0),rho,0)
    # print sy.limit(r, rho,0), sy.limit(sy.limit(r, phi,0),rho,0)



    # ssss
    # graduu0 = Expression(sy.ccode(sy.diff(u, rho) + (1./rho)*sy.diff(u, phi)))
    graduu0 = Expression((sy.ccode(sy.diff(u, rho)),sy.ccode(sy.diff(v, rho))))
    Laplacian = Expression((sy.ccode(L11),sy.ccode(L22)))
    Advection = Expression((sy.ccode(A11),sy.ccode(A22)))
    gradPres = Expression((sy.ccode(P11),sy.ccode(P22)))
    CurlCurl = Expression((sy.ccode(C11),sy.ccode(C22)))
    gradR = Expression((sy.ccode(R11).replace('M_PI','pi'),sy.ccode(R22).replace('M_PI','pi')))
    NS_Couple = Expression((sy.ccode(NS11),sy.ccode(NS22)))
    M_Couple = Expression((sy.ccode(M11),sy.ccode(M22)))

    # ignore this! Just removes the singularity (atan2(0,0) = NaN) and makes all functions zero at the origin
    class u0(Expression):
        def __init__(self, mesh, uu0):
            self.mesh = mesh
            self.u0 = uu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values[0] = 0.0
            #     values[1] = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                # print theta
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.u0(r, theta)[0]
                values[1] = self.u0(r,theta)[1]
        def value_shape(self):
            return (2,)

    class gradu0(Expression):
        def __init__(self, mesh, graduu0):
            self.mesh = mesh
            self.gradu0 = graduu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values =  0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values = self.gradu0(r,theta)
    class p0(Expression):
        def __init__(self, mesh, pu0):
            self.mesh = mesh
            self.p0 = pu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values[0] = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
        def eval(self, values, x):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
    class p0Vec(Expression):
        def __init__(self, mesh, pu0):
            self.mesh = mesh
            self.p0 = pu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values[0] = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
                values[1] = self.p0(r,theta)
        def eval(self, values, x):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
                values[1] = self.p0(r,theta)
        # def value_shape(self):
        #     return (1,)
    class b0(Expression):
        def __init__(self, mesh, bu0):
            self.mesh = mesh
            self.b0 = bu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values[0] = 0.0
            #     values[1] = 0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.b0(r, theta)[0]
                values[1] = self.b0(r,theta)[1]
                # print values
        def value_shape(self):
            return (2,)

    class r0(Expression):
        def __init__(self, mesh, element=None):
            self.mesh = mesh
        def eval(self, values, x):
            values[0] = 1.0
        # def value_shape(self):
        #     return ( )


    class F_NS(Expression):
        def __init__(self, mesh, Laplacian, Advection, gradPres, NS_Couple, params):
            self.mesh = mesh
            self.Laplacian = Laplacian
            self.Advection = Advection
            self.gradPres = gradPres
            self.NS_Couple = NS_Couple
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi

                values[0] =  self.Advection(r,theta)[0] - self.params[0]*self.NS_Couple(r,theta)[0]
                values[1] =  self.Advection(r,theta)[1] - self.params[0]*self.NS_Couple(r,theta)[1]
                # ssss
                # print values

        def value_shape(self):
            return (2,)

    class F_S(Expression):
        def __init__(self, mesh, Laplacian, gradPres, params):
            self.mesh = mesh
            self.Laplacian = Laplacian
            self.gradPres = gradPres
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
                values[0] = 0
                values[1] = 0
                # print r, theta, self.Laplacian(r,theta)

        def value_shape(self):
            return (2,)


        # params[1]*params[0]*CurlCurl+gradR -params[0]*M_Couple
    class F_M(Expression):
        def __init__(self, mesh, CurlCurl, gradR ,M_Couple, params):
            self.mesh = mesh
            self.CurlCurl = CurlCurl
            self.gradR = gradR
            self.M_Couple = M_Couple
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = - self.params[0]*self.M_Couple(r,theta)[0]
                values[1] = - self.params[0]*self.M_Couple(r,theta)[1]

        def value_shape(self):
            return (2,)
    class F_MX(Expression):
        def __init__(self, mesh):
            self.mesh = mesh
        def eval_cell(self, values, x, ufc_cell):
            values[0] = 0.0
            values[1] = 0.0


        def value_shape(self):
            return (2,)


    class Neumann(Expression):
        def __init__(self, mesh, pu0, graduu0, params, n):
            self.mesh = mesh
            self.p0 = pu0
            self.gradu0 = graduu0
            self.params = params
            self.n = n
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 2.0
                values[1] = 0.0
            else:
                # print x[0], x[1]
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                # cell = Cell(self.mesh, ufc_cell.index)
                # print ufc_cell
                # n = cell.normal(ufc_cell.local_facet)
                # n = FacetNormal(self.mesh)
                # print self.n
                # sss
                values[0] = (self.p0(r,theta) - self.params[0]*self.gradu0(r,theta)[0])
                # print -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta))
                values[1] = -(self.params[0]*self.gradu0(r,theta)[1])

        def value_shape(self):
            return (2,)

    # class NeumannGrad(Expression):
    #     def __init__(self, mesh, pu0, graduu0, params, n):
    #         self.mesh = mesh
    #         self.p0 = pu0
    #         self.gradu0 = graduu0
    #         self.params = params
    #         self.n = n
    #     def eval_cell(self, values, x, ufc_cell):
    #         if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
    #             values[0] = 2.0
    #             values[1] = 0.0
    #         else:
    #             # print x[0], x[1]
    #             r = sqrt(x[0]**2 + x[1]**2)
    #             theta = np.arctan2(x[1],x[0])
    #             if theta < 0:
    #                 theta += 2*np.pi
    #             # cell = Cell(self.mesh, ufc_cell.index)
    #             # print ufc_cell
    #             # n = cell.normal(ufc_cell.local_facet)
    #             # n = FacetNormal(self.mesh)
    #             # print self.n
    #             # sss
    #             values[0] = -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta)[0])
    #             # print -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta))
    #             values[1] = (self.params[0]*self.gradu0(r,theta)[1])

    #     def value_shape(self):
    #         return (2,)

    u0 = u0(mesh, uu0)
    p0 = p0(mesh, pu0)
    p0vec = p0Vec(mesh, pu0)
    b0 = b0(mesh, bu0)
    r0 = r0(mesh)
    F_NS = F_NS(mesh, Laplacian, Advection, gradPres, NS_Couple, params)
    F_M = F_M(mesh, CurlCurl, gradR, M_Couple, params)
    F_MX = F_MX(mesh)
    F_S = F_S(mesh, Laplacian, gradPres, params)
    gradu0 = gradu0(mesh, graduu0)
    Neumann = Neumann(mesh, pu0, graduu0, params, FacetNormal(mesh))
    # NeumannGrad = NeumannGrad(mesh, p0, graduu0, params, FacetNormal(mesh))
    return u0, p0, b0, r0, F_NS, F_M, F_MX, F_S, gradu0, Neumann, p0vec


def Solution2(mesh, params):

    l = 0.54448373678246
    omega = (3./2)*np.pi

    phi = sy.symbols('x[1]')
    rho = sy.symbols('x[0]')
    z = sy.symbols('z')

    # looked at all the exact solutions and they seems to be the same as the paper.....
    psi = (sy.sin((1+l)*phi)*sy.cos(l*omega))/(1+l) - sy.cos((1+l)*phi) - (sy.sin((1-l)*phi)*sy.cos(l*omega))/(1-l) + sy.cos((1-l)*phi)
    psi_prime = sy.diff(psi, phi)
    psi_3prime = sy.diff(psi, phi, phi, phi)

    u = rho**l*((1+l)*sy.sin(phi)*psi + sy.cos(phi)*psi_prime)
    v = rho**l*(-(1+l)*sy.cos(phi)*psi + sy.sin(phi)*psi_prime)

    uu0 = Expression((sy.ccode(u),sy.ccode(v)))

    p = -rho**(l-1)*((1+l)**2*psi_prime + psi_3prime)/(1-l)
    pu0 = Expression(sy.ccode(p))

    f = rho**(2./3)*sy.sin((2./3)*phi)
    # b = sy.diff(f,rho)#
    b = polarx(f, rho, phi)
    # d = (1./rho)*sy.diff(f,phi)#
    d = polary(f, rho, phi)

    bu0 = Expression((sy.ccode(b),sy.ccode(d)))

    r = sy.diff(phi,rho)
    ru0 = Expression(sy.ccode(r))


    # Defining polarx and polary as the x and y derivatives with respect to polar coordinates (rho, phi). Writing the right handside with respect to cartesian coords

    #Laplacian
    L1 = polarx(polarx(u, rho, phi), rho, phi) + polary(polary(u, rho, phi), rho, phi)
    L2 = polarx(polarx(v, rho, phi), rho, phi) + polary(polary(v, rho, phi), rho, phi)

    # Advection
    A1 = u*polarx(u, rho, phi)+v*polary(u, rho, phi)
    A2 = u*polarx(v, rho, phi)+v*polary(v, rho, phi)

    # Pressure gradient
    P1 = polarx(p, rho, phi)
    P2 = polary(p, rho, phi)

    # Curl-curl
    C1 = polarx(polary(d, rho, phi), rho, phi) - polary(polary(b, rho, phi), rho, phi)
    C2 = polarx(polary(b, rho, phi), rho, phi) - polary(polary(d, rho, phi), rho, phi)

    # Multiplier gradient
    R1 = sy.diff(r, rho)
    R2 = sy.diff(r, rho)

    # Coupling term for fluid variables
    NS1 = -d*(polarx(d, rho, phi)-polary(b, rho, phi))
    NS2 = b*(polarx(d, rho, phi)-polary(b, rho, phi))

    # Coupling term for Magnetic variables
    M1 = polary(u*d-v*b, rho, phi)
    M2 = -polarx(u*d-v*b, rho, phi)

    # Using https://en.wikipedia.org/wiki/Del_in_cylindrical_and_spherical_coordinates defintitions of the derivative operators      (sy.diff(u,rho) means partial derivative of u with respect to rho)

    # Laplacian
    L11 = (1./rho)*sy.diff(rho*sy.diff(u,rho),rho) + (1./(rho**2))*sy.diff(sy.diff(u,phi),phi) - (1./rho**2)*u - (2./rho**2)*sy.diff(v, phi)
    L22 = (1./rho)*sy.diff(rho*sy.diff(v,rho),rho) + (1./(rho**2))*sy.diff(sy.diff(v,phi),phi) - (1./rho**2)*v + (2./rho**2)*sy.diff(u, phi)


    # Advection
    A11 = u*sy.diff(u, rho) + (1./rho)*v*sy.diff(u, phi) - u**2/rho
    A22 = u*sy.diff(v, rho) + (1./rho)*v*sy.diff(v, phi) + v*u/rho

    # Pressure gradient
    P11 = sy.diff(p, rho)
    P22 = (1./rho)*sy.diff(p, phi)

    # Curl-curl
    c = (1./rho)*(sy.diff(rho*d, rho) - sy.diff(b, phi))
    C11 = (1./rho)*sy.diff(c, phi)
    C22 = -sy.diff(c, rho)

    # Multiplier gradient
    R11 = sy.diff(r, rho)
    R22 = sy.diff(r, rho)

    # Coupling term for fluid variables
    NS11 = -c*d
    NS22 = c*b

    # Coupling term for Magnetic variables
    c = u*d-v*b
    M11 = (1./rho)*sy.diff(c, phi)
    M22 = -sy.diff(c, rho)
    FF = sy.diff(u, rho) + (1./rho)*sy.diff(v, phi)

    # print "\n\n\nL limits \n\n"
    # print sy.limit(L1, rho,0), sy.limit(sy.limit(L1, phi,0),rho,0)
    # print sy.limit(L11, rho,0), sy.limit(sy.limit(L11, phi,0),rho,0)
    # print "\n", sy.limit(L2, rho,0), sy.limit(sy.limit(L2, phi,0),rho,0)
    # print sy.limit(L22, rho,0), sy.limit(sy.limit(L22, phi,0),rho,0)

    # print "\n\n\nA limits \n\n"
    # print sy.limit(A1, rho,0), sy.limit(sy.limit(A1, phi,0),rho,0)
    # print sy.limit(A11, rho,0), sy.limit(sy.limit(A11, phi,0),rho,0)
    # print "\n", sy.limit(A2, rho,0), sy.limit(sy.limit(A2, phi,0),rho,0)
    # print sy.limit(A22, rho,0), sy.limit(sy.limit(A22, phi,0),rho,0)

    # print "\n\n\nP limits \n\n"
    # print sy.limit(P1, rho,0), sy.limit(sy.limit(P1, phi,0),rho,0)
    # print sy.limit(P11, rho,0), sy.limit(sy.limit(P11, phi,0),rho,0)
    # print "\n", sy.limit(P2, rho,0), sy.limit(sy.limit(P2, phi,0),rho,0)
    # print sy.limit(P22, rho,0), sy.limit(sy.limit(P22, phi,0),rho,0)

    # print "\n\n\nC limits \n\n"
    # print sy.limit(C1, rho,0), sy.limit(sy.limit(C1, phi,0),rho,0)
    # print sy.limit(C11, rho,0), sy.limit(sy.limit(C11, phi,0),rho,0)
    # print "\n", sy.limit(C2, rho,0), sy.limit(sy.limit(C2, phi,0),rho,0)
    # print sy.limit(C22, rho,0), sy.limit(sy.limit(C22, phi,0),rho,0)

    # print "\n\n\nR limits \n\n"
    # print sy.limit(R1, rho,0), sy.limit(sy.limit(R1, phi,0),rho,0)
    # print sy.limit(R11, rho,0), sy.limit(sy.limit(R11, phi,0),rho,0)
    # print "\n", sy.limit(R2, rho,0), sy.limit(sy.limit(R2, phi,0),rho,0)
    # print sy.limit(R22, rho,0), sy.limit(sy.limit(R22, phi,0),rho,0)

    # print "N\n\n\nS limits \n\n"
    # print sy.limit(NS1, rho,0), sy.limit(sy.limit(NS1, phi,0),rho,0)
    # print sy.limit(NS11, rho,0), sy.limit(sy.limit(NS11, phi,0),rho,0)
    # print "\n", sy.limit(NS2, rho,0), sy.limit(sy.limit(NS2, phi,0),rho,0)
    # print sy.limit(NS22, rho,0), sy.limit(sy.limit(NS22, phi,0),rho,0)

    # print "\n\n\nM limits \n\n"
    # print sy.limit(M1, rho,0), sy.limit(sy.limit(M1, phi,0),rho,0)
    # print sy.limit(M11, rho,0), sy.limit(sy.limit(M11, phi,0),rho,0)
    # print "\n", sy.limit(M2, rho,0), sy.limit(sy.limit(M2, phi,0),rho,0)
    # print sy.limit(M22, rho,0), sy.limit(sy.limit(M22, phi,0),rho,0)

    # print "\n\n\Fluid limits \n\n"
    # print sy.limit(u, rho,0), sy.limit(sy.limit(u, phi,0),rho,0)
    # print sy.limit(v, rho,0), sy.limit(sy.limit(v, phi,0),rho,0)
    # print sy.limit(p, rho,0), sy.limit(sy.limit(p, phi,0),rho,0)

    # print "\n\n\nVelocity limits \n\n"
    # print sy.limit(b, rho,0), sy.limit(sy.limit(b, phi,0),rho,0)
    # print sy.limit(d, rho,0), sy.limit(sy.limit(d, phi,0),rho,0)
    # print sy.limit(r, rho,0), sy.limit(sy.limit(r, phi,0),rho,0)



    # ssss
    # graduu0 = Expression(sy.ccode(sy.diff(u, rho) + (1./rho)*sy.diff(u, phi)))
    graduu0 = Expression((sy.ccode(sy.diff(u, rho)),sy.ccode(sy.diff(v, rho))))
    Laplacian = Expression((sy.ccode(L11),sy.ccode(L22)))
    Advection = Expression((sy.ccode(A11),sy.ccode(A22)))
    gradPres = Expression((sy.ccode(P11),sy.ccode(P22)))
    CurlCurl = Expression((sy.ccode(C11),sy.ccode(C22)))
    gradR = Expression((sy.ccode(R11).replace('M_PI','pi'),sy.ccode(R22).replace('M_PI','pi')))
    NS_Couple = Expression((sy.ccode(NS11),sy.ccode(NS22)))
    M_Couple = Expression((sy.ccode(M11),sy.ccode(M22)))

    # ignore this! Just removes the singularity (atan2(0,0) = NaN) and makes all functions zero at the origin
    class u0(Expression):
        def __init__(self, mesh, uu0):
            self.mesh = mesh
            self.u0 = uu0
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                # print theta
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.u0(r, theta)[0]
                values[1] = self.u0(r,theta)[1]
        def value_shape(self):
            return (2,)

    class gradu0(Expression):
        def __init__(self, mesh, graduu0):
            self.mesh = mesh
            self.gradu0 = graduu0
        def eval_cell(self, values, x, ufc_cell):
            # if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
            #     values =  0.0
            # else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values = self.gradu0(r,theta)
    class p0(Expression):
        def __init__(self, mesh, pu0):
            self.mesh = mesh
            self.p0 = pu0
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
        def eval(self, values, x):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
    class p0Vec(Expression):
        def __init__(self, mesh, pu0):
            self.mesh = mesh
            self.p0 = pu0
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
                values[1] = self.p0(r,theta)
        def eval(self, values, x):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.p0(r,theta)
                values[1] = self.p0(r,theta)
        # def value_shape(self):
        #     return (1,)
    class b0(Expression):
        def __init__(self, mesh, bu0):
            self.mesh = mesh
            self.b0 = bu0
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = self.b0(r, theta)[0]
                values[1] = self.b0(r,theta)[1]
                # print values
        def value_shape(self):
            return (2,)

    class r0(Expression):
        def __init__(self, mesh, element=None):
            self.mesh = mesh
        def eval(self, values, x):
            values[0] = 1.0
        # def value_shape(self):
        #     return ( )


    class F_NS(Expression):
        def __init__(self, mesh, Laplacian, Advection, gradPres, NS_Couple, params):
            self.mesh = mesh
            self.Laplacian = Laplacian
            self.Advection = Advection
            self.gradPres = gradPres
            self.NS_Couple = NS_Couple
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi

                values[0] =  self.Advection(r,theta)[0] - self.params[0]*self.NS_Couple(r,theta)[0]
                values[1] =  self.Advection(r,theta)[1] - self.params[0]*self.NS_Couple(r,theta)[1]
                # ssss
                # print values

        def value_shape(self):
            return (2,)

    class F_S(Expression):
        def __init__(self, mesh, Laplacian, gradPres, params):
            self.mesh = mesh
            self.Laplacian = Laplacian
            self.gradPres = gradPres
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
                values[0] = 0
                values[1] = 0
                # print r, theta, self.Laplacian(r,theta)

        def value_shape(self):
            return (2,)


        # params[1]*params[0]*CurlCurl+gradR -params[0]*M_Couple
    class F_M(Expression):
        def __init__(self, mesh, CurlCurl, gradR ,M_Couple, params):
            self.mesh = mesh
            self.CurlCurl = CurlCurl
            self.gradR = gradR
            self.M_Couple = M_Couple
            self.params = params
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 0.0
                values[1] = 0.0
            else:
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                values[0] = - self.params[0]*self.M_Couple(r,theta)[0]
                values[1] = - self.params[0]*self.M_Couple(r,theta)[1]

        def value_shape(self):
            return (2,)
    class F_MX(Expression):
        def __init__(self, mesh):
            self.mesh = mesh
        def eval_cell(self, values, x, ufc_cell):
            values[0] = 0.0
            values[1] = 0.0


        def value_shape(self):
            return (2,)


    class Neumann(Expression):
        def __init__(self, mesh, pu0, graduu0, params, n):
            self.mesh = mesh
            self.p0 = pu0
            self.gradu0 = graduu0
            self.params = params
            self.n = n
        def eval_cell(self, values, x, ufc_cell):
            if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
                values[0] = 2.0
                values[1] = 0.0
            else:
                # print x[0], x[1]
                r = sqrt(x[0]**2 + x[1]**2)
                theta = np.arctan2(x[1],x[0])
                if theta < 0:
                    theta += 2*np.pi
                # cell = Cell(self.mesh, ufc_cell.index)
                # print ufc_cell
                # n = cell.normal(ufc_cell.local_facet)
                # n = FacetNormal(self.mesh)
                # print self.n
                # sss
                values[0] = (self.p0(r,theta) - self.params[0]*self.gradu0(r,theta)[0])
                # print -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta))
                values[1] = -(self.params[0]*self.gradu0(r,theta)[1])

        def value_shape(self):
            return (2,)

    # class NeumannGrad(Expression):
    #     def __init__(self, mesh, pu0, graduu0, params, n):
    #         self.mesh = mesh
    #         self.p0 = pu0
    #         self.gradu0 = graduu0
    #         self.params = params
    #         self.n = n
    #     def eval_cell(self, values, x, ufc_cell):
    #         if abs(x[0]) < 1e-8 and abs(x[1]) < 1e-8:
    #             values[0] = 2.0
    #             values[1] = 0.0
    #         else:
    #             # print x[0], x[1]
    #             r = sqrt(x[0]**2 + x[1]**2)
    #             theta = np.arctan2(x[1],x[0])
    #             if theta < 0:
    #                 theta += 2*np.pi
    #             # cell = Cell(self.mesh, ufc_cell.index)
    #             # print ufc_cell
    #             # n = cell.normal(ufc_cell.local_facet)
    #             # n = FacetNormal(self.mesh)
    #             # print self.n
    #             # sss
    #             values[0] = -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta)[0])
    #             # print -(self.p0(r,theta) - self.params[0]*self.gradu0(r,theta))
    #             values[1] = (self.params[0]*self.gradu0(r,theta)[1])

    #     def value_shape(self):
    #         return (2,)

    u0 = u0(mesh, uu0)
    p0 = p0(mesh, pu0)
    p0vec = p0Vec(mesh, pu0)
    b0 = b0(mesh, bu0)
    r0 = r0(mesh)
    F_NS = F_NS(mesh, Laplacian, Advection, gradPres, NS_Couple, params)
    F_M = F_M(mesh, CurlCurl, gradR, M_Couple, params)
    F_MX = F_MX(mesh)
    F_S = F_S(mesh, Laplacian, gradPres, params)
    gradu0 = gradu0(mesh, graduu0)
    Neumann = Neumann(mesh, pu0, graduu0, params, FacetNormal(mesh))
    # NeumannGrad = NeumannGrad(mesh, p0, graduu0, params, FacetNormal(mesh))
    return u0, p0, b0, r0, F_NS, F_M, F_MX, F_S, gradu0, Neumann, p0vec





# Sets up the initial guess for the MHD problem
def Stokes(V, Q, F, u0, p0, gradu0, params,boundaries, domains):
    parameters['reorder_dofs_serial'] = False

    W = V*Q
    IS = MO.IndexSet(W)
    mesh = W.mesh()
    ds = Measure('ds', domain=mesh, subdomain_data=boundaries)
    dx = Measure('dx', domain=mesh)
    (u, p) = TrialFunctions(W)
    (v, q) = TestFunctions(W)
    n = FacetNormal(W.mesh())

    a11 = params[2]*inner(grad(v), grad(u))*dx('everywhere')
    a12 = -div(v)*p*dx('everywhere')
    a21 = -div(u)*q*dx('everywhere')
    a = a11+a12+a21

    L = inner(v, F)*dx('everywhere') + inner(gradu0,v)*ds(2)

    def boundary(x, on_boundary):
        return on_boundary

    bcu = DirichletBC(W.sub(0), u0, boundaries, 1)

    A, b = assemble_system(a, L, bcu)
    A, b = CP.Assemble(A, b)
    u = b.duplicate()

    ksp = PETSc.KSP()
    ksp.create(comm=PETSc.COMM_WORLD)
    pc = ksp.getPC()
    ksp.setType('preonly')
    pc.setType('lu')
    OptDB = PETSc.Options()
    OptDB['pc_factor_mat_solver_package']  = "mumps"
    OptDB['pc_factor_mat_ordering_type']  = "rcm"
    ksp.setFromOptions()
    # print b.array
    # bbb
    scale = b.norm()
    b = b/scale
    ksp.setOperators(A,A)
    del A
    ksp.solve(b,u)
    # Mits +=dodim
    u = u*scale
    u_k = Function(V)
    p_k = Function(Q)
    u_k.vector()[:] = u.getSubVector(IS[0]).array
    p_k.vector()[:] = u.getSubVector(IS[1]).array
    ones = Function(Q)
    ones.vector()[:]=(0*ones.vector().array()+1)
    p_k.vector()[:] += -assemble(p_k*dx('everywhere'))/assemble(ones*dx('everywhere'))
    return u_k, p_k


def Maxwell(V, Q, F, b0, r0, params, boundaries):
    parameters['reorder_dofs_serial'] = False

    W = V*Q
    IS = MO.IndexSet(W)

    mesh = W.mesh()

    # dx = Measure('dx', domain=mesh)
    print params
    (u, p) = TrialFunctions(W)
    (v, q) = TestFunctions(W)
    n = FacetNormal(W.mesh())

    a11 = params[1]*params[2]*inner(curl(v), curl(u))*dx('everywhere')
    a21 = inner(u,grad(q))*dx('everywhere')
    a12 = inner(v,grad(p))*dx('everywhere')
    L = inner(v, F)*dx('everywhere')
    a = a11+a12+a21

    def boundary(x, on_boundary):
        return on_boundary

    bcb = DirichletBC(W.sub(0), b0, boundaries, 1)
    bcr = DirichletBC(W.sub(1), r0, boundaries, 1)
    bc = [bcb, bcr]

    A, b = assemble_system(a, L, bc)

    A, b = CP.Assemble(A, b)
    u = b.duplicate()

    ksp = PETSc.KSP()
    ksp.create(comm=PETSc.COMM_WORLD)
    pc = ksp.getPC()
    ksp.setType('preonly')
    pc.setType('lu')
    OptDB = PETSc.Options()
    OptDB['pc_factor_mat_solver_package']  = "mumps"
    OptDB['pc_factor_mat_ordering_type']  = "rcm"
    ksp.setFromOptions()
    scale = b.norm()
    b = b/scale
    ksp.setOperators(A,A)
    del A
    ksp.solve(b,u)
    # Mits +=dodim
    u = u*scale

    u_k = Function(V)
    p_k = Function(Q)
    u_k.vector()[:] = u.getSubVector(IS[0]).array
    p_k.vector()[:] = u.getSubVector(IS[1]).array
    # print u_k.vector().array()
    # sss
    return u_k, p_k

















