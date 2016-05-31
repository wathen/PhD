from dolfin import *

def CavityMesh3d(n):

    # Create empty Mesh
    mesh = BoxMesh(-1, -1, -1, 1, 1, 1, n, n,n)


    class DirichletT(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[2], 1.0 - DOLFIN_EPS) and 1 - DOLFIN_EPS x[0] > -1.0 + DOLFIN_EPS and 1 - DOLFIN_EPS x[1] > -1.0 + DOLFIN_EPS

    class DirichletB(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[2],-1.0 + DOLFIN_EPS)

    class DirichletR(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[0],1.0 - DOLFIN_EPS)

    class DirichletL(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[0],-1.0 + DOLFIN_EPS)

    class DirichletF(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[1],1.0 - DOLFIN_EPS)

    class DirichletP(SubDomain):
        def inside(self, x, on_boundary):
            return near(x[1],-1.0 + DOLFIN_EPS)


    dirichletT = DirichletT()
    dirichletB = DirichletB()
    dirichletR = DirichletR()
    dirichletL = DirichletL()
    dirichletF = DirichletF()
    dirichletP = DirichletP()

    boundaries = FacetFunction("size_t", mesh)
    boundaries.set_all(0)


    dirichletT.mark(boundaries, 2)
    dirichletB.mark(boundaries, 1)
    dirichletR.mark(boundaries, 1)
    dirichletL.mark(boundaries, 1)
    dirichletF.mark(boundaries, 1)
    dirichletP.mark(boundaries, 1)

    return mesh, boundaries