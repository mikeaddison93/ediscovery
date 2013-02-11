import wx
import os
from wx.lib.masked import NumCtrl
from file_utils import find_files_in_folder, copy_files_with_dir_tree
from sampler.random_sampler import random_sampler, SUPPORTED_CONFIDENCES
from file_list_control import file_list_control
from ed import output_folder

file_dict = {}
class RandomSamplerGUI(wx.Frame):
    
    def __init__(self, parent):
        
        wx.Frame.__init__(self, parent)
        
        self.dir_path = os.getcwd()
        self.output_dir_path = os.getcwd()
        self.confidence_val = 0.75
        self.precision_val = 0.01
        self.SEED = 2013 

        # Setting up the menu.
        
        self._create_menu_bar()


        # Sets the banner text 
        
        banner_text = """Random sampler for E-Discovery: 
        This application randomly (selects) samples the files given in the input directory 
        and copies to the output directory. The sample size is calculated by the given 
        confidence interval."""
        self.banner = wx.StaticText(self, id=wx.ID_ABOUT, label=banner_text, style=wx.TE_AUTO_SCROLL)
        
        # A Status bar in the bottom of the window
        
        self.CreateStatusBar() 
        
        # Layout sizers

        self._create_layout()
        
        # Handles the basic window events 
        
        self.Bind(wx.EVT_CLOSE, self._on_exit)

        # Sets the main window properties 
        
        self.SetSize((500, 300))
        self.SetTitle("Random Sampler")
        self.Centre()
        self.Show(True)


    def _create_layout(self):
        '''Creates the main window layout
        '''
        
        # Input folder section
        self.input_folder_label = wx.StaticText(self, label="Input directory")
        self.input_folder = wx.TextCtrl(self, style=wx.TE_BESTWRAP, size=(400, -1))
        self.input_folder.SetEditable(False)
        self.input_folder.SetValue(self.dir_path)
        self.input_folder_button = wx.Button(self, wx.ID_OPEN, "Select")
        self.Bind(wx.EVT_BUTTON, self._on_select_input_folder, self.input_folder_button)
        self.line = wx.StaticLine(self)
        
        # Setting output folder section
        self.output_folder_label = wx.StaticText(self, label="Output directory")
        self.output_folder = wx.TextCtrl(self, style=wx.TE_BESTWRAP, size=(400, -1))
        self.output_folder.SetEditable(False)
        self.output_folder.SetValue(self.output_dir_path)
        self.output_folder_button = wx.Button(self, wx.ID_ANY, "Select")
        self.Bind(wx.EVT_BUTTON, self._on_select_output_folder, self.output_folder_button)
        
        # Setting run and exit buttons
        self.button_exit = wx.Button(self, wx.ID_EXIT, "Exit")
        self.button_run = wx.Button(self, wx.ID_ANY, "Run Sampler")        
        self.Bind(wx.EVT_BUTTON, self._on_exit, self.button_exit)
        self.Bind(wx.EVT_BUTTON, self._on_run_sampler, self.button_run)
        
        # Setting parameters
        self.confidence_text = wx.StaticText(self, label="Confidence (%)")
        self.precision_text = wx.StaticText(self, label="Precision (%)")
        
        z_values = ['%.3f' % (w * 100.0) for w in  SUPPORTED_CONFIDENCES.keys()]
        z_values.sort()
        self.confidence = wx.ComboBox(self, -1, z_values[0], size=(150, -1), choices=z_values, style=wx.CB_READONLY) 
        self.precision = wx.lib.masked.NumCtrl(self, size=(20,1), fractionWidth=0, integerWidth=2, allowNegative=False, min=1, max=99, value=1) 

        # Layouts 
        
        sizer_input_folder = wx.BoxSizer(wx.HORIZONTAL)
        sizer_input_folder.Add(self.input_folder_label, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, border=5, )
        sizer_input_folder.Add(self.input_folder, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_input_folder.Add(self.input_folder_button, 0, wx.EXPAND | wx.ALL, border=5)
        
        
        sizer_output_folder = wx.BoxSizer(wx.HORIZONTAL)
        sizer_output_folder.Add(self.output_folder_label, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, border=5)
        sizer_output_folder.Add(self.output_folder, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_output_folder.Add(self.output_folder_button, 0, wx.EXPAND | wx.ALL, border=5)
        
        
        sizer_cp = wx.BoxSizer(wx.HORIZONTAL)
        sizer_cp.Add(self.confidence_text, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_cp.Add(self.confidence, 0, wx.ALL, border=5)
        sizer_cp.Add(self.precision_text, 1, wx.ALL, border=5)
        sizer_cp.Add(self.precision, 0, wx.ALL, border=5)
        
        
        sizer_cb = wx.BoxSizer(wx.HORIZONTAL)
        sizer_cb.Add(self.button_exit, 0, wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer_cb.Add(self.button_run, 0, wx.ALIGN_CENTER | wx.ALL, border=5)
        
        sizer_process_files = wx.BoxSizer(wx.VERTICAL)
        self.process_files_tree = file_list_control(None, -1, "",output_folder)
#        self.process_files_tree = wx.TreeCtrl(self, 1, wx.DefaultPosition, (-1,-1), wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)
#        self.process_files_tree.AddRoot("")
        sizer_process_files.Add(self.process_files_tree, 0,
                                wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, border=5)

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(self.banner, 0, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(sizer_input_folder, 0, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(sizer_output_folder, 0, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(self.line, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(sizer_cp, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(self.line, 1, wx.EXPAND | wx.ALL, border=5)
        sizer_main.Add(sizer_cb, 1, wx.ALIGN_CENTER | wx.ALL, border=5)
        sizer_main.Add(sizer_process_files, 1, wx.ALIGN_CENTER | wx.ALL, border=5)
        
        self.SetSizerAndFit(sizer_main)


    def _create_menu_bar(self):
        
        # Setting up the menu.
        menu_file = wx.Menu()
        mitem_about = menu_file.Append(wx.ID_ABOUT, "&About", " Information about this program")
        mitem_exit = menu_file.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        # Creating the menubar.
        menu_bar = wx.MenuBar()
        menu_bar.Append(menu_file,"&File") # Adding the "menu_file" to the MenuBar

        # Set events.
        self.Bind(wx.EVT_MENU, self._on_about, mitem_about)
        self.Bind(wx.EVT_MENU, self._on_exit, mitem_exit)    

        self.SetMenuBar(menu_bar)  # Adding the MenuBar to the Frame content.

        
    # Event handlers
  

    def _on_about(self, e):
        '''Create a message dialog box
        
        '''
        
        about_text = """Random sampler: 
        This application randomly (selects) samples the files 
        given in the input directory and copies to the output 
        directory. The sample size is calculated by the given 
        confidence interval."""
        dlg = wx.MessageDialog(self, about_text, "About Random Sampler", wx.OK)
        dlg.ShowModal() # Shows it
        dlg.Destroy() # finally destroy it when finished.

    def _on_exit(self,e):
        '''Handles the application exits EVENT 
        
        '''
        
        dlg = wx.MessageDialog(self, "Do you really want to close this application?", "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()

    def _on_select_input_folder(self, e):
        """Open a folder for input
        
        """

        dlg = wx.DirDialog(self, "Choose the input folder to sample",self.dir_path,wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.dir_path = dlg.GetPath()
        dlg.Destroy()
        self.input_folder.SetValue(self.dir_path)
        self.SetStatusText("The selected input folder is %s" % self.dir_path)
        
    def _on_select_output_folder(self, e):
        """ Open a folder for output 
        
        """
        dlg = wx.DirDialog(self,"Choose the Output folder to save",self.output_dir_path,wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.output_dir_path = dlg.GetPath()
        dlg.Destroy()
        self.output_folder.SetValue(self.output_dir_path)
        self.SetStatusText("The selected output folder is %s" % self.output_dir_path)
        
    def _on_run_sampler(self, e):
        '''Handles the run sampler button click event 
        
        '''
        try:
            
            self.confidence_val = float(self.confidence.GetValue()) / 100.0
            self.precision_val = float(self.precision.GetValue()) / 100.0 
            
            if not os.path.exists(self.dir_path) or not os.path.exists(self.output_dir_path):
                dlg = wx.MessageDialog(self, "Please enter a valid input/output directory", "Error", wx.ICON_ERROR)
                dlg.ShowModal()
                return 
            
            file_list = find_files_in_folder(self.dir_path)
            self.SetStatusText('%d files found in %s.' % (len(file_list), self.dir_path) )
            
            sampled_files = random_sampler(file_list, self.confidence_val, self.precision_val, self.SEED)
            self.SetStatusText('%d files are sampled out of %d files.' % (len(sampled_files), len(file_list)))
            
            copy_files_with_dir_tree(sampled_files, self.output_dir_path)
            self.SetStatusText('%d randomly sampled files (from %d files) are copied to the output folder.' % (len(sampled_files), len(file_list)))
            
        except Exception as anyException:
            dlg = wx.MessageDialog(self, str(anyException), "Error", wx.ICON_ERROR)
            dlg.ShowModal()
        
        return      

def main():
    
    app = wx.App(False)
    RandomSamplerGUI(None)
    app.MainLoop()  


if __name__ == '__main__':    
    main()
    
    

