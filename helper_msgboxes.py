# QT Message box helper module 
#
#

import enum
from PySide2.QtWidgets import QMessageBox, QWidget, QMainWindow


class msgTypes(enum.Enum):
    
    """Initialize enum 
    """
    warning = 'warning'
    info = 'info'


class utilMessageBox(QMainWindow):
    
    """
    Base Class for qt message box utility. 
    """

    def __init__(self,
                 message_box_type: str, 
                 message: str) -> None:
        """
        Initialize message box type and message text keywords

        Args:
            message_box_type (str): type of the message box to show warning or infos
            message (str): message text to show
        """

        super().__init__()
        self.message_box_type = message_box_type
        self.message = message
    
    def show_message(self) -> None:
        
        """
        Switcher method to switch between the type 
        of message box to show.
        """
        if self.message_box_type == msgTypes.warning.name:
            self.warning_messagebox()
        elif self.message_box_type == msgTypes.info.name:
            self.info_messagebox()
    
    def warning_messagebox(self) -> None:
        
        """Warning message box"""
        QMessageBox.warning(self,
                            'Warning',
                            self.message)
        
    def info_messagebox(self) -> None:
        
        """ Info message box """
        QMessageBox.information(self,
                            'Information',
                            self.message)

if __name__ == "__main__":
    
    import sys
    from PySide2.QtWidgets import QApplication
    app = QApplication(sys.argv)
    util_messagebox = utilMessageBox('warning', "warning")
    util_messagebox.show_message()
    util_messagebox = utilMessageBox('info', "TEst")
    util_messagebox.show_message()
    app.exec_()