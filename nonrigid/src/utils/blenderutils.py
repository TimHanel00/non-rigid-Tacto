import bpy
import mathutils
import random
import os
import sys
import bmesh
import numpy as np
import math
from typing import List, Tuple

"""Structure:
- Creation/Deletion of objects
- Settings
- Custom classes
- Cleaning operations
- Custom selections
- Manipulations
- Checks and calculations
- Camera
- Mesh import
- Mesh export
"""

#############################################################################
# Creation/Deletion of objects

def clear_scene() -> None:
    # Clear previous meshes:
    for o in bpy.data.objects:
        #o.select_set(True)
        bpy.data.objects.remove(o, do_unlink=True)
    #bpy.ops.object.delete()


def new_empty_object(
        name: str = "Unknown"
):
    # Create mesh 
    me = bpy.data.meshes.new(name)
    # Create object
    ob = bpy.data.objects.new(name, me)

    bpy.context.collection.objects.link(ob)

    return ob


def duplicate(
        obj,
        new_name: str
):
    new_obj = obj.copy()
    new_obj.data = obj.data.copy()
    new_obj.name = new_name
    bpy.context.collection.objects.link(new_obj)
    return new_obj


def delete_obj(
        obj
) -> None:
    set_mode("OBJECT")
    # Unselect all other objects:
    for o in bpy.data.objects:
        o.select_set(False)
    # Select object to delete:
    obj.select_set(True)
    bpy.ops.object.delete()


def create_noise_texture(
        freq
):
    tex = bpy.data.textures.new("clouds_noise", type='CLOUDS')
    tex.noise_scale = freq
    return tex


# From blender's object_print3d_utils addon:
def bmesh_copy_from_object(
        obj,
        transform: bool = True,
        triangulate: bool = True,
        apply_modifiers: bool = False
) -> bmesh.types.BMesh:
    """
    Returns a transformed, triangulated copy of the mesh
    """

    assert obj.type == 'MESH'

    if apply_modifiers and obj.modifiers:
        import bpy
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
        del bpy
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    # TODO. remove all customdata layers.
    # would save ram

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm


def object_from_verts(
        verts,
        name: str = "unknown"
):
    bm = bmesh.new()  # create an empty BMesh
    for v in verts:
        bm.verts.new(v.co)

    obj = new_empty_object(name)
    bm.to_mesh(obj.data)
    return obj


#############################################################################
# Settings

def set_mode(
        mode
) -> None:
    try:
        bpy.ops.object.mode_set(mode=mode)
    except:
        pass


#############################################################################
# Custom classes

class BoundingBox:

    def __init__(
            self,
            max_dim: float = None,
            vec_min: mathutils.Vector = None,
            vec_max: mathutils.Vector = None,
            bound_box: list = None
    ):
        if max_dim is not None:
            max_val = max_dim * 0.5
            self.vec_min = mathutils.Vector((-max_val, -max_val, -max_val))
            self.vec_max = mathutils.Vector((max_val, max_val, max_val))
            self.max_val = max_val
        elif vec_min is not None and vec_max is not None:
            self.vec_min = vec_min
            self.vec_max = vec_max
            self.max_val = max(self.vec_min[0], self.vec_min[1], self.vec_min[2],
                               self.vec_max[0], self.vec_max[1], self.vec_max[2])
        elif bound_box is not None:
            x_s = [v[:][0] for v in bound_box]
            y_s = [v[:][0] for v in bound_box]
            z_s = [v[:][0] for v in bound_box]
            self.vec_min = mathutils.Vector((min(x_s), min(y_s), min(z_s)))
            self.vec_max = mathutils.Vector((max(x_s), max(y_s), max(z_s)))

            self.max_val = max(self.vec_min[0], self.vec_min[1], self.vec_min[2],
                               self.vec_max[0], self.vec_max[1], self.vec_max[2])
        else:
            raise ArgumentError("Need to pass either max_val or vec_min and "
                                "vec_max or bound_box to BoundingBox constructor!")

    #    def __init__(self, max_val:float):
    #        print("IT'S A FLOAT", max_val, type(max_val))
    #        self.vec_min = mathutils.Vector((-max_val, -max_val, -max_val))
    #        self.vec_max = mathutils.Vector((max_val, max_val, max_val))
    #        self.max_val = max_val

    #    def __init__(self, bound_box:list):
    #        print("BOUND_BOX", bound_box, type(bound_box))
    #        print(bound_box[0:3], bound_box[3:6])
    #        self.vec_min = mathutils.Vector(bound_box[0:3])
    #        self.vec_max = mathutils.Vector(bound_box[3:6])

    #        self.max_val = max(self.vec_min[0], self.vec_min[1], self.vec_min[2],
    #                self.vec_max[0], self.vec_max[1], self.vec_max[2])

    @property
    def min_x(
            self
    ) -> float:
        return self.vec_min.x

    @property
    def max_x(
            self
    ) -> float:
        return self.vec_max.x

    @property
    def min_y(
            self
    ) -> float:
        return self.vec_min.y

    @property
    def max_y(
            self
    ) -> float:
        return self.vec_max.y

    @property
    def min_z(
            self
    ) -> float:
        return self.vec_min.z

    @property
    def max_z(
            self
    ) -> float:
        return self.vec_max.z

    def __repr__(
            self
    ) -> str:
        return f"(min: {self.vec_min}, max: {self.vec_max})"

    # def __repr__(self):
    #    return self.__str__()

    @property
    def dimensions(
            self
    ) -> mathutils.Vector:
        return self.vec_max - self.vec_min


