import tkinter as tk
from tkinter import ttk, filedialog
import uuid
from view.colors import text_color, bg_color, edit_color, default_color
from util.custom_tks import TextAware, ScrollableFrame
from util.react import *
from tkinter.scrolledtext import ScrolledText
from view.styles import textbox_config
from view.icons import Icons
import time
from util.util_tk import create_side_label, create_label, Entry, create_button, create_slider, create_combo_box, create_checkbutton
import os
from PIL import Image, ImageTk

buttons = {'go': 'arrow-green',
           'edit': 'edit-blue',
           'attach': 'leftarrow-lightgray',
           'archive': 'archive-yellow',
           'close': 'minus-lightgray',
           'delete': 'trash-red',
           'append': 'up-lightgray'}

icons = Icons()


class EvalCode:
    def __init__(self, init_text, callbacks):
        self.code_textbox = None
        self.label = None
        self.init_text = init_text
        self.callbacks = callbacks

    def body(self, master):
        self.label = tk.Label(master, text='**** HUMANS ONLY ****', bg=default_color(), fg=text_color())
        self.label.pack(side=tk.TOP, fill=tk.X)
        self.code_textbox = ScrolledText(master, height=2)
        self.code_textbox.pack(fill=tk.BOTH, expand=True)
        self.code_textbox.configure(**textbox_config(bg='black', font='Monaco'))
        self.code_textbox.insert(tk.INSERT, self.init_text)
        self.code_textbox.focus()

    def apply(self):
        code = self.code_textbox.get("1.0", 'end-1c')
        self.callbacks["Run"]["prev_cmd"] = code
        self.callbacks["Eval"]["callback"](code_string=code)


class Windows():
    def __init__(self, buttons):
        self.windows_pane = None
        self.windows = {}
        self.master = None
        self.scroll_frame = None
        self.buttons = buttons

    def body(self, master):
        self.master = master
        self.scroll_frame = ScrollableFrame(self.master)
        self.scroll_frame.pack(expand=True, fill="both")
        self.windows_pane = tk.PanedWindow(self.scroll_frame.scrollable_frame, orient='vertical')
        self.windows_pane.pack(side='top', fill='both', expand=True)

    def open_window(self, text):
        window_id = str(uuid.uuid1())
        self.windows[window_id] = {'frame': ttk.Frame(self.windows_pane, borderwidth=1)}
        tk.Grid.columnconfigure(self.windows[window_id]['frame'], 1, weight=1)
        for i in range(len(self.buttons)):
            tk.Grid.rowconfigure(self.windows[window_id]['frame'], i, weight=1)
        self.windows_pane.add(self.windows[window_id]['frame'], height=100)
        self.windows[window_id]['textbox'] = TextAware(self.windows[window_id]['frame'], bd=3, undo=True)
        self.windows[window_id]['textbox'].grid(row=0, column=1, rowspan=len(self.buttons), pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        self.windows[window_id]['textbox'].configure(**textbox_config(bg=edit_color(), pady=1, spacing2=3, spacing1=4))
        self.windows[window_id]['textbox'].insert("1.0", text)

        for i, button in enumerate(self.buttons):
             self.draw_button(i, window_id, button)

    def draw_button(self, row, window_id, button):
        self.windows[window_id][button] = tk.Label(self.windows[window_id]['frame'], image=icons.get_icon(buttons[button]), bg=bg_color(), cursor='hand2')
        self.windows[window_id][button].grid(row=row, column=2, padx=5)
        if button == 'close':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _id=window_id: self.close_window(_id))

    def close_window(self, window_id):
        self.remove_window(window_id)

    def remove_window(self, window_id):
        self.windows_pane.forget(self.windows[window_id]['frame'])
        self.windows[window_id]['frame'].destroy()
        del self.windows[window_id]
    
    def clear_windows(self):
        # self.windows_pane.pack_forget()
        # self.windows_pane.destroy()
        # self.windows_pane = tk.PanedWindow(self.scroll_frame.scrollable_frame, orient='vertical')
        # self.windows_pane.pack(side='top', fill='both', expand=True)
        # self.windows = {}
        for window in self.windows:
            self.remove_window(window)

