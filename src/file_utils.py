#!/usr/bin/env python2.7
'''
This script has all the basic file access/process 
utility functions 

Created by: Abhiram J.  
Created On: Jan 28, 2013   

@deprecated: this is deprecated as of March 08, 2013. Please use the utils.utils_file.py instead 
'''

import os
import shutil
import ConfigParser
import threading
import wx
import win32file

def copy_files_with_dir_tree(lcp, file_paths, output_dir_path, in_file_prefix=''):
    '''Copies the files given in path list into 
    the specified output directory. The directory structure 
    is preserved during this process. 
    
    Returns: 
        None 
        
    Arguments: 
        lcp - input directory 
        file_paths - list of files paths 
        output_dir_path - the output directory path 
    '''
    
    # find the longest common prefix (LCP)
    # lcp = os.path.commonprefix(file_paths) 
    
    for src_file_path in file_paths:
        s_fp = os.path.relpath(src_file_path, lcp)#src_file_path[len(lcp):] # ignores LCP from path   
        dest_dp, _ = os.path.split(s_fp) # to preserve source files directory structure 
        dest_dir_path = os.path.join(output_dir_path, dest_dp)

        if not os.path.exists(dest_dir_path):
            os.makedirs(dest_dir_path)
        
        if in_file_prefix <> '':            
            src_file_path = os.path.join(in_file_prefix, src_file_path)
        
        shutil.copy2(src_file_path, dest_dir_path)

def copy_with_dialog(lcp,tempdir, file_paths, output_dir_path, size, dialog, in_file_prefix=''):
    '''Copies the files given in path list into 
    the specified output directory. The directory structure 
    is preserved during this process. 
    This additionally allows for a progress bar to be set to show
    progress of copy.
    
    Returns: 
        None 
        
    Arguments: 
        lcp - input directory 
        file_paths - list of files paths 
        output_dir_path - the output directory path
        size - total size of files to copy in bytes
        dialog - front-end dialog to update 
    '''
    
    # find the longest common prefix (LCP)
    # lcp = os.path.commonprefix(file_paths) 
    current_copy = 0
    status = ''
    for src_file_path in file_paths:
        if src_file_path.startswith(tempdir)==True:
            s_fp = os.path.relpath(src_file_path, tempdir)#src_file_path[len(lcp):] # ignores LCP from path
        else:
            s_fp = os.path.relpath(src_file_path, lcp)#src_file_path[len(lcp):] # ignores LCP from path   
        
        dest_dp, _ = os.path.split(s_fp) # to preserve source files directory structure 
        dest_dir_path = os.path.join(output_dir_path, dest_dp)
    
        #print output_dir_path
        #print dest_dp
        #print s_fp
        if not os.path.exists(dest_dir_path):
            os.makedirs(dest_dir_path)
        
        if in_file_prefix <> '':            
            src_file_path = os.path.join(in_file_prefix, src_file_path)
        try:
            shutil.copy2(src_file_path, dest_dir_path)
        except OSError:
            status += src_file_path + " could not be copied. Check permissions.\n"
        except IOError:
            status += src_file_path + " could not be copied. Check permissions.\n"
        except Exception:
            status +=  src_file_path + " could not be copied.\n"
        current_copy += os.path.getsize(src_file_path)
        # This will update the UI, putting this thread on wait for 8 millisecs,
        # This is a thread safe method
        # python does not have true threading, only timeslicing
        try:
            #wx.MutexGuiEnter()
            dialog.Update(int(100*current_copy/size))
            wx.CallAfter(dialog.Update, int(100*current_copy/size))
            wx.MilliSleep(8)
            if (src_file_path == file_paths[len(file_paths) -1]):
                wx.CallAfter(dialog.Update, 100)
                dialog.Update(100)
                return status
        finally:
            #wx.MutexGuiLeave()
            pass
            

def get_destination_file_path(input_dir_path,tempdir, src_file_path, output_dir_path):
    '''
    Gets the copied file's path based on the same logic 
    we used to copy files into the destination folder 
    '''
    if src_file_path.startswith(tempdir)==True:
        s_fp = os.path.relpath(src_file_path, tempdir)#src_file_path[len(lcp):] # ignores LCP from path
    else:
        s_fp = os.path.relpath(src_file_path, input_dir_path)#src_file_path[len(lcp):] # ignores LCP from path   

    dest_file_path = os.path.join(output_dir_path, s_fp)

    return dest_file_path