class MaterialFactory:

    def __init__(self, unique_colors=False):
        """
        
        Args:
            unique_colors: If True, will raise an error when an attempt is made to use the same color twice
        """
        self.assert_unique_colors = unique_colors
        if self.assert_unique_colors:
            self.used_colors = {}

    def new_material(self, objs, col, material_name=None):
        
        if material_name == None:
            material_name = objs[0].name

        if self.assert_unique_colors:
            for name, ucol in self.used_colors.items():
                if ucol == col:
                    raise ValueError(f"Color {col} cannot be used for {objs[0].name}, was already used for {material_name}!")

        # Get or create material
        mat = bpy.data.materials.get(material_name)
        if mat is None:
            mat = bpy.data.materials.new(name=material_name)

        # Set color:
        mat.diffuse_color = col
        mat.metallic = 0.65
        mat.roughness = 0.17
        mat.specular_intensity = 0.5

        # Assign it to objects:
        for obj in objs:
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        if self.assert_unique_colors:
            self.used_colors[material_name] = col


##############################################################################
# Cleaning operations

def delete_islands(
        obj
) -> None:
    final_name = obj.name
    set_mode("EDIT")

    # Deselect everythig except for the obj:
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)

    # split into loose parts
    bpy.ops.mesh.separate(type='LOOSE')
    # object mode
    #bpy.ops.object.mode_set(mode='OBJECT')
    set_mode("OBJECT")

    parts = bpy.context.selected_objects
    # sort by number of verts (last has most)
    parts.sort(key=lambda o: len(o.data.vertices))
    # print
    for part in parts:
        print(part.name, len(part.data.vertices))
        part.select_set(True)

    parts[-1].select_set(False)
    largest = parts[-1]
    print("largest (to keep):", largest.name, len(largest.data.vertices))

    bpy.ops.object.delete()

    largest.name = final_name
    largest.select_set(True)

    return largest
    # parts = bpy.context.selected_objects
    # for part in parts:
    #    print("still there:", part.name, len(part.data.vertices))


def remove_non_manifolds(
        obj
) -> None:
    # Clean up possible non-manifolds
    cleanup_attempts = 0
    is_clean = False
    while not is_clean and cleanup_attempts < 15:
        is_clean = True
        cleanup_attempts = cleanup_attempts + 1

        set_mode("EDIT")
        # bpy.ops.mesh.select_mode(type="VERT")  # shows "CANCELLED" in the GUI
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold()

        mesh = bmesh.from_edit_mesh(obj.data)
        mesh.verts.ensure_lookup_table()

        non_manifold_verts = [v for v in mesh.verts if v.select]
        if len(non_manifold_verts) > 0:
            is_clean = False
            bpy.ops.mesh.dissolve_verts()
            bpy.ops.mesh.vert_connect_concave()
    print("Before delete islands: "+ str(len(obj.data.vertices)))
    obj = delete_islands(obj)
    print("After delete islands: "+ str(len(obj.data.vertices)))
    return obj


def clean_mesh(
        obj,
        rnd: random.Random = random.Random(),
        remesh_mode: str = "SMOOTH",
        remesh_octree_depth=4,
        remesh_scale: float = 0.5,
        target_minimum_voxel_size = 0.01,
        subdiv: bool = True,
        add_crease: bool = True,
) -> None:
    mesh = obj.data
    set_mode("OBJECT")

    # Remeshing
    remesh = obj.modifiers.new(type="REMESH", name="remesh")
    if remesh_mode == "SMOOTH":
        remesh.mode = "SMOOTH"
        remesh.octree_depth = remesh_octree_depth
        remesh.scale = remesh_scale
    else:
        # Make elements roughly target_minimum_voxel_size large:
        remesh.mode = "VOXEL"
        remesh.voxel_size = target_minimum_voxel_size
        remesh.adaptivity = 4*target_minimum_voxel_size   # ... but allow for larger elements as well!


    # remesh.sharpness = 0.1
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="remesh")

    # Subdivision - low pass filter, smoothes edges
    if subdiv:
        obj.modifiers.new(type="SUBSURF", name="subdivision")
        set_mode("EDIT")

        if add_crease and len(mesh.vertices) > 0:
            # Randomly add creased edges:
            # creased edges are retained and avoid everything being over-smoothed
            for k in range(0, 2):
                if rnd.random() > 0.2:
                    edge_len = rnd.randint(3, 10)
                    crease = rnd.uniform(0.7, 0.9)
                    # Start with a random vertex:
                    vert = mesh.vertices[rnd.randint(0, len(mesh.vertices) - 1)]
                    for i in range(0, edge_len):
                        edges = get_edges(mesh, vert)
                        edge = edges[rnd.randint(0, len(edges) - 1)]
                        edge.crease = crease
                        vert = other_vert(mesh, edge, vert)

        set_mode("OBJECT")
        bpy.ops.object.modifier_apply(modifier="subdivision")


