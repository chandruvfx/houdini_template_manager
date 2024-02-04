# 
# All houdini level node operations contains in this module.
# Like loading, removing bundles, creating appropriate 
# context, merging hip file operations 
# 

import os
import pickle 
import hou

class HoudiniOPs:
    
    """
    Base Class for all houdini functions. 
    """
    def __init__(self, 
                file_path: str=r"") -> None:
        """
        Initialize file path and mapping houdini
        context name to custom constant strings.

        Args:
            file_path (str, optional): File path to retrive or dump hip file. 
            Defaults to r"".
        """
        
        self.file_path = file_path
        # Mapping context to the strings
        self.node_catagory_map = {'Object': 'Obj',
                            'Sop': "Sop",
                            "Vop": 'Vop',
                            "Dop": "Dop",
                            "Driver" : "Out"}
    
    @staticmethod
    def load_houdini_nodes() -> list:
        
        """Util Hook for getting houdini node paths 

        Returns:
            list: Houdini node path 
                    ex /obj/geonode1/sphere1
        """
        return list(map(lambda node: node.path(), 
                        hou.selectedNodes())
                    )
        
    def check_node_category(self) -> list:
        
        """Returns the node type category name
        likewise Object, Sop, Vop, Rop

        Returns:
            list: Node category
        """
        selected_node_category = set(map(lambda node: node.type().category().name(), 
                        hou.selectedNodes())
                    )
        return self.node_catagory_map[list(selected_node_category)[0]]
    
    @staticmethod
    def node_count() -> list:
        
        """Util function for to count 
        Number of node selected in the houdini context 

        Returns:
            list: houdini node count numbers 
        """
        return len(hou.selectedNodes())
    
    @staticmethod
    def enable_selection_on_selected_nodes(node_path: str) -> None:

        """Enable selection for the given path of the houdini node 

        Args:
            node_path (str): node path ex: /obj/node/
        """
        
        hou.node(node_path).setSelected(True)
        
    
    def remove_selected_nodes(self,
                              node_path: str) -> None:
        """Remove selection for the node path

        Args:
            node_path (str): node path ex: /obj/node/
        """
        hou.node(node_path).setSelected(False)
        
    @staticmethod
    def getCurrentNetworkTab() -> hou.paneTabType.NetworkEditor:

        """Returns the users current network tab of the houdini 

        Returns:
            hou.paneTabType.NetworkEditor: network editor panel
        """
        network_tabs = [t for t in hou.ui.paneTabs() if t.type() == hou.paneTabType.NetworkEditor]
        if network_tabs:
            for tab in network_tabs:
                if tab.isCurrentTab():
                    return tab
        return None

    def save_node_snippets(self) -> None:
        
        """
        Master methode to save the selected node snippet into a 
        given extention
        """
        selected_nodes = hou.selectedNodes()
        parent = selected_nodes[0].parent()
        parent.saveItemsToFile(selected_nodes,self.file_path)
    
    def load_node_snippets(self, context: str) -> str:

        """
        Load the published bundle into a appropriate given context.
        Create the context and loads the bundles. 

        Args:
            context (str): Houdini Context passed as string

        Returns:
            str: Houdini context path loaded. EX: /obj/geo1/attribvop1/
        """
        
        desktop = hou.ui.curDesktop()
        pane =  desktop.paneTabUnderCursor()
        current_pane = pane.pwd()
        current_houdini_context = current_pane.childTypeCategory().name()

        if context != self.node_catagory_map[current_houdini_context]:
            geo_node = hou.node('/obj').createNode('geo')
            if context == 'Sop':
                pane.cd(geo_node.path())
                geo_node.loadItemsFromFile(self.file_path)
                return geo_node.path()
            elif context == 'Vop':
                vop_node = geo_node.createNode("attribvop")
                pane.cd(vop_node.path())
                vop_node.loadItemsFromFile(self.file_path)
                return vop_node.path()
            elif context == 'Dop':
                dop_node = geo_node.createNode("dopnet")
                pane.cd(dop_node.path())
                dop_node.loadItemsFromFile(self.file_path)
                return dop_node.path()
        else:
            network_tab = self.getCurrentNetworkTab()
            if network_tab and os.path.exists(self.file_path):
                parent = network_tab.pwd()  
                for nodes in hou.selectedNodes():
                    self.remove_selected_nodes(nodes.path())
                parent.loadItemsFromFile(self.file_path)
                for nodes in hou.selectedNodes():
                    nodes.setPosition(
                        hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor).cursorPosition()
                    )
                hou.node(parent.path()).layoutChildren(
                    items =  hou.selectedNodes(),
                    horizontal_spacing = 1,
                    vertical_spacing = 0.5
                )
                

    def save_hip(self) -> None:
        
        """Save the hip file in a given bundle name 
        and rename the file to the original name to 
        save further. 
        """

        path = hou.hipFile.path()
        hou.hipFile.save(file_name=self.file_path,
                         save_to_recent_files=False)
        hou.hipFile.setName(path)
    
    def merge_hip(self) -> None:
        
        """Merge the hip file to current working hip file"""
        
        hou.hipFile.merge(self.file_path,
                          overwrite_on_conflict=False
                          )