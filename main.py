import gi
import os
import sys
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Adw, Gio, GdkPixbuf
import glob
from rembg import remove
import io

class MyWindow(Adw.ApplicationWindow):
    def __init__(self, application, **kargs):
        super().__init__(application=application, **kargs)
        Adw.init()
        self.set_default_size(400, 300)
        self.set_title("rembg")

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        self.box.set_halign(Gtk.Align.CENTER)
        self.box.set_valign(Gtk.Align.CENTER)
        self.header = Adw.HeaderBar()

        # this is for a buttton with menu/about page
         
        action = Gio.SimpleAction.new("something", None)
        action.connect("activate", self.about)
        self.add_action(action)

        menu = Gio.Menu.new()
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

        self.tools = Adw.ToolbarView()
        self.tools.add_top_bar(self.header)
        self.tools.set_content(self.box)

        self.set_content(self.tools)
        
        self.head.add_css_class("big")
        self.popover.add_css_class("app")
        self.button.add_css_class("pill")
        self.box.add_css_class("app")

    def about(self, action, param):
        about = Adw.AboutWindow()
        about.add_css_class("app")
        about.set_application_name("rembg-gtk")
        about.set_version("1.0")
        about.set_developer_name("stainlesteel")
        about.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        about.set_comments("Remove a Background.")
        about.set_website("https://github.com/stainlesteel/rembg-gui")
        about.set_issue_url("https://github.com/stainlesteel/rembg-gui/issues")
        about.present()
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
        if fil:
            print("success!")
            fpath = fil.get_path()
            print(f"{fpath}")

            with open(fpath, 'rb') as f:
                ini = f.read()
            self.outi = remove(ini, return_bytes=True)
            opath = os.path.dirname(fpath)

            bmg = io.BytesIO(self.outi)

            self.cbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
            self.cbox.set_halign(Gtk.Align.CENTER)
            self.cbox.set_valign(Gtk.Align.CENTER)
            self.tools.set_content(self.cbox)

            fname = os.path.basename(fpath)
            split = os.path.splitext(fname)
            self.name = f"{split[0]}(no-bg).png"
            self.gex = Gtk.CenterBox()
            self.cbox.append(self.gex)

            self.img_txt = Gtk.Label(label=self.name)
            self.img_txt.set_wrap(True)
            self.img_txt.set_margin_start(20)
            self.img_txt.set_margin_top(10)
            self.gex.set_start_widget(self.img_txt)
            self.cbox.add_css_class("app")
            self.img_txt.add_css_class("mid")   
            
            self.bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

            self.copy = Gtk.Button.new_from_icon_name("edit-cut")
            self.copy.set_margin_end(20)
            self.bbox.append(self.copy)
            self.copy.set_margin_top(10)
            self.copy.connect("clicked", self.copt)
 
            self.save = Gtk.Button.new_from_icon_name("document-save")
            self.save.set_margin_end(20)
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
        fold = Gtk.FileDialog(title="Select Folder")

        fold.select_folder(self, None, self.buss)
    def buss(self, diag, result):
        dpath = diag.select_folder_finish(result).get_path()
        print("youre a blud")
        geuge = f"{dpath}/{self.name}"
        with open(geuge, 'wb') as o:
            o.write(self.outi)






            
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

        #adw_css_path = glob.glob('/usr/share/themes/Adwaita/gtk-4.0/gtk.css')
        #if adw_css_path:
        #    adw_gss = Gtk.CssProvider()
        #    adw_gss.load_from_path(adw_css_path[0])
        #    Gtk.StyleContext.add_provider_for_display(
        #        self.dis, adw_gss, Gtk.STYLE_PROVIDER_PRIORITY_THEME
        #    )


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

app = MyApp(application_id="com.example.GtkApplication")
app.run(sys.argv)
