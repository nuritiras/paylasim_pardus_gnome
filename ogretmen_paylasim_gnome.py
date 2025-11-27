#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

OKUL_ADI = "Ticaret ve Sanayi Odası TMTAL"
LOGO_YOLU = "/usr/share/pixmaps/okul-logo.png"  # Logo koyarsan üstte görünür


class OgretmenWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Öğretmen Paylaşımı Kurucu (GNOME / GTK4)")
        self.set_default_size(640, 420)

        if os.geteuid() != 0:
            self._hata_mesaji(
                "Bu uygulama sistem ayarlarını değiştirmek için root yetkisi ister.\n"
                "Önerilen kullanım:\n\n  pkexec /usr/local/sbin/ogretmen_paylasim_gnome.py"
            )

        self.build_ui()

    def build_ui(self):
        # Ana kutu
        outer = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )
        self.set_child(outer)

        # Üst başlık alanı
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.append(header_box)

        # Logo
        if os.path.exists(LOGO_YOLU):
            img = Gtk.Image.new_from_file(LOGO_YOLU)
            header_box.append(img)

        # Yazı alanı
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_box.append(title_box)

        lbl_title = Gtk.Label(label="Öğretmen Paylaşımı Kurucu")
        lbl_title.set_xalign(0.0)
        lbl_title.get_style_context().add_class("title-1")
        title_box.append(lbl_title)

        lbl_sub = Gtk.Label(
            label=f"{OKUL_ADI}\nWindows sunucudaki 'ogretmen' paylaşımını otomatik bağlama aracı"
        )
        lbl_sub.set_xalign(0.0)
        lbl_sub.set_wrap(True)
        title_box.append(lbl_sub)

        # Form alanı
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.append(form_box)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        form_box.append(grid)

        row = 0

        def add_label(text, row):
            lbl = Gtk.Label(label=text)
            lbl.set_xalign(1.0)
            grid.attach(lbl, 0, row, 1, 1)

        # Form girdileri
        self.entry_server = Gtk.Entry(text="10.10.10.5")
        add_label("Sunucu IP / Ad:", row)
        grid.attach(self.entry_server, 1, row, 1, 1)
        row += 1

        self.entry_share = Gtk.Entry(text="ogretmen")
        add_label("Paylaşım Adı:", row)
        grid.attach(self.entry_share, 1, row, 1, 1)
        row += 1

        self.entry_mount = Gtk.Entry(text="/mnt/ogretmen")
        add_label("Mount Noktası:", row)
        grid.attach(self.entry_mount, 1, row, 1, 1)
        row += 1

        self.entry_user = Gtk.Entry(text="ogrt")
        add_label("Windows Kullanıcı Adı:", row)
        grid.attach(self.entry_user, 1, row, 1, 1)
        row += 1

        self.entry_pass = Gtk.Entry()
        self.entry_pass.set_visibility(False)
        self.entry_pass.set_invisible_char("•")
        add_label("Windows Şifre:", row)
        grid.attach(self.entry_pass, 1, row, 1, 1)
        row += 1

        self.entry_domain = Gtk.Entry(text="WORKGROUP")
        add_label("Domain / Workgroup:", row)
        grid.attach(self.entry_domain, 1, row, 1, 1)
        row += 1

        note = Gtk.Label(
            label="Not: Bu ayarlar GNOME oturumundaki TÜM kullanıcılar için geçerlidir.\n"
                  "Öğretmen giriş yaptığında masaüstünde otomatik kısayol oluşacaktır."
        )
        note.set_xalign(0.0)
        note.set_wrap(True)
        form_box.append(note)

        # Alt alan: durum + butonlar
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.append(bottom)

        self.status_label = Gtk.Label(label="Hazır.")
        self.status_label.set_xalign(0.0)
        bottom.append(self.status_label)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        bottom.append(btn_box)

        self.btn_apply = Gtk.Button(label="Ayarları Uygula")
        self.btn_apply.connect("clicked", self.on_apply_clicked)
        btn_box.append(self.btn_apply)

        btn_close = Gtk.Button(label="Kapat")
        btn_close.connect("clicked", lambda w: self.get_application().quit())
        btn_box.append(btn_close)

    # -----------------------------
    # Mesaj pencereleri
    # -----------------------------
    def _hata_mesaji(self, mesaj):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Hata",
            secondary_text=mesaj,
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()

    def _info_mesaji(self, baslik, mesaj):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=baslik,
            secondary_text=mesaj,
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()

    def set_status(self, text):
        self.status_label.set_text(text)
        print(text)

    # -----------------------------
    # Uygula butonu tıklanınca
    # -----------------------------
    def on_apply_clicked(self, button):
        server = self.entry_server.get_text().strip()
        share = self.entry_share.get_text().strip()
        mount = self.entry_mount.get_text().strip()
        user = self.entry_user.get_text().strip()
        passwd = self.entry_pass.get_text().strip()
        domain = self.entry_domain.get_text().strip() or "WORKGROUP"

        if not all([server, share, mount, user, passwd]):
            self._hata_mesaji("Lütfen tüm alanları eksiksiz doldurun.")
            return

        self.btn_apply.set_sensitive(False)
        self.set_status("Ayarlar uygulanıyor...")

        try:
            self.apply_system_settings(server, share, mount, user, passwd, domain)
            self.set_status("Tamamlandı.")
            self._info_mesaji(
                "İşlem Bitti",
                "Öğretmen paylaşımı ayarlandı.\n"
                "Kullanıcı tekrar giriş yaptığında masaüstünde kısayol oluşacak."
            )
        except Exception as e:
            self._hata_mesaji(str(e))
            self.set_status("Hata oluştu.")
        finally:
            self.btn_apply.set_sensitive(True)

    # -----------------------------
    # SİSTEM AYARLARINI UYGULAR
    # -----------------------------
    def apply_system_settings(self, server, share, mount, user, passwd, domain):

        # /mnt klasörü
        os.makedirs(mount, exist_ok=True)

        # /etc/samba/creds-ogretmen
        cred_path = f"/etc/samba/creds-{share}"
        os.makedirs("/etc/samba", exist_ok=True)

        with open(cred_path, "w", encoding="utf-8") as f:
            f.write(f"username={user}\npassword={passwd}\ndomain={domain}\n")
        os.chmod(cred_path, 0o600)

        # fstab yedek
        backup_name = f"/etc/fstab.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy("/etc/fstab", backup_name)

        # fstab düzenleme
        marker_start = "# OGRETMEN_PAYLASIM_BASLA"
        marker_end = "# OGRETMEN_PAYLASIM_BITIR"

        new_lines = []
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
        new_lines.append(
            f"//{server}/{share}  {mount}  cifs  credentials={cred_path},"
            f"iocharset=utf8,uid=1000,gid=1000,file_mode=0777,dir_mode=0777,"
            f"noperm,nofail  0  0\n"
        )
        new_lines.append(f"{marker_end}\n")

        with open("/etc/fstab", "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # mount testi
        res = subprocess.run(["mount", "-a"], text=True, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"mount -a başarısız.\nHata:\n{res.stderr}\n\nYedek: {backup_name}"
            )

        # --------------------------
        # Kısayol scripti oluştur
        # --------------------------
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

# GNOME 'başlatmaya izin ver' istemesin:
gio set "$SHORTCUT" "metadata::trusted" true 2>/dev/null
"""

        with open(kisayol_script, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(kisayol_script, 0o755)

        # GNOME autostart
        autostart = "/etc/xdg/autostart/ogretmen-kisayol.desktop"
        os.makedirs("/etc/xdg/autostart", exist_ok=True)

        with open(autostart, "w", encoding="utf-8") as f:
            f.write("""[Desktop Entry]
Type=Application
Name=Öğretmen Paylaşımı Kısayol Oluşturucu
Exec=/usr/local/bin/ogretmen-kisayol.sh
OnlyShowIn=GNOME;
NoDisplay=true
""")

        os.chmod(autostart, 0o644)


class OgretmenApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="tr.okul.ogretmenpaylasim.gnome",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = OgretmenWindow(self)
        win.present()


def main():
    app = OgretmenApp()
    app.run([])


if __name__ == "__main__":
    main()

