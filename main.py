import gi
import os
import sys
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw, Gio, GdkPixbuf
import io
from PIL import UnidentifiedImageError
import threading
import time

class MyWindow(Adw.ApplicationWindow):
    def __init__(self, application, **kargs):
        super().__init__(application=application, **kargs)
        Adw.init()
        self.set_default_size(400, 300)
        self.set_title("rembg")

        self.splash = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        self.splash.set_valign(Gtk.Align.CENTER)
        self.splash.set_halign(Gtk.Align.CENTER)

        self.splash_title = Gtk.Label(label="Loading rembg...")
        self.splash_sub = Gtk.Label(label="The AI model for removing backgrounds is loading..., this will take 10-20 seconds.")

        self.splash.append(self.splash_title)
        self.splash.append(self.splash_sub)
        self.splash.add_css_class("app")
        self.splash_title.add_css_class("big")

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        self.box.set_halign(Gtk.Align.CENTER)
        self.box.set_valign(Gtk.Align.CENTER)
        self.header = Adw.HeaderBar()

        # this is for a buttton with menu/about page
         
        action = Gio.SimpleAction.new("something", None)
        action.connect("activate", self.about)
        self.add_action(action)

        sets = Gio.SimpleAction.new("settings", None)
        sets.connect("activate", self.sets)
        self.add_action(sets)

        menu = Gio.Menu.new()
        # below is for settings
        menu.append("Settings", "win.settings")
        menu.append("About rembg-gtk", "win.something") 

        self.popover = Gtk.PopoverMenu() 
        self.popover.set_menu_model(menu)

        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic") 
        self.header.pack_end(self.hamburger)

        # menu/about ends here
        self.title = Adw.WindowTitle(title="rembg") 
        self.header.set_title_widget(self.title)

        self.head = Gtk.Label(label="rembg")
        self.subtitle = Gtk.Label(label="Remove a Background")

        self.box.append(self.head)
        self.box.append(self.subtitle)

        self.button = Gtk.Button.new_with_label('Continue')
        self.button.connect("clicked", self.file)
        self.box.append(self.button)
        
        self.mask_b = Gtk.CheckButton(label='Get only mask')
        self.mask_b.connect('toggled', self.mask)
        self.mask_b.set_valign(Gtk.Align.CENTER)
        self.mask_b.set_halign(Gtk.Align.CENTER)
        self.box.append(self.mask_b)

        self.tools = Adw.ToolbarView()
        self.tools.add_top_bar(self.header)
        self.tools.set_content(self.splash)

        self.set_content(self.tools)
        
        self.head.add_css_class("big")
        self.header.add_css_class("app")
        self.popover.add_css_class("app")
        self.button.add_css_class("pill")
        self.box.add_css_class("app")
        
        self.m_state = False

    def sets(self, action, param):
        def theme(crow, _):
            sm = self.get_application().get_style_manager()
            index = crow.get_selected()
            item = crow.get_model().get_item(index)
            
            if item.get_string() == "Dark":
                sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                crow.set_selected(2)
            elif item.get_string() == "Light":
                sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                crow.set_selected(1)
            else:
                sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
                crow.set_selected(0)

        diag = Adw.PreferencesDialog()

        sets = Adw.PreferencesPage()
        sets.set_title("Settings")

        s_group = Adw.PreferencesGroup()
        s_group.set_title("Settings")

        slist = Gtk.StringList.new(["Default","Light", "Dark"])

        crow = Adw.ComboRow()
        crow.set_title("Colour Theme")
        crow.set_model(slist)
        crow.set_use_subtitle(True)
        crow.connect("notify::selected", theme)

        s_group.add(crow)
        sets.add(s_group)
        diag.add(sets)
        crow.add_css_class("app")
        diag.add_css_class("app")
        diag.present()

    def about(self, action, param):
        about = Adw.AboutWindow(
          application_name="rembg-gtk",
          version="1.0.3",
          developer_name="stainlesteel",
          license_type=Gtk.License.GPL_3_0,
          website="https://github.com/stainlesteel/rembg-gui",
          issue_url="https://github.com/stainlesteel/rembg-gui/issues",
          copyright="2025 stainlesteel, All Rights Reserved",
            
        )
        about.add_css_class("app")
        about.present()
    def mask(self, check):
        if self.mask_b.props.active:
            self.m_state = True
            self.error("Info", "This will heavily distort the image and isn't used for removing backgrounds.")
            print("mask is on")
        else:
            self.m_state = False
            print("mask is off")
    def loading(self):
        threading.Thread(target=self.rembg_start, daemon=True).start()
    def rembg_start(self):
        import rembg
        self.session = rembg.new_session()
        # hacky!
        globals()['rembg'] = rembg
        self.tools.set_content(self.box)
    def file(self, par):
      self.diag = Gtk.FileDialog(title="Open Image")
      self.diag.open(
            self,
            None,
            self.on_response
        )
    def on_response(self, diag, response):
        print(response)
        fil = self.diag.open_finish(response)
        try:
           if fil:
               fpath = fil.get_path()
               extensions = os.path.splitext(fpath)
               if extensions[1] == ".iso":
                    iso = self.error("Failure", "Did you just try to import an ISO image?")
                    # this works because the connecting below brings an error,
                    # and stops rembg from using an iso image
                    iso.connect("response", lambda d, r: d.destroy())
                    pass
               print(f"{fpath}")

               with open(fpath, 'rb') as f:
                   ini = f.read()
               if self.m_state:
                    self.outi = rembg.remove(ini, return_bytes=True, session=self.session, only_mask=True)
               else:
                    self.outi = rembg.remove(ini, return_bytes=True, session=self.session)
               opath = os.path.dirname(fpath)

               bmg = io.BytesIO(self.outi)

               self.cbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
               self.cbox.set_halign(Gtk.Align.CENTER)
               self.cbox.set_valign(Gtk.Align.CENTER)
               self.tools.set_content(self.cbox)

               fname = os.path.basename(fpath)
               split = os.path.splitext(fname)
               self.name = f"{split[0]}(no-bg).png"
               self.gex = Gtk.CenterBox()
               self.cbox.append(self.gex)

               self.img_txt = Gtk.EditableLabel()
               self.img_txt.set_text(f"{self.name}")
               self.img_txt.set_hexpand(True)
               self.img_txt.set_width_chars(20)
               self.img_txt.set_margin_start(20)
               self.img_txt.set_margin_top(10)
               self.gex.set_start_widget(self.img_txt)
               self.cbox.add_css_class("app")
               self.img_txt.add_css_class("mid")   
               
               self.bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

               self.copy = Gtk.Button.new_from_icon_name("edit-cut")
               self.copy.set_margin_end(20)
               self.copy.add_css_class("circular")
               self.bbox.append(self.copy)
               self.copy.set_margin_top(10)
               self.copy.connect("clicked", self.copt)
 
               self.save = Gtk.Button.new_from_icon_name("document-save")
               self.save.set_margin_end(20)
               self.save.add_css_class("circular")
               self.bbox.append(self.save)
               self.save.set_margin_top(10)
               self.save.connect("clicked", self.fifw)
               self.gex.set_end_widget(self.bbox)

               raw = bmg.getvalue()

               img = Gio.MemoryInputStream.new_from_data(raw)
               self.pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(img, 400, 400, True)
               print(f"image: {self.pixbuf.get_width()}x{self.pixbuf.get_height()}")

               self.pic = Gtk.Picture()
               self.pic.set_hexpand(True)
               self.pic.set_vexpand(True)

               self.pic.set_pixbuf(self.pixbuf)
               self.cbox.append(self.pic)
               self.back = Gtk.Button.new_from_icon_name("go-previous-symbolic")
               self.back.set_visible(True)
               self.header.pack_start(self.back)
               self.back.connect("clicked", self.rerun)
        except UnidentifiedImageError:
            self.error("Failure", "Python couldn't identify this as an image.")
    def error(self, text, secondary):
            info = Gtk.MessageDialog(
                   transient_for=self,
                   modal=True,
                   buttons=Gtk.ButtonsType.OK,
                   text=text,
                   secondary_text=secondary,
            )
            info.add_css_class("app")
            info.present()
            info.connect("response", lambda d, r: d.destroy())


    def rerun(self, button):
        self.back.set_visible(False)
        self.tools.set_content(self.box)

    def copt(self, button):
        clip = Gdk.Display.get_default().get_clipboard()
        
        self.toastlay = Adw.ToastOverlay()
        self.cbox.append(self.toastlay)

        try:
            forms = Gdk.ContentProvider.new_for_value(self.pixbuf)

            clip.set_content(forms)

            toast = Adw.Toast.new("Copied to clipboard")
            self.toastlay.add_toast(toast)
        except:
            toast = Adw.Toast.new(" failed to copy to clipboard")
            self.toastlay.add_toast(toast)


    def fifw(self, button):
        fold = Gtk.FileDialog.new()
        fold.set_title(title="Select Folder")
        fold.set_modal(modal=True)

        fold.select_folder(self, None, self.buss)
    def buss(self, diag, result):
        dpath = diag.select_folder_finish(result).get_path()
        print("youre a blud")
        try:
           geuge = f"{dpath}/{self.img_txt.get_text()}"
           with open(geuge, 'wb') as o:
               o.write(self.outi)
        except IsADirectoryError:
            self.error("Failure", "That is a directory.")
           
def on_activate(app):
    # Create window
    win = MyWindow(application=app)
    win.present()
    
class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        gss = Gtk.CssProvider()
        self.dis = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            self.dis, gss, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        cfile = os.path.join(os.path.dirname(__file__), "style.css")
        gss.load_from_path(cfile)
        Gtk.StyleContext.add_provider_for_display(
            self.dis, gss, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MyWindow(self, title="rembg-gtk")
            win.present()
            win.loading()

app = MyApp(application_id="com.github.stainlesteel.rembg-gui")
app.run(sys.argv)