class NodeWindows(Windows):
    def __init__(self, callbacks, buttons, buttons_visible=True, nav_icons_visible=True, editable=True, init_height=1):
        self.callbacks = callbacks
        self.blacklist = []
        self.whitelist = []
        self.buttons_visible = buttons_visible
        self.nav_icons_visible = nav_icons_visible
        self.editable = editable
        self.init_height = init_height
        Windows.__init__(self, buttons)

    def open_window(self, node, insert='end'):
        if node['id'] in self.windows:
            return
        self.windows[node['id']] = {'frame': ttk.Frame(self.windows_pane, borderwidth=1)}
        self.windows[node['id']]['node'] = node
        tk.Grid.columnconfigure(self.windows[node['id']]['frame'], 1, weight=1)
        for i in range(len(self.buttons)):
            tk.Grid.rowconfigure(self.windows[node['id']]['frame'], i, weight=1)
        # TODO adaptive init height
        self.windows_pane.add(self.windows[node['id']]['frame'], height=100)
        #self.windows_pane.paneconfig(self.windows[node['id']]['frame'])
        # if insert == 'end':
        #     self.windows_pane.add(self.windows[node['id']]['frame'], weight=1)
        # else:
        #     self.windows_pane.insert(0, self.windows[node['id']]['frame'], weight=1)
        self.windows[node['id']]['textbox'] = TextAware(self.windows[node['id']]['frame'], bd=3, undo=True)
        self.windows[node['id']]['textbox'].grid(row=0, column=1, rowspan=len(self.buttons), pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
        self.windows[node['id']]['textbox'].configure(**textbox_config(bg=edit_color()))
        # bind click event to goto node
        self.windows[node['id']]['textbox'].insert("1.0", node["text"])

        self.windows[node['id']]['textbox'].bind("<FocusOut>", lambda event, _id=node['id']: self.save_edits(_id))
        self.windows[node['id']]['textbox'].bind("<Button-1>", lambda event, _id=node['id']: self.window_clicked(_id))

        if not self.editable:
            self.edit_off(node['id'])
        else:
            self.edit_on(node['id'])
        if self.buttons_visible:
            for i, button in enumerate(self.buttons):
                self.draw_button(i, node['id'], button)
        if self.nav_icons_visible:
            self.draw_nav_icon(node['id'])

    def fix_heights(self):
        for i in range(len(self.windows) - 1):
            self.windows_pane.update_idletasks()
            self.windows_pane.sashpos(i, 100 * (i+1))

    def draw_nav_icon(self, window_id):
        icon = self.callbacks["Nav icon"]["callback"](node=self.windows[window_id]['node'])
        self.windows[window_id]['icon'] = tk.Label(self.windows[window_id]['frame'], image=icon, bg=bg_color())
        self.windows[window_id]['icon'].grid(row=0, column=0, rowspan=len(self.buttons))

    def draw_button(self, row, window_id, button):
        self.windows[window_id][button] = tk.Label(self.windows[window_id]['frame'], image=icons.get_icon(buttons[button]), bg=bg_color(), cursor='hand2')
        self.windows[window_id][button].grid(row=row, column=2, padx=5)
        if button == 'go':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _id=window_id: self.goto_node(_id))
        elif button == 'edit':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _id=window_id: self.toggle_edit(_id))
        elif button == 'attach':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _node=self.windows[window_id]['node']: self.attach_node(_node))
        elif button == 'archive':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _node=self.windows[window_id]['node']: self.archive_node(_node))
        elif button == 'close':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _id=window_id: self.close_window(_id))
        elif button == 'delete':
            self.windows[window_id][button].bind("<Button-1>", lambda event, _node=self.windows[window_id]['node']: self.delete_node(_node))

    def hide_buttons(self):
        for window_id in self.windows:
            for button in self.buttons:
                self.windows[window_id][button].grid_remove()

    def close_window(self, window_id):
        Windows.close_window(self, window_id)
        self.blacklist.append(window_id)

    def window_clicked(self, window_id):
        if self.windows[window_id]['textbox'].cget("state") == 'disabled':
            self.goto_node(window_id)

    def goto_node(self, node_id):
        node = self.windows[node_id]['node']
        self.callbacks["Select node"]["callback"](node=node)

    def save_edits(self, window_id):
        # why does this cause all windows to reload?
        node = self.windows[window_id]['node']
        new_text = self.windows[window_id]['textbox'].get("1.0", 'end-1c')
        self.callbacks["Update text"]["callback"](node=node, text=new_text)

    def save_windows(self):
        for window_id in self.windows:
            self.save_edits(window_id)

    def edit_off(self, window_id):
        if self.windows[window_id]['textbox'].cget("state") == "normal":
            self.windows[window_id]['textbox'].configure(state='disabled', 
                                                        background=bg_color(),
                                                        relief=tk.RAISED)
            self.save_edits(window_id)

    def edit_on(self, window_id):
        if self.windows[window_id]['textbox'].cget("state") == "disabled":
            self.windows[window_id]['textbox'].configure(state='normal', 
                                                         background=edit_color(),
                                                         relief=tk.SUNKEN)
        

    def toggle_edit(self, window_id):
        if self.windows[window_id]['textbox'].cget('state') == 'disabled':
            self.edit_on(window_id)
        else:
            self.edit_off(window_id)

    def focus_textbox(self, window_id):
        self.windows[window_id]['textbox'].focus_set()

    def attach_node(self, node):
        pass

    def archive_node(self, node):
        self.callbacks["Tag"]["callback"](node=node, tag="archived")

    def delete_node(self, node):
        #self.remove_window(node['id'])
        self.callbacks["Delete"]["callback"](node=node)

    def update_windows(self, nodes, insert='end'):
        new_windows, deleted_windows = react_changes(old_components=self.windows.keys(), new_components=[node['id'] for node in nodes])
        for window_id in deleted_windows:
            self.remove_window(window_id)
        new_nodes = [node for node in nodes if node['id'] in new_windows and node['id'] not in self.blacklist]
        for node in new_nodes:
            self.open_window(node, insert=insert)
        #self.fix_heights()

    def update_text(self):
        for window_id in self.windows:
            changed_edit = False
            if self.windows[window_id]['textbox'].cget('state') == 'disabled':
                self.windows[window_id]['textbox'].configure(state='normal')
                changed_edit = True
            self.windows[window_id]['textbox'].delete("1.0", "end")
            self.windows[window_id]['textbox'].insert("1.0", self.callbacks["Text"]["callback"](node_id=window_id))
            if changed_edit:
                self.windows[window_id]['textbox'].configure(state='disabled')