def decimate(
        obj,
        target_verts=None
) -> None:
    if target_verts is None:
        target_verts = int(len(obj.data.vertices) * 0.5)

    target_ratio = target_verts / len(obj.data.vertices)
    print("target_ratio:", target_ratio)
    set_mode("OBJECT")

    # Remeshing
    decimate = obj.modifiers.new(type="DECIMATE", name="decimate")
    decimate.decimate_type = "COLLAPSE"
    decimate.ratio = target_ratio
    # remesh.sharpness = 0.1
    # obj.select_set(True)
    # bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="decimate")


def triangulate(
        obj
) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    # V2.79 : bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(obj.data)
    bm.free()


def resort_mesh(
        bm
) -> bmesh.types.BMesh:
    """ Sort mesh vertices by their positions. Makes up for non-deterministic methods.

    Some functions in blender seem to be non-deterministic, likely due to parallelization.
    This results in our mesh vertices and faces not necessarily being in the same order
    each run. This function seeks to correct this, by re-creating the mesh with sorted
    vertices and faces.
    """

    bm_new = bmesh.new()
    bm.verts.ensure_lookup_table()
    verts = [(i, v) for i, v in enumerate(bm.verts)]

    def coords_to_key(c):
        return c.x, c.y, c.z

    def vert_to_key(a):
        # actual verts are stored in the second element of the tuples:
        # return coords_to_key( a[1].co )
        return coords_to_key(a[1].co)

    verts_sorted = sorted(verts, key=vert_to_key)
    old_to_new_vert_indices = {}
    for orig in verts_sorted:
        bm_new.verts.new(orig[1].co)
        old_to_new_vert_indices[orig[0]] = len(bm_new.verts) - 1
    bm_new.verts.ensure_lookup_table()

    def face_to_key(f):
        m1 = f.calc_center_median()
        return coords_to_key(m1)
        # return sort_coords( m1, m2 )

    faces_sorted = sorted(bm.faces, key=face_to_key)
    for f in faces_sorted:
        new_verts = []
        for v in f.verts:
            old_index = v.index
            new_index = old_to_new_vert_indices[old_index]
            new_vert = bm_new.verts[new_index]
            new_verts.append(new_vert)
        bm_new.faces.new(new_verts)

    return bm_new


##############################################################################
# Custom selections

def get_edges(
        mesh,
        vert
):
    edges = []
    for e in mesh.edges:
        if e.vertices[0] == vert.index or e.vertices[1] == vert.index:
            edges.append(e)
    return edges


def other_vert(
        mesh,
        edge,
        vert
):
    if vert.index == edge.vertices[0]:
        return mesh.vertices[edge.vertices[1]]
    return mesh.vertices[edge.vertices[0]]


def select_more(
        bm,
        ntimes=1
) -> None:
    for i in range(0, ntimes):
        sel_verts = [v for v in bm.verts if v.select]
        for v in sel_verts:
            for f in v.link_faces:
                f.select_set(True)
    # sel_edges = [ed for ed in bm.edges if ed.select]
    # for ed in sel_edges:
    #   for f in ed.link_faces:
    #       f.select_set(True)


def random_point_within_bounds(
        bm,
        rng: random.Random
) -> mathutils.Vector:
    """ Select a random position within the bmesh's bounds
    
    Arguments:
        - bm: Bmesh 
        - rng (Instance of random.Random()): Random number generator to (re-)use to get
            consistent behavior
    Returns:
        - mathutils.Vector: a random position within the axis aligned bounding box of bm
    """
    vx = [v.co.x for v in bm.verts]
    vy = [v.co.y for v in bm.verts]
    vz = [v.co.z for v in bm.verts]

    min_x = min(vx)
    max_x = max(vx)
    min_y = min(vy)
    max_y = max(vy)
    min_z = min(vz)
    max_z = max(vz)

    px = rng.uniform(min_x, max_x)
    py = rng.uniform(min_y, max_y)
    pz = rng.uniform(min_z, max_z)

    p = mathutils.Vector((px, py, pz))
    return p

# Retrieve a random point inside a mesh:
def random_point_within_mesh( obj, max_tries=1000, rnd=random ):
    """ Attempts to retrieve a random point within a mesh. 
    
    If no such point is found after max_tries tries, raises a ValueError.
    """
    tries = 0
    minX, maxX, minY, maxY, minZ, maxZ = get_obj_extent(obj)
    while tries < max_tries:
        x = rnd.uniform(minX, maxX)
        y = rnd.uniform(minY, maxY)
        z = rnd.uniform(minZ, maxZ)
        p = mathutils.Vector((x,y,z))
        p = obj.matrix_world @ p
        if point_inside_mesh( obj, p ):# and distToObject( p, obj ) > distToWall:
            return p
        tries += 1
    raise ValueError(f"Could not find random point inside object {obj.name}. Giving up." )



