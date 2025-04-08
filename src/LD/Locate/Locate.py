import sys
sys.path.append("..")
sys.path.append("../..")

import xml.etree.ElementTree as ET
import collections
from Logs.colorLogger import get_color_logger
from dataclasses import dataclass, field
from typing import Dict, Set, List
from LD.Block.test import BlockCategory, classify_block_element

# External module functions (assumed to be available)
from .dim import get_dimensions, compute_block_port_y, DIMENSIONS

# Constants for configuration
# WARN - BASE_ID MAGIC NUMBER IS NOT JUSTIFIED
LEFT_POWER_RAIL_BASE_ID = 20000
HORIZONTAL_GAP = 90
VERTICAL_GAP = 80

# Setup logging

logger = get_color_logger(__name__)

@dataclass
class Node:
    local_id: str
    tag: str
    element: ET.Element
    width: int = 0
    height: int = 0
    parents: Set[str] = field(default_factory=set)
    children: Set[str] = field(default_factory=set)
    x: int = None
    y: int = None
    layer: int = None
    story: int = 0

class Locator:
    """
    A class to locate XML elements in a layout document.
    The process involves:
      - Building nodes from XML elements.
      - Creating parent-child connections.
      - Assigning layers and positions.
      - Updating XML elements with computed positions.
    """
    def __init__(self, ld: ET.Element):
        self.ld = ld
        self.nodes: Dict[str, Node] = {}

    def build_nodes(self) -> Dict[str, Node]:
        """
        Build Node objects for each XML element that has a localId.
        Nodes are enhanced with dimensions and story information.
        """
        story = 0
        for node in self.ld:
            if node.tag == "comment":
                story += 1
                if story >= 2:
                    self.create_left_power_rail(story)
                continue
            if node.tag == "leftPowerRail" and story >= 2:
                continue

            local_id = node.attrib.get("localId")
            if local_id is None or node.tag == "rightPowerRail":
                continue

            typename = node.attrib.get("typeName")
            dims = get_dimensions(node.tag, typename)
            width = dims.get("width", 0)
            height = dims.get("height", 0)
            node.set("width", str(width))
            node.set("height", str(height))

            self.nodes[local_id] = Node(
                local_id=local_id,
                tag=node.tag,
                element=node,
                width=width,
                height=height,
                story=story
            )
        return self.nodes

    def create_left_power_rail(self, story: int) -> None:
        """
        Creates a new leftPowerRail element for the given story.
        """
        left_power_rail = ET.Element("leftPowerRail")
        local_id_lpr = LEFT_POWER_RAIL_BASE_ID + story
        left_power_rail.set("localId", str(local_id_lpr))
        left_power_rail.set("width", "10")
        left_power_rail.set("height", "100")
        # Create and append position element.
        pos = ET.Element("position")
        pos.attrib["x"] = "50"
        pos.attrib["y"] = "10"
        left_power_rail.append(pos)
        # Create connectionPointOut with a relPosition.
        cp_out = ET.Element("connectionPointOut")
        cp_out.attrib["formalParameter"] = ""
        rel_pos = ET.Element("relPosition")
        rel_pos.attrib["x"] = "10"
        rel_pos.attrib["y"] = "20"
        cp_out.append(rel_pos)
        left_power_rail.append(cp_out)
        self.ld.append(left_power_rail)
        logger.info("Created leftPowerRail with localId %s for story %d", local_id_lpr, story)
        self.nodes[str(local_id_lpr)] = Node(
            local_id=str(local_id_lpr),
            tag="leftPowerRail",
            element=left_power_rail,
            width=10,
            height=100,
            story=story
        )

    def build_connections(self) -> None:
        """
        Build parent-child relationships by reading connectionPointIn elements.
        """
        for node in self.ld:
            local_id = node.attrib.get("localId")
            if local_id is None or node.tag == "rightPowerRail":
                continue
            for cp_in in node.iter("connectionPointIn"):
                for conn in cp_in.findall("connection"):
                    ref_local_id = conn.attrib.get("refLocalId")
                    if ref_local_id and ref_local_id in self.nodes:
                        self.nodes[local_id].parents.add(ref_local_id)
                        self.nodes[ref_local_id].children.add(local_id)

    def assign_layers(self) -> None:
        """
        Assign layer numbers using topological sort (Kahn's algorithm).
        Layer represents the longest path from a source node (layer 0 or 1).
        leftPowerRail nodes are fixed at layer 0.
        Other nodes without parents start at layer 1.
        """
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        # Initialize layers to None before calculation
        for node in self.nodes.values():
            node.layer = None

        queue = collections.deque()

        # 1. Initialize layers for source nodes and calculate in-degrees
        for node_id, node in self.nodes.items():
            in_degree[node_id] = len(node.parents)
            if node.tag == "leftPowerRail":
                if node.layer is None: # Assign only if not already set
                    node.layer = 0
                    queue.append(node_id)
            elif in_degree[node_id] == 0:
                # Other nodes with no parents start at layer 1
                if node.layer is None:
                    node.layer = 1
                    queue.append(node_id)

        processed_count = 0
        # 2. Process nodes layer by layer using Kahn's algorithm
        while queue:
            u_id = queue.popleft()
            processed_count += 1
            u_node = self.nodes[u_id]

            # Ensure the dequeued node has a layer (should be guaranteed by initialization)
            if u_node.layer is None:
                 logger.error(f"CRITICAL: Node {u_id} dequeued but has no layer!")
                 # Attempt recovery: Assign based on parents if possible, else default
                 parent_layers = [self.nodes[p].layer for p in u_node.parents if p in self.nodes and self.nodes[p].layer is not None]
                 u_node.layer = (max(parent_layers) + 1) if parent_layers else (1 if u_node.tag != "leftPowerRail" else 0)
                 logger.warning(f"Recovered layer for {u_id} set to {u_node.layer}")

            # Process children
            for v_id in u_node.children:
                v_node = self.nodes[v_id]
                in_degree[v_id] -= 1
                if in_degree[v_id] == 0:
                    # All parents processed, calculate layer for v_node
                    parent_layers = [self.nodes[p].layer for p in v_node.parents if p in self.nodes and self.nodes[p].layer is not None]
                    if not parent_layers:
                         # This means a node's parents weren't processed or don't exist in the map,
                         # or it's connected to something outside the processed set.
                         # If it truly has parents, this indicates an issue.
                         # If it has no parents (in_degree was initially 0), it should have been handled already.
                         # Assign layer based on the current node u_node as a fallback.
                         logger.warning(f"Node {v_id} has 0 in-degree but no valid parent layers found. Assigning layer based on predecessor {u_id}.")
                         v_node.layer = u_node.layer + 1
                    else:
                        # Assign layer as max of parents' layers + 1
                        v_node.layer = max(parent_layers) + 1

                    queue.append(v_id)
                elif in_degree[v_id] < 0:
                     logger.error(f"In-degree for node {v_id} became negative. Graph connection issue?")


        # 3. Check for cycles or unprocessed nodes
        if processed_count != len(self.nodes):
            unprocessed_nodes = [nid for nid, node in self.nodes.items() if node.layer is None]
            logger.warning(f"Topological sort completed with potential issues.")
            logger.warning(f"Processed {processed_count}/{len(self.nodes)} nodes.")
            if unprocessed_nodes:
                 logger.warning(f"Unprocessed nodes (potential cycle members): {unprocessed_nodes}")
                 # Assign a default high layer to unprocessed nodes to prevent errors later
                 default_layer = max((node.layer for node in self.nodes.values() if node.layer is not None), default=-1) + 1
                 for node_id in unprocessed_nodes:
                     self.nodes[node_id].layer = default_layer
                     logger.warning(f"Assigned default layer {default_layer} to unprocessed node {node_id}")

        # 4. Post-processing: Scale layers (original logic: layer * 2 - 1)
        # Ensure all nodes have a layer assigned before scaling
        max_initial_layer = 0
        for node in self.nodes.values():
            if node.layer is None:
                # This should only happen if cycle detection failed to assign default
                logger.error(f"Critical error: Node {node.local_id} has no layer after topological sort and cycle check. Assigning default layer 1.")
                node.layer = 1 # Assign a fallback
            max_initial_layer = max(max_initial_layer, node.layer)

        logger.debug(f"Max initial layer assigned: {max_initial_layer}")

        for node in self.nodes.values():
            # Apply scaling: Multiply by 2 and subtract 1, ensuring minimum 0
            # Layer 0 (PowerRail) -> stays 0
            # Layer 1 (Sources) -> becomes 1 (2*1 - 1)
            # Layer 2 -> becomes 3 (2*2 - 1)
            node.layer = max(0, node.layer * 2 - 1 if node.layer > 0 else 0)

        # 5. Post-processing: Adjust specific types (original logic, applied once after scaling)
        # This adjustment logic can potentially conflict with topological sort, use cautiously.
        nodes_to_adjust = [n for n in self.nodes.values() if n.tag in ("inVariable", "outVariable")]
        if nodes_to_adjust:
            for node in nodes_to_adjust:
                 original_layer = node.layer
                 if node.tag == "outVariable":
                     # Rule: max(parent_layer) + 1. Topological sort should already achieve this using initial layers.
                     # Re-applying *after scaling* might shift it further right.
                     if node.parents:
                         parent_layers = [self.nodes[p].layer for p in node.parents if p in self.nodes and self.nodes[p].layer is not None]
                         if parent_layers:
                             new_layer = max(parent_layers) + 1 # Using scaled parent layers
                             if new_layer > node.layer:
                                 node.layer = new_layer
                 elif node.tag == "inVariable":
                     # Rule: min(child_layer) - 1. This pulls it left towards its first consumer.
                     if node.children:
                         child_layers = [self.nodes[c].layer for c in node.children if c in self.nodes and self.nodes[c].layer is not None]
                         if child_layers:
                             new_layer = min(child_layers) - 1 # Using scaled child layers
                             if new_layer != node.layer:
                                 #logger.debug(f"Adjusting inVariable {node.local_id} layer from {node.layer} to {new_layer}")
                                 node.layer = new_layer


    def assign_positions(self) -> None:
        """
        Assign x and y positions based on layers and story groups.
        """
        # Set horizontal positions based on layer.
        for node in self.nodes.values():
            if node.tag == "leftPowerRail":
                node.x = 10
                node.y = 10
            else:
                node.x = HORIZONTAL_GAP * node.layer

        # Group nodes by story.
        stories: Dict[int, List[Node]] = {}
        for node in self.nodes.values():
            stories.setdefault(node.story, []).append(node)
        sorted_stories = sorted(stories.keys())

        offset = 0  # initial y offset
        for s in sorted_stories:
            if s == 0:
                continue
            story_nodes = sorted(stories[s], key=lambda n: int(n.local_id))
            story_start = offset + 20
            max_y = story_start
            # Group nodes within the story by layer.
            layers: Dict[int, List[Node]] = {}
            logger.debug("Story %d nodes: %s", s, story_nodes)
            for node in story_nodes:
                layers.setdefault(node.layer, []).append(node)
            for layer_nodes in layers.values():
                for i, node in enumerate(layer_nodes):
                    node.y = story_start + i * VERTICAL_GAP
                    logger.debug("Assigning y=%d for node %s (layer %d)", node.y, node.local_id, node.layer)
                    max_y = max(max_y, node.y + node.height)
            offset = max_y

    def update_xml_positions(self) -> None:
        """
        Update XML elements with computed x and y coordinates.
        Delegates block and non-block node updates to separate methods.
        """
        for node in self.nodes.values():
            el = node.element
            pos = el.find("position")
            if pos is None:
                pos = ET.SubElement(el, "position")
            pos.attrib["x"] = str(node.x)
            pos.attrib["y"] = str(node.y)

            if node.tag == "block":
                self.update_block_node(el, node)
            else:
                self.update_non_block_node(el, node)

    def update_block_node(self, el: ET.Element, node: Node) -> None:
        """
        Update connection points for a block node, evenly spacing ports.
        """
        input_vars = el.find("inputVariables")
        if input_vars is not None:
            vars_list = input_vars.findall("variable")
            count = len(vars_list)
            for idx, var in enumerate(vars_list):
                cp_in = var.find("connectionPointIn")
                if cp_in is None:
                    cp_in = ET.SubElement(var, "connectionPointIn")
                rel = cp_in.find("relPosition")
                if rel is None:
                    rel = ET.Element("relPosition")
                    cp_in.insert(0, rel)
                rel.attrib["x"] = "0"
                rel.attrib["y"] = str(compute_block_port_y(el, count, idx))
        output_vars = el.find("outputVariables")
        if output_vars is not None:
            vars_list = output_vars.findall("variable")
            count = len(vars_list)
            for idx, var in enumerate(vars_list):
                cp_out = var.find("connectionPointOut")
                if cp_out is None:
                    cp_out = ET.SubElement(var, "connectionPointOut")
                rel = cp_out.find("relPosition")
                if rel is None:
                    rel = ET.Element("relPosition")
                    cp_out.insert(0, rel)
                rel.attrib["x"] = str(node.width)
                rel.attrib["y"] = str(compute_block_port_y(el, count, idx))

    def update_non_block_node(self, el: ET.Element, node: Node) -> None:
        """
        Update connection points for non-block nodes.
        """
        cp_out = el.find("connectionPointOut")
        if cp_out is not None:
            rel = cp_out.find("relPosition")
            if rel is None:
                rel = ET.Element("relPosition")
                cp_out.insert(0, rel)
            rel.attrib["x"] = str(node.width)
            rel.attrib["y"] = str(node.height // 2)
        cp_in = el.find("connectionPointIn")
        if cp_in is not None:
            rel = cp_in.find("relPosition")
            if rel is None:
                rel = ET.Element("relPosition")
                cp_in.insert(0, rel)
            rel.attrib["x"] = "0"
            rel.attrib["y"] = str(node.height // 2)

    def add_line_positions(self) -> None:
        """
        Add intermediate positions to connection lines between nodes.
        """
        for node in self.nodes.values():
            el = node.element
            if node.tag == "block":
                input_vars = el.find("inputVariables")
                if input_vars is not None:
                    for var in input_vars.findall("variable"):
                        cp_in = var.find("connectionPointIn")
                        if cp_in is not None:
                            for conn in cp_in.findall("connection"):
                                self.process_connection(conn, node)
            else:
                for cp_in in el.findall("connectionPointIn"):
                    for conn in cp_in.findall("connection"):
                        self.process_connection(conn, node)

    def get_element_type(self, elem: ET.Element) -> BlockCategory:
        return classify_block_element(elem)
        
    
    def process_connection(self, conn: ET.Element, node: Node) -> None:
        """
        Process a connection: adjust refLocalId if necessary, and add intermediate positions.
        """
        ref_local_id = conn.attrib.get("refLocalId")
        if ref_local_id is None:
            return
        if int(ref_local_id) == 0 and node.story >= 2:
            ref_local_id = str(LEFT_POWER_RAIL_BASE_ID + node.story)
            conn.attrib["refLocalId"] = ref_local_id

        node_end = self.nodes.get(ref_local_id)
        # set the formalParameter attribute to blocks that have 2 outputs in Beremiz while only 1 output in CODESYS
        fp = conn.attrib.get("formalParameter")
        tp = self.get_element_type(node_end.element)
        if fp == None:
            if tp == BlockCategory.CMP:
                conn.set("formalParameter", "OUT")
            elif tp == BlockCategory.TRIG:
                conn.set("formalParameter", "Q")
        if node_end:
            self.add_line_positions_to_connection(conn, node, node_end, fp)

    def add_line_positions_to_connection(self, conn: ET.Element, node_start: Node, node_end: Node, formalParamater: str | None = None) -> None:
        """
        Compute intermediate positions along the connection line.
        """
        start_x = node_start.x
        start_y = node_start.y + node_start.height // 2
        end_x = node_end.x + node_end.width
        if formalParamater == None:
            end_y = node_end.y + node_end.height // 2
        else:
            # find the node in DIMENSIONS
            dim = get_dimensions(node_end.tag, node_end.element.attrib.get("typeName"))
            if node_end.element.attrib.get("typeName") == 'Q':
                logger.warning(f"Q type found in connection, tag is{node_end.tag}")

            if formalParamater in dim:
                end_y = node_end.y + dim[formalParamater]
            else:
                end_y = node_end.y + 30

        mid1_x = (start_x + end_x) // 2
        mid1_y = start_y
        mid2_x = mid1_x
        mid2_y = end_y

        positions = [
            {"x": start_x, "y": start_y},
        ]
        if start_y != end_y:
            positions.append({"x": mid1_x, "y": mid1_y})
            positions.append({"x": mid2_x, "y": mid2_y})
        positions.append({"x": end_x, "y": end_y})
        for pos in positions:
            pos_el = ET.Element("position")
            pos_el.attrib["x"] = str(pos["x"])
            pos_el.attrib["y"] = str(pos["y"])
            conn.append(pos_el)

    def locate(self) -> ET.Element:
        """
        Execute the complete process to compute node positions and update the XML.
        """
        self.build_nodes()
        self.build_connections()
        self.assign_layers()
        logger.debug("Nodes after layer assignment: %s", self.nodes)
        self.assign_positions()
        self.update_xml_positions()
        self.add_line_positions()
        return self.ld

# Usage example:
# locator = Locator(xml_document_root)
# updated_xml = locator.locate()