class Thumbnails:
    def __init__(self, selection_callback):
        self.selection_callback = selection_callback
        self.thumbnails = {}
        self.scroll_frame = None
        self.master = None
        self.selected_file = None

    def body(self, master, height=400):
        self.master = master
        self.scroll_frame = ScrollableFrame(master, width=110, height=height)
        self.scroll_frame.pack(side='top', fill='both', expand=True)

    def get_thumbnail(self, filename):
        # open image
        img = Image.open(filename)
        # resize
        img.thumbnail((100, 100), Image.ANTIALIAS)
        # convert to tkinter image
        img = ImageTk.PhotoImage(img)
        return img

    def add_thumbnail(self, filename):
        if filename not in self.thumbnails:
            image = self.get_thumbnail(filename)
            self.thumbnails[filename] = tk.Label(self.scroll_frame.scrollable_frame, image=image,
                                                 bg="white", cursor='hand2', width=100, bd=5)
            self.thumbnails[filename].image = image
            self.thumbnails[filename].bind("<Button-1>", lambda event, filename=filename: self.select(filename=filename))
            self.thumbnails[filename].pack(side='top', pady=5, padx=5)
    
    def remove_thumbnail(self, filename):
        if filename in self.thumbnails:
            self.thumbnails[filename].destroy()
            del self.thumbnails[filename]

    def clear(self):
        for filename in self.thumbnails:
            self.thumbnails[filename].destroy()
        self.thumbnails = {}

    def update_thumbnails(self, image_files):
        new_windows, deleted_windows = react_changes(old_components=self.thumbnails.keys(), new_components=image_files)
        for filename in deleted_windows:
            self.remove_thumbnail(filename)
        for filename in new_windows:
            self.add_thumbnail(filename)
        self.selected_file = list(self.thumbnails.keys())[-1]

    def select(self, filename, *args):
        self.set_selection(filename)
        self.selection_callback(filename=filename)

    def set_selection(self, filename):
        self.thumbnails[self.selected_file].configure(relief="flat")
        self.selected_file = filename
        self.thumbnails[filename].configure(relief="sunken")

    def scroll_to_selected(self):
        pass

    def scroll_to_end(self):
        pass