def get_random_face(
        bm: bmesh.types.BMesh,
        rng: random.Random
) -> bmesh.types.BMFace:
    """ Deterministic method of getting a random face.

    This should work even if the face and vertex indices have changed before.
    Parameters:
    - bm (bmesh):
    - rng (Instance of random.Random()): Random number generator to (re-)use to get
    consistent behavior

    Returns: A face selected from bmesh.faces. If bmesh verts and face positions are the same
            and rng is in the same state, this should always be the same face.
    """
    p = random_point_within_bounds(bm, rng)

    closest_face = None
    min_dist_squared = float('inf')
    for f in bm.faces:
        dist_squared = (f.calc_center_bounds() - p).length_squared
        if dist_squared < min_dist_squared:
            min_dist_squared = dist_squared
            closest_face = f
    return closest_face


def get_random_vert(
        bm: bmesh.types.BMesh,
        rng: random.Random
) -> bmesh.types.BMVert:
    """ Deterministic method of getting a random vertex

    This should work even if the face and vertex indices have changed before.
    Parameters:
    - bm (bmesh):
    - rng (Instance of random.Random()): Random number generator to (re-)use to get
    consistent behavior

    Returns: A vertex selected from bmesh.verts. If bmesh verts and face positions are the
        same and rng is in the same state, this should always be the same vertex.
    """

    p = random_point_within_bounds(bm, rng)

    closest_vert = None
    min_dist_squared = float('inf')
    for v in bm.verts:
        dist_squared = (v.co - p).length_squared
        if dist_squared < min_dist_squared:
            min_dist_squared = dist_squared
            closest_vert = v
    return closest_vert


def get_neighbor_verts(
        vert: bmesh.types.BMVert
) -> List[bmesh.types.BMVert]:
    v = []
    for edge in vert.link_edges:
        v.append(edge.other_vert(vert))
    return v


def select_surface_path(
        surface_bm: bmesh.types.BMesh,
        start_node_id: int = None,
        direction: Tuple[float, float, float] = None,
        path_length: float = 0.1,
        rnd: random.Random = random.Random()
) -> List[int]:
    """ Select connected nodes along a surface.

    When selecting the next node, this function
    always looks at previously selected nodes and tries to select the new node along the
    same direction. This makes the path face roughly into a single direction.

    Parameters:
        surface_bm (Bmesh):
            The mesh topology
        start_node_id (int):
            The ID of the node for which neighbors are to be found.
            If None, a random node will be selected. Only nodes where the normal faces upwards
            will be considered in this case.
        direction (tuple of 3 floats):
            Direction in which the path should (roughly) go, starting at the node startNodeID.
            If None, a random direction will be selected.
        path_length (float):
            The algorithm will stop selecting more nodes as soon as the path is longer than
            pathLength. This means that it's possible that pathLength is exceeded.
        rnd:
            Random number generator to (re-)use to get consistent behavior

    Returns: list of int: IDs of the vertices that form the path

    """

    # If no start node ID is given, select a random one:
    if start_node_id is None:
        start_vert = get_random_vert(surface_bm, rnd)
        start_node_id = start_vert.index
        # start_node_id = int(rnd.random()*len(surface_bm.verts))
        # Only select start point where the normal faces upwards (positive Y)
        # if normals.GetTuple3( startNodeID )[1] < 0.3:
        #    startNodeID = None

    if direction is None:
        # Select a random direction:
        direction = mathutils.Vector(
            [rnd.random() - 0.5, rnd.random() - 0.5, rnd.random() - 0.5]
        )
        norm = direction.length
        if norm == 0:  # unlikely
            direction = np.asarray([1, 0, 0])
        else:
            direction = direction.normalized()

    path_nodes = [start_node_id]
    cur_vert = surface_bm.verts[start_node_id]
    cur_node_id = start_node_id
    cur_path_length = 0
    while cur_path_length < path_length:
        # Select next node:
        connected_verts = get_neighbor_verts(cur_vert)
        connected_verts = [v for v in connected_verts if v.index not in path_nodes]
        if len(connected_verts) == 0:
            break

        # Project current direction forward, select point closest to this projection:
        projection = cur_vert.co + direction
        dist_squared = np.inf
        next_node_id = -1
        for i in range(len(connected_verts)):
            p = connected_verts[i].co
            cur_dist_squared = (p - projection).length
            if cur_dist_squared < dist_squared:
                dist_squared = cur_dist_squared
                next_node_id = connected_verts[i].index

        assert next_node_id != -1, "Could not find suitable next point for path."

        next_vert = surface_bm.verts[next_node_id]
        direction = 0.9 * direction + 0.1 * (next_vert.co - cur_vert.co)
        cur_path_length += (next_vert.co - cur_vert.co).length
        path_nodes.append(cur_node_id)

        cur_node_id = next_node_id
        cur_vert = next_vert

    return path_nodes


