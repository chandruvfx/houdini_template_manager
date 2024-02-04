# View Model for publishing bundles. 

import os
import sys
import re
from datetime import datetime
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets
from PySide2.QtGui import  (QStandardItemModel, 
                            QStandardItem,
                            QPixmap, 
                            QIcon)
from PySide2.QtCore import Qt
from model import (Defaults,
                   Templates,
                   ThadamDB,
                   BundleOpearations)
from helpers import (ConfigFormat, 
                     InfoFormat,
                     MODULE_SAVE_FORMAT,
                     HIP_EXTENSION,
                     INFO_FILE,
                     CONFIG_FILE,
                     ROOT_TEMPLATE_PATH)
from helper_msgboxes import utilMessageBox
import houdini_ops 

class Saver(QtWidgets.QWidget):
    
    def __init__(self):
        
        super(Saver, self).__init__()
        
        dirname = os.path.dirname(__file__)
        ui_file = os.path.join(dirname, 
                               "ui\\node_template_saver.ui"
        )
        ui_loader = QUiLoader()
        self.saver_window = ui_loader.load(ui_file)
        
        if __name__ != '__main__':
            mainLayout = QtWidgets.QVBoxLayout()
            mainLayout.addWidget(self.saver_window)
            self.setLayout(mainLayout)
        
        self.defaults = Defaults()
        self.contexts = self.defaults.get_defaults_context()
        self.domains = self.defaults.get_default_domain()
        self.bundle_types = self.defaults.get_default_bundles_types()
        
        self.thadam_db = ThadamDB()
        self.projects = self.thadam_db.get_projects()
        
        self.templates = Templates()
        # self.available_project_bundles = self.templates.all_project_bundle()
        
        self.houdini_node_ops = houdini_ops.HoudiniOPs()

        self.bundle_name_ldt = self.saver_window.findChild(
            QtWidgets.QLineEdit,
            "bundle_name_ldt"
        )
        # self.bundle_name_ldt.setText("ground")
        self.bundle_name_ldt.textChanged[str].connect(
                    self.bundle_name_validation
        )
        
        self.bundle_name_rule_btn = self.saver_window.findChild(
            QtWidgets.QPushButton,
            "bundle_name_rule_btn"
        )
        self.bundle_name_rule_btn.clicked.connect(
            self.show_naming_rules_messagebox
        )           
            
        self.project_cbx = self.saver_window.findChild(
            QtWidgets.QComboBox,
            "project_cbx"
        )
        self.append_items_to_combobox(self.project_cbx,
                                      self.projects)
        self.project_cbx.setCurrentIndex(-1)
        self.project_cbx.activated[str].connect(
                self.bundle_validation
        )
        
        self.context_cbx = self.saver_window.findChild(
            QtWidgets.QComboBox,
            "context_cbx"
        )
        self.append_items_to_combobox(self.context_cbx,
                                      self.contexts)
        self.context_cbx.setCurrentIndex(-1)
        self.context_cbx.activated[str].connect(
                self.clear_node_list
        )
        
        self.domain_cbx = self.saver_window.findChild(
            QtWidgets.QComboBox,
            "domain_cbx"
        )
        self.append_items_to_combobox(self.domain_cbx,
                                      self.domains)
        self.domain_cbx.setCurrentIndex(-1)
        
        self.bundle_type_cbx = self.saver_window.findChild(
            QtWidgets.QComboBox,
            "bundle_type_cbx"
        )
        self.append_items_to_combobox(self.bundle_type_cbx,
                                      self.bundle_types)
        self.bundle_type_cbx.setCurrentIndex(-1)
        self.bundle_type_cbx.activated[str].connect(self.set_widgets_visibility)
        
        self.module_items_listview = self.saver_window.findChild(
            QtWidgets.QListView,
            "module_items_listview"
        )
        self.module_items_listview.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.module_items_listview.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )
        
        self.add_module_item_btn = self.saver_window.findChild(
            QtWidgets.QPushButton,
            "add_module_item_btn"
        )
        self.add_module_item_btn.clicked.connect(
                self.add_selected_node_from_context
        )
        
        self.remove_module_item_btn = self.saver_window.findChild(
            QtWidgets.QPushButton,
            "remove_module_item_btn"
        )
        self.remove_module_item_btn.clicked.connect(
                self.remove_selected_node_from_context
        )
        
        self.comments_tedt = self.saver_window.findChild(
            QtWidgets.QTextEdit,
            "comments_tedt"
        )
        
        self.publish_btn = self.saver_window.findChild(
            QtWidgets.QPushButton,
            "publish_btn"
        )
        self.publish_btn.clicked.connect(self.publish)
        
        self.select_scene_btn = self.saver_window.findChild(
            QtWidgets.QPushButton,
            "select_scene_btn"
        )
        self.select_scene_btn.clicked.connect(self.select_in_scene)
        self.set_bundle_type_visibility(False)
        
        publish_icon = os.path.join(dirname, "icons/publish.png")
        self.publish_btn.setIcon(QIcon(publish_icon))
        
        bundle_naming_info_icon = os.path.join(dirname, "icons/info.svg")
        self.bundle_name_rule_btn.setIcon(QIcon(bundle_naming_info_icon))
        
        self.tool_label =self.saver_window.findChild(
            QtWidgets.QLabel,
            "tool_label"
        )
        tool_icon = os.path.join(dirname, "icons/saver.png")
        tool_pixmap = QPixmap(tool_icon)
        self.tool_label.setPixmap(tool_pixmap.scaled(200,200, Qt.KeepAspectRatio))
        
        self.tool_title_label =self.saver_window.findChild(
            QtWidgets.QLabel,
            "title_label"
        )
        tool_title_icon = os.path.join(dirname, "icons/node_saver.PNG")
        tool_title_pixmap = QPixmap(tool_title_icon)
        self.tool_title_label.setPixmap(tool_title_pixmap.scaled(220,65))

    
    def bundle_name_validation(self, bundle_name):
        
        def show_message():
            
            msg = "Need begin with Small letters and underscore allowed in followups\n\n"
            msg += "Click the near button to find naming rules"
            bundle_name_messagebox = utilMessageBox('info',
                                            msg)
            bundle_name_messagebox.show_message()
            self.bundle_name_ldt.clear()
            
        if not re.match(r'^[a-z0-9_]*$', bundle_name):
            show_message()
        if bundle_name:
            if bundle_name[0].isdigit():
                show_message()
            elif bundle_name[0].startswith('_'):
                show_message()
                    
    def append_items_to_combobox(self, combobox, items):
        
        for item in items:
            combobox.addItem(item)
    
    def set_bundle_type_visibility(self, status):
        
        self.module_items_listview.setEnabled(status)
        self.add_module_item_btn.setEnabled(status)
        self.remove_module_item_btn.setEnabled(status)
        self.select_scene_btn.setEnabled(status)
    
    def clear_node_list(self):
        
        if self.module_items_listview.model():
            self.module_items_listview.model().clear()
        
    def set_widgets_visibility(self,
                               bundle_type):
        
        if bundle_type == "Whole Scene":
           self.set_bundle_type_visibility(False)
        else:
           self.set_bundle_type_visibility(True)
    
    def show_naming_rules_messagebox(self):
        
        rule_msg = "Bundle Naming Rules\n\n"
        rule_msg += "1. Name should start with small character\n\n"
        rule_msg += "2. Underscore allowed\n\n"
        rule_msg += "3. Special Character Wont Allowed\n\n"
        rule_msg += "4. Same Bundle Name Can not be Used in other Projects\n\n"
        
        naming_rule_msgbox = utilMessageBox('info',
                                            rule_msg)
        naming_rule_msgbox.show_message()
  
    @staticmethod
    def bundle_validation_message(bundle_name,
                                  project_name):
        
        msg = f"Bundle Name <b> {bundle_name}</b> "
        msg += f"Already Used in project <b>{project_name}</b>\n\n"
        msg += "Choose Other Name!!"
        return msg
    
    @staticmethod
    def next_version(version=False):
        
        if version:
            return version + 1
        else:
            return 1
    
    def select_in_scene(self):
        
        model = self.module_items_listview.model()
        for index in range(model.rowCount()):   
            node_path = model.item(index).text()
            self.houdini_node_ops.enable_selection_on_selected_nodes(node_path)
          
    def bundle_validation(self,
                          project_name):
        
        self.available_project_bundles = self.templates.all_project_bundle()
        
        list_bundles = []
        for _, bundles in self.available_project_bundles.items():
            for bundle in bundles:
                list_bundles.append(bundle)
        
        matched_bundle = []
        if self.bundle_name_ldt.text() in list_bundles:
            matched_bundle.append(self.bundle_name_ldt.text())
        
        if project_name in self.available_project_bundles:
            if not matched_bundle:
                return True
                
            elif matched_bundle[0] in list_bundles and matched_bundle[0] in \
                            self.available_project_bundles[project_name]:
                return True
                
            else:
                for project, bundle in self.available_project_bundles.items():
                    if matched_bundle[0] in bundle:
                        self.project_cbx.setCurrentIndex(-1)
                        self.bundle_name_ldt.clear()
                        msg = self.bundle_validation_message(matched_bundle[0],
                                                             project)
                        util_messagebox = utilMessageBox('warning',
                                            msg)
                        util_messagebox.show_message()
                        return False
       
        elif project_name not in self.available_project_bundles:
            
            if not matched_bundle:
                return True
                
            elif matched_bundle[0] in list_bundles:
                for project, bundle in self.available_project_bundles.items():
                    if matched_bundle[0] in bundle:
                        self.project_cbx.setCurrentIndex(-1)
                        self.bundle_name_ldt.clear()
                        msg = self.bundle_validation_message(matched_bundle[0],
                                                             project)
                        util_messagebox = utilMessageBox('warning',
                                            msg)
                        util_messagebox.show_message()
                        return False
                        
        
    def create_bundle_directory_path(self):
        
        bundle = os.path.join(
            self.domain_cbx.currentText(),
            self.context_cbx.currentText(),
            self.project_cbx.currentText(),
            self.bundle_name_ldt.text(),
        )
        return os.path.join(
            ROOT_TEMPLATE_PATH,bundle
        )
    
    def add_selected_node_from_context(self):
        
        if self.houdini_node_ops.node_count() == 0:
            no_node_selected_box = utilMessageBox('info',
                                            "Please Select Node to Add")
            no_node_selected_box.show_message()
        else:
            selected_nodes_network =  self.houdini_node_ops.check_node_category()
            if selected_nodes_network == self.context_cbx.currentText():
                module_list_model = QStandardItemModel()
                self.module_items_listview.setModel(module_list_model)
                for item in self.houdini_node_ops.load_houdini_nodes():
                    qstandarditem = QStandardItem(item)
                    module_list_model.appendRow(qstandarditem)
            else:
                msg = f"Selected nodes not belongs to <b>{self.context_cbx.currentText()}</b>\n"
                msg += "Choose appropriate context!!"
                util_messagebox = utilMessageBox('warning',
                                                msg)
                util_messagebox.show_message() 
    
    def remove_selected_node_from_context(self):
        
        rows = []
        node_paths = []
        for index in reversed(sorted(self.module_items_listview.selectedIndexes())):
            node_path = self.module_items_listview.model().itemFromIndex(index).text()
            self.module_items_listview.model().takeRow(index.row())
            self.houdini_node_ops.remove_selected_nodes(node_path=node_path)
            
        
    def create_bundles(self):
    
        def display_publish_message(version):
            
            message = f"A New Version <b>{str(version).zfill(3)}</b> Published Successfully!!"
            util_messagebox = utilMessageBox('info',
                                            message)
            util_messagebox.show_message()
            
        def helper(version):
            
            uti_file = f"{self.bundle_name_ldt.text()}{MODULE_SAVE_FORMAT}"
            hip_file = f"{self.bundle_name_ldt.text()}{HIP_EXTENSION}"
            
            if self.bundle_type_cbx.currentText() == 'Module':
                
                uti_file_path = os.path.join(
                        latest_version_path,
                        uti_file  
                )
                
                self.uti_houdini_ops = houdini_ops.HoudiniOPs(file_path=uti_file_path)
                self.uti_houdini_ops.save_node_snippets()
                node_count = self.uti_houdini_ops.node_count()
                file_size = os.stat(uti_file_path).st_size
                
                self.uti_config_formates = InfoFormat(os.environ['USERNAME'],
                                                    self.context_cbx.currentText(),
                                                    version,
                                                    node_count,
                                                    self.bundle_type_cbx.currentText(),
                                                    uti_file_path,
                                                    str(round(file_size/1024**2, 2))+"Mb",
                                                    datetime.now().strftime('%d-%m-%Y %H:%M'),
                                                    self.comments_tedt.toPlainText())
                bundle_operations.generate_info_file(self.uti_config_formates.data(),
                                                     file_type = INFO_FILE)

            else:
                hip_file_path = os.path.join(
                        latest_version_path,
                        hip_file  
                )
                self.hip_houdini_ops = houdini_ops.HoudiniOPs(file_path=hip_file_path)
                self.hip_houdini_ops.save_hip()
                file_size = os.stat(hip_file_path).st_size
                
                self.hip_config_formates = InfoFormat(os.environ['USERNAME'],
                                                    self.context_cbx.currentText(),
                                                    version,
                                                    0,
                                                    self.bundle_type_cbx.currentText(),
                                                    hip_file_path,
                                                    str(round(file_size/1024**2, 2))+"Mb",
                                                    datetime.now().strftime('%d-%m-%Y %H:%M'),
                                                    self.comments_tedt.toPlainText())
                bundle_operations.generate_info_file(self.hip_config_formates.data(),
                                                     file_type = INFO_FILE)
                pass
        
        bundle_directory = self.create_bundle_directory_path()
        bundle_dict = self.bundle_validation(self.project_cbx.currentText())
        if bundle_dict:
            if os.path.exists(bundle_directory):
                self.templates.get_version_info_paths(self.bundle_name_ldt.text(),
                                                      self.domain_cbx.currentText(),
                                                      self.context_cbx.currentText(),
                                                      project=self.project_cbx.currentText()
                                                    )
                max_version= max(
                            self.templates.get_versions(text_mode=False)
                )
                latest_version = self.next_version(max_version)
                display_publish_message(latest_version)
                
                bundle_operations = BundleOpearations(bundle_directory, latest_version)
                latest_version_path = bundle_operations.make_info_file_path_directory()
                helper(latest_version)

            else:
                first_version = self.next_version()
                bundle_operations = BundleOpearations(bundle_directory, first_version)
                first_config_bundle_path = bundle_operations.make_config_file_path_directory()
                self.bundle_config_formate = ConfigFormat(
                                self.bundle_name_ldt.text(),
                                self.project_cbx.currentText(),
                                self.domain_cbx.currentText(),
                                self.context_cbx.currentText(),
                                self.bundle_type_cbx.currentText(),
                                bundle_directory,
                )
                bundle_operations.generate_info_file(self.bundle_config_formate.data(),
                                                     file_type=CONFIG_FILE)
                latest_version_path = bundle_operations.make_info_file_path_directory()
                display_publish_message(first_version)
                helper(first_version)

          
    def publish(self):
        
        def display_messages(message):
            
            util_messagebox = utilMessageBox('info',
                                                message)
            util_messagebox.show_message()
        
        if not self.bundle_name_ldt.text() or \
            not self.project_cbx.currentText() or \
            not self.domain_cbx.currentText() or \
            not self.context_cbx.currentText() or \
            not self.bundle_type_cbx.currentText():
                msg = "One or More Field not selected. Please Fill All Fields!!"
                display_messages(msg)
                
        elif not self.comments_tedt.toPlainText():
            msg = "Comments Must Be Entered!!"
            display_messages(msg)
            
        elif self.bundle_type_cbx.currentText() == "Module" and \
            not self.module_items_listview.model():
                msg = "Please Fill Node Items!!"
                display_messages(msg)
                
        elif self.bundle_type_cbx.currentText() == "Module" and \
            self.module_items_listview.model() and \
            self.module_items_listview.model().rowCount() == 0:
                msg = "Please Fill Node Items!!"
                display_messages(msg)
                
        elif self.bundle_type_cbx.currentText() == "Module" and \
                self.houdini_node_ops.node_count() == 0:
                msg = "No Nodes Were Selected!!"
                msg += "Select Nodes and Add in Node list to publish"
                display_messages(msg)
        else:
            self.create_bundles()
            self.bundle_name_ldt.clear()
            self.project_cbx.setCurrentIndex(-1)
            self.domain_cbx.setCurrentIndex(-1)
            self.context_cbx.setCurrentIndex(-1)
            self.bundle_type_cbx.setCurrentIndex(-1)
            if self.module_items_listview.model():
                self.module_items_listview.model().clear()
            self.comments_tedt.clear()
            

if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    import_view = Saver()
    import_view.saver_window.show()
    app.exec_()
    