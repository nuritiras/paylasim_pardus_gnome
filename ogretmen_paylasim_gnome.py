#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

OKUL_ADI = "Ticaret ve Sanayi Odası TMTAL"
LOGO_YOLU = "/usr/share/pixmaps/okul-logo.png"  # İsterseniz logo koyabilirsiniz


class OgretmenWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Öğretmen Paylaşımı Kurucu (GNOME)")
        self.set_default_size(640, 420)

        if os.geteuid() != 0:
            # root değilse alt statüste uyarı
            print("Bu uygulama root yetkisiyle çalıştırılmalıdır (pkexec).")
        
        self.build_ui()

    def build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.set_content(outer)

        # Üst başlık
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Öğretmen Paylaşımı Kurucu"))
        header.set_subtitle(f"{OKUL_ADI} – GNOME/GTK4")
        self.set_titlebar(header)

        # İç kutu
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.append(main_box)

        # Okul bilgisi + logo
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.append(top_box)

        if os.path.exists(LOGO_YOLU):
            img = Gtk.Image.new_from_file(LOGO_YOLU)
            top_box.append(img)

        lbl_info = Gtk.Label(
            label="Windows sunucudaki 'öğretmen' paylaşımını otomatik bağlar\n"
                  "ve tüm kullanıcıların masaüstünde 'Öğretmen Paylaşımı' kısayolu oluşturur."
        )
        lbl_info.set_xalign(0.0)
        lbl_info.set_wrap(True)
        top_box.append(lbl_info)

        # Form alanı (grid)
        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        main_box.append(grid)

        row = 0

        def add_label(text, row):
            lbl = Gtk.Label(label=text)
            lbl.set_xalign(1.0)
            grid.attach(lbl, 0, row, 1, 1)

        # Sunucu IP / ad
        self.entry_server = Gtk.Entry()
        self.entry_server.set_text("10.10.10.5")
        add_label("Sunucu IP / Ad:", row)
        grid.attach(self.entry_server, 1, row, 1, 1)
        row += 1

        # Paylaşım adı
        self.entry_share = Gtk.Entry()
        self.entry_share.set_text("ogretmen")
        add_label("Paylaşım Adı:", row)
        grid.attach(self.entry_share, 1, row, 1, 1)
        row += 1

        # Mount noktası
        self.entry_mount = Gtk.Entry()
        self.entry_mount.set_text("/mnt/ogretmen")
        add_label("Mount Noktası:", row)
        grid.attach(self.entry_mount, 1, row, 1, 1)
        row += 1

        # Windows kullanıcı adı
        self.entry_user = Gtk.Entry()
        self.entry_user.set_text("ogrt")
        add_label("Windows Kullanıcı Adı:", row)
        grid.attach(self.entry_user, 1, row, 1, 1)
        row += 1

        # Windows şifre
        self.entry_pass = Gtk.Entry()
        self.entry_pass.set_visibility(False)
        self.entry_pass.set_invisible_char("•")
        add_label("Windows Şifre:", row)
        grid.attach(self.entry_pass, 1, row, 1, 1)
        row += 1

        # Domain / workgroup
        self.entry_domain = Gtk.Entry()
        self.entry_domain.set_text("WORKGROUP")
        add_label("Domain / Workgroup:", row)
        grid.attach(self.entry_domain, 1, row, 1, 1)
        row += 1

        note = Gtk.Label(
            label="Not: Bu ayarlar tüm GNOME kullanıcıları için geçerlidir.\n"
                  "Öğretmenler tekrar giriş yaptığında masaüstlerinde kısayol görünür."
        )
        note.set_xalign(0.0)
        note.set_wrap(True)
        main_box.append(note)

        # Alt butonlar + durum etiketi
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.append(bottom_box)

        self.status_label = Gtk.Label(label="Hazır.")
        self.status_label.set_xalign(0.0)
        bottom_box.append(self.status_label)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        bottom_box.append(btn_box)

        self.btn_apply = Gtk.Button(label="Ayarları Uygula")
        self.btn_apply.connect("clicked", self.on_apply_clicked)
        btn_box.append(self.btn_apply)

        btn_close = Gtk.Button(label="Kapat")
        btn_close.connect("clicked", lambda w: self.get_application().quit())
        btn_box.append(btn_close)

    def set_status(self, text):
        self.status_label.set_text(text)
        print(text)

    def on_apply_clicked(self, button):
        server = self.entry_server.get_text().strip()
        share = self.entry_share.get_text().strip()
        mount = self.entry_mount.get_text().strip()
        user = self.entry_user.get_text().strip()
        passwd = self.entry_pass.get_text().strip()
        domain = self.entry_domain.get_text().strip() or "WORKGROUP"

        if not all([server, share, mount, user, passwd]):
            self.set_status("Lütfen tüm alanları doldurun.")
            return

        self.btn_apply.set_sensitive(False)
        try:
            self.apply_system_settings(server, share, mount, user, passwd, domain)
            self.set_status("İşlem tamamlandı. Öğretmenler tekrar giriş yaptığında kısayol görünecek.")
        except Exception as e:
            self.set_status(f"Hata: {e}")
        finally:
            self.btn_apply.set_sensitive(True)

    def apply_system_settings(self, server, share, mount, user, passwd, domain):
        # 1) mount klasörü
        os.makedirs(mount, exist_ok=True)

        # 2) kimlik bilgisi
        cred_path = f"/etc/samba/creds-{share}"
        with open(cred_path, "w", encoding="utf-8") as f:
            f.write(f"username={user}\npassword={passwd}\ndomain={domain}\n")
        os.chmod(cred_path, 0o600)

        # 3) fstab yedek + düzenleme
        backup_name = f"/etc/fstab.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copy("/etc/fstab", backup_name)

        marker_start = "# OGRETMEN_PAYLASIM_BASLA"
        marker_end = "# OGRETMEN_PAYLASIM_BITIR"

        new_lines = []
        if os.path.exists("/etc/fstab"):
            with open("/etc/fstab", "r", encoding="utf-8") as f:
                skip = False
                for line in f:
                    if marker_start in line:
                        skip = True
                        continue
                    if marker_end in line:
                        skip = False
                        continue
                    if not skip:
                        new_lines.append(line)

        new_lines.append("\n")
        new_lines.append(f"{marker_start}\n")
        new_lines.append(f"//{server}/{share}  {mount}  cifs  credentials={cred_path},"
                         f"iocharset=utf8,uid=1000,gid=1000,file_mode=0777,dir_mode=0777,"
                         f"noperm,nofail  0  0\n")
        new_lines.append(f"{marker_end}\n")

        with open("/etc/fstab", "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # 4) mount -a testi
        res = subprocess.run(["mount", "-a"], text=True, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f"mount -a başarısız.\nSTDERR: {res.stderr}\nYedek: {backup_name}")

        # 5) kısayol scripti
        kisayol_script = "/usr/local/bin/ogretmen-kisayol.sh"
        script_content = f"""#!/bin/bash
MOUNT_DIR="{mount}"

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null)"

if [ -z "$DESKTOP_DIR" ]; then
    if [ -d "$HOME/Masaüstü" ]; then
        DESKTOP_DIR="$HOME/Masaüstü"
    elif [ -d "$HOME/Desktop" ]; then
        DESKTOP_DIR="$HOME/Desktop"
    else
        DESKTOP_DIR="$HOME/Masaüstü"
        mkdir -p "$DESKTOP_DIR"
    fi
fi

mkdir -p "$DESKTOP_DIR"

SHORTCUT="$DESKTOP_DIR/ogretmen-paylasim.desktop"

cat <<EOD > "$SHORTCUT"
[Desktop Entry]
Type=Application
Name=Öğretmen Paylaşımı
Icon=folder-remote
Exec=xdg-open "{mount}"
Terminal=false
EOD

chmod +x "$SHORTCUT"
"""
        with open(kisayol_script, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(kisayol_script, 0o755)

        # 6) GNOME autostart
        autostart_dir = "/etc/xdg/autostart"
        os.makedirs(autostart_dir, exist_ok=True)
        autostart_file = os.path.join(autostart_dir, "ogretmen-kisayol.desktop")
        desktop_content = """[Desktop Entry]
Type=Application
Name=Öğretmen Paylaşımı Kısayol Oluşturucu
Exec=/usr/local/bin/ogretmen-kisayol.sh
OnlyShowIn=GNOME;
NoDisplay=true
"""
        with open(autostart_file, "w", encoding="utf-8") as f:
            f.write(desktop_content)
        os.chmod(autostart_file, 0o644)


class OgretmenApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="tr.okul.ogretmenpaylasim.gnome",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = OgretmenWindow(self)
        win.present()


def main():
    Adw.init()
    app = OgretmenApp()
    app.run([])


if __name__ == "__main__":
    main()