def select_random_partial_surface(
        obj,
        target_surface_amount: float,
        rnd: random.Random = random.Random(),
        name: str = "unknown"
):
    bm = bmesh.new()  # create an empty BMesh
    bm.from_mesh(obj.data)  # fill it in from a Mesh

    center_face = get_random_face(bm, rnd)

    # Turn from relative value into absolute:
    tgt = target_surface_amount * get_object_surface(bm)

    cur_surface_amount = 0
    selected_faces = set()
    front = set([center_face])
    while cur_surface_amount < tgt and len(front) > 0:
        cur_face = front.pop()
        cur_surface_amount += cur_face.calc_area()
        selected_faces.add(cur_face)
        for e in cur_face.edges:
            for f in e.link_faces:
                if f not in selected_faces:
                    front.add(f)

    selected_verts = set()
    for f in selected_faces:
        for v in f.verts:
            if v.is_valid:
                selected_verts.add(v)

    obj = object_from_verts(selected_verts, name)

    return obj


def unselect_all() -> None:
    """Unselect all objects in the scene."""
    for o in bpy.context.scene.objects:
        o.select_set(False)

    # careful: this does not work!
    # for o in bpy.data.objects:
    #    o.select_set(True)

##############################################################################
# Manipulations
# manipulate the object

def enlarge_to_fit(
        surrounding_object,
        internal_object,
        rnd: random.Random = random.Random(),
        padding: float = 0.01
):
    """ Enlarge surrounding_object until internal_object lies entirely inside it.
    """

    assert padding >= 0

    def find_external_point():
        """ Find point from 'internal_object' which lies _outside_ surrounding_object."""
        l = [v for v in internal_object.data.vertices]
        rnd.shuffle(l)
        for v in l:
            if not point_inside_mesh(surrounding_object, v.co):
                return v
        return None

    external_point = find_external_point()
    num_rescales = 0
    while external_point is not None and num_rescales < 10:
        found, closest, _, _ = surrounding_object.closest_point_on_mesh(external_point.co)
        dist_closest = closest.length
        dist_external = external_point.co.length + padding
        rescale = dist_external / dist_closest
        surrounding_object.scale = surrounding_object.scale * rescale
        surrounding_object.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        external_point = find_external_point()
        num_rescales += 1
    return surrounding_object


def push_outside(
        pushed_obj,
        static_obj,
        offset: float = 0.01,
        rnd: random.Random = random.Random()
):
    """ Move pushed_obj until it no longer intersects with static_obj.
    """

    axis = mathutils.Vector((rnd.random() - 0.5, rnd.random() - 0.5, rnd.random() - 0.5))
    if axis.length == 0:  # unlikely
        axis = mathutils.Vector((0, 0, 1))
    axis.normalize()

    def find_extreme_point_along_axis(obj, plane_orig, plane_normal, farthest=False):
        """ Find the point in obj which is closest to (or fathest from) the plane
        """

        if not farthest:
            dist_min = math.inf
            # Calculate the distance from each point p onto the plane:
            for p in obj.data.vertices:
                v = p.co - plane_orig
                dist = v.dot(axis)
                # Look for the point which is closest to the plane:
                if dist < dist_min:
                    dist_min = dist
            return dist_min
        else:
            dist_max = 0
            # Calculate the distance from each point p onto the plane:
            for p in obj.data.vertices:
                v = p.co - plane_orig
                dist = v.dot(axis)
                # Look for the point which is closest to the plane:
                if dist > dist_max:
                    dist_max = dist
            return dist_max

    # We create a plane with "axis" as the normal vector. The plane's origin
    # should be outside both objects.
    max_dist_from_origin = 0
    for bounding_box_corner in pushed_obj.bound_box:
        corner = mathutils.Vector(bounding_box_corner)
        max_dist_from_origin = max(max_dist_from_origin, corner.length)
    for bounding_box_corner in static_obj.bound_box:
        corner = mathutils.Vector(bounding_box_corner)
        max_dist_from_origin = max(max_dist_from_origin, corner.length)

    plane_orig = -axis * max_dist_from_origin
    closest = find_extreme_point_along_axis(pushed_obj, plane_orig, axis)
    farthest = find_extreme_point_along_axis(static_obj, plane_orig, axis,
                                             farthest=True)

    dist = farthest - closest
    pushed_obj.location += axis * dist  # +offset)
    pushed_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return pushed_obj


