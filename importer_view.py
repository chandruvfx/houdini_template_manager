#
# An Houdini Importer python panel tool. Houdini Artist can able to
# Import the published budle into their scene files. 
# Tools has embedded features like filtereing and showing informations of bundles.
# Bundles Filtering acheived through four methods. project, context, 
# domain and search based on the text. Artist can locate the bundle
# using filters and search options and import into the scene.
# Tool automatically determine the bundle type while importing. 
# 'Module' or 'Whole Scene'. Artist importing 'Module' then, the importer tool
# first try to locate the appropriate houdini context(sop, dop, vop nodes), 
# if exist it import the Nodes directly into it, else it create the entire context
# and dump it. For Artist importing 'Whole scene', the importer tool 
# do the houdini native merge operation. 
#   

import os
import sys
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets
from PySide2.QtGui import (QStandardItemModel, 
                            QStandardItem, 
                            QPixmap, 
                            QIcon)
from PySide2.QtCore import (Qt,
                            QModelIndex,
                            QSortFilterProxyModel,
                            QRegExp)
from model import (Defaults, 
                   Templates,
                   ThadamDB)
from helper_msgboxes import utilMessageBox
ALL_PROJECTS_KEY = "all"


class Importer(QtWidgets.QWidget):
    
    """
    Master Importer Class Hook. QT Window Loads Widget with related bundles
    content. Initially the GUI act like a dash board. Shows all the 
    bundles and it's published versions. Artist allowed to choose and import it.
    Bundles published as 'module' bundle type imported into the current houdini session.
    Bundles published as 'Whole Scene' bundle type merged into the current hip file.
    The houdini native 'merge' or 'import' option determined by the time of 
    user selecting the bundle name. For 'Module' type, it checks whether the
    corresponding houdini context exist or not, if exist it import the nodes into
    that context, else it create the context and import it. With that this class
    has widget allows users to filter the bundles and show cases the bundles and related 
    informations to the users. 

    Example:
        For 'Modules', Consider bundle is published from the vop context. While importing the 
        tool check whether the user is in inside of the vopsop context.
        if so, it just dump the nodes, else it create /obj/geo_node1/attrib_vop1
        and dump it.

    The importer class has three sections. project operations, filter 
    bundles, info showcaser.Below showing widgets and its jobs 
    
    Project Operations
    ------------------
    Select Project Combobox:
        Load all the active projects from the thadam DB for user to select

    Bundles Section:
        Contains a search box and Listview widget. All published bundles
        shown here. Search box filter out the matching bundles based upon
        the user input text. These updation works dynamically.

    Version List:
        List all the versions of the bundle. User can choose version number 
        allowed to import it.
    
    Filters Bundles 
    ---------------
    Domain Filters:
        Filter bundles based upon domain names 

    Context Filters:
        Filter bundles based upon context names
    
    Infos showcaser:
    ---------------
    Comments:
        Shows Comments of all the bundles 

    infos:
        Shows additional infos like created time  node count ,user info, etc..
    """

    def __init__(self) -> None:

        """
        Initialize the widgets and the bundle datas. 
        The Widgets were readed from node template importer.ui file
        and widget datas were loaded from the filesystem.
        """
                
        super().__init__()
        
        dirname = os.path.dirname(__file__)

        # ui file path 
        ui_file = os.path.join(dirname, 
                               "ui\\node_template_importer.ui"
        )

        # Load the ui file 
        ui_loader = QUiLoader()
        self.importer_window = ui_loader.load(ui_file)
        
        # Works when loaded from houdini. An override for 
        # execution environment.  
        # Dock the QMainWindow inside the layout.
        if __name__ != '__main__':
            mainLayout = QtWidgets.QVBoxLayout()
            mainLayout.addWidget(self.importer_window)
            self.setLayout(mainLayout)
        
        # Access the defaults registered context and domains
        # from the .yaml files 
        self.defaults = Defaults()
        self.contexts = self.defaults.get_defaults_context()
        self.domains = self.defaults.get_default_domain()
        
        # Initialize to Read Bundle templates in various ways
        self.templates = Templates()

        # Initialize thadam DB api to gather the projects      
        self.thadam_db = ThadamDB()
        self.projects = self.thadam_db.get_projects()
        
        # Initialize Project combobox from ui.
        self.project_combo_box = self.importer_window.findChild(
            QtWidgets.QComboBox,
            "project_cbx"
        )
        # Resized the dropdown the QlistView
        # to certain size. AS so the horizontal text gonna fit well
        self.project_combo_box.view().setFixedSize(
                        250,
                        500
        )
        
        # Add all the 'ALL' project string and also the projects 
        # names as combobox items 
        self.project_combo_box.addItem(ALL_PROJECTS_KEY)
        self.append_items_to_combobox(self.project_combo_box,
                                      self.projects)
                                      
        # The context, domain, info, comments, bundles and version
        # list updated to respective widgets upon the project
        # selected by the user ftom the project list combobox 
        #
        # Selecting project in project combobobx, Clear all the filters and 
        # widget contents current state. Loads up all the 
        # default contents based upon the projects in the widgets.
        # update_all = True in the signaling method do all updates operation
        # 
        self.project_combo_box.activated[str].connect(
                    self.filter_bundle_to_selected_project
        )
        
        # Search box to filter the bundles. 
        self.filter_bundle_lineedit = self.importer_window.findChild(
            QtWidgets.QLineEdit,
            "bundle_ldt"
        )
        self.filter_bundle_lineedit.textEdited.connect(
                lambda: self.filter_bundle_to_selected_project(
                    self.project_combo_box.currentText()
                )
        )
        
        # Initialize domain combobox filters and add all
        # the domain list context as items. set current item to nil 
        self.filter_domain_cbx = self.importer_window.findChild(
            QtWidgets.QComboBox,
            "domain_cbx"
        )
        self.append_items_to_combobox(self.filter_domain_cbx,
                                      self.domains)
        self.filter_domain_cbx.setCurrentIndex(-1)

        # Initialize context combobox filters and add all
        # the context list context as items. set current item to nil  
        self.filter_context_cbx = self.importer_window.findChild(
            QtWidgets.QComboBox,
            "context_cbx"
        )
        self.append_items_to_combobox(self.filter_context_cbx,
                                      self.contexts)
        self.filter_context_cbx.setCurrentIndex(-1) 

        # Initialize bundle list primary widget. 
        # All bundles were loaded into the widget.
        self.bundle_list = self.importer_window.findChild(
            QtWidgets.QListView,
            "bundle_list"
        )
        # Disabled Editing the items in the list view and the model item to 
        # show it to the view.
        self.bundle_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.bundle_model = QStandardItemModel()

        # Call for loading bundles 
        self.load_bundles()

        # Qt Signal. If user click a bundle name in the bundle list view 
        # it updates the widgets related to the selected bundle
        self.bundle_list.clicked.connect(self.filter_selected_bundle_items)

        # Search box input text dynamically trigger the filter item method.
        # Based upon the inputing text lively the bundle and version views updated.
        self.filter_bundle_lineedit.textEdited.connect(
                    lambda: self.filter_items(self.bundle_list,
                                                self.bundle_model,
                                                self.filter_bundle_lineedit.text(),
                                                self.bundle_list.objectName())
        )
        
        # Initialize domain list view widget. 
        self.domain_list =self.importer_window.findChild(
            QtWidgets.QListView,
            "domain_list"
        )
        # Disable editing and also the selection. Reason is, The filtering gonna
        # taken care by the domain combobox. 
        self.domain_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.domain_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.domain_model = QStandardItemModel()

        # append retrived domain list items to the model of the domain list view
        self.append_items_to_list_view(self.domain_model, 
                                  self.domain_list, 
                                  self.domains)

        # Signals to filter the Bundles and its related user infos based upon the 
        # selected domain from the domain combobox
        self.filter_domain_cbx.activated.connect(
                    lambda: self.filter_items(self.domain_list,
                                                self.domain_model,
                                                self.filter_domain_cbx.currentText(),
                                                self.domain_list.objectName(),
                                                self.domains)
        )

        # Entire widgets contents updated based upon the domain filter selected 
        # if 'Magical' domain selected then magical domain related datas retrived and 
        # all bundle list, contex domain, version list, comments and info widgets
        # updated with the relative content and show cases it. 
        # Here bundle search box, context domain and bundle selection
        # also taken into account. 
        self.filter_domain_cbx.activated[str].connect(
                self.filter_version_on_domain
        )
        
        # Works Same as somain bundle
        self.context_list =self.importer_window.findChild(
            QtWidgets.QListView,
            "context_list"
        )
        self.context_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.context_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.context_model = QStandardItemModel()
        self.append_items_to_list_view(self.context_model, 
                                  self.context_list, 
                                  self.contexts)
        
        # Do Filter bundles based on context. 
        # All operations Splited into two base class methods 
        self.filter_context_cbx.activated[str].connect(
                self.filter_version_on_context_by_domain
        )
        self.filter_context_cbx.activated[str].connect(
                self.filter_version_on_context_of_all_domain
        )
        self.filter_context_cbx.activated.connect(
                    lambda: self.filter_items(self.context_list,
                                                self.context_model,
                                                self.filter_context_cbx.currentText(),
                                                self.context_list.objectName(),
                                                self.contexts)
        ) 
        
        # Initialize info widget section to show case 
        # the  additional info of bundles 
        self.info_textedit =self.importer_window.findChild(
            QtWidgets.QTextEdit,
            "info_tedt"
        )
        
        # Initialize the comments widget. Display the 
        # comments of the publishd bundles 
        self.comments_textedit =self.importer_window.findChild(
            QtWidgets.QTextEdit,
            "comments_tedt"
        )
        
        #  Initialize the bundle type label. Dynamically the 
        # the text changed whether 'module' selected or 'whole
        # scene' selected
        self.bundle_type_label =self.importer_window.findChild(
            QtWidgets.QLabel,
            "bundle_type_lbl"
        )
        
        # Initialize version list view widget. 
        self.version_list =self.importer_window.findChild(
            QtWidgets.QListView,
            "version_list"
        )
        self.version_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        # Initialize the action drop down menus for the version list 
        self.version_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.version_list.customContextMenuRequested.connect(self.action_menus)
        
        self.version_model = QStandardItemModel()
        self.load_versions()
        # Signal to change the bundle type
        self.version_list.clicked[QModelIndex].connect(
                    self.apply_bundle_buton_type
        )
        # Qt Signal to filter the comments of the versions 
        self.version_list.clicked[QModelIndex].connect(
                self.filter_selected_version_comments
        )
        
        # Button Widget to import or merge the bundle
        self.import_btn =self.importer_window.findChild(
            QtWidgets.QPushButton,
            "import_btn"
        )
        self.import_btn.clicked.connect(self.load)

        # Button Widget to reload flush the bundle list
        self.reload_btn =self.importer_window.findChild(
            QtWidgets.QPushButton,
            "reload_btn"
        )
        self.reload_btn.clicked.connect(self.reload)
        
        # Icons for search lineedit widget
        self.search_icon =self.importer_window.findChild(
            QtWidgets.QLabel,
            "search_icon"
        )
        icon = os.path.join(dirname, "icons/search.png")
        pixmap = QPixmap(icon)
        self.search_icon.setPixmap(pixmap.scaled(40,40, Qt.KeepAspectRatio))
        
        button_icon = os.path.join(dirname, "icons/Refresh.png")
        self.reload_btn.setIcon(QIcon(button_icon))
        
        import_btn_icon = os.path.join(dirname, "icons/visualize.svg")
        self.import_btn.setIcon(QIcon(import_btn_icon))
        
        self.tool_label =self.importer_window.findChild(
            QtWidgets.QLabel,
            "tool_label"
        )
        tool_icon = os.path.join(dirname, "icons/alien.png")
        tool_pixmap = QPixmap(tool_icon)
        self.tool_label.setPixmap(tool_pixmap.scaled(200,200, Qt.KeepAspectRatio))
        
        self.tool_title_label =self.importer_window.findChild(
            QtWidgets.QLabel,
            "title_label"
        )
        tool_title_icon = os.path.join(dirname, "icons/node_importer.PNG")
        tool_title_pixmap = QPixmap(tool_title_icon)
        self.tool_title_label.setPixmap(tool_title_pixmap.scaled(300,90))
    
    def append_items_to_combobox(self, 
                                combobox: QtWidgets.QComboBox, 
                                items: list) -> None:

        """Itarate over the items in the list 
        add it into as combobox items

        Args:
            combobox (QtWidgets.QComboBox): combobox widget object
            items (list): List string items.
        """
        
        for item in items:
            combobox.addItem(item)
    
    def switch_util_buttons_state(self, 
                                  status: bool = False) -> None:
        """Switch the appearance of the widget to the given status

        Args:
            status (bool, optional): Determine the On and Off condition
            to a widget. Defaults to False.
        """
        
        self.reload_btn.setEnabled(status)
        self.filter_bundle_lineedit.setEnabled(status)
        self.filter_context_cbx.setEnabled(status)
        self.filter_domain_cbx.setEnabled(status)
        
    
    def reload(self) -> None:

        """Revert back the GUI into a dashboard state"""
        
        self.load_bundles()
        self.load_versions()
        self.filter_context_cbx.setCurrentIndex(-1)
        self.filter_domain_cbx.setCurrentIndex(-1)
        self.filter_bundle_lineedit.setText('')
    
    def load_bundles(self) -> None:

        """
        Retrive all the bundles names based upon the project selected
        and update as bundle list view widget items. 
        """
        
        # get all the project name for 'all' keyword selected.
        if self.project_combo_box.currentText() == ALL_PROJECTS_KEY:
            self.bundles = self.templates.get_all_bundles(return_with_project_name=True)
            self.append_items_to_list_view(self.bundle_model, 
                                        self.bundle_list, 
                                        self.bundles,
                                        include_tool_tip=True)
        # Collect bundle names only if the user selected bundle names is
        # matching with the bundle entity project name
        else:
            self.bundles = []
            for project, entities in self.templates.list_all_bundle_entity().items():
                if self.project_combo_box.currentText() == project:
                    for entity in entities:
                        self.bundles.append(entity['bundle_name'])
            
            # sort the bundle name and ingest into the list view
            self.bundles = sorted(set(self.bundles))
            self.append_items_to_list_view(self.bundle_model, 
                                        self.bundle_list, 
                                        self.bundles)
        
    def load_versions(self) -> None:

        """
        Collect all the versions strings from the bundle entity dictionary 
        add in to the version list view, based upon the project selected by the
        user. also, the comments and user infos.

        For versions the bundle entity dict passed as a meta data. 
        The qstandarditems in the version list view hold this metadata.
        The version string 'v001', v002, v003 are go for display role. user 
        can see and interact. for each version string the bundle entity dict 
        goes as a user role. it wont visible. it holded as meta data.
        """
        
        # Retrive all registerd bundle entities. For all collected version
        # set the bundle entity as value and bundle version as key
        # This key is gonna used as Display Role and value is gonna used 
        # as UserRole in qt widgets.

        # Versions to store version key and entity as value dictionary
        self.all_versions = []
        self.registered_domains = set()
        self.all_bundle_info_entities = self.templates.list_all_bundle_entity()
        for project, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                if self.project_combo_box.currentText() == ALL_PROJECTS_KEY:
                    self.all_versions.append(
                                {bundle_entity['version']: bundle_entity}
                    )
                    self.add_comments_and_infos()
                if self.project_combo_box.currentText() == project:
                    self.all_versions.append(
                                {bundle_entity['version']: bundle_entity}
                    )
                    self.add_comments_and_infos(project_name=project)
                # Register the collected domain in the set 
                self.registered_domains.add(bundle_entity['domain'])
        
        # Meta data is enabled. The key of the dict loaded as user
        # viewable items in the list. The value of the dict loaded 
        # as userrole in meta data . 
        self.append_items_to_list_view(self.version_model, 
                                  self.version_list, 
                                  self.all_versions,
                                  metadata = True)
        self.append_items_to_list_view(self.domain_model, 
                                  self.domain_list, 
                                  self.domains)
        self.append_items_to_list_view(self.context_model, 
                                  self.context_list, 
                                  self.contexts)

    def append_items_to_list_view(self, 
                             model: QStandardItemModel, 
                             listview: QtWidgets.QListView, 
                             items: list or dict,
                             include_tool_tip: bool= False,
                             metadata: bool = False) -> None:
        """
        Iterate over the given list or dict declare each items
        into the qstandarditem of the model. Embed the model to
        the given list view. 

        For each bundle name the respective project names were 
        included as tool tip. If user hoever the mouse point over 
        the bundle name, the project name belong to the bundle names 
        showned up. 

        metadata for qstandarditem to hold. version list view 
        items holds the respective dictionary of a bundle. 
        metadata goes as UserRole of qstandarditem and others 
        goes as DisplayRole

        Args:
            model (QStandardItemModel): Model of the list view
            listview (QtWidgets.QListView): pyqt List view
            items (list | dict): list or dict item to update to the list view
            include_tool_tip (bool, optional): Helps to add the tool tip 
                                                text for items in the list. Defaults to False.
            metadata (bool, optional): Metadata structure to holds up by
                                        the list view items . Defaults to False.
        """

        
        self.list_model = model
        self.list_model.clear()
        self.list_model.setObjectName(listview.objectName())
        listview.setModel(self.list_model)
        if not metadata and not include_tool_tip:
            for item in items:
                qstandarditem = QStandardItem(item)
                self.list_model.appendRow(qstandarditem)
        elif not metadata and include_tool_tip:
            for bundle_name, project_name in items.items():
                qstandarditem = QStandardItem(bundle_name)
                qstandarditem.setData(project_name, Qt.ToolTipRole)
                self.list_model.appendRow(qstandarditem)
        else:
            for item in items:
                version_label = list(item.keys())[0]
                versions_metadata = list(item.values())[0]
                qstandarditem = QStandardItem()
                qstandarditem.setData(version_label, Qt.DisplayRole)
                qstandarditem.setData(versions_metadata, Qt.UserRole)
                
                self.list_model.appendRow(qstandarditem)
                
    def filter_selected_version_comments(self, 
                                        index: QModelIndex) -> None:
        """
        Works in two ways. in GUI, if no items were selected in 
        any bundle list view and user selecting directly the version in 
        version list view, then the related widgets contents updated 
        corresponding to that selected version. 

        Args:
            index (QModelIndex): Qt Model index of the selected 
                                version from the version list view
        """
        
        selected_version = index.data(Qt.UserRole)
        bundle_name = []
        domain =set()
        context = set()
        for _, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                if bundle_entity['version'] == selected_version['version'] and \
                    bundle_entity['bundle_name'] == selected_version['bundle_name'] and \
                    bundle_entity['project_name'] == selected_version['project_name'] and \
                    bundle_entity['domain'] == selected_version['domain'] and \
                    bundle_entity['context'] == selected_version['context']:
                        
                    domain.add(bundle_entity['domain'])
                    context.add(bundle_entity['context'])
                    bundle_name.append(bundle_entity['bundle_name'])
                    
                    # Call the method to update the comments and infos
                    # exist for the version used by the user 
                    self.add_comments_and_infos(
                        version=bundle_entity['version'],
                        bundle_name=bundle_entity['bundle_name'],
                        project_name=bundle_entity['project_name'],
                        domain=bundle_entity['domain'],
                        context=bundle_entity['context']
                        )
        
        # user selected version bundle name, domain, and conext infos
        # updated into the  respective widgets.
        if not self.bundle_list.currentIndex().data():            
            self.append_items_to_list_view(self.bundle_model, 
                                    self.bundle_list, 
                                    bundle_name)
            self.append_items_to_list_view(self.domain_model, 
                                    self.domain_list, 
                                    domain)
            self.append_items_to_list_view(self.context_model, 
                                    self.context_list, 
                                    context)
            self.project_combo_box.setCurrentIndex(-1)
            self.switch_util_buttons_state(status=False)
            
                      
    def filter_selected_bundle_items(self, 
                                    index: QModelIndex) -> None:
        """All Widgets content updated based upon the bundle seleced by the 
        user from the bundle list. Clean up all the widgets, 
        For a User selected bundle, this method collect all the 
        context, domain, comments, infos and versions of that
        bundle from json and load it into the respective widgets.

        This works with combination. If context or domain or both filters
        selected by user then that too taken into account. Only filters
        matching with the bundle name, versions, comments, and infos showed

        Example:
            Consider 'fog_rig_a' is saved under domain 'magical' and
            'volumetrics' of context 'sop'. versions list shows 
            'v001' , 'v001'. one v001 for magical and other for 
            volumetrics. now user select magical from the domain
            filter. for 'for_rig_a' domain is 'magical' context
            'sop' version now shows only 'v001'. this time the 
            'volumetric' domain is ignored as of domain filers used 
            and 'magical' is choosed.

        Args:
            index (QModelIndex): Qt Model index of the selected 
                                version from the version list view
        """
        

        project_versions = []
        domain =set()
        context = set()
        
        user_filter_domain = self.filter_domain_cbx.currentText()
        user_filter_context = self.filter_context_cbx.currentText()
        self.selected_bundle = self.bundle_list.model().data(index)
        
        def update_all_entities():
            """Upadate the items to the data structures"""
            project_versions.append(
                            {bundle_entity['version']: bundle_entity}
            )
            domain.add(bundle_entity['domain'])
            context.add(bundle_entity['context'])
        
        for _, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                
                # Check the retrived bundles list matches with the 
                # bundle name user selected from the widget
                if bundle_entity['bundle_name'] == self.selected_bundle:

                    # no domain and context filter selected
                    if not user_filter_domain and not user_filter_context:
                        update_all_entities()   
                        self.filter_domain_cbx.setCurrentIndex(-1)
                        self.filter_context_cbx.setCurrentIndex(-1)
                        self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'])
                    
                    # domain and context filter selected
                    elif user_filter_domain == bundle_entity['domain'] and \
                        user_filter_context == bundle_entity['context']:
                        update_all_entities() 
                        self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                    domain=user_filter_domain,
                                                    context=user_filter_context)

                    # domain selected and  no context filter selected
                    elif user_filter_domain == bundle_entity['domain'] and \
                        not user_filter_context:
                        update_all_entities()
                        self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                domain=user_filter_domain)
                    
                    # no domain and context filter selected
                    elif not user_filter_domain and \
                        user_filter_context == bundle_entity['context']:
                        update_all_entities()
                        self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                context=user_filter_context)

        # For a selected combination version , domain
        # context were updated into the respective 
        # qt widgets  
        self.append_items_to_list_view(self.version_model, 
                                self.version_list, 
                                project_versions,
                                metadata=True)
        self.append_items_to_list_view(self.domain_model, 
                                self.domain_list, 
                                domain)
        self.append_items_to_list_view(self.context_model, 
                                self.context_list, 
                                context)
        self.bundle_type_label.setText('')
        
        
    def filter_version_on_domain(self, 
                                domain: str) -> None:
        """
        Filter bundle, context, version, info, comments upon selecting
        the domain selection. Few cases also taken into consideration
        
        1.  The user entered any text in the bundle search box 
            also taken into account. The matching text filtered bundles with 
            matching selected domain names filtered. also the all widget contents.
        2.  If bundle selected and the bundle is exist in more than one
            domain names then it is also filtered based on the domain name
            selected
        3.  Finally, it Works in combination. The context, project, search box text
            user selection bundle considered with domain filters.
            Example: If context is selected. all bundles, versions , info and comments
                    updated and filtered for selected context. now, user select domain 
                    to filter based on it. This domain filter applied upon the exiting
                    context filter. 

        Args:
            domain (str): User selected Domain name
                        EX: Magical, Volumetrics, etc ..,
        """
        
        proceed = True 
        proceed1 = True
        proceed_clear_for_domain_mismatch = True
        filtered_version = []
        filtered_bundles = []
        filtered_domains = []
        contexts_of_domains = set()
        user_selected_bundle = self.bundle_list.currentIndex().data()
        
        # For the selected project and domain only retrive and update the 
        # bundle, domain, context widget content. 
        # update=False indicates the version list view, info and comments 
        # were left empty. This is left for user to choose a bundle 
        # Choosing bundle now shows the info and comments related to that 
        # bundle 
        if not user_selected_bundle:
            self.filter_bundle_to_selected_project(
                        self.project_combo_box.currentText(),
                        update_all = False
            )
        
        # Read all the bundles exist in the bundle list view 
        # add in the set data structure. Using for filtering in later part
        model = self.bundle_model
        items = model.findItems(self.filter_bundle_lineedit.text(), 
                                flags=Qt.MatchContains)
        filtered_bundled_names1 = set()
        for index in items:
            filtered_bundled_names1.add(index.text())
        
        for project, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                
                # check selected domain match with collected entity domain 
                # not with the context
                if bundle_entity['domain'] == domain and not \
                            self.filter_context_cbx.currentText():

                    # User selected no bundle and selected project drop down match with
                    # 'all' or any thadam project and no serachbox text were
                    # included condition checks        
                    if not user_selected_bundle and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                         self.project_combo_box.currentText() == project) and \
                        not self.filter_bundle_lineedit.text():

                        # Collect the bundle names for the condition matched
                        filtered_bundles.append(
                                bundle_entity['bundle_name']
                        )
                        # Sort it based on the bundles index
                        filtered_bundles = sorted(
                                set(filtered_bundles), key=filtered_bundles.index
                        )
                        # Collect domain, context of matched condition and sort it 
                        filtered_domains.append(bundle_entity['domain'])
                        filtered_domains = sorted(
                                set(filtered_domains), key=filtered_domains.index
                        )
                        contexts_of_domains.add(bundle_entity['context'])

                        # Update the content  in to the respective list views of 
                        # bundles and domain 
                        self.append_items_to_list_view(self.bundle_model, 
                                                self.bundle_list, 
                                                filtered_bundles)
                        self.append_items_to_list_view(self.domain_model, 
                                            self.domain_list, 
                                            filtered_domains)

                        # Clear the version models of version list view 
                        self.version_model.clear()

                        # Clear all the comments 
                        self.add_comments_and_infos(clear=True)
                        
                        # Versbose to other condition to not proceed 
                        # if this block executed 
                        proceed1 = False
                        
                    # User selected no bundle and selected project drop down match with
                    # 'all' or any thadam project and any serachbox text were
                    # included then below condition checks        
                    elif not user_selected_bundle and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                        self.project_combo_box.currentText() == project) and \
                        self.filter_bundle_lineedit.text():
                        for filtered_bundled_name in filtered_bundled_names1:
                            if filtered_bundled_name == bundle_entity['bundle_name']:

                                contexts_of_domains.add(bundle_entity['context'])

                                filtered_bundles.append(
                                        bundle_entity['bundle_name']
                                )
                                filtered_bundles = sorted(
                                        set(filtered_bundles), key=filtered_bundles.index
                                )
                                filtered_domains.append(bundle_entity['domain'])
                                filtered_domains = sorted(
                                        set(filtered_domains), key=filtered_domains.index
                                )
                                contexts_of_domains.add(bundle_entity['context'])
                                self.append_items_to_list_view(self.bundle_model, 
                                                        self.bundle_list, 
                                                        filtered_bundles)
                                self.append_items_to_list_view(self.domain_model, 
                                                    self.domain_list, 
                                                    filtered_domains)
                                self.version_model.clear()
                                self.add_comments_and_infos(clear=True)
                                proceed1 = False

                    # No context is selected              
                    if not self.filter_context_cbx.currentText():
                        # entity bundle name matching with user selected bundles
                        # collect the context and version
                        if bundle_entity['bundle_name'] == user_selected_bundle:
                            contexts_of_domains.add(bundle_entity['context'])
                            filtered_version.append(
                                    {bundle_entity['version']: bundle_entity}   
                            )
                            # update info and comment section of the bundle name
                            # and domain 
                            self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                    domain=domain)
                            # Make contextcombobox to no selection
                            self.filter_context_cbx.setCurrentIndex(-1)
                            proceed_clear_for_domain_mismatch = False

                # No bundle selected by bundle list view                 
                elif not user_selected_bundle:
                    
                    # Clear version, info, comments and bundle model
                    # nothing to show if domain is not register
                    if domain not in self.registered_domains:
                        self.version_model.clear()
                        self.add_comments_and_infos(clear=True)
                        self.bundle_model.clear()

                    if bundle_entity['domain'] != domain and \
                        not self.filter_bundle_lineedit.text() and \
                        self.project_combo_box.currentText() == project and \
                        not self.filter_context_cbx.currentText() and \
                        proceed1:
                            self.version_model.clear()
                            self.add_comments_and_infos(clear=True)
                            self.bundle_model.clear()
                    
                    if bundle_entity['domain'] != domain and \
                        self.filter_bundle_lineedit.text() and \
                        not self.filter_context_cbx.currentText() and \
                        proceed1:
                            self.version_model.clear()
                            self.add_comments_and_infos(clear=True)
                            self.bundle_model.clear()
                    
                    if self.filter_context_cbx.currentText() == bundle_entity['context'] and \
                        bundle_entity['domain'] == domain and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                        self.project_combo_box.currentText() == project) and \
                        not self.filter_bundle_lineedit.text():
                            filtered_bundles.append(
                                bundle_entity['bundle_name']
                            )
                            filtered_bundles = sorted(
                                    set(filtered_bundles), key=filtered_bundles.index
                            )
                            filtered_domains.append(bundle_entity['domain'])
                            filtered_domains = sorted(
                                    set(filtered_domains), key=filtered_domains.index
                            )
                            if bundle_entity['context'] == self.filter_context_cbx.currentText():
                                contexts_of_domains.add(bundle_entity['context'])
                            self.append_items_to_list_view(self.bundle_model, 
                                                    self.bundle_list, 
                                                    filtered_bundles)
                            self.append_items_to_list_view(self.domain_model, 
                                                self.domain_list, 
                                                filtered_domains)
                            self.version_model.clear()
                            self.add_comments_and_infos(clear=True)
                            proceed = False
                            pass 
                        
                    if self.filter_context_cbx.currentText() == bundle_entity['context'] and \
                        bundle_entity['domain'] == domain and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                        self.project_combo_box.currentText() == project) and \
                        self.filter_bundle_lineedit.text():
                        for filtered_bundled_name in filtered_bundled_names1:
                            if filtered_bundled_name == bundle_entity['bundle_name']:
                                contexts_of_domains.add(bundle_entity['context'])

                                filtered_bundles.append(
                                        bundle_entity['bundle_name']
                                )
                                filtered_bundles = sorted(
                                        set(filtered_bundles), key=filtered_bundles.index
                                )
                                filtered_domains.append(bundle_entity['domain'])
                                filtered_domains = sorted(
                                        set(filtered_domains), key=filtered_domains.index
                                )
                                if bundle_entity['context'] == self.filter_context_cbx.currentText():
                                    contexts_of_domains.add(bundle_entity['context'])
                                self.append_items_to_list_view(self.bundle_model, 
                                                        self.bundle_list, 
                                                        filtered_bundles)
                                self.append_items_to_list_view(self.domain_model, 
                                                    self.domain_list, 
                                                    filtered_domains)
                                self.version_model.clear()
                                self.add_comments_and_infos(clear=True)
                                proceed = False
                            
                    elif self.filter_context_cbx.currentText() == bundle_entity['context'] and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                        self.project_combo_box.currentText() == project) and \
                        proceed: 
                        self.bundle_model.clear()
                        self.add_comments_and_infos(clear=True)
                      
                elif user_selected_bundle and \
                    bundle_entity['bundle_name'] == user_selected_bundle and \
                    bundle_entity['context'] == self.filter_context_cbx.currentText() and \
                    bundle_entity['domain'] == domain:
                        filtered_version.append(
                             {bundle_entity['version']: bundle_entity}   
                        )
                        filtered_domains.append(bundle_entity['domain'])
                        filtered_domains = sorted(
                                set(filtered_domains), key=filtered_domains.index
                        )
                        contexts_of_domains.add(bundle_entity['context'])
                        self.append_items_to_list_view(self.version_model, 
                                            self.version_list, 
                                            filtered_version,
                                            metadata=True)
                        self.append_items_to_list_view(self.domain_model, 
                                                self.domain_list, 
                                                filtered_domains)
                        self.add_comments_and_infos(bundle_name=user_selected_bundle,
                                                    domain=domain,
                                                    context=self.filter_context_cbx.currentText())
                        proceed_clear_for_domain_mismatch = False
                        
                        
                elif user_selected_bundle and \
                    self.filter_domain_cbx.currentText() != bundle_entity['domain'] and \
                    (self.filter_context_cbx.currentText() !=  bundle_entity['context'] or \
                    not self.filter_context_cbx.currentText()) and \
                    proceed_clear_for_domain_mismatch:
                        self.add_comments_and_infos(clear=True)
                    
                if not user_selected_bundle and \
                    bundle_entity['bundle_name'] == user_selected_bundle and \
                    self.filter_domain_cbx.currentText() == bundle_entity['domain']:
                    filtered_domains.append(bundle_entity['domain'])
                    filtered_domains = sorted(
                            set(filtered_domains), key=filtered_domains.index
                    )
                    self.append_items_to_list_view(self.domain_model, 
                                            self.domain_list, 
                                            filtered_domains)

                # User not selected any bundle, domain not exist in bundle entity
                # contex not exist in bundle entity then clear version, info.
                # comments and bundles    
                if proceed:  
                    if not user_selected_bundle and \
                        domain not in bundle_entity['domain'] and \
                        self.filter_context_cbx.currentText() not in bundle_entity['context']:
                            self.version_model.clear()
                            self.add_comments_and_infos(clear=True)
                            self.bundle_model.clear()

            if not user_selected_bundle and \
                not self.filter_bundle_lineedit.text() and \
                not self.filter_context_cbx.currentText() and \
                not self.filter_domain_cbx.currentText():
                contexts_of_domains = sorted(set(self.contexts), 
                                            key = self.contexts.index)
                self.append_items_to_list_view(self.context_model, 
                                                self.context_list, 
                                                contexts_of_domains)  
                        
            if self.bundle_list.currentIndex().data():
                self.append_items_to_list_view(self.version_model, 
                                        self.version_list, 
                                        filtered_version,
                                        metadata=True)

            self.append_items_to_list_view(self.context_model, 
                                    self.context_list, 
                                    contexts_of_domains)
        self.bundle_type_label.setText('')
                
    def filter_version_on_context_by_domain(self, 
                                            context: str) -> None:
        """Method do several filtering operations.
        Update all the widgets based upon the context 
        filter

        Args:
            context (str): context keyword paramater
                            vop, sop, dop or rop etc
        """
        
        context_versions = []
        filtered_context = set()
        filtered_bundles = []
        filtered_domains = []
        proceed_clear = True
        user_selected_bundle = self.bundle_list.currentIndex().data()
        user_selected_domain = self.filter_domain_cbx.currentText()
        user_selected_project = self.project_combo_box.currentText()
        
        # If user not selected any bundle initially it loads the 
        # projects based bundles based upon the project choosen
        if not user_selected_bundle:
            self.filter_bundle_to_selected_project(
                        self.project_combo_box.currentText(),
                        update_all = False
            )
        # Get the user entered text in the bundle search text box.
        # if any matching text exist with bundle list view items save it 
        # in a set.
        # 
        # Reteive the bundle list model 
        model = self.bundle_model
        # Find qstandard items matching with the search text box 
        items = model.findItems(self.filter_bundle_lineedit.text(), 
                                flags=Qt.MatchContains)
        # For each qstandard item aquire the text and save it in set
        filtered_bundled_names1 = set()
        for index in items:
            filtered_bundled_names1.add(index.text())
            
        for _, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                if bundle_entity['context'] == context and \
                        not self.filter_bundle_lineedit.text():
                    if bundle_entity['bundle_name'] == user_selected_bundle and \
                        bundle_entity['domain'] == user_selected_domain:
                            self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                    domain=user_selected_domain,
                                                    context=context)
                            filtered_context.add(
                                    bundle_entity['context']
                            )
                            context_versions.append(
                                    {bundle_entity['version']: bundle_entity}
                            )
                            
                    elif bundle_entity['context'] == context and \
                        not user_selected_bundle and not user_selected_domain and \
                        (user_selected_project == ALL_PROJECTS_KEY or \
                        user_selected_project == bundle_entity['project_name']) and \
                        not self.filter_bundle_lineedit.text():
                        filtered_bundles.append(
                                bundle_entity['bundle_name']
                        )
                        filtered_bundles = sorted(
                                set(filtered_bundles), key=filtered_bundles.index
                        )
                        filtered_context.add(
                                    bundle_entity['context']
                        )
                        filtered_domains.append(
                            bundle_entity['domain']
                        )
                        filtered_domains = sorted(
                                set(filtered_domains), key=filtered_domains.index
                        )
                        self.append_items_to_list_view(self.bundle_model, 
                                                self.bundle_list, 
                                                filtered_bundles)
                        self.append_items_to_list_view(self.domain_model, 
                                                self.domain_list, 
                                                filtered_domains)
                        self.version_model.clear()
                        self.add_comments_and_infos(clear=True)
                        proceed_clear = False
                        
                            
                elif bundle_entity['context'] == context and \
                    not user_selected_bundle and not user_selected_domain and \
                    (user_selected_project == bundle_entity['project_name'] or \
                    user_selected_project == ALL_PROJECTS_KEY) and \
                    self.filter_bundle_lineedit.text():
                    for filtered_bundled_name in filtered_bundled_names1:
                        if filtered_bundled_name == bundle_entity['bundle_name']:
                            filtered_context.add(bundle_entity['context'])
                            filtered_bundles.append(
                                        bundle_entity['bundle_name']
                            )
                            filtered_bundles = sorted(
                                    set(filtered_bundles), key=filtered_bundles.index
                            )
                            filtered_context.add(
                                        bundle_entity['context']
                            )
                            filtered_domains.append(
                                bundle_entity['domain']
                            )
                            filtered_domains = sorted(
                                    set(filtered_domains), key=filtered_domains.index
                            )
                            self.append_items_to_list_view(self.bundle_model, 
                                                    self.bundle_list, 
                                                    filtered_bundles)
                            self.append_items_to_list_view(self.domain_model, 
                                                    self.domain_list, 
                                                    filtered_domains)
                            self.version_model.clear()
                            self.add_comments_and_infos(clear=True)
                            proceed_clear = False
                
                elif bundle_entity['context'] != context and \
                        not user_selected_bundle and not user_selected_domain and \
                        (user_selected_project == ALL_PROJECTS_KEY or \
                        user_selected_project == bundle_entity['project_name']):
                    if proceed_clear:
                        self.bundle_model.clear()
                        self.add_comments_and_infos(clear=True)
                        self.domain_model.clear()
                          
                elif not self.bundle_list.currentIndex().data() and \
                        bundle_entity['context'] != context and \
                        (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                        self.project_combo_box.currentText() == bundle_entity['project_name']) and \
                        not user_selected_bundle:
                        self.bundle_model.clear()
                        self.add_comments_and_infos(clear=True)
                
                elif self.filter_domain_cbx.currentText() and \
                    bundle_entity['domain'] != user_selected_domain and \
                    not user_selected_bundle:
                    self.bundle_model.clear()
                    self.domain_model.clear()

                else:
                    if proceed_clear:
                        self.version_model.clear()
                        self.add_comments_and_infos(clear=True)
                
        self.append_items_to_list_view(self.version_model, 
                                self.version_list, 
                                context_versions,
                                metadata=True)
        self.append_items_to_list_view(self.context_model, 
                                    self.context_list, 
                                    filtered_context)
        self.bundle_type_label.setText('')               
        pass
    
    def filter_version_on_context_of_all_domain(self, context: str) -> None:

        """Works same as filter_version_on_context_by_domain.
        Domain filter and othe filter factors seperated as 
        into this method.

        Args:
            context (str): Context name passed by the user selection
        """
        
        versions = []
        filtered_context = set()
        filtered_bundles = []
        filtered_domains = []
        proceed = True
        for project, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                if bundle_entity['context'] == context: 
                    if not self.filter_domain_cbx.currentText():
                        if bundle_entity['bundle_name'] == self.bundle_list.currentIndex().data():
                            filtered_context.add(bundle_entity['context'])
                            versions.append(
                                    {bundle_entity['version']: bundle_entity}
                            )
                            self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                        context=context)
                            
                    elif not self.bundle_list.currentIndex().data() and \
                            bundle_entity['domain'] == self.filter_domain_cbx.currentText() and \
                            bundle_entity['context'] == context and \
                            (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                            self.project_combo_box.currentText() == project) and \
                            self.filter_bundle_lineedit.text() in bundle_entity['bundle_name']:
                        filtered_context.add(bundle_entity['context'])
                        filtered_bundles.append(
                            bundle_entity['bundle_name']
                        )
                        filtered_bundles = sorted(
                                set(filtered_bundles), key=filtered_bundles.index
                        )
                        filtered_domains.append(
                            bundle_entity['domain']
                        )
                        filtered_domains = sorted(
                                set(filtered_domains), key=filtered_domains.index
                        )
                        self.append_items_to_list_view(self.bundle_model, 
                                                self.bundle_list, 
                                                filtered_bundles)
                        self.append_items_to_list_view(self.domain_model, 
                                                self.domain_list, 
                                                filtered_domains)
                        self.version_model.clear()
                        self.add_comments_and_infos(clear=True)
                        proceed = False
                          
                    elif self.filter_domain_cbx.currentText():
                        if bundle_entity['bundle_name'] == self.bundle_list.currentIndex().data() and \
                            bundle_entity['context'] == context and \
                            bundle_entity['domain'] == self.filter_domain_cbx.currentText():
                                filtered_context.add(bundle_entity['context'])
                                self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'],
                                                    domain=self.filter_domain_cbx.currentText(),
                                                    context=self.filter_context_cbx.currentText())
                                versions.append(
                                    {bundle_entity['version']: bundle_entity}
                                )
                                
                elif not self.bundle_list.currentIndex().data() and \
                    bundle_entity['domain'] == self.filter_domain_cbx.currentText() and \
                    bundle_entity['context'] != context and \
                    (self.project_combo_box.currentText() == ALL_PROJECTS_KEY or \
                    self.project_combo_box.currentText() == project) and \
                    proceed:
                        self.bundle_model.clear()
                        self.add_comments_and_infos(clear=True)
                                
           
        if self.bundle_list.currentIndex().data():
            self.append_items_to_list_view(self.version_model, 
                                    self.version_list, 
                                    versions,
                                    metadata=True)
        if filtered_context:
            self.append_items_to_list_view(self.context_model, 
                                        self.context_list, 
                                        filtered_context)

    def filter_bundle_to_selected_project(self, 
                                          project_name: str,
                                          update_all: bool = True) -> None:
        """
        For a selected project name from project selection combobbox
        the related bundle, info, comments, version and domain, conext 
        uploaded into respective qt widgets.

        update_all boolean determine whetheter to update version, info 
        and comments or not

        Args:
            project_name (str): Project name passed from the combobox
                                selected by user
            update_all (bool, optional): version, info, comments update status
                                        if passed true then it updated. Defaults to True.
        """
        # Get search box text  
        filter_input_text= self.filter_bundle_lineedit.text()

        # All project selection and no search box text input
        # collect all bundles. Collected with various combination
        if project_name == ALL_PROJECTS_KEY and \
                not filter_input_text:
             bundles = self.templates.get_all_bundles()

        # project name is 'all' and search box input is exist
        # get all the project names matching with the text
        elif project_name == ALL_PROJECTS_KEY and \
                filter_input_text:
            # serach box text sended as filter input text
            bundles = self.templates.get_all_bundles(all_mode=True,
                                                     matching_text=filter_input_text)
        
        # given project name is match with project combobox text and 
        # filter text exist, then collect only the bundles registered
        # for that project
        elif project_name == self.project_combo_box.currentText() and \
                    filter_input_text:
            # all_mode set false to not retrive all projects
            bundles = self.templates.get_all_bundles(
                project_name=project_name, 
                all_mode=False, 
                matching_text=filter_input_text
            )  
            
        elif not filter_input_text:

            bundles = self.templates.get_all_bundles(
                project_name=project_name, all_mode=False
            )
        
        # 'all' project not selected and no serach input is there
        # collect all projects, domain, context and update the 
        # info and comments of the project
        domains = set()
        contexts = set()
        available_projects = set()
        available_projects.add(ALL_PROJECTS_KEY)
        versions = []
        if project_name != ALL_PROJECTS_KEY and not \
                    filter_input_text:
            for project, bundle_entities in self.all_bundle_info_entities.items():
                available_projects.add(project)
                for bundle_entity in bundle_entities:
                    if project == project_name:
                        domains.add(bundle_entity['domain'])
                        contexts.add(bundle_entity['context'])
                        versions.append({bundle_entity['version']: bundle_entity})
                        self.add_comments_and_infos(project_name=project)
                    
        # no search text and 'all' project selected 
        # assign default bundle, context, domain and versions
        # update info and comments for all bundles                
        elif not filter_input_text and \
                    self.project_combo_box.currentText() == ALL_PROJECTS_KEY:
            bundles = self.bundles
            contexts = self.contexts
            domains = self.domains
            versions = self.all_versions
            self.add_comments_and_infos() 

        # Update the widget content based upon the search box text
        # all matching text bundle updated into the bundle list view
        # as so other context, domain, version, info and comments 
        # also updated            
        elif filter_input_text:
            bundles = set()
            model = self.bundle_model
            self.append_items_to_list_view(self.bundle_model, 
                                self.bundle_list, 
                                self.bundles)
            items = model.findItems(filter_input_text, flags=Qt.MatchContains)
            filtered_bundled_names = set()
            for index in items:
                filtered_bundled_names.add(index.text())

            for filtered_bundled_name in filtered_bundled_names:
                for project, bundle_entities in self.all_bundle_info_entities.items():
                    available_projects.add(project)
                    for bundle_entity in bundle_entities:
                        if filtered_bundled_name == bundle_entity['bundle_name']:
                            
                            def add_entities():
                                bundles.add(bundle_entity['bundle_name'])
                                domains.add(bundle_entity['domain'])
                                contexts.add(bundle_entity['context'])
                                versions.append(
                                    {bundle_entity['version']: bundle_entity}
                                )
                                self.add_comments_and_infos(bundle_list=bundles,
                                                        multi_bundle_append=True)
                            if project == self.project_combo_box.currentText():
                                add_entities()

                            if ALL_PROJECTS_KEY == self.project_combo_box.currentText():
                                add_entities()
                                
            if not bundles:
                self.add_comments_and_infos(clear=True)

        if self.project_combo_box.currentText() not in available_projects:
            self.add_comments_and_infos(clear=True)   
        
        self.append_items_to_list_view(self.bundle_model, 
                                self.bundle_list, 
                                bundles)

        # Ensure the context, domain, version, info, comments 
        # widgets wont updated
        if update_all:
            
            self.filter_domain_cbx.setCurrentIndex(-1)
            self.filter_context_cbx.setCurrentIndex(-1)
            
            self.append_items_to_list_view(self.domain_model, 
                                    self.domain_list, 
                                    domains)
            self.append_items_to_list_view(self.context_model, 
                                    self.context_list, 
                                    contexts)
            self.append_items_to_list_view(self.version_model, 
                                    self.version_list, 
                                    [],
                                    metadata=True
                                    )
            self.add_comments_and_infos(clear=True)
            
            # Reload all bundles and version if no user
            # search box text is exist
            if not self.filter_bundle_lineedit.text():
                self.load_bundles()
                self.load_versions()
        
        self.switch_util_buttons_state(status=True)
        self.bundle_type_label.setText('')

    def add_comments_and_infos(self,
                               project_name: str = '',
                               bundle_name: str = '',
                               bundle_list: set = '',
                               domain:str ='',
                               context: str ='',
                               version:str = '',
                               clear: bool = False,
                               multi_bundle_append: bool = False) -> None:
        """
        Info and comments from bundle entities registered into 
        info line edit and comments line edit widgets.
        These widgets Updated with different combinations. 
        In dashboard mode this method retrive all the bundles infos 
        load the addtional infos in the info line edit widget and
        load the comments in the comments line edit widget

        Example: 
            1.  For a selected bundle this method loads the info and 
                comments of that bundle
            2.  For a selected domain and context this method loads 
                the infos and comments of that domain and context

        Args:
            project_name (str, optional): Project name selected by the user from 
                                        project combobox. Defaults to ''.
            bundle_name (str, optional): Bundle name selected by user from 
                                        the bundle list view. Defaults to ''.
            bundle_list (set, optional): list of bundle names. Defaults to ''.
            domain (str, optional): domain name . Defaults to ''.
            context (str, optional): context name. Defaults to ''.
            version (str, optional): version label (v001, v002). Defaults to ''.
            clear (bool, optional): Clear all the info and comments while set to true.
                                     Defaults to False.
            multi_bundle_append (bool, optional): Iteration enabled while seted true. 
                                                Defaults to False.
        """
        
        
        def fill_widgets():

            """
            Create a textual representation for the info and 
            comments widgets which is retrived from the bundle 
            entity. 
            """
            self.comments_textedit.append(bundle_entity['comments'])
            self.comments_textedit.append("-"*75)
            for key, value in bundle_entity.items():
                if key != 'bundle_name' and key != 'bundle_type' and \
                    key != 'comments' and key != 'module_path' and \
                    key != 'config_path' and key != 'project_name':
                    self.info_textedit.append(f"{key}:  {value}")
            self.info_textedit.append("-"*60)

        # For each time the widgets cleared while user actions changed
        self.info_textedit.clear()
        self.comments_textedit.clear()
        for project, bundle_entities in self.all_bundle_info_entities.items():
            for bundle_entity in bundle_entities:
                if project_name and not version and not bundle_name and \
                    not domain and not context:
                    if project_name ==project:
                       fill_widgets()
                
                elif context and not domain and not bundle_name and \
                    not project_name and not version:
                    if context== bundle_entity["context"]:
                        fill_widgets()
                        
                elif project_name and context and not domain and \
                    not version and not bundle_name and not version:
                        if project_name== bundle_entity["project_name"] and \
                                    context == bundle_entity["context"]:
                            fill_widgets()
                
                elif bundle_list and multi_bundle_append and \
                    context and not domain and \
                    not version and not bundle_name:
                    for bundle in bundle_list:
                        if bundle == bundle_entity["bundle_name"] and \
                        context == bundle_entity["context"]:
                            fill_widgets()
                
                        
                elif bundle_list and multi_bundle_append and \
                    domain and context:
                    for bundle in bundle_list:
                        if bundle == bundle_entity["bundle_name"] and \
                        domain == bundle_entity["domain"] and \
                        context == bundle_entity["context"]:
                            fill_widgets()
           
                            
                elif bundle_list and multi_bundle_append and not domain and not context:
                    for bundle in bundle_list:
                        if bundle == bundle_entity["bundle_name"]:
                            fill_widgets()
                            
                elif domain and not multi_bundle_append and \
                    not bundle_name and not context:
                    if domain== bundle_entity["domain"]:
                        fill_widgets()
                        
                elif domain and multi_bundle_append and \
                    not bundle_name and not context:
                    for bundle in bundle_list:
                        if bundle == bundle_entity["bundle_name"] and \
                        domain == bundle_entity["domain"]:
                            fill_widgets()
                        
                elif context and domain and not bundle_name and \
                    not bundle_list and not multi_bundle_append and \
                    not version:
                    if context== bundle_entity["context"] and \
                            domain == bundle_entity["domain"]:
                        fill_widgets()
                        
                elif bundle_name and not domain and not context:
                    if bundle_name == bundle_entity["bundle_name"]:
                        fill_widgets()
                        
                elif bundle_name and domain and not context:
                    if domain== bundle_entity["domain"] and \
                                bundle_name == bundle_entity["bundle_name"]:
                        fill_widgets()
                        
                elif bundle_name and not domain and context:
                    if context== bundle_entity["context"] and \
                                bundle_name == bundle_entity["bundle_name"]:
                        fill_widgets()
                        
                elif bundle_name and domain and context and \
                    not project_name and not version:
                    if domain== bundle_entity["domain"] and \
                                bundle_name == bundle_entity["bundle_name"] and \
                                context == bundle_entity["context"]:
                        fill_widgets()
                
                elif version and bundle_name and project_name and \
                    domain and context:
                    if  bundle_entity['version'] == version and \
                        bundle_entity['bundle_name'] == bundle_name and \
                        bundle_entity['project_name'] == project_name and \
                        bundle_entity['domain'] == domain and \
                        bundle_entity['context'] == context:
                            fill_widgets()
                        
                elif clear:
                    self.info_textedit.clear()
                    
                else:
                    fill_widgets()

        # Preserve the scroll bar position into starting point of the
        # line wdit widget. The line edit scroll always goes to bottome
        # after added huge text. Below line ensures always the 
        # cursor of he textedit go to beginning of the text
        info_textedit_cursor = self.info_textedit.textCursor()
        info_textedit_cursor.movePosition(info_textedit_cursor.Start)
        self.info_textedit.setTextCursor(info_textedit_cursor)
        
        comments_textedit_cursor = self.comments_textedit.textCursor()
        comments_textedit_cursor.movePosition(comments_textedit_cursor.Start)
        self.comments_textedit.setTextCursor(comments_textedit_cursor)
    
    def action_menus(self, position) -> None:
        
        """Version list view enabled with right-click action menus
        A remove texted menu appeared if user right click on any items
        in the version list view
        """

        # Get postion of the version list view 
        mdlIdx = self.version_list.indexAt(position)
        # retrive item
        item = self.version_model.itemFromIndex(mdlIdx)
        # Create the menu of rigth click
        right_click_menu = QtWidgets.QMenu()
        
        # Add action item remove 
        act_add = right_click_menu.addAction("Remove")
        # Signal to remove bundle to remove bundle in the 
        # temolate importer
        act_add.triggered.connect(
                    lambda: self.remove_bundle(item)
        )
        if self.bundle_list.currentIndex().data():
            right_click_menu.exec_(self.sender().viewport().mapToGlobal(position))
    
    def remove_bundle(self, item: QModelIndex) -> None:

        """
        The selected version of the bundle deleted from the widget
        and also from the file system. 

        Only the owner of the bundle allowed to remove the version of 
        the bundle

        Args:
            item (QModelIndex): selected item model index
        """
        
        items = item.data(Qt.UserRole)
        if items['user_name'] == os.environ['USERNAME']:
            clear_listview_enitities = self.templates.remove_bundle(items)

            if clear_listview_enitities:
                self.add_comments_and_infos(clear=True)
                self.version_model.clear()
                self.domain_model.clear()
                self.context_model.clear()
            else:

                project_versions = []
                selected_bundle = self.bundle_list.currentIndex().data()
                
                self.all_bundle_info_entities = self.templates.list_all_bundle_entity()
                if selected_bundle:
                    for _, bundle_entities in self.all_bundle_info_entities.items():
                        for bundle_entity in bundle_entities:
                            if bundle_entity['bundle_name'] == selected_bundle:
                                project_versions.append(
                                            {bundle_entity['version']: bundle_entity}
                                )
                                self.add_comments_and_infos(bundle_name=bundle_entity['bundle_name'])
                          
                self.append_items_to_list_view(self.version_model, 
                                        self.version_list, 
                                        project_versions,
                                        metadata=True)

            self.load_bundles()
        else:
            msg = f"The Bundle <b>{items['bundle_name']}</b> "
            msg +=f"created by <b>{items['user_name']}</b> "
            msg += "\nYou Cannot Delete!!"
            user_warning_msgbox = utilMessageBox('warning',
                                            msg)
            user_warning_msgbox.show_message()

    
    def apply_bundle_buton_type(self, 
                                index: QModelIndex) -> None:
        """
        The bundle import button label name gonna switched 
        based on the bundle type. module level bundles 
        selection switch button label to 'Import'
        'Whole Scene' type bundle selection switch button
        label to "Merge"

        Args:
            index (QModelIndex): Selected item model index
        """

        self.version_metadata = self.version_model.data(index, Qt.UserRole)
        self.bundle_type = self.version_metadata['bundle_type']
        bundle_text = f"Bundle Type:  {self.bundle_type}"
        self.bundle_type_label.setText(bundle_text)
        if self.bundle_type == "Module":
            self.import_btn.setText("Import")
        elif self.bundle_type == "Whole Scene":
            self.import_btn.setText("Merge")
        else:
            self.import_btn.setText("Import")
        
    
    def filter_items(self, 
                    listview: QtWidgets.QListView , 
                    model: QStandardItemModel, 
                    text: str, 
                    listview_name: str, 
                    items: list=[]) -> None:
        """
        Implementing bundle filtering model. 
        qt filter proxy model for bundle list view. 
        The given text is looked upon in the list view
        using qt regex condition. 

        Args:
            listview (QtWidgets.QListView): qt list view widget
            model (QStandardItemModel): model of the list view
            text (str): text string for filtering 
            listview_name (str): List view widget name
            items (list, optional): items list. context or domain Defaults to [].
        """
        
        if text != ALL_PROJECTS_KEY:
            self.bundle_list_filter_proxy = QSortFilterProxyModel()
            self.bundle_list_filter_proxy.setObjectName(listview_name)
            self.bundle_list_filter_proxy.setDynamicSortFilter(True)
            self.bundle_list_filter_proxy.setRecursiveFilteringEnabled(True)
            self.bundle_list_filter_proxy.setSourceModel(model)
            listview.setModel(self.bundle_list_filter_proxy)
            pattern = QRegExp(text, Qt.CaseSensitive, QRegExp.RegExp)
            self.bundle_list_filter_proxy.setFilterRegExp(pattern)
        else:
            self.append_items_to_list_view(model, listview, items=items)
        self.bundle_type_label.setText('')
        
    def load(self) -> None:

        """
        Load the bundle into the current hip file.
        'module' bundles imported if the appropriate context exist else 
        it create the entire nodes. 'Whole scene' merge the hip files 
        into current hip file
        """
        try:
            import houdini_ops
            self.houdini_ops = houdini_ops.HoudiniOPs(file_path=self.version_metadata['module_path'],)
            if self.bundle_type == 'Module':
                bundle_context = self.version_metadata['context']

                # Check whether a suitable context exist for the selected bundle 
                # if not it creat it and import the bundle of 'Module' type
                created_context = self.houdini_ops.load_node_snippets(bundle_context)
                if created_context:
                    msg = f"No <b>{bundle_context}</b> Network Found. Importing Under <b>{created_context}</b>"
                    bundle_creation_msgbox = utilMessageBox('warning',
                                                    msg)
                    bundle_creation_msgbox.show_message()
            else:
                # merge the selected bundle to current hip file
                self.houdini_ops.merge_hip()
            self.bundle_type_label.setText('')
        except Exception:
            print("Exception!!!")
    
if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    import_view = Importer()
    import_view.importer_window.show()
    app.exec_()
    