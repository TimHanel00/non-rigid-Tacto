import re
import numpy as np
from inspect import cleandoc
from math import dist
from pathlib import Path
from xml.etree import ElementTree
from typing import Tuple, List, Dict, Union, TypeVar, Type
from copy import deepcopy

from .branch import Branch, BranchFactory, StraightFactory, SineGeneratedFactory
from core.log import Log

# this needs reworking to avoid for loops and boilerplate code
# array operations, e.g. numpy? Python maps? Pre-built binary tree structure?
# - binarytree can't do composite node values
# edges should be a dataclass, nodes a NamedTuple

# for typing the copy constructor
TreeType = TypeVar('TreeType', bound='VascularTree')

class VascularTree:
    """
    Provides I/O and utility functions for representation of vascular trees.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    # node_attributes: additional attributes to fetch for nodes,
    # besides their position and node id
    # edge_attributes: additional attributes to fetch for edges,
    # besides their radius and source- /target node ids
    def __init__(self, filepath: str=None, **kwargs) -> None:
        """
        Initializes the vascular tree, optionally from a GXL or GRAPHML file.

        Attributes that are to be taken into account when exporting the tree
        must be read from the input file or added to all node or edge dictionaries
        CONSISTENTLY later.
        
        Args:
            filepath: Path to GXL or GRAPHML file with tree structure information.
                If not provided, tree will be initialised empty.
        """
        self.nodes = dict()
        # a node is: {'id':id, 'pos':(x,y,z)}
        # nodes is: {id: node}, where type(id)=int
        # IDs seem to start at 0
        self.edgelist = list()
        # edgelist is: [edge]
        # an edge is: {"source_id": source_node_id, "target_node_id": target_id, "radius_avg": radius}
        # potentially more attributes added to that dictionary later

        if filepath is not None:
            self._create_from_file(filepath, **kwargs)

    def _create_from_file(
            self,
            filepath: str,
            node_attributes: List[str] = [],
            edge_attributes: List[str] = []
    ) -> None:
        """
        Read and store tree structure from a GXL or GRAPHML file.

        If attributes other than the node positions and edge radii
        should be retrieved from the file (e.g. branch tortuosities),
        this must be specified using the
        node_attribute and edge_attribute parameters.

        Args:
            filepath: Path to GXL or GRAPHML file that is to be parsed
            node_attributes: Names of additional node attributes that should be read
                from the input file. Node positions should not be specified here.
                They are read automatically because every node must have a position.
            edge_attributes: Names of additional edge attributes that should be read
                from the input file. Edge radii should not be specified here.
                They are read automatically because every edge must have a radius.

        """
        tree_path = Path(filepath)
        extension = tree_path.suffix
        if not tree_path.exists():
            raise FileNotFoundError
        if extension not in (".gxl", ".graphml"):
            raise ValueError

        if extension == ".gxl":
            self._parse_GXL(tree_path)
        else:
            self._parse_GRAPHML(tree_path, node_attributes=node_attributes,
                                edge_attributes=edge_attributes)

    @classmethod
    def create_from_tree(
            cls: Type[TreeType],
            tree: TreeType
    ) -> TreeType:
        """
        Instantiate a new VascularTree from a VascularTree instance by copying
        the node and edge information.

        Intended to be used for conversions from superclass to subclasses.
        """
        # create empty tree
        new_tree = cls()
        # copy information
        new_tree.nodes = deepcopy(tree.nodes)
        new_tree.edgelist = deepcopy(tree.edgelist)
        return new_tree

    @staticmethod
    def _get_attr(xml_node, name: str) -> float:
        """
        Fetches arbitrary attribute from GRAPHML edge or node entry

        Args:
            xml_node: the xml node that contains the attribute
            name: attribute name
        """

        xml_entries = xml_node.findall(f"data[@key='{name}']")
        if len(xml_entries) != 1:
            raise ValueError
        try:
            return float(xml_entries[0].text)
        except ValueError:
            return xml_entries[0].text

    @staticmethod
    def _get_tuple(node, name: str) -> Union[Tuple[float, ...], None]:
        """
        Fetches tuple attribute from GXL node entry

        Args:
            node: the xml node that contains the attribute
            name: attribute name
        """

        # findall is guaranteed to return attributes in document order
        xml_entries = node.findall(f"attr[@name='{name}']/tup/float")  # list of xml.etree.ElementTree.Element
        # if attribute (name) not found, findall() returns an empty list
        if xml_entries:
            xml_entries_float = (float(entry.text) for entry in xml_entries)
            return tuple(xml_entries_float)
        else:
            return None

    @staticmethod
    def _get_float(node, name: str) -> Union[float, None]:
        """
        Fetches float attribute from GXL node entry

        Args:
            node: the xml node that contains the attribute
            name: attribute name
        """

        xml_entries = node.findall(f"attr[@name='{name}']/float")
        # if attribute (name) not found, findall() returns an empty list
        if xml_entries:
            return float(xml_entries[0].text)
        else:
            return None

    def _parse_GXL(self, tree_path: Path) -> None:
        """
        Initializes tree from VascuSynth GXL file
        """

        parser_tree = ElementTree.parse(tree_path)

        for xml_node in parser_tree.findall("graph/node"):

            id = int(xml_node.get("id")[1:])
            pos = self._get_tuple(xml_node, " position")
            node = {"id": id, "pos": pos}
            self.nodes[id] = node  # ID saved redundantly?

        for xml_edge in parser_tree.findall("graph/edge"):

            source_id = int(xml_edge.get("from")[1:])  # Get ID of source node
            target_id = int(xml_edge.get("to")[1:])  # Get ID of target node
            radius = self._get_float(xml_edge, " radius")
            height = self._get_float(xml_edge, " curveHeight")
            dir = self._get_tuple(xml_edge, " curveDirection")

            edge = {"source_id": source_id,
                    "target_id": target_id,
                    "radius_avg": radius}

            # the curve information is only relevant for CurvedTrees and may not be present
            if height is not None:
                edge.update({"curveHeight": height})
            if dir is not None:
                edge.update({"curveDirection_X": dir[0],
                             "curveDirection_Y": dir[1],
                             "curveDirection_Z": dir[2]})
            self.edgelist.append(edge)

    def _parse_GRAPHML(
            self,
            tree_path: Path,
            node_attributes: List[str] = [],
            edge_attributes: List[str] = []
    ) -> None:
        """
        Initializes tree from GRAPHML file.
        """

        xml_string = tree_path.read_text()
        # Strip xml namespace tag to simplify parsing
        xml_string = re.sub("<graphml[^>]*>", "<graphml>", xml_string, 1)
        parser_tree = ElementTree.fromstring(xml_string)

        # Check if graph is undirected
        # VesselVio misspells the "edgedefault" attribute as "edgefault"
        undirected = "undirected" in (parser_tree.find("graph").get("edgedefault"),
                                      parser_tree.find("graph").get("edgefault"))

        # Read all nodes in tree and cache their positions
        for xml_node in parser_tree.findall("graph/node"):

            id = int(xml_node.get("id")[1:])
            x_pos = self._get_attr(xml_node, "v_X")
            y_pos = self._get_attr(xml_node, "v_Y")
            z_pos = self._get_attr(xml_node, "v_Z")

            node = {"id": id, "pos": (x_pos, y_pos, z_pos)}

            for attr in node_attributes:
                node.update({attr: self._get_attr(xml_node, f"v_{attr}")})

            self.nodes[id] = node

        for xml_edge in parser_tree.findall("graph/edge"):

            #edge = dict()
            source_id = int(xml_edge.get("source")[1:])  # Get ID of source node
            target_id = int(xml_edge.get("target")[1:])  # Get ID of target node
            radius = self._get_attr(xml_edge, "e_radius_avg")
            height = self._get_attr(xml_edge, "e_curveHeight")
            dir_x = self._get_attr(xml_edge, "e_curveDirection_X")
            dir_y = self._get_attr(xml_edge, "e_curveDirection_Y")
            dir_z = self._get_attr(xml_edge, "e_curveDirection_Z")
            # always read in curved tree info
            edge_attributes += ["curveHeight", "curveDirection_X", "curveDirection_Y", "curveDirection_Z",
                                "branching_angle", "tortuosity"]

            edge = {"source_id": source_id, "target_id": target_id, "radius_avg": radius}

            for attr in edge_attributes:
                # switch-case for errors in attribute finding
                value = self._get_attr(xml_edge, f"e_{attr}")
                if value is not None:
                    edge.update({attr: value})

            self.edgelist.append(edge)

        if undirected:
            self._orient_edges()

    def _orient_edges(self) -> None:
        """
        Best effort search for suitable edge directions.

        VesselVio generates undirected graphs during its analyses.
        Metrics such as branching angles can be computet only if edge orientations
        are known.
        This function is used to compute the orientation based on a majority vote
        for each edge.
        It attempts to find orientations such that parent segments have
        larger radii than their child segments.
        """

        swap_direction = lambda edge: edge.update({"source_id": edge["target_id"],
                                                   "target_id": edge["source_id"]})
      
        vote_swap = lambda edge: edge.update({"swap_votes": edge.get("swap_votes", 0) + 1})
        vote_no_swap = lambda edge: edge.update({"no_swap_votes": edge.get("no_swap_votes", 0) + 1})
        neighbour_edges = dict()
        
        # Find the adjacent edges for each node
        for edge in self.edgelist:

            neighbour_edges_target = neighbour_edges.get(edge["target_id"], [])
            neighbour_edges_source = neighbour_edges.get(edge["source_id"], [])
            neighbour_edges_target.append(edge)
            neighbour_edges_source.append(edge)
            neighbour_edges[edge["target_id"]] = neighbour_edges_target
            neighbour_edges[edge["source_id"]] = neighbour_edges_source 

        # Collect votes to determine optimal edge orientations 
        for node, neighbours in neighbour_edges.items():

            neighbours_sorted = sorted(neighbours, key=lambda edge: edge["radius_avg"])
            parent = neighbours_sorted[-1]
            if node != parent["target_id"]:
                vote_swap(parent)
            else:
                vote_no_swap(parent)

            for child in neighbours_sorted[:-1]:

                if node != child["source_id"]:
                    vote_swap(child)
                else:
                    vote_no_swap(child)

        # Orient edges according to collected votes
        for edge in self.edgelist:

            swap_votes = edge.pop("swap_votes", 0)
            no_swap_votes = edge.pop("no_swap_votes", 0)
            if swap_votes > no_swap_votes:
                swap_direction(edge)

    def store_graphml(self,  filepath: str) -> None:
        """
        Export the vascular tree as a GRAPHML file.

        Args:
            filepath: Path to the target file including desired name.
        """

        # Set up xml file header with attribute declarations
        xml_header = cleandoc(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
            <graphml xmlns="http://graphml.graphdrawing.org/xmlns"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
            http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
           <key id=\"v_X\" for=\"node\" attr.name=\"X\" attr.type=\"double\"/>
           <key id=\"v_Y\" for=\"node\" attr.name=\"Y\" attr.type=\"double\"/>
           <key id=\"v_Z\" for=\"node\" attr.name=\"Z\" attr.type=\"double\"/>
           <key id=\"e_radius_avg\" for=\"edge\" attr.name=\"radius_avg\" attr.type=\"double\"/>""")

        # Declare node attributes in header
        for attr in self.nodes[0].keys():
            if attr not in ['id', 'pos']:
                xml_header += f"\n<key id=\"v_{attr}\" for=\"node\" attr.name=\"{attr}\" attr.type=\"double\"/>"

        # Declare edge attributes in header
        for attr in self.edgelist[0].keys():
            if attr not in ['source_id', 'target_id', 'radius_avg']:
                xml_header += f"\n<key id=\"e_{attr}\" for=\"edge\" attr.name=\"{attr}\" attr.type=\"double\"/>"

        xml_header += "\n<graph id=\"G\" edgedefault=\"directed\">\n"

        graphml_file = open(filepath, "w")
        graphml_file.write(xml_header)

        # Insert data for nodes
        for node in self.nodes.values():

            x, y, z = node["pos"]

            # Write node positions
            node_str = cleandoc(
                f"""<node id=\"n{node['id']}\">
                    <data key=\"v_X\">{x}</data>
                    <data key=\"v_Y\">{y}</data>
                    <data key=\"v_Z\">{z}</data>""")
            
            # Write potential node attributes
            for attr in node.keys():
                if attr not in ['id', 'pos']:
                    value = node[attr]
                    node_str += f"\n<data key=\"v_{attr}\">{value}</data>"

            node_str += "\n</node>\n"
            graphml_file.write(node_str)

        # Insert data for edges
        for edge in self.edgelist:

            source_id = edge["source_id"]
            target_id = edge["target_id"]
            radius = edge["radius_avg"]

            # Write source and target node as well as edge radius
            edge_str = cleandoc(
                f"""<edge target=\"n{target_id}\" source=\"n{source_id}\">
                    <data key=\"e_radius_avg\">{radius}</data>""")

            # Write potential edge attributes
            for attr in edge.keys():
                if attr not in ['source_id', 'target_id', 'radius_avg']:
                    value = edge[attr]
                    edge_str += f"\n<data key=\"e_{attr}\">{value}</data>"

            edge_str += "\n</edge>\n"
            graphml_file.write(edge_str)

        graphml_file.write("</graph>\n</graphml>")
        graphml_file.close()

    def get_branch_factory(
            self,
            *args,
            **kwargs
    ) -> BranchFactory:
        """
        Return the type of branch factory that should be used for creating a 3D model of this tree.
        """
        return StraightFactory()

    def calculate_lengths(self) -> None:

        # warn if lengths are overwritten
        length_changed = False

        for edge in self.edgelist:

            source_pos = self.nodes[edge["source_id"]]["pos"]
            target_pos = self.nodes[edge["target_id"]]["pos"]
            calc_value = dist(source_pos, target_pos)
            if edge.get('length', calc_value) != calc_value:
                length_changed = True
            edge['length'] = calc_value
            # this only works for read-in trees or after calling SineGeneratedFactory.produce() on this tree
            if 'tortuosity' in edge:
                tortuosity = edge.get("tortuosity", 1.0)
                edge["arc_length"] = edge['length'] * tortuosity

        if length_changed:
            msg = "Warning: overwriting existing values for edge length attribute"
            Log.log("VascularTree", msg=msg)

    def _attr_by_target_id(self, attr_name: str) -> dict:

        return self._attr_by_id_dispatcher(attr_name, id_type="target_id")

    def _attr_by_source_id(self, attr_name: str) -> dict:

        return self._attr_by_id_dispatcher(attr_name, id_type="source_id")

    def _attr_by_id_dispatcher(self, attr_name: str, id_type: str) -> dict:
        """
        Maps some edge attribute to the ids of the edges source or target nodes.

        Args:
            attr_name: name of the attribute
            id_type: determines whether source or target nodes are used as keys        
        """

        attr = dict()

        for edge in self.edgelist:

            # Disregard self-loops
            if edge["source_id"] == edge["target_id"]:
                continue

            id = edge[id_type]

            # Insert attribute value for the current edge
            attr_at_id = attr.get(id, [])
            attr_at_id.append(edge[attr_name])
            # Update attr dict
            attr[id] = attr_at_id

        return attr

    def calculate_branching_angles(self) -> None:
        """
        Computes the branching angle in radian measure to each child segment.

        If there are no parent segments or multiple parent segments,
        no branching angle is computed.
        """

        if "branching_angle" in self.edgelist[0].keys():
            msg = "Warning: overwriting existing values for branching_angle attribute"
            Log.log("VascularTree", msg=msg)

        pos = lambda id: np.array(self.nodes[id]["pos"])
        source_ids = self._attr_by_target_id("source_id")
        #radii_by_id = {(edge["source_id"], edge["target_id"]): edge["radius_avg"] for edge in self.edgelist}

        for edge in self.edgelist:

            target_id = edge["target_id"]
            source_id = edge["source_id"]

            # If there is no parent segment or more than one parent segment, 
            # do not compute a branching angle
            # This occurs at all root nodes and occasionally in ground truth data
            parent_source_ids = source_ids.get(source_id, [])

            # If there are no parent segments or multiple parent segments,
            # do not compute a branching angle
            if len(parent_source_ids) != 1:
                edge["branching_angle"] = -1
                continue

            else:
                parent_source_id = parent_source_ids[0]

            child_dir = pos(target_id) - pos(source_id)
            parent_dir = pos(source_id) - pos(parent_source_id)
            # Do not assign branching angle if parent_dir or child_dir is zero
            # This can occur in ground truth data
            epsilon = 1e-9
            if np.all(np.abs(child_dir) < epsilon) or np.all(np.abs(parent_dir) < epsilon):
                edge["branching_angle"] = -1
                continue

            child_dir /= np.linalg.norm(child_dir)
            parent_dir /= np.linalg.norm(parent_dir)

            cos_of_angle = np.dot(child_dir, parent_dir)
            # Clip cos_of_angle in case of rounding errors
            edge["branching_angle"] = np.arccos(np.clip(cos_of_angle, -1.0, 1.0))

    def scale_edge_attributes(
            self,
            attributes: List[str],
            scaling_factors: List[float]
    ) -> None:
        """
        Scale attributes of all edges by corresponding factors.

        Attributes can be provided as a list such that edge list has to be traversed only once.

        Args:
            attributes: Edge attributes to scale
            scaling_factors: Factors to multiply the respective attribute value with
        """
        if len(attributes) != len(scaling_factors):
            msg = (f"Requested scaling of attributes {attributes} but provided too many "
                   f"or too few scaling factors {scaling_factors}! Not scaling.")
            Log.log(module="VascularTree", severity="WARN", msg=msg)
            return

        missing_attributes = []
        filtered_attributes = []
        edge_attributes = self.edgelist[0].keys()

        for attribute in attributes:
            if attribute not in edge_attributes:
                missing_attributes.append(attribute)
            else:
                filtered_attributes.append(attribute)

        for edge in self.edgelist:
            for attribute, scaling_factor in zip(attributes, scaling_factors):
                # not asking if attribute is there because they've been filtered beforehand
                # but missing consistency sucks, so we need error handling
                try:
                    edge[attribute] *= scaling_factor
                except KeyError:
                    msg = (f"Some edges don't have attribute {attribute} although "
                           f"the first edge does. Skipping scaling for this edge. "
                           f"Check consistency of the VascularTree!")
                    Log.log(module="VascularTree", msg=msg, severity='WARN')

        if missing_attributes:
            msg = (f"VascularTree edges do not have attribute(s) {missing_attributes}, only:"
                   f" {list(self.edgelist[0].keys())}.")
            Log.log(module="VascularTree", msg=msg)

    def transform_node_coordinates(
            self,
            new_origin: Tuple[float, float, float],
            scaling_factor: float
    ) -> None:
        """
        Adapt coordinates ("pos" argument) of all nodes to a new scaled and shifted coordinate system.

        Args:
            new_origin: Origin of new coordinate system as tuple (x, y, z)
            scaling_factor: Factor by which extents in x, y, z should be multiplied
        """
        for node in self.nodes.values():
            x, y, z = node["pos"]
            new_x = new_origin[0] + x * scaling_factor
            new_y = new_origin[1] + y * scaling_factor
            new_z = new_origin[2] + z * scaling_factor
            node["pos"] = (new_x, new_y, new_z)

    def create_linked_branches(
            self,
            branch_factory: BranchFactory
    ) -> Tuple[Dict[int, Branch], List[List[int]], Dict[int, Tuple[float, float, float]]]:
        """
        Create branches for the tree and a connectivity overview how they
        are linked.

        Returns:
            branches: Dictionary of Branch objects indexed by the ID
                of the target node of their edge. Branches are created
                using the passed BranchFactory.
            bifurcations: Nested list of node IDs around bifurcations
                structured as [[parent, child1, child2]].
            centers: Bifurcation center points in space as tuples (x, y, z)
        """
        # Maps ids of parent nodes to a list of their child nodes
        child_ids = {i: [] for i in range(len(self.nodes))}  # Dict[int, List[int]]
        branches = dict()

        for edge in self.edgelist:
            # this is where, for curved branches, tortuosity is added
            branch = branch_factory.produce(self.nodes[edge["source_id"]]["pos"],
                                            self.nodes[edge["target_id"]]["pos"],
                                            edge)
            branches[edge["target_id"]] = branch
            child_ids[edge["source_id"]].append(edge["target_id"])

        bifurcations = [[parent, *children] for parent, children in child_ids.items()
                        if len(children) == 2]  # [[int, int, int]]  [[parent, child1, child2]]

        # get center positions = position of parent node because branches are indexed by
        # target node
        # - needs to be done after filtering
        centers = {bifurcations[i][0]: self.nodes[bifurcations[i][0]]["pos"] for i in range(len(bifurcations))}
        # [(x, y, z)]

        #for i, (parent, *children) in enumerate(bifurcations):
        #    print(f"Bifurcation {i} describing link between node {parent} and {children}\n"
        #          f"Center node calculated: {centers[parent]}, from node array: {self.nodes[parent]['pos']}\n"
        #          f"Parent branch: {branches[parent]}, child branch 1: {branches[children[0]]}, "
        #          f"child branch 2: {branches[children[1]]}")
            #print(branches[i])
            #print(centers[i])
            #print[self.nodes[parent['pos']]]
            #print(parent)
            #print(children)

        return branches, bifurcations, centers

    def get_root_node_position(
            self
    ) -> Tuple[float, float, float]:
        """ Return the position of the tree's root node. """
        return self.nodes[0]["pos"]