def perturb_direction(
        direction: mathutils.Vector,
        min_alpha: float = 0.0,
        max_alpha: float = 360.0,
        rnd: random.Random = random.Random()
) -> mathutils.Vector:
    """ Perturbates a direction by applying a rotation over a random axis

    Note: This function is not entirely fair, some directions might be chosen a bit
        more often than others, due to the way the axis is chosen. However, for our
        purposes, it should be fine.

    Args:
        direction: starting force direction that has to be perturbed.
        min_alpha: Minimum angle to perturb the direction in degrees.
        max_alpha: Maximum angle to perturb the direction in degrees.
        rnd: Random number generator to use

    Returns:
        direction: Rotated direction
    """

    ang = rnd.uniform(min_alpha, max_alpha) * math.pi / 180
    vec = mathutils.Vector((
        rnd.uniform(-1, 1),
        rnd.uniform(-1, 1),
        rnd.uniform(-1, 1)
    ))
    axis = vec.normalized()
    rot = mathutils.Quaternion(axis, ang)

    direction = direction.copy()  # don't modify original?
    direction.rotate(rot)
    return direction


def random_scale(
        bm,
        i,
        extrusions,
        verts,
        rnd: random.Random = random.Random()
) -> None:
    # Randomly discard some of the vertices:
    vert_coords = []
    for vert in verts:
        if rnd.random() > 0.3:
            vert_coords.append(vert.co)
    # Make sure you didn't discard all verts:
    if len(vert_coords) == 0:
        vert_coords = [vert.co for vert in verts]

    pivot = sum(vert_coords, mathutils.Vector()) / len(vert_coords)

    min_scale = (extrusions - i) / extrusions * 0.5 + 0.3
    max_scale = min_scale + 0.6
    scale = rnd.uniform(min_scale, max_scale)  # - abs((float(i)-extrusions/2)/(extrusions/2))*0.4
    # bpy.ops.transform.resize(value=(scale,scale,scale));
    # bmesh.ops.scale(bm, vec=mathutils.Vector((scale,scale,scale)), verts=verts, space=mat)
    for vert in verts:
        vert.co = pivot + (vert.co - pivot) * scale

def rotate_towards(obj: bpy.types.Object,
                   target_pos: mathutils.Vector,
                   forward_vec=mathutils.Vector((0, 1, 0)),
                   roll_ang: float = 0,
                   ):
    """ Make the object point its forward_vec at target pos

    """

    assert forward_vec.length_squared > 0, f"forward_vec may not be zero!"


    forward_vec = forward_vec.normalized()

    # target axis to look at:
    target_axis = (target_pos - obj.location).normalized()

    assert target_axis.length_squared > 0, f"Cannot look at {target_pos}, object location ({obj.location}) is too close!"

    # get axis to rotate around:
    rot_axis = forward_vec.cross(target_axis)
    rot_ang = target_axis.angle(forward_vec)

    rot = mathutils.Quaternion(rot_axis, rot_ang)
    rot_roll = mathutils.Quaternion(target_axis, roll_ang)

    rot_full = rot_roll @ rot

    # Apply rotation:
    # self.cam.rotation = rot.to_matrix()
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rot_full


def shade_smooth(
        obj: bpy.types.Object
) -> None:
    mesh = obj.data
    for f in mesh.polygons:
        f.use_smooth = True
    for e in mesh.edges:
        e.use_edge_sharp = False
    obj.data.update()


##############################################################################
# Checks and calculations
# calculate things based on information of the object

def get_obj_extent( obj ):
    """ Return the bounding box of an object as a collection of min/max values
    """
    minX, minY, minZ = float('Inf'),float('Inf'),float('Inf')
    maxX, maxY, maxZ = -float('Inf'), -float('Inf'), -float('Inf')
    for v in obj.bound_box:
        if v[0] < minX:
            minX = v[0]
        if v[1] < minY:
            minY = v[1]
        if v[2] < minZ:
            minZ = v[2]
        if v[0] > maxX:
            maxX = v[0]
        if v[1] > maxY:
            maxY = v[1]
        if v[2] > maxZ:
            maxZ = v[2]
    return minX, maxX, minY, maxY, minZ, maxZ

def get_center_point( obj ):
    vec = mathutils.Vector()
    for v in obj.bound_box:
        vec += mathutils.Vector(v)
    center = vec/len(obj.bound_box)
    return center
        

def get_object_surface(
        bm: bmesh.types.BMesh
) -> float:
    surface = 0
    for f in bm.faces:
        surface += f.calc_area()
    return surface


def first_vert_pos_along_axis(
        obj,
        axis
):
    """ Return the position of the first vertex when sorting all verts along axis
    """

    assert len(obj.data.vertices) > 0, "Object has no vertices!"

    diag = obj.dimensions.length

    axis_norm = axis.normalized() * diag

    local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in obj.bound_box), mathutils.Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center

    start_point = global_bbox_center + axis_norm

    min_dist2 = 0
    closest = None
    for v in obj.data.vertices:
        dist2 = (start_point - v.co).length_squared
        if dist2 > min_dist2:
            closest = v
            min_dist2 = dist2
    return closest.co


