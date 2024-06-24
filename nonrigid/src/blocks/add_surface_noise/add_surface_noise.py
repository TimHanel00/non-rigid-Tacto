from vtk import vtkPoints, vtkAdaptiveSubdivisionFilter, vtkDoubleArray, vtkPerlinNoise, vtkThreshold
import random

def add_gauss_noise_to_surface( surface, sigma=0.001, rnd=random ):
    """ Take a surface and move the points randomly.
    Note: This replaces the surface's points with a new vtkPoints object.

    Arguments:
        surface (vtkPolyData):
            surface data
        sigma (float):
            standard deviation of the gaussian noise added to the point positions
    """
    pts = vtkPoints()
    for i in range( surface.GetNumberOfPoints() ):
        pt = surface.GetPoint( i )
        x = rnd.gauss( pt[0], sigma )
        y = rnd.gauss( pt[1], sigma )
        z = rnd.gauss( pt[2], sigma )
        pts.InsertNextPoint( (x,y,z) )

    surface.SetPoints( pts )

    return surface

def subdivide_surface( surface, subdivFactor ):
    """
    Subdivide a surface.
    The number of triangles are increased by (roughly) a factor of 'subdivFactor'.
    Warning: If mesh was watertight before, this function may break that!
    """
   
    initial_cell_number = surface.GetNumberOfCells()

    subdiv_filter = vtkAdaptiveSubdivisionFilter()
    max_new_triangles = int( surface.GetNumberOfCells()*(subdivFactor-1) )
    subdiv_filter.SetMaximumNumberOfTriangles( maxNewTriangles )
    subdiv_filter.SetMaximumTriangleArea( 0.00001 )
    subdiv_filter.SetMaximumEdgeLength( 0.00001 )
    subdiv_filter.SetInputData( surface )
    subdiv_filter.Update()
    surface = subdiv_filter.GetOutput()

    return surface
    
def sparsify_surface( surface, scale=1, shift=0, frequency=9 ):
    """ Randomly "sparsifies" a point cloud.

    This function considers removing every point according to a 3D perlin noise function:
    the higher the noise value at the point's position, the higher the likelihood of the point being removed.

    Arguments:
        surface (vtkPolyData):
            surface data
        scale (float):
            Controls the scale factor of the perlin noise. High values (>1) make areas more diverse, low values (~0) mean that all points are removed with the same probability.
        shift (float):
            Increase (shift > 0) or decrease (shift < 0) probability of all points that they will be removed.
        frequency (float):
            Noise frequency. High frequency leads to many small sparse areas, low frequency leads to fewer, larger ones.
            Default: 9
    """

    removal = vtkDoubleArray()
    removal.SetName( "removeThreshold" )
    removal.SetNumberOfTuples( surface.GetNumberOfPoints() )
    removal.SetNumberOfComponents( 1 )
    removal.Fill(0)
    surface.GetPointData().AddArray( removal )

    noise = vtkPerlinNoise()
    noise.SetFrequency( frequency, frequency, frequency )
    noise.SetPhase( random.random()*150, random.random()*150, random.random()*150 )

    for i in range( surface.GetNumberOfPoints() ):
        pt = surface.GetPoint( i )

        # Get random value at the point's position in the range of (0,1)
        rnd = (noise.EvaluateFunction( pt ) + 1)/2

        # Adjust the random value to the strength:
        rnd = rnd*scale + shift

        # Depending on random value...
        if random.uniform( 0, 1 ) < rnd:
            # Set up for removal:
            removal.SetTuple1( i, 1 )

    thresh = vtkThreshold()
    thresh.SetInputData( surface )
    thresh.SetInputArrayToProcess( 0,0,0,
            vtkDataObject.FIELD_ASSOCIATION_POINTS, "removeThreshold" )
    thresh.ThresholdByLower( 0.5 ) # Everything higher than 0.5 will be removed
    thresh.Update()

    surface = thresh.GetOutput()

    return surface