class Multimedia:
    def __init__(self, callbacks, state):
        self.img = None
        self.state = state
        self.caption = None
        self.viewing = None
        self.master = None
        self.selected_node_text = None
        self.next_button = None
        self.prev_button = None
        self.move_up_button = None
        self.move_down_button = None
        self.delete_button = None
        self.caption_button = None
        self.n = 0
        self.thumbnails = None
        self.thumbnails_frame = None
        self.callbacks = callbacks
        self.state = state
    
    def body(self, master):
        self.master = master
        #button = create_button(master, "Add media", self.add_media)
        #button.grid(row=1, column=1, sticky='w')
        #tk.Grid.rowconfigure(master, 0, weight=1)
        tk.Grid.rowconfigure(master, 2, weight=1)
        tk.Grid.columnconfigure(master, 1, weight=1)
        self.thumbnails_frame = tk.Frame(self.master)
        self.thumbnails_frame.grid(row=0, column=3)
        self.thumbnails = Thumbnails(selection_callback=self.select_file)
        self.thumbnails.body(self.thumbnails_frame)
        self.populate_thumbnails()
        self.create_image()
        self.create_buttons()
        self.refresh()

    def refresh(self):
        self.populate_thumbnails()
        self.display_image()
        self.set_buttons()
        self.set_node_text()

    def populate_thumbnails(self):
        self.thumbnails.clear()
        if 'multimedia' in self.state.selected_node:
            self.thumbnails.update_thumbnails([media['file'] for media in self.state.selected_node['multimedia']])

    def num_media(self):
        if 'multimedia' in self.state.selected_node:
            return len(self.state.selected_node['multimedia'])
        else:
            return 0

    def create_image(self):
        img = tk.PhotoImage(file='static/media/black.png')
        self.img = tk.Label(self.master, image=img, bg="white")
        self.img.grid(row=0, column=1)
        self.caption = tk.Label(self.master, text='', bg=default_color())
        self.caption.grid(row=1, column=0, columnspan=3)
        self.selected_node_text = TextAware(self.master)
        self.selected_node_text.config(state='disabled', **textbox_config())
        self.selected_node_text.grid(row=2, column=0, columnspan=4)
        #self.viewing = tk.Label(self.master, text=f"{self.n + 1} / {self.num_media()}", bg=default_color())
        #self.viewing.grid(row=3, column=1)

    def create_buttons(self):
        self.prev_button = tk.Label(self.master, image=icons.get_icon("left-white", size=25), bg=bg_color(), cursor="hand2")
        self.prev_button.grid(row=0, column=0)
        self.prev_button.bind("<Button-1>", lambda event: self.traverse(1))
        self.next_button = tk.Label(self.master, image=icons.get_icon("right-white", size=25), bg=bg_color(), cursor="hand2")
        self.next_button.grid(row=0, column=2)
        self.next_button.bind("<Button-1>", lambda event: self.traverse(-1))
        # self.next_button = create_button(self.master, "Next", lambda: self.traverse(1))
        # self.next_button.grid(row=4, column=1, sticky='e')
        # self.prev_button = create_button(self.master, "Prev", lambda: self.traverse(-1))
        # self.prev_button.grid(row=4, column=1, sticky='w')
        # self.move_up_button = create_button(self.master, "Move >", lambda: self.shift(1))
        # self.move_up_button.grid(row=5, column=1, sticky='e')
        # self.move_down_button = create_button(self.master, "< Move", lambda: self.shift(-1))
        # self.move_down_button.grid(row=5, column=1, sticky='w')
        # self.caption_button = create_button(self.master, "Change caption", self.change_caption)
        # self.caption_button.grid(row=5, column=1)
        # self.caption_button.config(width=15)
        # self.delete_button = create_button(self.master, "Delete", self.delete_media)
        # self.delete_button.grid(row=1, column=1, sticky='e')

    def set_buttons(self):
        if not self.next_button:
            self.create_buttons()
        if self.num_media() > 0:
            self.next_button.grid()
            self.prev_button.grid()
            # self.next_button["state"] = "normal"
            # self.prev_button["state"] = "normal"
            # self.move_up_button["state"] = "normal"
            # self.move_down_button["state"] = "normal"
            # self.delete_button["state"] = "normal"
            # self.caption_button["state"] = "normal"
        else:
            self.next_button.grid_remove()
            self.prev_button.grid_remove()
            # self.next_button["state"] = "disabled"
            # self.prev_button["state"] = "disabled"
            # self.move_up_button["state"] = "disabled"
            # self.move_down_button["state"] = "disabled"
            # self.delete_button["state"] = "disabled"
            # self.caption_button["state"] = "disabled"

    def set_node_text(self):
        self.selected_node_text.config(state='normal')
        self.selected_node_text.delete("1.0", "end")
        self.selected_node_text.insert("1.0", self.callbacks["Text"]["callback"](node_id=self.state.selected_node_id))
        self.selected_node_text.config(state='disabled')

    def change_caption(self):
        if self.num_media() > 0:
            self.state.selected_node['multimedia'][self.n]['caption'] = 'new caption'
            self.display_image()

    # def repair_type(self):
    #     if self.num_media() > 0:
    #         new_multimedia = []
    #         for media in self.state.selected_node['multimedia']:
    #             if isinstance(media, str):
    #                 new_multimedia.append({'file': media, 'caption': ''})
    #             elif isinstance(media, dict):
    #                 new_multimedia.append(media)
    #             else:
    #                 print('error invalid type')
    #         self.state.selected_node['multimedia'] = new_multimedia

    def display_image(self):
        if not self.img:
            self.create_image()
        if self.num_media() > 0:
            try:
                #self.repair_type()
                img = tk.PhotoImage(file=self.state.selected_node['multimedia'][self.n]['file'])
                caption = self.state.selected_node['multimedia'][self.n]['caption']
            except tk.TclError:
                return
            self.img.configure(image=img)
            self.img.image = img
            self.caption.configure(text=caption)
            #self.viewing.configure(text=f"{self.n + 1} / {self.num_media()}")
        else:
            try:
                self.img.image.blank()
                self.img.image = None
                self.caption.configure(text='')
            except AttributeError:
                return

    def add_media(self):
        tree_dir = self.state.tree_dir()
        # if media folder not in tree directory, create it
        if not os.path.isdir(tree_dir + '/media'):
            os.mkdir(tree_dir + '/media')
        options = {
            'initialdir': tree_dir + '/media',
        }
        filenames = filedialog.askopenfilenames(**options)
        if not filenames:
            return
        self.callbacks["Add multimedia"]["callback"](filenames=filenames)
        self.n = self.num_media() - 1
        self.display_image()
        self.set_buttons()

    def delete_media(self):
        del self.state.selected_node['multimedia'][self.n]
        if self.n != 0:
            self.n -= 1
        self.populate_thumbnails()
        self.display_image()
        self.set_buttons()

    def traverse(self, interval):
        self.n = (self.n + interval) % self.num_media()
        self.display_image()
        self.set_buttons()

    def shift(self, interval):
        new_index = (self.n + interval) % self.num_media()
        self.state.selected_node['multimedia'][self.n], self.state.selected_node['multimedia'][new_index] = self.state.selected_node['multimedia'][new_index],\
                                                                              self.state.selected_node['multimedia'][self.n]
        self.n = new_index
        self.display_image()
        self.set_buttons()

    def select_file(self, filename, *args):
        filename_list = [media['file'] for media in self.state.selected_node['multimedia']]
        self.n = filename_list.index(filename)
        self.display_image()
        self.set_buttons()
        