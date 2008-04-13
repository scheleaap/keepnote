




# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk


from takenote.treemodel import \
    DROP_TREE_MOVE, \
    DROP_PAGE_MOVE, \
    DROP_NO, \
    compute_new_path, \
    copy_row, \
    TakeNoteTreeStore

from takenote import get_resource


class TakeNoteTreeView (gtk.TreeView):
    
    def __init__(self):
        gtk.TreeView.__init__(self)
    
        self.on_select_node = None
        
        
        # create a TreeStore with one string column to use as the model
        self.model = TakeNoteTreeStore(2, gdk.Pixbuf, str, object)
                        
        # init treeview
        self.set_model(self.model)
        
        self.connect("key-release-event", self.on_key_released)
        self.expanded_id = self.connect("row-expanded", self.on_row_expanded)
        self.collapsed_id = self.connect("row-collapsed", self.on_row_collapsed)
                 
        self.connect("drag-begin", self.on_drag_begin)
        self.connect("drag-motion", self.on_drag_motion)
        self.connect("drag-data-received", self.on_drag_data_received)
        #self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.get_selection().connect("changed", self.on_select_changed)
        self.set_headers_visible(False)
        #self.set_property("enable-tree-lines", True)
        # make treeview searchable
        self.set_search_column(1) 
        self.set_reorderable(True)        
        self.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK, [DROP_TREE_MOVE], gtk.gdk.ACTION_MOVE)
        self.enable_model_drag_dest(
            [DROP_TREE_MOVE, DROP_PAGE_MOVE], gtk.gdk.ACTION_MOVE)
        #self.set_fixed_height_mode(True)       

        # create the treeview column
        self.column = gtk.TreeViewColumn()
        self.column.set_clickable(False)
        self.append_column(self.column)

        # create a cell renderers
        self.cell_icon = gtk.CellRendererPixbuf()
        self.cell_text = gtk.CellRendererText()
        self.cell_text.connect("edited", self.on_edit_title)
        self.cell_text.set_property("editable", True)        

        # add the cells to column
        self.column.pack_start(self.cell_icon, False)
        self.column.pack_start(self.cell_text, True)

        # map cells to columns in treestore
        self.column.add_attribute(self.cell_icon, 'pixbuf', 0)
        self.column.add_attribute(self.cell_text, 'text', 1)
        
        self.icon = gdk.pixbuf_new_from_file(get_resource("images", "open.xpm"))
        #self.drag_source_set_icon_pixbuf(self.icon)
        

        
    
    #=============================================
    # drag and drop callbacks    
    
    
    def get_drag_node(self):
        model, source = self.get_selection().get_selected()
        source_path = model.get_path(source)
        return self.model.get_data(source_path)
    
    
    def on_drag_begin(self, widget, drag_context):
        pass
        #drag_context.drag_set_selection("tree")
        #drag_context.set_icon_pixbuf(self.icon, 0, 0)
        #self.stop_emission("drag-begin")
     
    
    def on_drag_motion(self, treeview, drag_context, x, y, eventtime):
        """Callback for drag motion.
           Indicate which drops are allowed"""
        
        # determine destination row   
        dest_row = treeview.get_dest_row_at_pos(x, y)
        
        if dest_row is None:
            return
        
        # get target info
        target_path, drop_position  = dest_row
        target_node = self.model.get_data(target_path)
        target = self.model.get_iter(target_path)
        new_path = compute_new_path(self.model, target, drop_position)
        
        # process node drops
        if "drop_node" in drag_context.targets:
        
            # get source
            source_widget = drag_context.get_source_widget()
            source_node = source_widget.get_drag_node()
            source_path = self.model.get_path_from_data(source_node)
            
            # determine if drag is allowed
            if self.drop_allowed(source_node, target_node, drop_position):
                treeview.enable_model_drag_dest([DROP_TREE_MOVE, DROP_PAGE_MOVE], gtk.gdk.ACTION_MOVE)
            else:
                treeview.enable_model_drag_dest([DROP_NO], gtk.gdk.ACTION_MOVE)
        
        elif "drop_selector" in drag_context.targets:
            # NOTE: this is until pages are in treeview
            
            # get source
            source_widget = drag_context.get_source_widget()
            source_node = source_widget.get_drag_node()
            source_path = self.model.get_path_from_data(source_node)
            
            # determine if drag is allowed
            if self.drop_allowed(source_node, target_node, drop_position) and \
               drop_position not in (gtk.TREE_VIEW_DROP_BEFORE,
                                     gtk.TREE_VIEW_DROP_AFTER):
                treeview.enable_model_drag_dest([DROP_TREE_MOVE, DROP_PAGE_MOVE], gtk.gdk.ACTION_MOVE)
            else:
                treeview.enable_model_drag_dest([DROP_NO], gtk.gdk.ACTION_MOVE)

        
    
    def on_drag_data_received(self, treeview, drag_context, x, y,
                              selection_data, info, eventtime):
            
         
        # determine destination row
        dest_row = treeview.get_dest_row_at_pos(x, y)
        if dest_row is None:
            drag_context.finish(False, False, eventtime)
            return
        
        # process node drops
        if "drop_node" in drag_context.targets or \
           "drop_selector" in drag_context.targets:
            
            # get target
            target_path, drop_position  = dest_row
            target = self.model.get_iter(target_path)
            target_node = self.model.get_data(target_path)
            new_path = compute_new_path(self.model, target, drop_position)
            
            # get source
            source_widget = drag_context.get_source_widget()
            source_node = source_widget.get_drag_node()
            source_path = self.model.get_path_from_data(source_node)
            
            
            # determine if drop is allowed
            if not self.drop_allowed(source_node, target_node, drop_position):
                drag_context.finish(False, False, eventtime)
                return
            
            # do tree move if source path is in our tree
            if source_path is not None:
                # get target and source iters
                source = self.model.get_iter(source_path)
                
                
                # record old and new parent paths
                old_parent = source_node.get_parent()
                old_parent_path = source_path[:-1]                
                new_parent_path = new_path[:-1]
                new_parent = self.model.get_data(new_parent_path)

                # perform move in notebook model
                source_node.move(new_parent, new_path[-1])

                # perform move in tree model
                self.handler_block(self.expanded_id)
                self.handler_block(self.collapsed_id)

                copy_row(treeview, self.model, source, target, drop_position)

                self.handler_unblock(self.expanded_id)
                self.handler_unblock(self.collapsed_id)
                
                # make sure to show new children
                if (drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or
                    drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
                    treeview.expand_row(target_path, False)
                
                drag_context.finish(True, True, eventtime)
            else:
                assert source_node.is_page()
                
                # NOTE: this is here until pages are in treeview
                if drop_position in (gtk.TREE_VIEW_DROP_BEFORE,
                                     gtk.TREE_VIEW_DROP_AFTER):
                    drag_context.finish(False, False, eventtime)
                else:
                    # process node move that is not in treeview
                    new_parent_path = new_path[:-1]
                    new_parent = self.model.get_data(new_parent_path)
                    source_node.move(new_parent, new_path[-1])
                    drag_context.finish(True, True, eventtime)
        else:
            drag_context.finish(False, False, eventtime)
            
    
        
    def drop_allowed(self, source_node, target_node, drop_position):
        """Determine if drop is allowed"""
        
        # source cannot be an ancestor of target
        ptr = target_node
        while ptr is not None:
            if ptr == source_node:
                return False
            ptr = ptr.get_parent()
        
        
        return not (target_node.get_parent() is None and \
                    (drop_position == gtk.TREE_VIEW_DROP_BEFORE or 
                     drop_position == gtk.TREE_VIEW_DROP_AFTER))
    
    #=============================================
    # gui callbacks    
    
    def on_row_expanded(self, treeview, it, path):
        self.model.get_data(path).set_expand(True)

    def on_row_collapsed(self, treeview, it, path):
        self.model.get_data(path).set_expand(False)

        
    def on_key_released(self, widget, event):
        if event.keyval == gdk.keyval_from_name("Delete"):
            self.on_delete_node()
            self.stop_emission("key-release-event")
            

    def on_edit_title(self, cellrenderertext, path, new_text):
        try:
            node = self.model.get_data(path)
            node.rename(new_text)
            
            self.model[path][1] = new_text
        except Exception, e:
            print e
            print "takenote: could not rename '%s'" % node.get_title()
    
    
    def on_select_changed(self, treeselect): 
        model, paths = treeselect.get_selected_rows()
        
        if len(paths) > 0 and self.on_select_node:
            self.on_select_node(self.model.get_data(paths[0]))
        return True
    
    
    def on_delete_node(self):
        
        model, it = self.get_selection().get_selected()
        node = self.model.get_data(model.get_path(it))
        parent = node.get_parent()
        
        if parent is not None:
            node.delete()
            self.update_node(parent)
        else:
            # warn
            print "Cannot delete notebook's toplevel directory"
        
        if self.on_select_node:
            self.on_select_node(None)
           
    
    #==============================================
    # actions
    
    def set_notebook(self, notebook):
        self.notebook = notebook
        
        if self.notebook is None:
            self.model.clear()
        
        else:
            root = self.notebook.get_root_node()
            self.add_node(None, root)
            
    
    
    def edit_node(self, node):
        path = self.model.get_path_from_data(node)
        self.set_cursor_on_cell(path, self.column, self.cell_text, 
                                         True)
        self.scroll_to_cell(path)

    
    def expand_node(self, node):
        path = self.model.get_path_from_data(node)
        self.expand_to_path(path)
        
    
    def add_node(self, parent, node):
        it = self.model.append(parent, [self.icon, node.get_title(), node])
        path = self.model.get_path(it)
        
        for child in node.get_children():
            self.add_node(it, child)
        
        if node.is_expanded():
            self.expand_to_path(self.model.get_path_from_data(node))
    
    
    def update_node(self, node):
        path = self.model.get_path_from_data(node)
        expanded = self.row_expanded(path)
        
        for child in self.model[path].iterchildren():
            self.model.remove(child.iter)
        
        it = self.model.get_iter(path)
        for child in node.get_children():
            self.add_node(it, child)
        
        self.expand_to_path(path)
        