def edge_fully_outside(
        obj,
        edge
) -> bool:
    # If any point lies inside the mesh, the edge is not fully outside:
    for i in range(len(edge)):
        v = edge[i]
        if point_inside_mesh(obj, v):
            return False

    # Iterate over all edges in the vertex list and check if they intersect the mesh:
    world2obj = obj.matrix_world.inverted()
    for i in range(1, len(edge)):
        v0 = edge[i - 1]
        v1 = edge[i]
        v0 = world2obj @ v0
        v1 = world2obj @ v1
        d = v1 - v0
        if bpy.app.version >= (2, 77, 0):  # API changed
            result, _, _, _ = obj.ray_cast(v0, d.normalized(), distance=d.length)
        else:
            location, _, index = obj.ray_cast(v0, v1)
            result = not (index == -1)
        if result:
            return False
    return True


# From aothms on https://blenderartists.org/t/detecting-if-a-point-is-inside-a-mesh-2-5-api/485866/4
def point_inside_mesh(
        obj,
        point,
        depsgraph=None
) -> bool:
    axes = [mathutils.Vector((1, 0, 0)), mathutils.Vector((0, 1, 0)), mathutils.Vector((0, 0, 1))]
    outside = False

    mat = obj.matrix_world.inverted()
    # f = obj.ray_cast(mat * ray_origin, mat * ray_destination)
    for axis in axes:
        orig = mat @ point
        count = 0
        while True:
            if bpy.app.version >= (2, 77, 0):  # API changed
                result, location, normal, index = obj.ray_cast(orig, axis, depsgraph=depsgraph)
            else:
                end = orig + axis * 1e10
                location, normal, index = obj.ray_cast(orig, end)
            if index == -1:
                break
            count += 1
            orig = location + axis * 0.000001
        if count % 2 == 0:
            outside = True
            break
    return not outside


def check_side_overlap(
        obj,
        cutout,
        edge0,
        edge1,
        edge2,
        edge3
) -> bool:
    # Move into world space:
    # world2obj = obj.matrix_world.inverted()
    e0 = [cutout.matrix_world @ mathutils.Vector(b) for b in edge0]
    e1 = [cutout.matrix_world @ mathutils.Vector(b) for b in edge1]
    e2 = [cutout.matrix_world @ mathutils.Vector(b) for b in edge2]
    e3 = [cutout.matrix_world @ mathutils.Vector(b) for b in edge3]

    edge0_outside = edge_fully_outside(obj, e0)
    edge1_outside = edge_fully_outside(obj, e1)
    edge2_outside = edge_fully_outside(obj, e2)
    edge3_outside = edge_fully_outside(obj, e3)

    edges_outside = int(edge0_outside) + int(edge1_outside) + int(edge2_outside) + int(edge3_outside)

    # Exactly 2 of the edges should be fully outside for the check to succeed:
    return edges_outside == 2

    ## If all are outside, there is no overlap with the mesh:
    # if edge0_outside and edge1_outside and edge2_outside and edge3_outside:
    #    return False

    ## Two neighbouring edges must lie entirely outside:
    # if edge0_outside and edge1_outside:
    #    return True
    # if edge1_outside and edge2_outside:
    #    return True
    # if edge2_outside and edge3_outside:
    #    return True
    # if edge3_outside and edge0_outside:
    #    return True
    # return False


def get_average_edge_length(
        obj
) -> float:
    ow_matrix = obj.matrix_world
    avg_length = 0

    for e in obj.data.edges:
        v0 = e.vertices[0]
        v1 = e.vertices[1]
        v0_pos = ow_matrix @ obj.data.vertices[v0].co
        v1_pos = ow_matrix @ obj.data.vertices[v1].co
        edge_length = (v0_pos - v1_pos).length
        avg_length += edge_length

    return avg_length / len(obj.data.edges)

