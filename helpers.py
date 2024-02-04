#
# Various helper function provided for template pilot
# 
import os
import sys
import re
import yaml

ROOT_DEFAULT_PATH = os.path.join(
        os.environ['HOUDINI_INTERNAL_PACKAGE_DIR'], 
        "hooks\\template_manager\\config\\defaults"
)
ROOT_TEMPLATE_PATH = r"R:\templates\bundles"
CONFIG_FILE = 'config.json'
INFO_FILE = 'info.json'
MODULE_SAVE_FORMAT = '.uti'
HIP_EXTENSION = '.hip'

class FileOperations:
    
    """
    Base Class for read and write files.
    """

    def __init__(self) -> None:
    
        self.dir_path = ''
    
    def set_file_path(self,
                     dir_path: str) -> None:
        """set file path object 

        Args:
            dir_path (str): file path 
        """
        self.dir_path = dir_path
        
    def read_file_datas(self, 
                        file_name: str) -> list:
        """
        Open the file and read the data.

        Args:
            file_name (str): Name of the file 

        Returns:
            list: list items readed from the file 
        """
        
        self.read_file = os.path.join(
            self.dir_path, file_name
        )
        
        with open(self.read_file, 'r') as read_file:
            datas = yaml.safe_load(read_file)
        return datas

    def write_file_datas(self, 
                         file_name: str, 
                         datas: dict) -> None:
        """Write the data to the file

        Args:
            file_name (str): name of the file 
            datas (dict): dict object 
        """
        self.write_file = os.path.join(
            self.dir_path, file_name
        )
        with open(self.write_file, 'w') as write_file:
            write_file.write(datas)
        


class VersionOperations:
    
    """
    Base class to do version related operations. 
    pad or remove zeros from the version number 
    """
    def __init__(self, 
                text: str) -> None:
        """Intialize the version operation parms

        Args:
            text (str): version number 
        """
        
        self.text = str(text)
        self.version_identifier =  'v'
    
    def pad_version_identifier_to_number(self) -> str:

        """three pad the zeros to the version number 
        and prefix the 'v' letter

        Returns:
            str: version number string 'v001'
        """
        return f'{self.version_identifier}{self.text.zfill(3)}'
    
    def trim_version_identifier_from_number(self) -> str:

        """Purge out the version number from version string

        Returns:
            str: version number 'v003' -> 3
        """
        
        return re.findall('\d+', self.text)[0]
    

class Defaults(FileOperations):
    
    """
    Read the constants for the given file
    """
    def __init__(self) -> None:
        
        """Intialize the ROOT path dir"""
        super().__init__()
        self.set_file_path(ROOT_DEFAULT_PATH)
    
    def get_defaults(self, file_name) -> str:
        
        """Read the file datas.

        Returns:
            str : file datas
        """
        return self.read_file_datas(file_name)
        
    def get_defaults_context(self) -> list:
        
        """Read conetext.yml and get data

        Returns:
            list: list of context items 
        """
        return self.get_defaults("context.yml")['list']

    def get_default_domain(self)  -> list:
        
        """Read domain.yml and get data

        Returns:
            list: list of domain items 
        """

        return self.get_defaults("domain.yml")['list']

    def get_default_bundles_types(self) -> list:
        
        """Read bundle_type.yml and get data

        Returns:
            list: list of bundle_type items 
        """

        return self.get_defaults("bundle_type.yml")['list']


class InfoFormat:

    """
    For each published bundle name info.json file created
    Holds all the necessary information to show to the user. 
    It makes up the dictionary to save in the info.json file.
    """
    def __init__(self,
                 user_name,
                 context,
                 version,
                 node_count,
                 bundle_type,
                 module_path,
                 file_size,
                 date_now,
                 comments) -> None:

        self.user_name = user_name
        self.context = context
        self.version = version
        self.node_count = node_count
        self.bundle_type = bundle_type
        self.module_path = module_path
        self.file_size = file_size
        self.date_now = date_now
        self.comments = comments
        
    def data(self):
        
        return {
                "user_name": f"{self.user_name}",
                "context": f"{self.context}",
                "version": int(f"{self.version}"),
                "node_count": int(f"{self.node_count}"),
                "type": f"{self.bundle_type}",
                "module_path": f"{self.module_path}",
                "file_size": f"{self.file_size}",
                "Created On": f"{self.date_now}",
                "comments": f"{self.comments}",
                }

class ConfigFormat:
    
    """For each version of the bundle a config formate 
    stored in the config.json. helps to retrive back while
    importing. The importer first search for this path to 
    locate the bundle.  
    """
    def __init__(self,
                 bundle_name,
                 project,
                 domain,
                 context,
                 bundle_type,
                 config_path):
        
        self.bundle_name = bundle_name
        self.project = project
        self.domain = domain
        self.context = context
        self.bundle_type = bundle_type
        self.config_path = config_path
    
    def data(self):
        
        return {
            "name": f"{self.bundle_name}",
            "project": f"{self.project}",
            "domain": f"{self.domain}",
            "context": f"{self.context}",
            "bundle_type": f"{self.bundle_type}",
            "config_path": f"{self.config_path}"
        }

if __name__ == '__main__':
    
    
    defaults = Defaults()
    print(defaults.get_default_domain())
    
    versionops = VersionOperations(1)
    print(versionops.pad_version_identifier_to_number())
    
    versionops = VersionOperations('v001')
    print(versionops.trim_version_identifier_from_number())