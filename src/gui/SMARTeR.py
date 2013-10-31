'''
Created on Feb 23, 2013

@author: cgeorge
'''
import sys 
import wx 
import shelve
import os 
import mimetypes


from lucene import BooleanClause
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin, \
    ColumnSorterMixin
from gui.SMARTeRGUI import SMARTeRGUI, RatingControl, PreferencesDialog, NewProject
from lucenesearch.lucene_index_dir import search_lucene_index, MetadataType, get_indexed_file_details
import re
import webbrowser
from const import NUMBER_OF_COLUMNS_IN_UI_FOR_EMAILS, \
    CHAR_LIMIT_IN_RESULTS_TAB_CELLS, SHELVE_CHUNK_SIZE, SHELVE_FILE_EXTENSION, \
    COLUMN_NUMBER_OF_RATING
from collections import OrderedDict
from utils.utils_file import read_config, load_file_paths_index, nexists
from tm.process_query import load_lda_variables, load_dictionary, \
    search_lda_model, load_lsi_variables, get_lda_query_td, \
    compute_topic_similarities
from const import SEARCH_RESULTS_LIMIT
from index_data import index_data
from decimal import Decimal
from sampler.random_sampler import random_sampler, SUPPORTED_CONFIDENCES, DEFAULT_CONFIDENCE_INTERVAL, DEFAULT_CONFIDENCE_LEVEL
from gui.TaggingControlGUI import TaggingControlGUI
from gui.TaggingControlSmarter import TaggingControlSmarter
from gui.TaggingControlFeedback import TaggingControlFeedback
from matplotlib.backend_bases import Event


###########################################################################
# # This global dictionary is used to keep track of the query-results 
dictionary_of_rows = OrderedDict()

# Global variables to keep track of the chunk of results displayed
present_chunk = 0

# Constants 
SHELVE_DIR_NAME = 'shelf'
USER_RATINGS_CUT_OFF = 5  # TODO: this needs to be learned
CUT_OFF=0.5 

###########################################################################

###########################################################################
# # Class ResultsCheckListCtrl
###########################################################################

class ResultsCheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    def __init__(self, parent_panel, parent_window,rbx_response):
        wx.ListCtrl.__init__(self, parent_panel, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        CheckListCtrlMixin.__init__(self)
        ListCtrlAutoWidthMixin.__init__(self)
        ColumnSorterMixin.__init__(self, NUMBER_OF_COLUMNS_IN_UI_FOR_EMAILS)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_list_item_select)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_list_item_deselect)
        self.Bind(wx.EVT_LEFT_DCLICK, self._on_row_double_click)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_row_right_click)
        self._shelve_dir = ''
        self._parent_window = parent_window  
        self._rbx_res=rbx_response
        
    def _set_table_headers(self):
        
        self.ClearAll()
        #Remove this after Testing
        columnHeaders = ['File Name','File Path','File Score','Responsive']# MetadataType._types
        columnNumber = 0
        #for c in columnHeaders:
        self.InsertColumn(columnNumber, columnHeaders[0])
        columnNumber = columnNumber + 1
        self.InsertColumn(columnNumber, "File Path")
        self.InsertColumn(columnNumber + 1, "File Score")
        self.InsertColumn(columnNumber + 2, "Rating")        
        
    
    def _set_shelve_dir(self, _dir_path):
        self._shelve_dir = _dir_path
    
    def _populate_results(self, chunk_number, doc_list):
        """ Given the 'chunk_number' 
            1. Reads from that particular shelved-file
            2. Updates the dictionary_of_rows with this chunk of results
            3. Sorts the dictionary_of_rows based on rating
            4. Change all keys in the dictionary to correspond to row_numbers in the UI
            5. Change all keys in the shelved-file to correspond to row_numbers in the UI
            6. Displays the content in the RESULT tab of the UI            
        """
        # The below section of commented lines were used when search results were 
        # being fetched from the global dictionary.  
        # They are now commented because search results are now loaded from shelved-files
        # for paging the results
        '''
        global dictionary_of_rows
        self.DeleteAllItems()
        self.Refresh()
        items = dictionary_of_rows.items() 
        for key, row in items:
        '''
        # Populate the column names using the metadata types from MetadataType_types &RB
        self._set_table_headers()
        
        i=chunk_number*5
        end=0
        if (chunk_number+1)*5>len(doc_list):
            end=len(doc_list)
        else:
            end=(chunk_number+1)*5
        
        while i<end:
            index = self.InsertStringItem(sys.maxint, doc_list[i][0])
            self.SetItemData(index, i)
            cell = str(doc_list[i][0])
            self.SetStringItem(index, 0, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
            cell = str(doc_list[i][1])
            self.SetStringItem(index, 1, cell)
            cell = str(doc_list[i][2])
            self.SetStringItem(index, 2, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
            cell = str("")
            self.SetStringItem(index, 3, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
            i= i+1
        
        # 1. Reads from that particular shelved-file
        '''
        shelve_file = shelve.open(os.path.join(self._shelve_dir, str(chunk_number) + SHELVE_FILE_EXTENSION))
        self.DeleteAllItems()
        global dictionary_of_rows
        dictionary_of_rows = OrderedDict()
        
        # print "Re-initialized dictionary = ", dictionary_of_rows
        for key in shelve_file.keys():
            row = shelve_file[key]
            # 2. Updates the dictionary_of_rows with this chunk of results
            dictionary_of_rows.__setitem__(key, row) 
        # print "Populated Dictionary from file: \n", dictionary_of_rows.keys()
        # print "Rows size = ", len( dictionary_of_rows.values()[0] )
        # 3. Sorts the dictionary_of_rows based on rating
        dictionary_sorted_as_list = sorted(dictionary_of_rows.items(), key=lambda (k, v): v[COLUMN_NUMBER_OF_RATING], reverse=True)
        keys = map(lambda (k, v): k, dictionary_sorted_as_list)
        values = map(lambda (k, v): v, dictionary_sorted_as_list)
        dictionary_of_rows = OrderedDict(zip(keys, values))

        # print "Sorted Dictionary: \n", dictionary_of_rows.keys()
        # print "Rows size = ", len( dictionary_of_rows.values()[3] )
        
        # 4. Change all keys in the dictionary to correspond to row_numbers in the UI
        k_in_String = dictionary_of_rows.keys()
        k_in_ints = map(int, k_in_String)
        k = sorted(k_in_ints)
        v = dictionary_of_rows.values()
        dictionary_of_rows = OrderedDict(zip(map(str, k), v))
           
        # 5. Change all keys in the shelved-file to correspond to row_numbers in the UI
        for key, row in dictionary_of_rows.items():
            shelve_file[key] = row
        shelve_file.close()
        
        
        # 6. Displays the content in the RESULT tab of the UI
        items = dictionary_of_rows.items()
        
        if responsive=="true":
            low=CUT_OFF
            high=1.1
        else:
            low=0
            high=CUT_OFF
         
        for key, row in items:
            #print row[10]
            #exit()
            if float(row[10])>=low and float(row[10])<high:
                index = self.InsertStringItem(sys.maxint, row[0])
                self.SetItemData(index, long(key))
                cell = str(row[0])
                self.SetStringItem(index, 0, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
                cell = str(row[1])
                self.SetStringItem(index, 1, cell)
                cell = str(row[10])
                self.SetStringItem(index, 2, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
                cell = str("")
                self.SetStringItem(index, 3, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
            i = 0
            for cell in row:
                j = 0
                if(i==0 | i==8 | i==9):
                    column_name = self.GetColumn(j).GetText()  
                    cell = str(cell)        
                    # Only the file_path is displayed completely.
                    # The content of all other cells are restricted to 30 characters.                 
                    if(column_name <> 'file_path') and len(cell) > CHAR_LIMIT_IN_RESULTS_TAB_CELLS:
                        self.SetStringItem(index, j, cell[:CHAR_LIMIT_IN_RESULTS_TAB_CELLS])
                    else:
                        self.SetStringItem(index, j, cell)
                    j+=1
                i+=1
               ''' 
        # self.Refresh()
    
    def _on_row_right_click(self, event):
        """Right-Clicking on a row to specify the search-relevancy of the file"""
        #Rating(None, self, self._shelve_dir)
         
    def _on_row_double_click(self, event):
        focussed_item_index = self.GetFocusedItem()
        file_Name = self.GetItem(focussed_item_index, 1)
        webbrowser.get().open(file_Name.GetText())
    
    def _on_list_item_select(self, event) :
        '''
        Handles the result list row select event 
        '''
        
        focussed_item_index = self.GetFocusedItem()
        print self.GetItemText(focussed_item_index,3)
        
        responsive=self.GetItemText(focussed_item_index,3)
        if responsive == 'Yes':
            self._rbx_res.SetSelection(0)
        elif responsive == 'No':
            self._rbx_res.SetSelection(1)
        else:
            self._rbx_res.SetSelection(2)
            
        
        file_name = self.GetItem(focussed_item_index, 1).GetText()
        _, file_ext = os.path.splitext(file_name)
        msg_text = 'Cannot open "%s" in this viewer! Please double click the row to open the file in a default system file viewer.' % file_name
        try: 
            if file_ext == '.txt' or file_ext == '': 
                import unicodedata
                with open(file_name) as fp:
                    msg_text = fp.read()
                    msg_text = unicodedata.normalize('NFKD', msg_text).encode('ascii', 'ignore')  # converts to ascii 

            else:
                file_type, _ = mimetypes.guess_type(file_name, strict=True)
                msg_text = 'Cannot open "%s (type:%s)" in this viewer! Please double click the row to open the file in a default system file viewer.' % (file_name, file_type)
        except:
            pass             
            
        self._parent_window._tc_file_preview_pane.SetValue(msg_text)
    
    def _on_list_item_deselect(self, event) :
        self._parent_window._tc_file_preview_pane.SetValue('')
    
    def GetListCtrl(self):
        return self
    
    def _on_header_column_click(self, event):
        """
        This method is used to sort the rows in the RESULTS ResultsCheckListCtrl
        """
        self._populate_results(present_chunk)
        


###########################################################################
# # Class Rating
###########################################################################

class Rating (RatingControl):
    selected_record_index = None
    checklist_control = None
    
    def __init__(self, parent, checklist_control, _shelve_dir):
        """ Calls the parent class's method """ 
        super(Rating, self).__init__(parent) 
        self.Center()
        self.Show(True)
        self.checklist_control = checklist_control
        self.selected_record_index = checklist_control.GetFocusedItem()
        
        # If the Relevance-recording window is opened again, it must show the score already given  
        relevance_score = checklist_control.GetItem(self.selected_record_index, COLUMN_NUMBER_OF_RATING)
        # self.radio_control.SetSelection( int(relevance_score.GetText()) )
        
        self._rating_slider.SetValue(int(relevance_score.GetText()))
        self._shelve_dir = _shelve_dir
    

    def _on_btn_click_submit(self, event):
        """
        1. Updates the Relevance column with the given rating
        2. Stores this new rating in the dictionary
        3. Stores this new rating in the shelved-file
        """

        # 1. Updates the Relevance column with the given rating
        # rating = self.radio_control.GetSelection()
        rating = self._rating_slider.GetValue()
        self.checklist_control.SetStringItem(self.selected_record_index, COLUMN_NUMBER_OF_RATING, str(rating))
        
        # Statements to just debug
        # print "Old rating = ", dictionary_of_rows[self.selected_record_index][-1]
        # print "New rating = ", rating
        
        selected_row_in_dict = present_chunk * SHELVE_CHUNK_SIZE + self.selected_record_index
        # 2. Stores this new rating in the dictionary
        dictionary_of_rows[str(selected_row_in_dict)][-1] = str(rating)

        shelve_file = shelve.open(os.path.join(self._shelve_dir, str(present_chunk) + SHELVE_FILE_EXTENSION))
        row = shelve_file[str(selected_row_in_dict)]
        # print "Before SUBMIT : ", shelve_file[str(selected_row_in_dict)]
        row[-1] = str(rating)
        shelve_file[str(selected_row_in_dict)] = row
        # print "changed : ", shelve_file[str(selected_row_in_dict)] 
        shelve_file.close()
        
        self.checklist_control.itemDataMap = dictionary_of_rows
        self.Destroy()
'''        
class CreateProject (NewProject):
    def __init__(self, parent):
        """ Calls the parent class's method """ 
        super(NewProject, self).__init__(parent)
        self.Center()
        self.Show(True)
'''
        
class NewProject1 ( wx.Dialog ):
    smarter=None
    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = (u"Create New Project"), pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
        
        self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
        
        bSizer5 = wx.BoxSizer( wx.VERTICAL )
        
        sbsizer_project = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY,(u"Project Details") ), wx.VERTICAL )
        
        gbsizer_project = wx.GridBagSizer( 0, 0 )
        gbsizer_project.SetFlexibleDirection( wx.BOTH )
        gbsizer_project.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        self._tc_project_name = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )

        
        gbsizer_project.Add( self._tc_project_name, wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, (u"Input Data Folder"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )
        gbsizer_project.Add( self.m_staticText6, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        self._data_dir_picker = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, (u"Select a folder"), wx.DefaultPosition, wx.Size( -1,-1 ), wx.DIRP_DEFAULT_STYLE )
        gbsizer_project.Add( self._data_dir_picker, wx.GBPosition( 1, 1 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        gbsizer_project.Add( self.m_staticline3, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 3 ), wx.EXPAND |wx.ALL, 5 )
        
        self._btn_clear_project_details = wx.Button( self, wx.ID_ANY, (u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        gbsizer_project.Add( self._btn_clear_project_details, wx.GBPosition( 3, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        self._btn_index_data = wx.Button( self, wx.ID_ANY, (u"Create Project"), wx.DefaultPosition, wx.DefaultSize, 0 )
        gbsizer_project.Add( self._btn_index_data, wx.GBPosition( 3, 2 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, (u"Enter New Project Title"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText14.Wrap( -1 )
        gbsizer_project.Add( self.m_staticText14, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )
        
        
        sbsizer_project.Add( gbsizer_project, 1, wx.EXPAND, 5 )
        
        
        bSizer5.Add( sbsizer_project, 0, wx.ALL, 10 )
        
        
        self.SetSizer( bSizer5 )
        self.Layout()
        bSizer5.Fit( self )
        
        self.Centre( wx.BOTH )
        
        # Connect Events
        self._btn_clear_project_details.Bind( wx.EVT_BUTTON, self._on_click_cancel )
        self._btn_index_data.Bind( wx.EVT_BUTTON, self._on_click_index_data )
        self._tc_project_name.Bind( wx.EVT_KILL_FOCUS, self._on_focus_kill_chk_dup )
        
        self.smarter=parent
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def _on_click_cancel( self, event ):
        self.Destroy()
    
    def _on_click_index_data( self, event ):
        
        project_name=self._tc_project_name.GetValue()
        if project_name in self.smarter._cbx_project_title.GetStrings():
            self.smarter._show_error_message("Duplicate Project!", "Project already exists, Enter a unique name")
            self._tc_project_name.SetValue("")
        else:
            data_folder = self._data_dir_picker.GetPath()
            project_name = ""
            #     print project_name, data_folder, output_folder, self._num_topics, self._num_passes, self._min_token_freq, self._min_token_len
            project_name = self._tc_project_name.GetValue()
            index_data(data_folder, self.smarter.directory, project_name, self.smarter._cfg_dir, self.smarter._num_topics, self.smarter._num_passes, self.smarter._min_token_freq, self.smarter._min_token_len, log_to_file=True)
            self.smarter._cbx_project_title.Append(project_name)        
            print 'Indexing is completed.'
            self.Destroy()
            
    def _on_focus_kill_chk_dup( self, event ):
        event.Skip()
        project_name=self._tc_project_name.GetValue()
        if project_name in self.smarter._cbx_project_title.GetStrings():
            self.smarter._show_error_message("Duplicate Project!", "Project already exists, Enter a unique name")
            self._tc_project_name.SetValue("")
            
        

###########################################################################
# # Class Preferences 
###########################################################################

class Preferences (PreferencesDialog):
    
    def __init__(self, parent):
        '''
        Calls the parent class's method 
        '''
        super(Preferences, self).__init__(parent) 
        
        self._parent = parent  # refers to the parent object    
        self._load_existing_indexing_preferences()
        
        self.Center()
        self.Show(True)
        
     
    def _load_existing_indexing_preferences(self):
        '''
        Loads and sets the existing preferences from the 
        the main class -- SMARTeR  

        Arguments: 
            parent - the main class reference 
        '''

        self._tc_num_topics.SetValue(str(self._parent._num_topics))
        self._tc_num_passes.SetValue(str(self._parent._num_passes))
        self._tc_min_token_freq.SetValue(str(self._parent._min_token_freq))
        self._tc_min_token_len.SetValue(str(self._parent._min_token_len))


    def _on_click_reset_defaults_indexing_preferences(self, event):
        '''
        Resets the indexing preferences to the default values 
        
        '''
        
        self._load_existing_indexing_preferences()
        
        
    def _on_click_save_indexing_preferences(self, event):
        '''
        Saves the indexing preferences to the class variables 
        
        TODO: 
            1. Need to save all these variables into the persistent storage 
            2. Need to handle validations such as clicking another tab, negative values, etc. 
        '''
                
        self._parent._num_topics = int(self._tc_num_topics.GetValue().strip())
        self._parent._num_passes = int(self._tc_num_passes.GetValue().strip())
        self._parent._min_token_freq = int(self._tc_min_token_freq.GetValue().strip())
        self._parent._min_token_len = int(self._tc_min_token_len.GetValue().strip()) 
        
        # destroys the pop up 
        self.Destroy()




###########################################################################
# # Class SMARTeR
###########################################################################

class SMARTeR (SMARTeRGUI):

    def __init__(self, parent):

        # Calls the parent class's method 
        super(SMARTeR, self).__init__(parent)
        self.SEED = 2013  
        self._is_lucene_index_available = False 
        self._is_tm_index_available = False
        self._current_page = 0
        
        self._shelve_dir = ''
        self._shelve_file_names = []  # this keeps all of the shelf files path 
        self._responsive_files = []
        self._unresponsive_files = []
        self._responsive_files_display = []
        self._unresponsive_files_display = []
        self._build_query_results_panel()
        self._populate_metadata_fields()
        self._reset_defaults_indexing_preferences()    
        
        self._lda_num_topics = self._num_topics
        self._init_results = []     
        
        self.Center()
        from os.path import expanduser
        home = expanduser("~")
        self.directory=os.path.join(home,"SMARTeR")
        if(os.path.exists(self.directory)==False):
            os.makedirs(self.directory)
            
        #self._panel_review_res= TaggingControlGUI(self._panel_review_res,self)
        #self._panel_review_unres= TaggingControlGUI(self._panel_review_unres,self)
        self._cfg_dir = os.path.join(self.directory,"repository")
        if(os.path.exists(self._cfg_dir)==False):
            os.makedirs(self._cfg_dir)
        for _, _, files in os.walk(self._cfg_dir):
            for file_name in files:
                project, _ = os.path.splitext(file_name)
                self._cbx_project_title.Append(project)
        self._load_cbx_confidence_levels()
        self._init_confidence()
        self.Show(True)
        
    def _reset_defaults_indexing_preferences(self):
        
        self._num_topics = 30
        self._num_passes = 99
        self._min_token_freq = 1 
        self._min_token_len = 2
        
    def _on_menu_sel_preferences(self, event):
        '''
        
        '''
        Preferences(parent=self)
        
    def _populate_metadata_fields(self):
        '''
        This function will populate the metadata combo box 
        dynamically at the time of file loading. This will help
        to accommodate new metadata types as and when they are needed. 
        '''
        meta_data_types = MetadataType._types
        #self._cbx_meta_type.Append(MetadataType.ALL)  # adds the all field to the combo box
        self._cbx_meta_type1.Append(MetadataType.ALL) 
        for l in meta_data_types :
            #self._cbx_meta_type.Append(l)
            self._cbx_meta_type1.Append(l) 
        #self._cbx_meta_type.SetSelection(0)
        self._cbx_meta_type1.SetSelection(0)


    def _build_query_results_panel(self):
        '''
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        _panel_left = wx.Panel(self._panel_query_results, -1)
        _panel_right = wx.Panel(self._panel_query_results, -1)

        self._st_file_preview_header = wx.StaticText(_panel_right, -1, 'File Review Pane (Text Files)')
        self._tc_file_preview_pane = wx.TextCtrl(_panel_right, -1, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 200))
        '''
        self._lc_results_res = ResultsCheckListCtrl(self._panel_res, self, self._rbx_feedack_res)
        self._lc_results_res._set_table_headers()  # Populate the column names using the metadata types from MetadataType_types &RB
        
        self._lc_results_unres = ResultsCheckListCtrl(self._panel_unres, self,self._rbx_feedack_unres)
        self._lc_results_unres._set_table_headers()  # Populate the column names using the metadata types from MetadataType_types &RB
        '''
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self._st_responsive_doc = wx.StaticText(_panel_right, -1, 'Responsive Files')
        self._st_unresponsive_doc = wx.StaticText(_panel_right, -1, 'Unresponsive Files')
        
        vbox_res = wx.BoxSizer(wx.VERTICAL)
        vbox_unres = wx.BoxSizer(wx.VERTICAL)

        self._btn_sel_all = wx.Button(_panel_left, -1, 'Select All', size=(100, -1))
        self._btn_desel_all = wx.Button(_panel_left, -1, 'Deselect All', size=(100, -1))
        self._btn_log_files = wx.Button(_panel_left, -1, 'Log', size=(100, -1))
        self._btn_load_next_chunk = wx.Button(_panel_left, -1, 'Next >', size=(100, -1))
        self._btn_load_previous_chunk = wx.Button(_panel_left, -1, '< Previous', size=(100, -1))
        self._btn_update_results = wx.Button(_panel_left, -1, 'Update Results', size=(100, -1))
        self._btn_continue = wx.Button(_panel_left, -1, 'Continue', size=(100, -1))

        self.Bind(wx.EVT_BUTTON, self._on_click_sel_all, id=self._btn_sel_all.GetId())
        self.Bind(wx.EVT_BUTTON, self._on_click_desel_all, id=self._btn_desel_all.GetId())
        self.Bind(wx.EVT_BUTTON, self._on_click_log_files, id=self._btn_log_files.GetId())
        self.Bind(wx.EVT_BUTTON, self._on_click_next, id=self._btn_load_next_chunk.GetId())
        self.Bind(wx.EVT_BUTTON, self._on_click_previous, id=self._btn_load_previous_chunk.GetId())        
        self.Bind(wx.EVT_BUTTON, self._on_click_update_results, id=self._btn_update_results.GetId())
        self.Bind(wx.EVT_BUTTON, self._on_click_continue, id=self._btn_continue.GetId())  

        vbox2.Add(self._btn_sel_all, 0, wx.TOP, 5)
        vbox2.Add(self._btn_desel_all)
        vbox2.Add(self._btn_log_files)
        vbox2.Add(self._btn_load_next_chunk);
        vbox2.Add(self._btn_load_previous_chunk);
        vbox2.Add(self._btn_update_results);
        vbox2.Add(self._btn_continue);
        
        _panel_left.SetSizer(vbox2)
        vbox_res.Add(self._st_responsive_doc)
        vbox_res.Add(self._lc_results_res, 1, wx.EXPAND, 5)
        vbox_unres.Add(self._st_unresponsive_doc)
        vbox_unres.Add(self._lc_results_unres, 0, wx.EXPAND, 5)
        hbox2.Add(vbox_res)
        hbox2.Add((50, -1))
        hbox2.Add(vbox_unres)
        #hbox2.Add(self._lc_results_unres, 0.5, wx.EXPAND, 5)
        vbox.Add(hbox2)
        vbox.Add((-1, 10))
        vbox.Add(self._st_file_preview_header, 0.5, wx.EXPAND)
        vbox.Add((-1, 5))
        vbox.Add(self._tc_file_preview_pane, 0.5, wx.EXPAND)
        vbox.Add((-1, 10))
        #vbox.Add(vbox_unres)

        _panel_right.SetSizer(vbox)

        hbox.Add(_panel_left, 0, wx.EXPAND | wx.RIGHT, 5)
        hbox.Add(_panel_right, 1, wx.EXPAND)
        hbox.Add((3, -1))

        self._panel_query_results.SetSizer(hbox)
        '''
    def _on_menu_sel_exit(self, event):

        dlg = wx.MessageDialog(self,
                               "Do you really want to close this application?",
                               "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()        
        
    def _on_notebook_page_changed(self, event):
        '''
        Handles the note book page change event 
        '''
        
        self._current_page = event.Selection
        self._notebook.ChangeSelection(self._current_page)
  
    def _create_persistent_shelves(self, items):
        """
            Stores the query-results into shelves. 
            *** Currently, the shelved files are named chunkNumber.shelve ***
            *** Come up with a logic to name files so that they represent 
                the query string
            ***
        """
        self._shelve_file_names = []
        chunk_number = -1;
        shelve_file = None
        for key, row in items:
            if(int(key) % SHELVE_CHUNK_SIZE == 0):
                chunk_number = chunk_number + 1 
                fileName = str(chunk_number)
                fileName = os.path.join(self._shelve_dir, fileName + SHELVE_FILE_EXTENSION)
                self._shelve_file_names.append(fileName)
                if shelve_file is not None: 
                    shelve_file.close()
                shelve_file = shelve.open(fileName)
            shelve_file[str(key)] = row;
        global num_of_chunks
        num_of_chunks = chunk_number + 1
        shelve_file.close()
        
    def _reset_persistent_shelves(self):
        '''
        Removes all existing shelves 
        '''
        for file_name in self._shelve_file_names:
            os.remove(file_name) 
        global num_of_chunks
        num_of_chunks = 0
    
    def _on_click_io_sel_new_project(self,event):
        
        super(SMARTeR, self)._on_click_io_sel_new_project(event)
       
        if self._chk_io_new_project.Value==True:
            self._tc_project_name.Show(True)
            self._tc_project_name.Enable()
            self._tc_project_name.SetValue("")
            self._cbx_project_title.Disable()
            self._cbx_project_title.SetSelection(-1)
        else:
            #self._tc_project_name.Show(False)
            self._tc_project_name.Disable()
            self._tc_project_name.SetValue("Title of new project...")
            self._cbx_project_title.Enable()
            self._cbx_project_title.SetSelection(0)
            
    def _on_click_new_project(self, event):
        SMARTeRGUI._on_click_new_project(self, event)
        msg_dlg=NewProject1(self)
        msg_dlg.Show()
    
    def _on_click_next(self, event):
        global present_chunk
        current_chunk = present_chunk;
        
        if(current_chunk <> num_of_chunks - 1): 
            current_chunk += 1
            self._lc_results_res._populate_results(current_chunk,"true")
            self._lc_results_unres._populate_results(current_chunk,"false")
            present_chunk = current_chunk
    
    def _on_click_next_res(self, event):
        global present_chunk_res
        current_chunk = present_chunk_res;
        import math
           
                        
        if(current_chunk <> math.ceil(len(self._responsive_files)/5) ): 
            current_chunk += 1
            self._lc_results_res._populate_results(current_chunk,self._responsive_files_display)
            present_chunk_res = current_chunk
            
    def _on_click_next_unres(self, event):
        global present_chunk_unres
        import math
        current_chunk = present_chunk_unres;
        
        if(current_chunk <> math.ceil(len(self._unresponsive_files)/5)):
            
            current_chunk += 1
        
            self._lc_results_unres._populate_results(current_chunk,self._unresponsive_files_display)
            present_chunk_unres = current_chunk
            
    
    def _on_click_previous(self, event):
        global present_chunk
        current_chunk = present_chunk;
        current_chunk -= 1
        if(current_chunk >= 0): 
            self._lc_results_res._populate_results(current_chunk,"true")
            self._lc_results_unres._populate_results(current_chunk,"false")
            present_chunk = current_chunk
                
    def _on_click_previous_res(self, event):
        global present_chunk_res
        current_chunk = present_chunk_res;
        current_chunk -= 1
        if(current_chunk >= 0): 
            self._lc_results_res._populate_results(current_chunk,self._responsive_files_display)
            present_chunk_res = current_chunk
            
    def _on_click_previous_unres(self, event):
        global present_chunk_unres
        current_chunk = present_chunk_unres;
        current_chunk -= 1
        if(current_chunk >= 0): 
            self._lc_results_unres._populate_results(current_chunk,self._unresponsive_files_display)
            present_chunk_unres = current_chunk
            
    def _on_click_sel_all(self, event):
        num = self._lc_results_res.GetItemCount()
        for i in range(num):
            self._lc_results_res.CheckItem(i)
            
        num = self._lc_results_unres.GetItemCount()
        for i in range(num):
            self._lc_results_unres.CheckItem(i)

    def _on_click_desel_all(self, event):
        num = self._lc_results_res.GetItemCount()
        for i in range(num):
            self._lc_results_res.CheckItem(i, False)
            
        num = self._lc_results_unres.GetItemCount()
        for i in range(num):
            self._lc_results_unres.CheckItem(i, False)

    def _on_click_log_files(self, event):
#        num = self._lc_results_res.GetItemCount()
#        for i in range(num):
#            if i == 0: self._tc_files_log.Clear()
#            if self._lc_results_res.IsChecked(i):
#                self._tc_files_log.AppendText(self._lc_results_res.GetItemText(i) + '\n')
        pass 
    
    def _on_file_change_mdl(self, event):
        '''
        Handles the model file change event  
        '''
        
        file_name = self._file_picker_mdl.GetPath()
        self.project_name = file_name
        self._load_model(file_name)

        if self._is_tm_index_available or self._is_lucene_index_available:
            self.SetStatusText("The %s model is loaded." % self.mdl_cfg['DATA']['name'])
        else: 
            self._show_error_message("Model Error", "Please select a valid model.")
            self._file_picker_mdl.SetPath("")
            self.mdl_cfg = None 
                    
    def _load_model(self, model_cfg_file):
        '''
        Loads the models specified in the model configuration file  
        
        Arguments: 
            model_cfg_file - the model configuration file  
        
        '''
        print model_cfg_file
        self.mdl_cfg = read_config(model_cfg_file)
        self._tc_data_fld.SetValue(self.mdl_cfg['DATA']['root_dir'])
        self._shelve_dir = os.path.join(self.mdl_cfg['DATA']['project_dir'], SHELVE_DIR_NAME)
        print self._shelve_dir
        if not os.path.exists(self._shelve_dir): 
            os.makedirs(self._shelve_dir)
        
        # Retrieve topic model file names 
        
        dictionary_file = self.mdl_cfg['CORPUS']['dict_file']
        path_index_file = self.mdl_cfg['CORPUS']['path_index_file']
        lda_mdl_file = self.mdl_cfg['LDA']['lda_model_file']
        lda_cos_index_file = self.mdl_cfg['LDA']['lda_cos_index_file']
        lda_num_topics = self.mdl_cfg['LDA']['num_topics']
#        lsi_mdl_file = self.mdl_cfg['LSI']['lsi_model_file']
#        lsi_cos_index_file = self.mdl_cfg['LSI']['lsi_cos_index_file']
        

        # Loads learned topic models and file details 
        if nexists(dictionary_file) and nexists(path_index_file):
                
            self.lda_file_path_index = load_file_paths_index(path_index_file)
            self.lda_dictionary = load_dictionary(dictionary_file)
            self.lda_num_files = len(self.lda_file_path_index)
            self.lda_vocab_size = len(self.lda_dictionary)        
            
            # loads LDA model details 
            if nexists(lda_mdl_file) and nexists(lda_cos_index_file): 
                self.lda_mdl, self.lda_index = load_lda_variables(lda_mdl_file, lda_cos_index_file)
                self._lda_num_topics = int(lda_num_topics)
                self._is_tm_index_available = True      
                    
#            # loads LSI model details 
#            if nexists(lsi_mdl_file) and nexists(lsi_cos_index_file):
#                self.lsi_mdl, self.lsi_index = load_lsi_variables(lsi_mdl_file, lsi_cos_index_file)
#                self._is_tm_index_available = True  
#                self._tc_available_mdl.AppendText('[LSI] ')    
                                   

        # Loads Lucene index files 
        lucene_dir = self.mdl_cfg['LUCENE']['lucene_index_dir']
        
        if nexists(lucene_dir):
            self.lucene_index_dir = lucene_dir
            self._is_lucene_index_available = True  

   
    def _on_click_add_to_query(self, event):
        metadataSelected = self._cbx_meta_type.GetValue()
        queryBoxText = self._tc_query_input.GetValue()
        # Uncomment the below lines if it is decided that the conjunctions AND OR NOT should be there. 
        # if(self._rbtn_conjunction.Enabled) :
        # self._tc_query.AppendText(self._rbtn_compulsion_level.GetStringSelection() + " " + metadataSelected + ":" + queryBoxText + " ");
        # else :
        # self._tc_query.AppendText(metadataSelected + ":" + queryBoxText + ":");
        #    self._rbtn_conjunction.Enable()   
        self._tc_query.AppendText(metadataSelected + ":" + queryBoxText + ":" + self._rbtn_compulsion_level.GetStringSelection() + ' ')
        
    def _on_click_add_to_query1(self, event):
        metadataSelected = self._cbx_meta_type1.GetValue()
        operatorSelected = self._cbx_meta_type2.GetValue()
        queryBoxText = '"'+self._tc_query_input1.GetValue()+'"'
        # Uncomment the below lines if it is decided that the conjunctions AND OR NOT should be there. 
        # if(self._rbtn_conjunction.Enabled) :
        # self._tc_query.AppendText(self._rbtn_compulsion_level.GetStringSelection() + " " + metadataSelected + ":" + queryBoxText + " ");
        # else :
        # self._tc_query.AppendText(metadataSelected + ":" + queryBoxText + ":");
        #    self._rbtn_conjunction.Enable()
        self._tc_query.AppendText(metadataSelected + ":" + self._tc_query_input1.GetValue() + ":MUST")
        if(self._tc_query1.GetValue()==""):   
            self._tc_query1.AppendText(metadataSelected + ":" + queryBoxText)
        else:
            self._tc_query1.AppendText("\n"+operatorSelected + "\n" )
            self._tc_query1.AppendText(metadataSelected + ":" + queryBoxText)
    
    def _show_error_message(self, _header, _message):
        '''
        Shows error messages in a pop up 
        '''
        
        dlg = wx.MessageDialog(self, _message, _header, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
    
    
    def _on_chbx_topic_search(self, event):
        self._chbx_facet_search.SetValue(False)
        
    def _on_chbx_facet_search(self, event):
        self._chbx_topic_search.SetValue(False)
    
    def _on_click_run_query(self, event):
        # 1. Parse the query
        
        global dictionary_of_rows
        dictionary_of_rows = OrderedDict()
        queryText = self._tc_query.GetValue().strip() 
        print queryText
        
        # 0. Validations 
        if not self._is_lucene_index_available:
            # Lucene index is mandatory 
            self._show_error_message('Run Query Error!', 'Please select a valid index for searching.')
            return   
        elif queryText == '':
            self._show_error_message('Run Query Error!', 'Please enter a valid query.')
            return 
        elif not self._is_tm_index_available:
            self._show_error_message('Run Query Error!', 'Topic model is not available for topic search.')
            return 
        
        topics = self.lda_mdl.show_topics(topics= -1, topn=10, log=False, formatted=False)
        topic_key = []
        for topic in topics:
            cnt = 0
            keywords = ""
            for tuple_ele in topic:
                keywords = keywords + tuple_ele[1] + ", "
                cnt += 1
                if(cnt == 5):
                    break
            topic_key.append(keywords.strip()[:-1])
        
        
        queries = []
        fields = []
        clauses = []
        filteredQuery = re.split(' ', queryText)
        
        for l in filteredQuery:
            res = re.split(':', l)
            print res 
            if len(res) > 1:
                fields.append(res[0])
                queries.append(res[1])
                if res[2] is 'MUST':
                    clauses.append(BooleanClause.Occur.MUST)
                elif res[2] is 'MUST_NOT':
                    clauses.append(BooleanClause.Occur.MUST_NOT)
                else:
                    clauses.append(BooleanClause.Occur.SHOULD)
        
        query_text = ' '.join(queries)  # combines all the text in a query model 
        ts_results = search_lda_model(query_text, self.lda_dictionary,
                                          self.lda_mdl, self.lda_index,
                                          self.lda_file_path_index, SEARCH_RESULTS_LIMIT)
            # # ts_results are in this format  [doc_id, doc_dir_path, doc_name, score] 
        ts_results = get_indexed_file_details(ts_results, self.lucene_index_dir)  # grabs the files details from the index
        
        self.ts_results = []
        i = 0
        for ts in ts_results:
            self.ts_results.append([ts[0], ts[1], ''])
            i += 1
            if i == 100:
                break
        self._init_results = ts_results
        
        self.load_document_feedback()
        
        self._current_page = 2
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _on_click_recalculate(self, event):
        """
        Actions to be done when the "Run Query" button is clicked
        0. Validations 
        1. Parse the query
        2. Run Lucene query 
        3. Put the results to the dictionary_of_rows
        
        
        Note: According to our current logic we do search on the 
        lucene index to retrieve documents 
        """
        
        
        # 1. Parse the query
        
        global dictionary_of_rows
        dictionary_of_rows = OrderedDict()
        queryText = self._tc_query.GetValue().strip() 

        # 0. Validations 
        if not self._is_lucene_index_available:
            # Lucene index is mandatory 
            self._show_error_message('Run Query Error!', 'Please select a valid index for searching.')
            return  
        elif queryText == '':
            self._show_error_message('Run Query Error!', 'Please enter a valid query.')
            return 
        elif not self._is_tm_index_available:
            self._show_error_message('Run Query Error!', 'Topic model is not available for topic search.')
            return 
        elif not self._is_lucene_index_available:
            self._show_error_message('Run Query Error!', 'Lucene index is not available for facet search.')
            return
        
        # queryText has Queries, Fields, BooleanClauses
        queries = []
        fields = []
        clauses = []
        filteredQuery = re.split(' ', queryText)
        
        for l in filteredQuery:
            res = re.split(':', l)
            print res 
            if len(res) > 1:
                fields.append(res[0])
                queries.append(res[1])
                if res[2] is 'MUST':
                    clauses.append(BooleanClause.Occur.MUST)
                elif res[2] is 'MUST_NOT':
                    clauses.append(BooleanClause.Occur.MUST_NOT)
                else:
                    clauses.append(BooleanClause.Occur.SHOULD)
        
        queryList = []
        queryList.append(queries)
        queryList.append(fields)
        queryList.append(clauses)

        rows = [] 
        fs_results = []
        ts_results = [] 

        
        
        fs_results = search_lucene_index(self.lucene_index_dir,
                                             queryList, SEARCH_RESULTS_LIMIT)
            
         
        query_text = ' '.join(queries)  # combines all the text in a query model 
        ts_results = search_lda_model(query_text, self.lda_dictionary,
                                          self.lda_mdl, self.lda_index,
                                          self.lda_file_path_index, SEARCH_RESULTS_LIMIT)
            # # ts_results are in this format  [doc_id, doc_dir_path, doc_name, score] 
        ts_results = get_indexed_file_details(ts_results, self.lucene_index_dir)  # grabs the files details from the index 
            
        # if facet_search and not topic_search: 
            # 2. Run Lucene query
        #    rows = fs_results
        # elif not facet_search and topic_search: 
        rows = ts_results
        # elif facet_search and topic_search: 
            # Combine results  
            # rows = self._combine_lucene_tm_results(fs_results, ts_results)
         #   print 'TODO'
          #  return 
            
        if len(rows) == 0: 
            self.SetStatusText('No documents found.')
            return 
        
        # 3. Put the results to the dictionary_of_rows
        
        key = 0 
        for row in rows:
            # file_id = row[9] # key is obtained from the lucene index
            # print retrieve_document_details(file_id, self.lucene_index_dir).get('email_subject')
            file_details = row  # values of the defined MetadataTypes 
            file_details.append('0')  # Add a 'relevance' value of '0' to each search-result
            
            if float(file_details[10])>=CUT_OFF:
                self._responsive_files.append([file_details[1],"",""])
                self._responsive_files_display.append([file_details[0],file_details[1],file_details[10],""])
            else:
                self._unresponsive_files.append([file_details[1],"",""])
                self._unresponsive_files_display.append([file_details[0],file_details[1],file_details[10],""])
            
            dictionary_of_rows.__setitem__(str(key), file_details)
            key += 1
            
        self._lc_results_res._set_shelve_dir(self._shelve_dir)
        self._lc_results_res.itemDataMap = dictionary_of_rows
        self._lc_results_res.Bind(wx.EVT_LIST_COL_CLICK, self._lc_results_res._on_header_column_click)

        self._lc_results_unres._set_shelve_dir(self._shelve_dir)
        self._lc_results_unres.itemDataMap = dictionary_of_rows
        self._lc_results_unres.Bind(wx.EVT_LIST_COL_CLICK, self._lc_results_unres._on_header_column_click)
        
        items = dictionary_of_rows.items()
        self._reset_persistent_shelves()
        self._create_persistent_shelves(items)
        global present_chunk_res
        global present_chunk_unres
        present_chunk_res = 0
        present_chunk_unres = 0
        self._lc_results_res._populate_results(present_chunk,self._responsive_files_display)
        self._lc_results_unres._populate_results(present_chunk,self._unresponsive_files_display)
        self._tc_file_preview_pane.SetValue('')
        
        
        # Goes to the results tab 
        self._current_page = 3
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
                  
    def _on_click_update_results(self, event):
        '''
        This function incorporates the user ratings into 
        the ranked list. Here, we combine the highly rated 
        documents, represent it in topic modeling space, 
        and search for similar documents.  
        
        '''
        from datetime import datetime
        self.shelf_query = shelve.open(os.path.join(self._shelve_dir, str("rating" + SHELVE_FILE_EXTENSION)), writeback=True)  # open -- file may get suffix added by low-level
        self.shelf_query['query'] = self._tc_query.GetValue().strip() 
        for row in dictionary_of_rows:
            result = dictionary_of_rows[row]
            if result[11] != 0:
                self.shelf_query[str(result[0])] = str(result[11])
        self.shelf_query.close()
        dlg = wx.MessageDialog(self, "Information is recorded, Thank you", "Update Results", wx.OK)
        dlg.ShowModal()  # Shows it
        dlg.Destroy()  # finally destroy it when finished.
        
    def load_contextual_feedback(self, topic_list):
        _bgd_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.m_staticText = wx.StaticText(self._panel_topics, wx.ID_ANY, (
            u"You may be interested in highlighting the following topics (relevant topical words) in the search process.\nPlease mark relevant keywords or skip to next page"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText.Wrap(-1)
        _bgd_sizer.Add(self.m_staticText, 0, wx.ALL, 5)
        
        _chk_Sizer = wx.GridBagSizer(0, 0)
        _chk_Sizer.SetFlexibleDirection(wx.BOTH)
        _chk_Sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        
        chkbox_cnt = 0
        self.chk_box = []
        
        for topic in topic_list:
            radioBox_choices = [ (u"Relevant"), (u"Neutral"), (u"Irrelevant") ]
            self.chk_box.append(wx.RadioBox(self._panel_topics, wx.ID_ANY, (topic), wx.DefaultPosition, wx.Size(500, 50) , radioBox_choices, 1, wx.RA_SPECIFY_ROWS))
            self.chk_box[chkbox_cnt].SetSelection(1)
            
            _chk_Sizer.Add(self.chk_box[chkbox_cnt], wx.GBPosition(int(chkbox_cnt / 2), int(2 + chkbox_cnt % 2)), wx.GBSpan(1, 1), wx.ALL, 5)
            chkbox_cnt += 1
            if chkbox_cnt == 10:
                break
            
        self._next_cf_button = wx.Button(self._panel_topics, wx.ID_ANY, (u"Save Keywords"), wx.DefaultPosition, wx.DefaultSize, 0)
        self._skip_cf_button = wx.Button(self._panel_topics, wx.ID_ANY, (u"Skip"), wx.DefaultPosition, wx.DefaultSize, 0)
        self._next_cf_button.Bind(wx.EVT_BUTTON, self._on_click_contextual_feed)
        self._skip_cf_button.Bind(wx.EVT_BUTTON, self._on_click_skip_contextual_feed)
        _chk_Sizer.Add(self._next_cf_button, wx.GBPosition(chkbox_cnt / 2, 2), wx.GBSpan(1, 1), wx.ALL, 5)
        _chk_Sizer.Add(self._skip_cf_button, wx.GBPosition(chkbox_cnt / 2, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        
        _bgd_sizer.Add(_chk_Sizer, 1, wx.EXPAND, 5)
        self._panel_topics.SetSizer(_bgd_sizer)
        self._panel_topics.Layout()
        _bgd_sizer.Fit(self._panel_topics)
        
    def _on_click_skip_contextual_feed(self, event):
        self._current_page = 3
        self.load_document_feedback()
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _on_click_contextual_feed(self, event):
        
        # for chk_box in self.chk_box:
            # print chk_box.GetSelection()
        
        self._current_page = 3
        self.load_document_feedback()
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def load_document_feedback(self):
        self.panel_feedback_doc = TaggingControlFeedback(self._panel_feedback_doc, self)
        self.panel_feedback_doc._setup_review_tab()
        
    def _on_rbx_result_responsive_update(self, event):
        
        
        try:
            selected_doc_id = self._lc_results_res.GetFocusedItem()
            responsive_status = self._rbx_feedack_res.GetStringSelection()
            if responsive_status == 'Responsive': 
                self._lc_results_res.SetStringItem(selected_doc_id, 3, 'Yes')
                #self.ts_results[selected_doc_id][2] = 'Responsive'
            elif responsive_status == 'Unresponsive': 
                self._lc_results_res.SetStringItem(selected_doc_id, 3, 'No')
                #self.ts_results[selected_doc_id][2] = 'Unresponsive'
            else: 
                self._lc_results_res.SetStringItem(selected_doc_id, 3, '')
                #self.ts_results[selected_doc_id][2] = ''
            
        except Exception, e:
            print e
            
    def _on_rbx_result_unresponsive_update(self, event):
        
        try:
            selected_doc_id = self._lc_results_unres.GetFocusedItem()
            responsive_status = self._rbx_feedack_unres.GetStringSelection()
            if responsive_status == 'Responsive': 
                self._lc_results_unres.SetStringItem(selected_doc_id, 3, 'Yes')
                #self.ts_results[selected_doc_id][2] = 'Responsive'
            elif responsive_status == 'Unresponsive': 
                self._lc_results_unres.SetStringItem(selected_doc_id, 3, 'No')
                #self.ts_results[selected_doc_id][2] = 'Unresponsive'
            else: 
                self._lc_results_unres.SetStringItem(selected_doc_id, 3, '')
                #self.ts_results[selected_doc_id][2] = ''
            
        except Exception, e:
            print e
    
    def _on_rbx_responsive_updated(self, event):
        '''
        Handles the selected document responsive check box 
        check and uncheck events 
         
        '''
        try:
            selected_doc_id = self.panel_feedback_doc.GetFocusedItem()
            responsive_status = self._rbx_responsive.GetStringSelection()
            if responsive_status == 'Responsive': 
                self.panel_feedback_doc.SetStringItem(selected_doc_id, 2, 'Yes')
                self.ts_results[selected_doc_id][2] = 'Responsive'
            elif responsive_status == 'Unresponsive': 
                self.panel_feedback_doc.SetStringItem(selected_doc_id, 2, 'No')
                self.ts_results[selected_doc_id][2] = 'Unresponsive'
            else: 
                self.panel_feedback_doc.SetStringItem(selected_doc_id, 2, '')
                self.ts_results[selected_doc_id][2] = ''
            self.update_results()
        except Exception, e:
            print e
    def update_results(self):
        
        ###########
        #Only for trec data set
        ###########
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for ts in self._init_results:
            result = os.path.split(os.path.split(ts[1])[0])[1]
            if  result == "1" and float(ts[10])>CUT_OFF:
                tp=tp+1
            #exit()
            elif result == "1" and float(ts[10])<=CUT_OFF:
                fn=fn+1
            elif result == "0" and float(ts[10])>CUT_OFF:
                fp=fp+1
            else:
                tn=tn+1
        
        self._st_false_negative.SetLabel(str(fn))
        self._st_true_positive.SetLabel(str(tp))
        self._st_true_negative.SetLabel(str(tn))
        self._st_false_positive.SetLabel(str(fp))
        
        
    def _init_confidence(self):
        '''
        Sets default confidence level and interval in Top Level interface
        Arguments: None
        Returns: None
        '''
        
        self.confidence_val = DEFAULT_CONFIDENCE_LEVEL / Decimal('100')
        self.confidence_val_unres=self.confidence_val
        items = self._cbx_confidence_levels.GetItems()
        items_unres=self._cbx_confidence_levels_unres.GetItems()
        index = -1
        try:
            index = items.index(str(DEFAULT_CONFIDENCE_LEVEL))
            self._cbx_confidence_levels.SetSelection(index)
        except ValueError:
            self._cbx_confidence_levels.ChangeValue(str(DEFAULT_CONFIDENCE_LEVEL))
            
        try:
            index = items_unres.index(str(DEFAULT_CONFIDENCE_LEVEL))
            self._cbx_confidence_levels_unres.SetSelection(index)
        except ValueError:
            self._cbx_confidence_levels_unres.ChangeValue(str(DEFAULT_CONFIDENCE_LEVEL))
    
        
        # Set default confidence interval 
        self.precision_val = DEFAULT_CONFIDENCE_INTERVAL / 100
        str_precision = str(int(DEFAULT_CONFIDENCE_INTERVAL))
        self._tc_confidence_interval.ChangeValue(str_precision)
        
        self.precision_val_unres = DEFAULT_CONFIDENCE_INTERVAL / 100
        str_precision = str(int(DEFAULT_CONFIDENCE_INTERVAL))
        self._tc_confidence_interval_unres.ChangeValue(str_precision)

        # Hides the status messages 
        self._st_num_samples_res.Show(False)
        self._st_num_samples_unres.Show(False)
        #self._st_num_samples_ind_unres.Show(False)            
    
        
    def _on_click_continue(self, event):
        self._generate_file_samples()
        self._generate_file_samples_unres()
        self._current_page = 4
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _load_cbx_confidence_levels(self):
        '''
        Loads the supported confidence levels 
        '''
        try:
            confidence_levels = ['%.3f' % (w * Decimal('100')) for w in  SUPPORTED_CONFIDENCES.keys()]
            confidence_levels.sort(reverse=True)
            self._cbx_confidence_levels.Clear()
            for cl in confidence_levels:
                self._cbx_confidence_levels.Append(cl)
                self._cbx_confidence_levels_unres.Append(cl)
        except Exception,e:
            self.error(e)
            
    def _on_precision_changed(self, event):
        '''
        Triggers an event and updates the sample list on precision - aka 
        confidence interval change.
        Arguments: Event of new precision value
        Returns: Nothing
        '''
        
        def show_precision_error():
            self._show_error_message("Value Error!", "Please enter a confidence interval between 0 and 100.")
            self._tc_confidence_interval.ChangeValue(str(int(DEFAULT_CONFIDENCE_INTERVAL))) # Sets the default value 
            self._tc_confidence_interval.SetFocus()
            

        # Maybe intermittently null string, escaping 
        try:
            # Checks for positive values 
            ci = float(self._tc_confidence_interval.GetValue())
            if ci <= 0 or ci > 99:
                show_precision_error()
                return 
            
            self.get_precision_as_float()
            if self._chk_toggle_cl_level.Value==True:
                self.precision_val_unres=self.precision_val
            #self._tc_out_confidence_interval.ChangeValue(self._tc_confidence_interval.GetValue())
            #self.SetStatusText('Confidence interval is changed as ' + self._tc_confidence_interval.GetValue())
        except ValueError:
            show_precision_error()
            return None 
        
        self._generate_file_samples()
        
        
    def _on_precision_changed_unres(self, event):
        '''
        Triggers an event and updates the sample list on precision - aka 
        confidence interval change.
        Arguments: Event of new precision value
        Returns: Nothing
        '''
        
        def show_precision_error():
            self._show_error_message("Value Error!", "Please enter a confidence interval between 0 and 100.")
            self._tc_confidence_interval.ChangeValue(str(int(DEFAULT_CONFIDENCE_INTERVAL))) # Sets the default value 
            self._tc_confidence_interval.SetFocus()
            

        # Maybe intermittently null string, escaping 
        try:
            # Checks for positive values 
            ci = float(self._tc_confidence_interval.GetValue())
            if ci <= 0 or ci > 99:
                show_precision_error()
                return 
            
            self.get_precision_as_float_unres()
            #self._tc_out_confidence_interval.ChangeValue(self._tc_confidence_interval.GetValue())
            #self.SetStatusText('Confidence interval is changed as ' + self._tc_confidence_interval.GetValue())
        except ValueError:
            show_precision_error()
            return None 
        
        self._generate_file_samples_unres()
        
    def _generate_file_samples(self):
        '''
        This function generates file sample based on the 
        class variables such as file_list, confidence_val, 
        and precision_val and sets the sample status label     
        '''

        # Generate samples
        self.sampled_files_responsive = random_sampler(self._responsive_files, self.confidence_val, self.precision_val, self.SEED)
        if self._chk_toggle_cl_level.Value==True:
            self.sampled_files_unresponsive = random_sampler(self._unresponsive_files, self.confidence_val, self.precision_val, self.SEED)
        print self.confidence_val
        self._st_num_samples_res.SetLabel('Responsive: %d sample documents will be selected' % len(self.sampled_files_responsive))
        self._st_num_samples_res.Show()
        
        if self._chk_toggle_cl_level.Value==True:
            self._st_num_samples_unres.SetLabel('Unresponsive: %d sample documents will be selected'% len(self.sampled_files_unresponsive))
            self._st_num_samples_unres.Show()
        
        
    def _generate_file_samples_unres(self):
        '''
        This function generates file sample based on the 
        class variables such as file_list, confidence_val, 
        and precision_val and sets the sample status label     
        '''

        # Generate samples
        
        self.sampled_files_unresponsive = random_sampler(self._unresponsive_files, self.confidence_val_unres, self.precision_val_unres, self.SEED)
        self._st_num_samples_ind_unres.SetLabel('Unresponsive: %d sample documents will be selected'% len(self.sampled_files_unresponsive))
        self._st_num_samples_ind_unres.Show(True)

     
#        # step 1: gets highly rated documents 
#        
#        
#        selected_docs = []  
#        excluded_docs = []
#        
#        for shelf_file_name in self._shelve_file_names:
#            sd = shelve.open(shelf_file_name)
#            for k in sd.keys():
#                row = sd[k]
#                if int(row[-1]) > USER_RATINGS_CUT_OFF:
#                    selected_docs.append(row) 
#                else: 
#                    excluded_docs.append(row) 
#            sd.close()
#            
#        # step 2: combine all email bodies to a single document 
#        # row index 5 is for the body field 
#        
#        bag_of_words = ''
#        for sdoc in selected_docs:
#            bag_of_words += sdoc[5]
#        
#        # bag_of_words_td = get_lda_query_td(bag_of_words, self.lda_dictionary, self.lda_mdl)
#        
#        # step 3: compute the distances between bag_of_words and 
#        # all other documents 
#        
#        excluded_docs = compute_topic_similarities(bag_of_words, selected_docs + excluded_docs, self.lda_dictionary, self.lda_mdl, self._lda_num_topics)
#        
#        
#        # TODO: need to figure out a good way to combine topic modeling 
#        #       similarity score and lucene scores      
#        
#        

    def get_precision_as_float(self):
        '''
        Converts precision to float
        Returns: Nothing
        Arguments: Nothing
        '''
        try:
            self.precision_val = float(self._tc_confidence_interval.GetValue()
                                       ) / 100.0 
        except ValueError:
            self.precision_val = float(int(self._tc_confidence_interval.GetValue())
                                       ) / 100.0
                                       
    def get_precision_as_float_unres(self):
        '''
        Converts precision to float
        Returns: Nothing
        Arguments: Nothing
        '''
        try:
            self.precision_val_unres = float(self._tc_confidence_interval_unres.GetValue()
                                       ) / 100.0 
        except ValueError:
            self.precision_val_unres = float(int(self._tc_confidence_interval_unres.GetValue())
                                       ) / 100.0
                                       
    def _on_confidence_changed(self, event):
        '''
        Triggers an event and updates the sample list on confidence - aka 
        confidence level change
        Arguments: Event of new confidence
        Returns: Nothing
        '''
        self.confidence_val = Decimal(self._cbx_confidence_levels.GetValue()) / Decimal('100')
        if self._chk_toggle_cl_level.Value==True:
            self.confidence_val_unres=self.confidence_val
        self._generate_file_samples()
        
    def _on_confidence_changed_unres(self, event):
        
        self.confidence_val_unres = Decimal(self._cbx_confidence_levels_unres.GetValue()) / Decimal('100')
        self._generate_file_samples_unres()

    def _on_click_cl_goback( self, event ):
        self._current_page = 3
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
    
    def _on_click_cl_next( self, event ):
        self._review_res = TaggingControlSmarter(self._panel_review_res, self.sampled_files_responsive,self._rbx_response_res,self._rbx_privilage_res,self._tc_preview_tags,self._panel_doc_tag_res)
        self._review_res._setup_review_tab()
        self._current_page = 5
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')

    def _on_click_index_data(self, event):
        '''
        Handles the data folder files' indexing and topic modeling 
         
         
        TODO: 
            1. validations to be done 
        
        '''
    
        project_name = self._cbx_project_title.GetValue()
        #ADD
        if project_name=="":
            self._show_error_message("Missing input", "Please enter or select a project.")
        else:

            if self._is_tm_index_available or self._is_lucene_index_available:
                self.SetStatusText("The %s model is loaded." % self.mdl_cfg['DATA']['name'])
                self._current_page = 1
                self._notebook.ChangeSelection(self._current_page)
                self.SetStatusText('')
            else: 
                self._show_error_message("Model Error", "Please select a valid model.")
                self._file_picker_mdl.SetPath("")
                self.mdl_cfg = None
                
    def _on_set_existing_project(self,event):
        project_name = self._cbx_project_title.GetValue()
        cfg_file_name = os.path.join(self._cfg_dir,project_name+".cfg")
        self.project_name = cfg_file_name
        self._load_model(cfg_file_name)
              
    def _on_click_clear_project_details(self, event):
        '''
        Clears the project details 
        
        '''
        
        self._tc_project_name.SetValue('')
        self._data_dir_picker.SetPath('')
        self._application_dir_picker.SetPath('')
        
    def _on_click_change_unres_focus(self,event):
        if self._chk_toggle_cl_level.Value==True:
            self.precision_val_unres=self.precision_val
            self.confidence_val_unres=self.confidence_val
            self._generate_file_samples()
            self._panel_unres_cl.Show(False)
            self._st_num_samples_unres.Show(True)
        else:
            self.confidence_val_unres = Decimal(self._cbx_confidence_levels_unres.GetValue()) / Decimal('100')
            self.precision_val_unres = float(self._tc_confidence_interval_unres.GetValue()) / 100.0
            self._generate_file_samples_unres()
            self._panel_unres_cl.Show(True)
            self._st_num_samples_unres.Show(False)
        
    def _combine_lucene_tm_results(self, fs_results, ts_results):
        
        num_metadata_types = len(MetadataType._types)
        default_lowest_score = -99999
        
        def get_tm_score(file_id, ts_results):
            '''
            TODO: Need to improve this logic. It'd be 
            good if we can keep the scores in a dictionary. 
            Otherwise, this function will be in efficient 
            '''
            
            for ts_row in ts_results:
                if ts_row[num_metadata_types] == file_id:
                    return ts_row[num_metadata_types + 1]
                
            return default_lowest_score    
        
        
        rows = [] 
        
        for fs_row in fs_results:
            tm_score = get_tm_score(fs_row[num_metadata_types], ts_results)
            fs_row[num_metadata_types + 1] = tm_score
            rows.append(fs_row) 
            print fs_row
        
        return rows 
        
    def _on_rbx_responsive_updated_res( self, event ):
        '''
        Handles the selected document responsive check box 
        check and uncheck events 
         
        '''
        responsive_status = self._rbx_response_res.GetStringSelection() 
        if responsive_status == 'Yes': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 2, 'Yes')
        elif responsive_status == 'No': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 2, 'No')
        elif responsive_status == 'Unknown': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 2, '')

    
    
    def _on_rbx_privileged_updated_res( self, event ):
        '''
        Handles the selected document privileged check box 
        check and uncheck events 
         
        '''
        privileged_status = self._rbx_privilage_res.GetStringSelection() 
        if privileged_status == 'Yes': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 3, 'Yes')
        elif privileged_status == 'No': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 3, 'No')
        elif privileged_status == 'Unknown': 
            self._review_res.SetStringItem(self._review_res.GetFocusedItem(), 3, '')

    def _on_click_clear_all_doc_tags_res( self, event ):
        '''
        Clear all assigned document tags from the list control 
        '''
        try:
            for i in range(0, len(self.sampled_files_responsive)):
                self._review_res.SetStringItem(i, 2, '')
                self._review_res.SetStringItem(i, 3, '')       
            
            self._rbx_response_res.SetStringSelection('Unknown')    
            self._rbx_privilage_res.SetStringSelection('Unknown')  
                
    
            self._is_rt_updated = True
        except Exception,e:
            self.error(e)

    def _on_rbx_responsive_updated_unres( self, event ):
        '''
        Handles the selected document responsive check box 
        check and uncheck events 
         
        '''
        responsive_status = self._rbx_response_unres.GetStringSelection() 
        if responsive_status == 'Yes': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 2, 'Yes')
        elif responsive_status == 'No': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 2, 'No')
        elif responsive_status == 'Unknown': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 2, '')    
    def _on_rbx_privileged_updated_unres( self, event ):
        '''
        Handles the selected document privileged check box 
        check and uncheck events 
         
        '''
        privileged_status = self._rbx_privilage_unres.GetStringSelection() 
        if privileged_status == 'Yes': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 3, 'Yes')
        elif privileged_status == 'No': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 3, 'No')
        elif privileged_status == 'Unknown': 
            self._review_unres.SetStringItem(self._review_unres.GetFocusedItem(), 3, '')

    def _on_click_clear_all_doc_tags_unres( self, event ):
        '''
        Clear all assigned document tags from the list control 
        '''
        try:
            for i in range(0, len(self.sampled_files_unresponsive)):
                self._review_unres.SetStringItem(i, 2, '')
                self._review_unres.SetStringItem(i, 3, '')       
            
            self._rbx_response_unres.SetStringSelection('Unknown')    
            self._rbx_privilage_unres.SetStringSelection('Unknown')  
                
    
            self._is_rt_updated = True
        except Exception,e:
            self.error(e)
            
    def _btn_sample_back_res(self, event):
        self._review_res.Destroy()
        self._current_page = 4
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _btn_sample_back_unres(self, event):
        self._review_unres.Destroy()
        self._current_page = 5
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _on_click_sample_next( self, event ):
        self._review_unres = TaggingControlSmarter(self._panel_review_unres, self.sampled_files_unresponsive,self._rbx_response_unres,self._rbx_privilage_unres,self._tc_preview_tags_unres,self._panel_doc_tag_unres)
        self._review_unres._setup_review_tab()
        self._current_page = 6
        self._notebook.ChangeSelection(self._current_page)
        self.SetStatusText('')
        
    def _btn_sample_exit(self, Event):
        exit()

def main():
    '''
    The main function call 
    '''
    
    ex = wx.App()
    SMARTeR(None)
    ex.MainLoop()    


if __name__ == '__main__':
    
    main()

    