class CurvedTree(VascularTree):
    """
    Adds IO functions specifically for vascular trees with curved branches.

    Functionality partially extended, structure adapted
    from the bachelor thesis work of Jan Biedermann:
    "Generating Synthetic Vasculature in Organ-Like 3D
    Meshes" in the Translational Surgical Oncology (TSO)
    group of the National Center for Tumor Diseases (NCT)
    Dresden.
    """

    def get_branch_factory(
            self,
            percentile_max_branch_length: float,
            *args,
            **kwargs
    ) -> SineGeneratedFactory:
        """
        Return the type of branch factory that should be used for creating a 3D model of this tree.

        Args:
            percentile_max_branch_length: Percentile of branch lengths which is considered the
                maximum branch length in the vascular tree. Used for 3D model creation. The
                maximum branch length is then used to decide which branches get a higher curvature
                (the longer, the curvier) -> the lower the percentile, the curvier the tree.
        """
        if "length" not in self.edgelist[0].keys():
            self.calculate_lengths()

        # Get maximum length of all occurring branches
        # careful: max_length introduces a circular dependency: curved branches use this to
        # calculate a suitable omega but they introduce edge['tortuosity'] which is
        # taken into account for then calculating the length of curved branches into
        # edge['length'], which means that giving out a new branch factory after the first
        # will end up with different values!
        max_length = np.percentile([edge["length"] for edge in self.edgelist],
                                   percentile_max_branch_length)

        return SineGeneratedFactory(max_length, *args)