def random_pos_in_vicinity( obj: bpy.types.Object,
        min_dist_from_surface: float = 0.025,
        max_dist_from_surface: float = 0.25,
        rnd: random.Random = random.Random ):
    """ Get random position close to the given object's surface

    The object may be concave. A bit of ray-tracing will be done
    to ensure that the position is not inside the object.

    Args:
        obj: bpy.types.object with mesh content!
        min_dist_from_surface:

    Returns:
        mathutils.Vector: The random position
    """
    
    assert max_dist_from_surface > min_dist_from_surface
    assert min_dist_from_surface >= 0
    
    # Get bounding box in global space:
    global_bb = [ obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    
    # Get the center of the bounding box by averaging the bounding box corners:
    global_bbox_center = 0.125 * sum((mathutils.Vector(corner) for corner in global_bb), mathutils.Vector())
        
    xs = [corner.x for corner in global_bb]
    ys = [corner.y for corner in global_bb]
    zs = [corner.z for corner in global_bb]
    max_corner = mathutils.Vector((max(xs), max(ys), max(zs)))
    min_corner = mathutils.Vector((min(xs), min(ys), min(zs)))

    diagonal = (max_corner - min_corner).length
    
    # Random point _outside_ the bounding box:
    dir = mathutils.Vector((
        rnd.uniform(-1,1),
        rnd.uniform(-1,1),
        rnd.uniform(-1,1)
        ))
    dir = dir.normalized() * diagonal
    outside_pos = global_bbox_center + dir
    
    # outside_pos is definitely _outside_ the bounding box.
    # So if we trace from it to the center pos, we may hit the mesh
    # (but not necessarily), because the center position may
    # also be outside the mesh, for example in a concave object.
    dir_to_center = (global_bbox_center-outside_pos).normalized()
    #depsgraph = bpy.context.evaluated_depsgraph_get()
    #print(obj.evaluated_get(depsgraph))
    #obj_eval = obj.evaluated_get( depsgraph )
    #print(obj_eval)
    #print(obj_eval.is_evaluated)
    #print(obj_eval.data)
    #print(obj_eval.data.vertices)
    #set_mode( "OBJECT" )
    #set_mode( "EDIT" )
    #set_mode( "OBJECT" )
    #print("vis?", obj.hide_render, obj_eval.hide_render, obj.hide_viewport, obj_eval.hide_viewport)
    #for i in range(30):
        #bpy.context.scene.frame_set( i )
    bpy.context.view_layer.update()
    result, location, normal, index = obj.ray_cast(
            origin=outside_pos,
            direction=dir_to_center )
            #depsgraph = depsgraph)
        #print("\tsuccess!")
    
    # let the position get as close as the bbox center...
    closest_pos = global_bbox_center
    # ... unless the ray hit the mesh along the way:
    if result:
        # In this case, let the closest position be close to the
        # surface:
        closest_pos = location - 0.1*dir_to_center
    
    # The farthest point can now be calculated by the closest position
    # plus an offset outwards:
    farthest_pos = closest_pos - dir_to_center*max_dist_from_surface
    
    # select a random position between farthest and closest pos:
    random_pos = rnd.random()*(farthest_pos-closest_pos) + closest_pos
    
    return random_pos

    
#############################################################################
# Camera  

def img_type_to_extension(img_type):
    """ This attempts to return an image file extension for a blender image type.
    Note that only common types are supported at the moment, feel
    free to add more.
    See also: https://docs.blender.org/api/current/bpy_types_enum_items/image_type_items.html
    """

    if img_type == "BMP":
        return ".bmp"
    elif img_type == "PNG":
        return ".png"
    elif img_type == "JPEG":
        return ".jpg"
    elif img_type == "OPEN_EXR":
        return ".exr"
    else:
        raise NotImplementedError(f"Don't know extension for image type {img_type}!")


#########################################################
## Mesh import

def import_mesh(
        filename: str
):
    prev_objects = [o for o in bpy.context.scene.objects]
    if filename.endswith(".stl"):
        bpy.ops.import_mesh.stl(filepath=filename)
    elif filename.endswith(".ply"):
        bpy.ops.import_mesh.ply(filepath=filename)
    elif filename.endswith(".obj"):
        bpy.ops.import_scene.obj(filepath=filename)
    else:
        raise ValueError(f"Do not know how to import '{filename}'. No import function implemented for this file type.")
    # Return the new objects:

    new_objects = [o for o in bpy.context.scene.objects if o not in prev_objects]
    for o in new_objects:
        o.select_set(False)
    return new_objects[0]


#########################################################
## Mesh export

def export(
        obj,
        outdir: str,
        filename: str
) -> None:
    if filename.endswith(".stl"):
        export_stl(obj, outdir, filename)
    elif filename.endswith(".ply"):
        export_ply(obj, outdir, filename)
    elif filename.endswith(".obj"):
        export_obj(obj, outdir, filename)
    else:
        raise ValueError(f"Do not know how to export '{filename}'. No export function implemented for this file type.")


def export_stl(
        obj,
        outdir: str,
        filename: str
) -> None:
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    filepath = os.path.join(outdir, str(filename))
    bpy.ops.export_mesh.stl(filepath=filepath, check_existing=False, use_selection=True, filter_glob="*.stl",
                            ascii=True, use_mesh_modifiers=True, axis_forward='Y', axis_up='Z', global_scale=1.0)
    print("Exported mesh to " + filepath)


def export_ply(
        obj,
        outdir: str,
        filename: str
) -> None:
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    filepath = os.path.join(outdir, str(filename))
    bpy.ops.export_mesh.ply(filepath=filepath, check_existing=False, filter_glob="*.ply", use_ascii=False,
                            use_selection=True, use_mesh_modifiers=True, axis_forward='Y', axis_up='Z',
                            global_scale=1.0, use_normals=False, use_uv_coords=False, use_colors=False)
    print("Exported mesh to " + filepath, len(obj.data.vertices))


def export_obj(
        obj,
        outdir: str,
        filename: str
) -> None:
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    filepath = os.path.join(outdir, str(filename))
    bpy.ops.export_scene.obj(filepath=filepath, check_existing=False, filter_glob="*.obj", use_animation=False,
                             use_selection=True, use_mesh_modifiers=True, axis_forward='Y', axis_up='Z',
                             global_scale=1.0)
    print("Exported mesh to " + filepath, len(obj.data.vertices))
