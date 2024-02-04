# Data model for template pilot. all underlying operations carried out
# with this model. 
import os
import sys
import re
import json
import shutil
from thadam_base import thadam_api
from helpers import(FileOperations,
                    VersionOperations,
                    Defaults,
                    ROOT_DEFAULT_PATH,
                    ROOT_TEMPLATE_PATH,
                    CONFIG_FILE,
                    INFO_FILE)


class Templates(FileOperations, VersionOperations):
    
    """
    Model class for Template view widget operations.
    """
    def __init__(self) -> None:
        
        """INitialization. calling super for file operations"""
        FileOperations.__init__(self)
        
        
    def get_all_bundles(self,
                        matching_text: str ='',
                        project_name: str='',
                        all_mode: bool =True,
                        return_with_project_name: bool=False) -> list | dict :
        """
        From bundle entity this method returns bundles list 
        for given combination of conditions. The config.json file readed from here
        to retrive bundles. 

        Few condition also works here. 
        1. the bundle name as key and project name as value returned.
        2. Any text matching with the bundle names retrived  

        Args:
            matching_text (str, optional): regex text. Defaults to ''.
            project_name (str, optional): name of the project . Defaults to ''.
            all_mode (bool, optional): boolean to not proceed for some cases. Defaults to True.
            return_with_project_name (bool, optional): bundle as key, project name as value saved in 
                                    dict if tis mode enabled. Defaults to False.

        Returns:
            list | dict:    bundles list or bundle name as key and project name 
                            as value returned
        """
        
        self.bundles = set()
        self.bundle_with_project_dict = {}
        for root,_,config_file in os.walk(ROOT_TEMPLATE_PATH):
            if config_file:
                if config_file[0] == CONFIG_FILE:
                        self.set_file_path(root)
                        read_config_file = self.read_file_datas(CONFIG_FILE)
                        if all_mode and not project_name and not matching_text:
                                self.bundles.add(
                                    read_config_file['name']
                                )
                        elif all_mode and not project_name and matching_text:
                            if matching_text in read_config_file['name']:
                                self.bundles.add(
                                    read_config_file['name']
                                )
                        elif project_name and not all_mode and not matching_text:
                            if project_name == read_config_file['project']:
                                self.bundles.add(
                                    read_config_file['name']
                                )
                        elif project_name and not all_mode and matching_text:
                            if project_name == read_config_file['project'] and \
                                matching_text in read_config_file['name']:
                                    self.bundles.add(
                                        read_config_file['name']
                                    )
                        if all_mode and return_with_project_name:
                            self.bundle_with_project_dict.update(
                                {
                                    read_config_file['name']:  read_config_file['project']
                                }
                            )
        if return_with_project_name:
            return dict(sorted(self.bundle_with_project_dict.items()))
        else:                           
            return sorted(self.bundles)
        
    def get_version_info_paths(self, 
                               bundle: str,
                               domain: str, 
                               context: str,
                               project: str ='') -> None:
        """
        set the config path to the info_file_paths attribute by 
        retriving the config_path  from the config_json. 
        the config path combined with the latest version and
        set the path

        Args:
            bundle (str): bundle name
            domain (str): domain name
            context (str): context name
            project (str, optional): Name of the project.
                                    if project name given then only those path set
                                    deafult it set for all projects. Defaults to ''.
        """
        
        def list_info_file_paths():
            
            if bundle == template_config_file['name']:
                if domain == template_config_file['domain'] and \
                    context == template_config_file['context']:
                        filter_folders = list(
                            filter(lambda x: re.findall('^v\d+', x), folders)
                        )
                        self.info_file_paths = list(
                            map(
                                lambda x: os.path.join(template_config_file['config_path'], x),
                                filter_folders
                            )
                        )
                    
            elif not hasattr(self, 'info_file_paths'):
                self.info_file_paths[:] = []
            
        self.info_file_paths = []
        for root,directories,config_file in os.walk(ROOT_TEMPLATE_PATH):
            if config_file:
                if config_file[0] == CONFIG_FILE:
                    self.set_file_path(root)
                    folders = directories
                    template_config_file = self.read_file_datas(CONFIG_FILE)
                    if project == template_config_file['project']:
                        list_info_file_paths()
                    if not project:
                        list_info_file_paths()
        
    def list_all_bundle_entity(self) -> dict:

        """
        Retrive all entities from the config.json and info.json 
        and make a dictionary.

        Returns:
            dict:   The returned dict project is the key and 
                    bundle info entities were values
        """
        
        raw_project_bundle_dicts = []
        for root,directories,config_file in os.walk(ROOT_TEMPLATE_PATH):
            if config_file:
                if config_file[0] == CONFIG_FILE:
                    self.set_file_path(root)
                    config_info_datas = self.read_file_datas(CONFIG_FILE)
                    project_name = config_info_datas['project']
                    domain = config_info_datas['domain']
                    context = config_info_datas['context']
                    bundle_name = config_info_datas['name']
                    config_path = config_info_datas['config_path']
                    for directory in directories:
                        verison_folders = os.path.join(
                            root,directory
                        )
                        self.set_file_path(verison_folders)
                        version_info_datas = self.read_file_datas(INFO_FILE)
                        version_no = version_info_datas['version']
                        user_name = version_info_datas['user_name']
                        comments = version_info_datas['comments']
                        node_count = version_info_datas['node_count']
                        bundle_type = version_info_datas['type']
                        file_size = version_info_datas['file_size']
                        created_on = version_info_datas['Created On']
                        module_path = version_info_datas['module_path']
                        VersionOperations.__init__(self, version_no)
                        version = self.pad_version_identifier_to_number()
                        raw_project_bundle_dicts.append(
                                        {project_name:  dict(bundle_name=bundle_name,
                                                            project_name = project_name,
                                                            user_name=user_name,
                                                            node_count=node_count,
                                                            domain=domain, 
                                                            context=context,
                                                            bundle_type=bundle_type,
                                                            file_size=file_size,
                                                            created_on=created_on,
                                                            version=version,
                                                            module_path=module_path,
                                                            config_path=config_path,
                                                            comments=comments)
                                                    }
                        )

        all_projects_entities = {}           
        for raw_project_bundle_dict in raw_project_bundle_dicts:
            for project, _ in raw_project_bundle_dict.items():
                    all_projects_entities[project] = []
        for raw_project_bundle_dict in raw_project_bundle_dicts:
            for project, bundles in raw_project_bundle_dict.items():
                if project in all_projects_entities:
                     all_projects_entities[project].append(bundles) 
        return all_projects_entities
        
    def get_versions(self,
                     text_mode: str =True) -> list:
        """
        Get all the versions. a padding operation also
        proccessed for numertic versions 

        Args:
            text_mode (str, optional):  Return numeric whole numbers for 
                                        true else return textual mode (v001)
                                        . Defaults to True.

        Returns:
            list: Sorted versions list
        """
        
        version_nos = set()
        versions = set()
        for info_file_path in self.info_file_paths:
            self.set_file_path(info_file_path)
            version_file_config = self.read_file_datas(INFO_FILE)
            version_nos.add(version_file_config['version'])
        
        for version_no in version_nos:
            VersionOperations.__init__(self, version_no)
            versions.add(self.pad_version_identifier_to_number())
        
        if text_mode:
            return sorted(versions, reverse=True)
        else:
            return sorted(version_nos, reverse=True)
    
    def get_infos(self, 
                version: str) -> tuple:
        """
        Retrive info, comments and bundle type of the bundles for 
        versions from the info.json file

        Args:
            version (str): version label Example:v001

        Returns:
            tuple:  comments, 
                    bundle_type 'whole scene' or 'Module', 
                    extra infos of the bundles, 
                    current module_path 
        """
        
        info_file_path = [info_file_path 
                          for info_file_path in self.info_file_paths 
                          if version in info_file_path
                         ]

        self.set_file_path(info_file_path[0])
        read_file_data = self.read_file_datas(INFO_FILE)
        comments = read_file_data['comments']
        bundle_type = read_file_data['type']
        module_path = read_file_data['module_path']
        del(read_file_data['comments'])
        del(read_file_data['type'])
        del(read_file_data['module_path'])
        infos = read_file_data
        return comments, bundle_type, infos, module_path

    def all_project_bundle(self) -> dict:
        """
        Returns Dict of project name as key and bundle name as value

        Returns:
            dict: project name as key and bundle name as value
        """
        
        template_config_files = []
        for root,directories,config_file in os.walk(ROOT_TEMPLATE_PATH):
            if config_file:
                if config_file[0] == CONFIG_FILE:
                    self.set_file_path(root)
                    template_config_file = self.read_file_datas(CONFIG_FILE)
                    template_config_files.append(template_config_file)
        all_project_bundle ={}
        filtered_bundles = []
        for template_config_file in template_config_files:
            filtered_bundles.append({template_config_file['project']: template_config_file['name']})
        for filtered_bundle in filtered_bundles:
            for project,_ in filtered_bundle.items():
                all_project_bundle[project] = []
        for filtered_bundle in filtered_bundles:
            for project,bundle in filtered_bundle.items():
                all_project_bundle[project].append(bundle)
        return all_project_bundle
    
    def remove_bundle(self,
                      bundle_metadata: dict) -> bool:
        """
        Remove the specific version bundle from the file system.
        if only one version of the bundle found then remove entire 
        bundle name structure from the root. For more than one versions
        remove only those versions for selected bundle.

        Args:
            bundle_metadata (dict): each version label holds a dict as 
                                    metadata. version label as dispaly role 
                                    metadata as user role. bundle_metadata is 
                                    the userrole dict sent from a version. 

        Returns:
            bool:   Remove entire config and bundle if false else remove
                    only the specific version of the bundle
        """
        
        
        VersionOperations.__init__(self, 
                                   bundle_metadata['version'])
        version_no = int(self.trim_version_identifier_from_number())
        
        self.get_version_info_paths(bundle_metadata['bundle_name'],
                                    bundle_metadata['domain'],
                                    bundle_metadata['context'], 
                                    project=bundle_metadata['project_name'])
        
        if len(self.get_versions()) > 1:
            shutil.rmtree(
                os.path.dirname(bundle_metadata['module_path'])
            )
            return False
        else:
            shutil.rmtree(
                bundle_metadata['config_path']
            )
            return True
            

