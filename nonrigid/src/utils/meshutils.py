"""Operations on meshes with other libraries than vtk, blender or sofa."""

from meshlib import mrmeshpy
import re
import os

def check_self_intersection(
        filename: str
) -> (bool, str):
    """Check for self intersections of mesh from file filename using meshlib.

     Returns
     -------
     error_found, comment
        * error_found = True if there is a self intersection or a meshlib processing error
        * comment: explanation if error_found is True
     """
    # load mesh and check if loading was successful
    try:
        mesh = mrmeshpy.loadMesh(mrmeshpy.Path(filename))
    except RuntimeError as e:
        return True, f"Meshlib cannot read mesh from file {filename}"
    
    mp = mrmeshpy.MeshPart(mesh)
    ret = mrmeshpy.findSelfCollidingTriangles(mp)
    if ret.empty():
        return False, ""
    else:
        return True, f"Self intersection found in mesh {filename}."

def check_self_intersection_all_matches(
        path: str,
        regex: str
) -> (bool, str):
    """Check for self intersections of all meshes in folder path that match the pattern regex using meshlib.
    Works the same as check_self_intersection() but loops through files at a path itself.

     Returns
     -------
     error_found, comment
        * error_found = True if there is a self intersection or a meshlib processing error
        * comment: explanation if error_found is True
     """
    error_found = None
    all_filenames = os.listdir(path)  # after flushing data the files of interest will be present
    for fname in all_filenames:
        if re.match(regex, fname):
            input_filename = os.path.join(path, fname)
            error_found, comment = check_self_intersection(input_filename)
            if error_found:
                return error_found, comment

    if error_found is None:
        return True, f"No files matching \"{regex}\" found at {path}!"
    else:
        # if nothing is found, the last return value from check_self_intersection gives the appropriate details
        return error_found, comment