def find_files_in_folder(input_dir):
    '''Recursive descent to find files in folder.
    
    Returns: 
        a list of absolute path of all files
    Arguments: 
        input_dir - the input folder
    '''
    
    
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file_name in files:
            file_list.append(os.path.join(root, file_name))
    return file_list

def read_config(file_name):
    
    config = ConfigParser.ConfigParser()
    config.read(file_name)
    config_dict = {}
    
    for section in config.sections():
        options_dict = {}
        for option in config.options(section):
            try:
                options_dict[option] = config.get(section, option)
                if options_dict[option] == -1: print "skip: %s" % option
            except:
                print("exception on %s!" % option)
                options_dict[option] = None
        config_dict[section] = options_dict
    
    return config_dict

def convert_size(size_bytes):
    '''
    Size in bytes to human readable file sizes
    
    Returns:
    Human readable size string
    
    Arguments:
    Size in bytes
    '''
    # Unit of reference
    UNIT_MULTIPLIER = 1024
    conversion = [
    (UNIT_MULTIPLIER ** 5, ' PB'),
    (UNIT_MULTIPLIER ** 4, ' TB'), 
    (UNIT_MULTIPLIER ** 3, ' GB'), 
    (UNIT_MULTIPLIER ** 2, ' MB'), 
    (UNIT_MULTIPLIER ** 1, ' KB'),
    (UNIT_MULTIPLIER ** 0, (' byte', ' bytes')),
    ]
    
    for factor, suffix in conversion:
        if size_bytes >= factor:
            break
    amount = int(size_bytes/factor)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix

# helper method to run a function in another thread
def start_thread(func, *args): 
    thread = threading.Thread(target=func, args=args)
    thread.setDaemon(True)
    thread.start()
    thread.join(timeout = 20)
    return thread

def free_space(input_file_path):
    """
    Returns the number of free bytes on the drive that input_file_path is on
    """
    secsPerClus, bytesPerSec, nFreeClus, totClus = win32file.GetDiskFreeSpace(input_file_path)
    return secsPerClus * bytesPerSec * nFreeClus


'''
Obsolete methods 
'''

def copy_random_files(dir_path, random_list):
    '''Copies the random files to a given folder. 
    
    TODO: Throws error for sample already existing. Need to fix
    
    Returns: 
        None 
    Arguments: 
        dir_path - output directory path 
        random_list - list of file paths 
    '''
    try:
        if  not os.path.exists(dir_path):
            os.makedirs(dir_path)
        i = 1
        for file_name in random_list:
            curr_file_name = os.path.basename(file_name)
            shutil.copy2(file_name, dir_path)
            # Do rename to avoid overwriting files with same name
            os.rename(os.path.join(dir_path, curr_file_name), os.path.join(dir_path, curr_file_name + "--" + str(i)))
            i += 1
    except OSError:
            print str(OSError)
            print "Cannot copy the required files. Check that destination directory is empty"

class FileLoadDialog(wx.Dialog):
    def __init__(self, gui, title, to_add=1, cancellable=False):
        wx.Dialog.__init__(self, gui, title=title,
                          style=wx.CAPTION)
        
        self.gui = gui
        self.count = 0
        self.to_add = to_add
        self.timer = wx.Timer(self)
        self.gauge = wx.Gauge(self, range=100, size=(180, 30))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.gauge, 0, wx.ALL, 10)

        if cancellable:
            cancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")
            cancel.SetDefault()
            cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
            btnSizer = wx.StdDialogButtonSizer()
            btnSizer.AddButton(cancel)
            btnSizer.Realize()
            sizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetFocus()

        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(30)


    def on_timer(self, event):
        """Increases the gauge's progress."""
        self.count += self.to_add
        self.gauge.SetValue(self.count)
        if self.count > 100:
            self.count = 0


    def on_cancel(self, event):
        """Cancels the conversion process"""
        # do whatever
        self.Close()