class BundleOpearations(FileOperations,
                        VersionOperations):
    
    """
    Generate config.json and info.json. simply this method
    Create folders for bundles and take care bundle related file and 
    folder creation operations 
    """
    def __init__(self, 
                 bundle_folder_path: str,
                 version: str
                 ) -> None:

        """Initialize of version and file operations.
        For a bundle folder path initialize the bundle folder
        path and version label

        Args:
            bundle_folder_path (str): Bundle folder path
            version (str): Numeric version number
        """
        
        VersionOperations.__init__(self, version)
        FileOperations.__init__(self)
        
        self.bundle_folder_path = bundle_folder_path
        self.version = version
        self.folder_path = os.path.join(
                    self.bundle_folder_path,
                    self.pad_version_identifier_to_number()
        )
        self.config_file_path = os.path.join(self.folder_path,
                                        CONFIG_FILE)
        self.info_file_path = os.path.join(self.folder_path,
                                      INFO_FILE)
        
    @staticmethod
    def create_directory(dir_path: str) -> None:

        """Create Directory for the given path

        Args:
            dir_path (str): Path to the folder
        """
        
        try:
            os.makedirs(dir_path)
        except Exception:
            pass
    
    def make_config_file_path_directory(self) -> str:
        
        """
        Generate config file path folders

        Returns:
            str: Path of the config file 
        """
        if not os.path.exists(self.bundle_folder_path):
            
             self.create_directory(self.bundle_folder_path)
             return self.bundle_folder_path
             
    
    def make_info_file_path_directory(self) -> str:

        """
        Generate info file path folders

        Returns:
            str: Path of the info file 
        """
        
        if os.path.exists(self.bundle_folder_path):
                
            self.create_directory(self.folder_path)
            return self.folder_path
        
    def generate_info_file(self,
                           datas: dict,
                           file_type: str='') -> None:
        """
        Write datas into info.json and config.json

        Args:
            datas (dict): dict entitiy contains for config and info datas
            file_type (str, optional): passed config.json or info.json. Defaults to ''.
        """
        
        if file_type == INFO_FILE:
            self.set_file_path(self.folder_path)
            json_object = json.dumps(datas, indent=4)
            self.write_file_datas(INFO_FILE, json_object)
        if file_type == CONFIG_FILE:
            self.set_file_path(self.bundle_folder_path)
            json_object = json.dumps(datas, indent=4)
            self.write_file_datas(CONFIG_FILE, json_object)

        
        
