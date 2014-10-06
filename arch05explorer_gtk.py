#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:     arch05 and embb explorer
#
# Author:      gregkwaste
#
# Created:     05/10/2014
# Copyright:   (c) gregkwaste 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import zlib,os,struct
from StringIO import StringIO
import gtk,webbrowser

def read_string(f):
    c=''
    temp=struct.unpack('<B', f.read(1))[0]
    while not temp:
        temp=struct.unpack('<B',f.read(1))[0]
        continue
    if temp:
        c=chr(temp)
    for i in range(128):
        s = struct.unpack('<B', f.read(1))[0]
        if s == 0:
            #print(c)
            return c
        c += chr(s)
    return {'FINISHED'}

def rec_tree(iter,mps,index,data,path,tree,hist):
    if index==len(mps)-1:
        hist[index][mps[index]]=tree.append(iter,[mps[index],data[0],data[1],data[2],data[3]])
    else:
        try:
            nextiter=hist[index][mps[index]]
        except:
            nextiter=tree.append(iter,[mps[index],0,0,0,''])
            hist[index][mps[index]]=nextiter

        index+=1

        rec_tree(nextiter, mps, index, data, path, tree, hist)

class FileChooserWindow(gtk.Window):

    def __init__(self):
        self.path = ''
        self.fcd = gtk.FileChooserDialog("Select Big File", None, gtk.FILE_CHOOSER_ACTION_OPEN,
               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self.response = self.fcd.run()
        if self.response==gtk.RESPONSE_OK:
            self.path = self.fcd.get_filename()
            print("Selected File: " + self.fcd.get_filename())
            self.fcd.destroy()
        elif self.response == gtk.RESPONSE_CANCEL:
            print("Closing File Dialog")
            self.fcd.destroy()


class AppWindow:
    def __init__(self):
        self.gladefile = "full_layout.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        self.window.connect("delete-event", self.on_window_destroy)
        self.about_win = self.builder.get_object("about")
        #arch05 list
        self.main_list = self.builder.get_object("liststore1")
        self.main_viewer = self.builder.get_object("arch05_tree")
        self.main_viewer.connect("row-activated",self.row_activate)
        #embb list
        self.embb_list = self.builder.get_object("treestore1")
        self.embb_viewer = self.builder.get_object("embb_tree")
        self.embb_viewer.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        #xml_text_viewer
        self.xml_viewer=self.builder.get_object("xml_viewer")
        #embb file
        self.embb_file=StringIO()
        self.status_label = self.builder.get_object("status_label")
        self.about_win = self.builder.get_object("about")
        #notebook
        self.notebook=self.builder.get_object("notebook1")
        #excplicit signal connections
        item=self.builder.get_object("pack_export")
        item.connect("activate",self.menu_item_response,"packed_export")



        #initialize file dictionary
        self.hist=[]
        self.hist[0:7]={},{},{},{},{},{},{},{}

    def menu_item_response(self,widget,mode):
        (model,pathlist)=self.embb_viewer.get_selection().get_selected_rows()
        if mode=="packed_export":
            print('I am exporting packed')

            for path in pathlist:
                tree_iter=model.get_iter(path)
                off=model.get_value(tree_iter,1)
                size=model.get_value(tree_iter,2)
                path=model.get_value(tree_iter,4)
                self.embb_file.seek(off)
                if path=='': continue
                path='C:\\'+path
                print(path)
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
                #print(path,off,size)
                t=open(path,'wb')
                t.write(self.embb_file.read(size))
                t.close()

    def clear_hist(self):
        self.hist[0:7]={},{},{},{},{},{},{},{}

    def open_file(self,event):
        self.clear_hist()
        self.main_list.clear()
        self.active_file=FileChooserWindow()
        num=self.load_arch05()
        print("Total Files Detected: ",num)
        self.status_label.set_label("Current File: "+self.active_file.path)


    def about_win(self,event):
        response=self.about_win.run()
        if response == gtk.RESPONSE_DELETE_EVENT or response == gtk.RESPONSE_CANCEL:
            self.about_win.hide()

    def visit_url(self,widget):
        webbrowser.open(widget.get_uri())

    def visit_url_about(self,widget,uri):
        webbrowser.open(uri)

    def on_window_destroy(self, *args):
        self.window.destroy()
        gtk.main_quit(*args)

    def on_button1_pressed(self,button):
        print("Button Clicked")

    def on_treeview1_button_press_event(self,widget,event):
        if event.button==3 and self.treeview.get_selection().count_selected_rows():

            self.context_menu.popup(None,None,None,event.button,event.time)

    def load_arch05(self):
        t=StringIO() #name buffer init
        f=open(self.active_file.path,'rb') #open archive
        #read file
        f.read(4) #LTAR Header
        f.read(4) #03000000
        offset_offset=struct.unpack('<I',f.read(4))[0]
        dir_num=struct.unpack('<I',f.read(4))[0]-1 #descr num???
        file_num=struct.unpack("<I",f.read(4))[0]
        file_names=[]
        print(file_num)
        #get file names
        f.seek(0x30)#Get to the description start
        t.write(f.read(offset_offset))



        #return(file_num)
        t.seek(struct.unpack('<I',f.read(4))[0])

        #get file data
        for i in range(file_num):
            offset=struct.unpack('<I',f.read(4))[0]
            f.read(4)
            comp_size=struct.unpack('<I',f.read(4))[0]
            f.read(4)
            decomp_size=struct.unpack('<I',f.read(4))[0]
            f.read(8)
            name_offset=struct.unpack('<I',f.read(4))[0]
            name=read_string(t)
            t.seek(name_offset)

            self.main_list.append((name,offset,comp_size,decomp_size,name))


        f.close()
        return len(self.main_list)

    def row_activate(self,treeview,path,view_column):
        if self.main_list[path[0]][0].split('.')[-1]=='bndlxml05':
            print('openingxml')
            self.read_xml(self.main_list[path[0]][1],self.main_list[path[0]][2])
            self.notebook.set_page(1)
        elif self.main_list[path[0]][0].split('.')[-1]=='embb':
            print('openning embb: ',self.main_list[path[0]][0])
            self.embb_list.clear()
            self.load_embb(self.main_list[path[0]][1],self.main_list[path[0]][2])
            self.notebook.set_page(0)


    def decomp_data(self,offset,file_comp_size):
        #load file into memory
        t=StringIO()
        f=open(self.active_file.path,'rb')
        f.seek(offset)
        temp_size=0
        parts=0
        while temp_size<file_comp_size:
            comp_size,decomp_size=struct.unpack('<2I',f.read(8))
            data=f.read(comp_size)
            data=zlib.decompress(data)
            t.write(data)
            #Uniform the offset
            off=f.tell() % 4
            if off: f.read(4-off)
            #print(f.tell())
            temp_size+=comp_size+8+(4-off)
            parts+=1
        print('Total Zlib Chunks: ',hex(parts))
        f.close()
        #read file from memory
        t.seek(0)
        return t

    def read_xml(self,offset,file_comp_size):
        self.embb_file=self.decomp_data(offset,file_comp_size)
        buf=self.xml_viewer.get_buffer()
        buf.set_text(self.embb_file.buf)




    def load_embb(self,offset,file_comp_size):
        self.embb_file=self.decomp_data(offset,file_comp_size)
        self.embb_file.read(4) #BNDL Header
        self.embb_file.read(4) #04000000
        offset_offset=struct.unpack('<I',self.embb_file.read(4))[0]
        other_offset=struct.unpack('<I',self.embb_file.read(4))[0]
        self.embb_file.read(8) #000000
        file_num=struct.unpack("<I",self.embb_file.read(4))[0]

        file_list=[]
        #print(file_num)
        temp=file_num

        dir=''
        while file_num:
            name=read_string(self.embb_file)
            if len(name.split('.'))==1:
                dir=name+'\\'
                continue
            file_list.append(dir+name)
            file_num-=1
        file_num=temp
        self.embb_file.seek(0x1C+other_offset)

        tree=self.embb_list
        self.clear_hist()
        for i in range(file_num):
            data_id=struct.unpack('<I',self.embb_file.read(4))[0]
            data_size=struct.unpack('<I',self.embb_file.read(4))[0]
            data_off=self.embb_file.tell()
            mps=file_list[i].split('\\')
            rec_tree(None,mps,0,(data_off,data_size,data_id,file_list[i]),'',tree,self.hist)
            self.embb_file.seek(data_size,1)

        return file_num








app=AppWindow()
app.window.show_all()
gtk.main()

