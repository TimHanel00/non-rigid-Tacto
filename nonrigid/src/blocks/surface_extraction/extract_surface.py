import random
import numpy as np
from vtk import vtkPerlinNoise, vtkDoubleArray, vtkMath, vtkThreshold, vtkDataObject
import os
import math
import sys

from utils.vtkutils import generate_point_normals, calc_geodesic_distance, calc_surface_area, extract_surface

def random_surface( full_surface, w_distance=1, w_normal=1, w_noise=1, surface_amount=None, center_point_id=None, rnd=None ):
    """ Extract a random part of a surface mesh.

    Starting from a (random) center node c, the
    surrounding points p are assigned three values:
    - Geodesic distance from the center node c
    - Angle difference between the normal of p and the normal of c
    - Random perlin noise value, sampled at the position p.
    From these three values, we build a weighted sum, which acts as the likelihood of a point
    being removed. We then select a threshold and remove all points whose likelihood exceeds
    this threshold. The remaining points are the selected surface.
    The weights in the weighted sum can be used to influence whether the geodesic distance,
    the normals or the random perlin noise value should have a higher influence on the
    removal.

    Arguments:
        full_surface (vtkPolyData):
            Full surface. A part of this mesh will be returned. Point IDs and Cell IDs will not
            be kept.
        w_distance (float):
            Influence of the geodesic distance of a point to the center point c.
            If this value is > 0 and the other weights are == 0, only the distance will be
            taken into account.
        w_normal (float):
            Influence of the angle between normals.
            If this value is > 0 and the other weights are == 0, only points with a similar
            normal as the center point will be selected.
        w_noise (float):
            Influence of the highest noise.
            If this value is > 0 and the other weights are == 0, entirely random parts of the
            surface will be selected.
        surface_amount (float):
            Amount of the surface which we want to select. If None, a random amount
            between 0 and 1 will be selected.
            Valid range: (0,1)
        center_point_id (int):
            Index of the center point c. If None, a random index of all the surface indices will be selected.
        rnd (random.Random):
            Optional random number generator. Instance of random.Random. Pass this for
            reproducible results!

    Returns:
        vtkPolyData
            Describes the part of the full_surface which was selected
    """

    # Fall back to the standard random number generator if there is none given:
    if rnd is None:
        rnd = random.Random()

    # Decide how many points we want to select:
    if surface_amount is None:
        surface_amount = rnd.random()
    assert surface_amount <= 1 and surface_amount > 0, "surface_amount must be between 0 and 1."

    points_to_select = surface_amount * full_surface.GetNumberOfPoints()
    # print("================================================================")
    
    full_surface = generate_point_normals( full_surface )
    normals = full_surface.GetPointData().GetArray( "Normals" )
    # Store the IDs of all triangles:
    #triangleIDs = []
    #for i in range(0,full_surface.GetNumberOfCells()):
    #    if full_surface.GetCell(i).GetCellType() == VTK_TRIANGLE:
    #        triangleIDs.append(i)

    # Select a random point on the surface around which to center the selected part, if it is not provided:
    if center_point_id is None:
        center_point_id = rnd.randint(0,full_surface.GetNumberOfPoints()-1)
    center_point = full_surface.GetPoint( center_point_id )

    distance = calc_geodesic_distance( full_surface, center_point_id )
    full_surface.GetPointData().AddArray( distance )


    # Get normal of that point:
    center_point_normal = normals.GetTuple3( center_point_id )


    # Decrease with:
    # - distance from center point
    # - normal difference
    # - perlin noise

    noise = vtkPerlinNoise()
    noise.SetFrequency( 15, 15, 15 )
    noise.SetPhase( rnd.random()*150, rnd.random()*150, rnd.random()*150 )

    # Create an array which will be filled and then used for thresholding
    likelihood = vtkDoubleArray()
    likelihood.SetNumberOfComponents(1)
    likelihood.SetNumberOfTuples(full_surface.GetNumberOfPoints())
    likelihood.SetName("likelihood")

    min_val = 99999
    max_val = -1
    for i in range( full_surface.GetNumberOfPoints() ):
        pt = full_surface.GetPoint( i )
        dist = math.sqrt( vtkMath.Distance2BetweenPoints(center_point, pt) )

        normal = normals.GetTuple3( i )
        dot = vtkMath.Dot( center_point_normal, normal )
        normal_ang = math.acos( max( min( dot, 1 ), -1 ) )

        rnd = abs(noise.EvaluateFunction( pt ))

        cur_likelihood = w_distance * dist + w_normal * normal_ang + w_noise * rnd
        likelihood.SetTuple1( i, cur_likelihood )
        min_val = min( min_val, cur_likelihood )
        max_val = max( max_val, cur_likelihood )

    #print("Likelihood range:", min_val, max_val)

    # Build histogram of likelihoods:
    hist_bins = 50
    hist = [0]*hist_bins
    for i in range( full_surface.GetNumberOfPoints() ):
        l = likelihood.GetTuple1( i )
        cur_bin = int(l/max_val*(hist_bins-1))
        hist[cur_bin] += 1
   
    # Find out where to set the threshold so that surfaceAmount points are selected.
    # We do this by going through the histogram and summing up the values in the bins. As
    # soon as more than surfaceAmount points are selected, we stop
    thresholded_points = 0
    threshold = max_val  # Start with default of selecting everything
    for i in range( hist_bins ):
        thresholded_points += hist[i]
        if thresholded_points >= points_to_select:
            threshold = (i+1)/hist_bins*max_val
            break
    #print("Selected threshold", threshold)

    full_surface.GetPointData().AddArray( likelihood )

    #likelihoodRange = max_val - min_val

    #rndThreshold = (rnd.random()*0.75 + 0.25)*likelihoodRange + min_val

    thresh = vtkThreshold()
    thresh.SetInputData( full_surface )
    thresh.SetInputArrayToProcess( 0,0,0,
            vtkDataObject.FIELD_ASSOCIATION_POINTS, "likelihood" )
    thresh.ThresholdBetween( 0, threshold )
    thresh.Update()

    # Write resulting surface to file:
    # Debug output:
    # writer = vtkXMLPolyDataWriter()
    # writer.SetFileName( "partialSurfaceLikelihood.vtp" )
    # writer.SetInputData( full_surface )
    # writer.Update()

    partial_surface = extract_surface( thresh.GetOutput() )

    #full_area = calc_surface_area( full_surface )
    partial_area = calc_surface_area( partial_surface )

    #print( "Original area:", fullArea )
    #print( "Partial area:", partialArea )
    #print( "Selected amount: {:.2f}% (Target was {:.2f}%)".format( 100*partialArea/fullArea,
    #    100*surfaceAmount ) )

    return partial_surface