class ThadamDB:
    
    """
    Connects to thadam db to retrive the current running 
    status of the projects
    """
    def __init__(self) -> None:
        
        """
        Thadam server API initialization
        """
        
        self.thadam_api_server = thadam_api.ThadamParser()
    
    def get_projects(self) -> list:

        """Retrive list of projects in WIP status from thadam.

        Returns:
            list: List of Project entries 
        """
        
        projects = set()
        get_projects = self.thadam_api_server.get_projects()
        for proj_code in get_projects:
            projects.add(proj_code['proj_code'])
        return sorted(projects)


if __name__ == '__main__':
    
    templates = Templates()

    print(templates.get_all_bundles(return_with_project_name=True))
    print(templates.get_all_bundles())
    print(templates.get_all_bundles(all_mode=True, matching_text='bk'))
    print(templates.get_all_bundles(project_name='aln', all_mode=False))
    print(templates.get_all_bundles(project_name='aln', all_mode=False, matching_text='t'))
    templates.get_version_info_paths('ground', 'Magical', "Obj", project='aln')
    templates.get_version_info_paths('tank', 'Magical', "Obj")
    print(templates.get_versions())
    print(templates.get_versions(text_mode=False))
    
    print(templates.get_infos('v001'))
    print(templates.all_project_bundle())
    
    meta_data1 = {'bundle_name': 'obj_test',
                 'bundle_type': 'Module',
                 'comments': 'grid \n\n\nsecond \n\ntest',
                 'config_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\obj_test',
                 'context': 'Obj',
                 'created_on': '01-12-2023 22:12',
                 'domain': 'Magical',
                 'file_size': '0.03Mb',
                 'module_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\obj_test\\v002\\obj_test.uti',
                 'node_count': 1, 
                 'project_name': 'aln',
                 'user_name': 'chandrakanth',
                 'version': 'v002'
                }
    print(templates.remove_bundle(meta_data1))
    
    meta_data2 = {'bundle_name': 'aln_sop_test',
                  'bundle_type': 'Module',
                  'comments': 'Obj Showing',
                  'config_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\aln_sop_test',
                  'context': 'Obj',
                  'created_on': '02-12-2023 00:00',
                  'domain': 'Magical',
                  'file_size': '0.03Mb',
                  'module_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\aln_sop_test\\v001\\aln_sop_test.uti',
                  'node_count': 1,
                  'project_name': 'aln',
                  'user_name': 'chandrakanth',
                  'version': 'v001'
                  }
    print(templates.remove_bundle(meta_data2))
    
    thadam_db = ThadamDB()
    print(thadam_db.get_projects())
    
    bundle_operations = BundleOpearations(r"\\cache\3D_CACHE\templates\bundles\Magical\Obj\aln\ground", 3)
    print(bundle_operations.make_info_file_path_directory())
    data ={'user_name': 'chandrakanth',
            'context': 'Obj',
            'version': 3,
            'node_count': 1,
            'type': 'Module',
            'module_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\ground\\v003\\ground.uti',
            'file_size': '',
            'comments': 'test'
            }
    print(bundle_operations.generate_info_file(data, file_type=INFO_FILE))
    
    bundle_operations = BundleOpearations(r"\\cache\3D_CACHE\templates\bundles\Magical\Obj\aln\ground1", 1)
    print(bundle_operations.make_config_file_path_directory())
    data ={
        "name": "ground1",
        "project": "aln",
        "domain": "Magical",
        "context": "Obj",
        "bundle_type": "module",
        "config_path": "\\\\cache\\3D_CACHE\\templates\\bundles\\magical\\Obj\\aln\\ground1"
    }
    bundle_operations.generate_info_file(data, file_type=CONFIG_FILE)
    print(bundle_operations.make_info_file_path_directory())
    data ={'user_name': 'chandrakanth',
            'context': 'Obj',
            'version': 3,
            'node_count': 1,
            'type': 'Module',
            'module_path': '\\\\cache\\3D_CACHE\\templates\\bundles\\Magical\\Obj\\aln\\ground1\\v001\\ground.uti',
            'file_size': '',
            'comments': 'test'
    }
    bundle_operations.generate_info_file(data, file_type=INFO_FILE)

    
        