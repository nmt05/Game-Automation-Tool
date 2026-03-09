# eggtool_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os 
import json
from eggtool import (
    connect_device, find_hatch, egg_loop, loot_egg, back_all_nests,
    find_hp, find_atk, check_and_untap_gray_image, tap, banish, home, reset_count, use_ticket,
    min_atk, min_hp, min_speed, DELAY_TIME, hp_count, atk_count, speed_count
)
from license import check_license
import sys
from hunttool import tap_x_to_close, check_and_tap_gray_image
from hunt import screenshot, merge_color_regions, get_filtered_centroids_and_contours, get_region_centroids,find_large_green_regions,extract_and_sort_final_red_locations,remove_nearby_red_regions_optimized,find_color_regions,find_large_red_regions,highlight_color_path,highlight_color_regions
# DEBUG: Thêm log khởi động
#print("🔧 DEBUG: eggtool_gui.py đang khởi động...")
from PIL import Image, ImageTk
# KIỂM TRA LICENSE TRƯỚC KHI CHẠY GUI
if not check_license():
    #print("❌ DEBUG: License check failed")
    sys.exit(1)

# ... phần còn lại của eggtool_gui.py ...
class EggToolGUI:
    def __init__(self, root):
        #print("🔧 DEBUG: Khởi tạo EggToolGUI...")
        self.root = root
        self.root.title("Egg Tool - Dino Auto Management")
        self.root.geometry("500x700")
        self.root.resizable(True, True)
        
        # Control variables
        self.root.iconbitmap("Graphics/icon.ico")
        self.pho_icon = ImageTk.PhotoImage(Image.open("Graphics/pho.png").resize((24, 24)))
        self.tik_icon = ImageTk.PhotoImage(Image.open("Graphics/tik.png").resize((24, 24)))

        self.is_running = False
        self.auto_mode = False
        self.thread = None
        self.config_file = "config.json" 
        self.golden_running = False    # Golden bật hay không
        self.golden_allowed = True     # Auto có cho Golden chạy không
        self.golden_delay_ms = 60000

        self.setup_eggtool_logging() 
        self.setup_gui()
        self.load_config()
        self.calculate_lvl()
        # self.setup_auto_refresh()
        #print("✅ DEBUG: EggToolGUI khởi tạo thành công")

    def setup_eggtool_logging(self):
        """Thiết lập logging cho eggtool.py"""
        #print("🔧 DEBUG: Thiết lập logging cho eggtool...")
        import eggtool
        # Truyền reference của GUI sang eggtool
        eggtool.gui_logger = self
        #print("✅ DEBUG: Logging setup completed")

    def load_config(self):
        """Load cấu hình từ file JSON"""
        #print(f"🔧 DEBUG: Đang load config từ {self.config_file}")
        try:
            if os.path.exists(self.config_file):
                #print(f"✅ DEBUG: Tìm thấy file config tại {os.path.abspath(self.config_file)}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                #print(f"🔧 DEBUG: Config content: {config}")
                
                # Lấy giá trị từ config
                new_port = config.get('port', '5559')
                new_min_hp = config.get('min_hp', min_hp)
                new_min_atk = config.get('min_atk', min_atk)
                new_min_speed = config.get('min_speed', min_speed)
                
                # Cập nhật GUI
                self.port_var.set(str(new_port))
                self.min_hp_var.set(str(new_min_hp))
                self.min_atk_var.set(str(new_min_atk))
                self.min_speed_var.set(str(new_min_speed))
                
                # CẬP NHẬT GLOBAL VARIABLES TRONG eggtool.py
                import eggtool
                eggtool.DEVICE = f"127.0.0.1:{new_port}"
                eggtool.min_hp = new_min_hp
                eggtool.min_atk = new_min_atk
                eggtool.min_speed = new_min_speed
                
                #print(f"✅ DEBUG: Đã load config - Port: {new_port}, HP: {new_min_hp}, ATK: {new_min_atk}, Speed: {new_min_speed}")
                # self.log_message("✅ Đã load cấu hình từ config.json")
                # self.log_message(f"Config: HP={new_min_hp}, ATK={new_min_atk}, Speed={new_min_speed}")
            else:
                #print("⚠️ DEBUG: Không tìm thấy config.json, sử dụng giá trị mặc định")
                self.log_message("ℹ️ Không tìm thấy config.json, sử dụng giá trị mặc định")
        except Exception as e:
            #print(f"❌ DEBUG: Lỗi load config: {e}")
            self.log_message(f"❌ Lỗi load config: {e}")

    def update_settings(self):
        """Update the global settings và lưu vào file"""
        #print("🔧 DEBUG: Đang update settings...")
        try:
            import eggtool
            
            # Lấy giá trị từ GUI
            new_port = self.port_var.get()
            new_min_hp = int(self.min_hp_var.get())
            new_min_atk = int(self.min_atk_var.get())
            new_min_speed = int(self.min_speed_var.get())
            
            # Cập nhật global variables trong eggtool.py
            eggtool.DEVICE = f"127.0.0.1:{new_port}"
            eggtool.min_hp = new_min_hp
            eggtool.min_atk = new_min_atk
            eggtool.min_speed = new_min_speed
            
            #print(f"✅ DEBUG: Updated settings - Port: {new_port}, HP: {new_min_hp}, ATK: {new_min_atk}, Speed: {new_min_speed}")
            
            # Lưu vào file JSON
            self.save_config()
            
            self.log_message(f"Settings updated - HP: {new_min_hp}, ATK: {new_min_atk}, Speed: {new_min_speed}")
        except ValueError as e:
            #print(f"❌ DEBUG: Lỗi giá trị khi update settings: {e}")
            messagebox.showerror("Error", "Please enter valid numbers for settings")

    def save_config(self):
        #print("🔧 DEBUG: Đang save config...")
        try:
            # Lấy giá trị TRỰC TIẾP từ GUI, không thông qua eggtool
            config = {
                "port": self.port_var.get(),
                "min_hp": int(self.min_hp_var.get()),
                "min_atk": int(self.min_atk_var.get()),
                "min_speed": int(self.min_speed_var.get())
            }
            
            #print(f"🔧 DEBUG: Config data to save: {config}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            #print(f"✅ DEBUG: Đã lưu config vào {os.path.abspath(self.config_file)}")
            # self.log_message("💾 Đã lưu cấu hình vào config.json")
            # self.log_message(f"📁 File: {os.path.abspath(self.config_file)}")
            
            # Kiểm tra file đã được ghi chưa
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                #print(f"📄 DEBUG: Nội dung file config: {content}")
            else:
                #print("❌ DEBUG: File config không tồn tại sau khi ghi!")
                self.log_message("❌ File config không tồn tại sau khi ghi!")
                
        except Exception as e:
            #print(f"❌ DEBUG: Lỗi save config: {e}")
            self.log_message(f"❌ Lỗi save config: {e}")
            
    def setup_gui(self):
        # Notebook (Tab control)
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 1: Main
        main_tab = ttk.Frame(notebook, padding="10")
        notebook.add(main_tab, text="Main")
        
        #print("🔧 DEBUG: Đang thiết lập GUI...")
        
        # Title
        title_label = ttk.Label(main_tab, text="Egg Tool - Dino Management", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Connection Section
        conn_frame = ttk.LabelFrame(main_tab, text="Device Connection", padding="10")
        conn_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        # Port input
        ttk.Label(conn_frame, text="ADB Port:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value="5559")  # Giá trị mặc định
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        self.conn_status = ttk.Label(conn_frame, text="Status: Not Connected", foreground="red")
        self.conn_status.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(conn_frame, text="Connect Device", 
                  command=self.connect_device).grid(row=0, column=2, padx=(10, 0))
        
        # Settings Section
        settings_frame = ttk.LabelFrame(main_tab, text="Dino Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Min HP
        # Min HP
# Min HP
        # Min HP
        ttk.Label(settings_frame, text="Min HP:").grid(row=0, column=0, sticky=tk.W)
        self.min_hp_var = tk.StringVar(value=str(min_hp))
        hp_entry = ttk.Entry(settings_frame, textvariable=self.min_hp_var, width=8)
        hp_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        # Nút tăng giảm HP với icon
        ttk.Button(settings_frame, text="➖", width=3,
                command=lambda: self.decrease_value('hp', 10)).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(settings_frame, text="➕", width=3,
                command=lambda: self.increase_value('hp', 10)).grid(row=0, column=3, padx=(2, 0))
        
        # Min ATK
        ttk.Label(settings_frame, text="Min ATK:").grid(row=1, column=0, sticky=tk.W)
        self.min_atk_var = tk.StringVar(value=str(min_atk))
        atk_entry = ttk.Entry(settings_frame, textvariable=self.min_atk_var, width=8)
        atk_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

        # Nút tăng giảm ATK với icon
        ttk.Button(settings_frame, text="➖", width=3,
                command=lambda: self.decrease_value('atk', 1)).grid(row=1, column=2, padx=(5, 0))
        ttk.Button(settings_frame, text="➕", width=3,
                command=lambda: self.increase_value('atk', 1)).grid(row=1, column=3, padx=(2, 0))

        # Min Speed
        ttk.Label(settings_frame, text="Min Speed:").grid(row=2, column=0, sticky=tk.W)
        self.min_speed_var = tk.StringVar(value=str(min_speed))
        speed_entry = ttk.Entry(settings_frame, textvariable=self.min_speed_var, width=8)
        speed_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0))

        # Nút tăng giảm Speed với icon
        ttk.Button(settings_frame, text="➖", width=3,
                command=lambda: self.decrease_value('speed', 1)).grid(row=2, column=2, padx=(5, 0))
        ttk.Button(settings_frame, text="➕", width=3,
                command=lambda: self.increase_value('speed', 1)).grid(row=2, column=3, padx=(2, 0))
                
        # Min Lvl (HIỂN THỊ ĐƠN GIẢN)
        ttk.Label(settings_frame, text="COUNT:").grid(row=0, column=4, sticky=tk.W)
        self.hp_count_label = ttk.Label(settings_frame, text=str(hp_count), width=8, 
                               background="white", relief="sunken", padding=(5, 2))
        self.hp_count_label.grid(row=0, column=5, sticky=tk.W, padx=(5, 0))

        ttk.Label(settings_frame, text="COUNT:").grid(row=1, column=4, sticky=tk.W)
        self.atk_count_label = ttk.Label(settings_frame, text=str(atk_count), width=8, 
                                background="white", relief="sunken", padding=(5, 2))
        self.atk_count_label.grid(row=1, column=5, sticky=tk.W, padx=(5, 0))

        ttk.Label(settings_frame, text="COUNT:").grid(row=2, column=4, sticky=tk.W)
        self.speed_count_label = ttk.Label(settings_frame, text=str(speed_count), width=8, 
                                  background="white", relief="sunken", padding=(5, 2))
        self.speed_count_label.grid(row=2, column=5, sticky=tk.W, padx=(5, 0))
        ttk.Label(settings_frame, text="Min Lvl:").grid(row=1, column=6, sticky=tk.W)
        self.min_lvl_label = ttk.Label(settings_frame, text="0", width=8, 
                                    background="white", relief="sunken", padding=(5, 2))
        self.min_lvl_label.grid(row=1, column=7, sticky=tk.W, padx=(5, 0))
        # Update settings button
        # Trong phần Settings Section, thêm nút Save
        # ttk.Button(settings_frame, text="Save Config", 
        #         command=self.save_config).grid(row=3, column=2, pady=(10, 0), sticky=tk.E)
        ttk.Button(settings_frame, text="Update Current Process", 
                  command=self.update_settings).grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(settings_frame, text="Reset Count", 
                  command=self.scan_team_stats).grid(row=3, column=4, columnspan=2, pady=(10, 0))
        stats_frame = ttk.LabelFrame(main_tab, text="Scan Team Stats -- UPDATING...", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        
        # ttk.Button(stats_frame, text="Scan Team Stats -- UPDATING...", 
        #           command=self.scan_team_stats).grid(row=1, column=0, pady=(10, 0))
        
        # Control Section
        control_frame = ttk.LabelFrame(main_tab, text="Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        
# Auto mode và Control buttons - Cùng hàng với kích thước tương đồng
        self.auto_button = ttk.Button(control_frame, text="🚀 BẮT ĐẦU", 
                                    command=self.toggle_auto_mode,
                                    style="Large.TButton")
        self.auto_button.grid(row=1, column=0, padx=(0, 5), pady=(10, 5), sticky=(tk.W, tk.E))

        ttk.Button(control_frame, text="🛑 DỪNG", 
                  command=self.stop_all,
                  style="Large.TButton").grid(row=1, column=1, padx=5, pady=(10, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="❌ THOÁT", 
                  command=self.exit_app,
                  style="Large.TButton").grid(row=1, column=2, padx=(5, 0), pady=(10, 5), sticky=(tk.W, tk.E))

        # Configure button styles
        style = ttk.Style()
        style.configure("Large.TButton", font=('Arial', 11, 'bold'), padding=(15, 10))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_tab, text="Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", 
                  command=self.clear_log).grid(row=1, column=0, pady=(10, 0))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_tab.columnconfigure(0, weight=1)
        main_tab.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Configure control frame columns to expand
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
        #print("✅ DEBUG: GUI setup completed")
        apply_tap = ttk.Frame(notebook, padding="10")
        notebook.add(apply_tap, text="Application")

        # biến trạng thái

        # label "Enable application" ở bên trái
        phero_frame = ttk.LabelFrame(
            apply_tap,
            text="Phoromone",
            padding="10"
        )
        phero_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.apply_phoromone_atk = tk.BooleanVar(value=False)
        self.apply_phoromone_hp = tk.BooleanVar(value=False)
        ttk.Label(
            phero_frame,
            image=self.pho_icon,
            takefocus=0
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            phero_frame,
            text="ATK",
            takefocus=0
        ).grid(row=1, column=0, sticky="w")
        
        ttk.Checkbutton(
            phero_frame,
            variable=self.apply_phoromone_atk
        ).grid(row=1, column=1, padx=(20, 0), sticky="w")
        ttk.Label(
            phero_frame,
            text="HP",
            takefocus=0
        ).grid(row=2, column=0, sticky="w")
        
        ttk.Checkbutton(
            phero_frame,
            variable=self.apply_phoromone_hp
        ).grid(row=2, column=1, padx=(20, 0), sticky="w")
        #ticket
        ticket_frame = ttk.LabelFrame(
            apply_tap,
            text="Ticket",
            padding="10"
        )
        ticket_frame.grid(row=1, column=0, sticky="w")

        self.apply_ticket_grow = tk.BooleanVar(value=False)
        self.apply_ticket_hatch = tk.BooleanVar(value=False)

        # Ticket for Growing
        ttk.Label(ticket_frame, image=self.tik_icon, takefocus=0).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(ticket_frame, text="GROWING", takefocus=0).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Checkbutton(
            ticket_frame,
            variable=self.apply_ticket_grow
        ).grid(row=1, column=1, padx=(20, 0), sticky="w")
        #atk
        ttk.Label(ticket_frame, text="for ATK:", takefocus=0).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(ticket_frame, text ="+1:", takefocus=0).grid(
            row=3, column=1, sticky="w"
        )
        self.number_of_atk_1 = tk.IntVar(value=1)
        self.number_of_atk_2 = tk.IntVar(value=1)
        self.number_of_atk_3 = tk.IntVar(value=1)

        atk_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_atk_1,
            width=4
        )
        atk_nums.grid(row=3, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=3, column=3, sticky=tk.W)
        ttk.Label(ticket_frame, text ="+2:", takefocus=0).grid(
            row=4, column=1, sticky="w"
        )
        self.number_of_atk_1 = tk.IntVar(value=1)
        self.number_of_atk_2 = tk.IntVar(value=1)
        self.number_of_atk_3 = tk.IntVar(value=1)

        atk_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_atk_2,
            width=4
        )
        atk_nums.grid(row=4, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=4, column=3, sticky=tk.W)
        ttk.Label(ticket_frame, text ="+3:", takefocus=0).grid(
            row=5, column=1, sticky="w"
        )
        self.number_of_atk_1 = tk.IntVar(value=1)
        self.number_of_atk_2 = tk.IntVar(value=1)
        self.number_of_atk_3 = tk.IntVar(value=1)

        atk_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_atk_3,
            width=4
        )
        atk_nums.grid(row=5, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=5, column=3, sticky=tk.W)

        ttk.Label(
            ticket_frame,
            text=" "
        ).grid(row=6, column=0, sticky=tk.W)
        #hp
        ttk.Label(ticket_frame, text="for HP:", takefocus=0).grid(
            row=7, column=0, sticky="w"
        )
        ttk.Label(ticket_frame, text ="+1:", takefocus=0).grid(
            row=8, column=1, sticky="w"
        )
        self.number_of_hp_1 = tk.IntVar(value=1)
        self.number_of_hp_2 = tk.IntVar(value=1)
        self.number_of_hp_3 = tk.IntVar(value=1)

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_hp_1,
            width=4
        )
        hp_nums.grid(row=8, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=8, column=3, sticky=tk.W)
        ttk.Label(ticket_frame, text ="+2:", takefocus=0).grid(
            row=9, column=1, sticky="w"
        )
        self.number_of_atk_1 = tk.IntVar(value=1)
        self.number_of_atk_2 = tk.IntVar(value=1)
        self.number_of_atk_3 = tk.IntVar(value=1)

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_hp_2,
            width=4
        )
        hp_nums.grid(row=9, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=9, column=3, sticky=tk.W)
        ttk.Label(ticket_frame, text ="+3:", takefocus=0).grid(
            row=10, column=1, sticky="w"
        )
        self.number_of_atk_1 = tk.IntVar(value=1)
        self.number_of_atk_2 = tk.IntVar(value=1)
        self.number_of_atk_3 = tk.IntVar(value=1)

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=1,
            to=5,
            increment=1,
            textvariable=self.number_of_hp_3,
            width=4
        )
        hp_nums.grid(row=10, column=2, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            ticket_frame,
            text="time(s)"
        ).grid(row=10, column=3, sticky=tk.W)
        ttk.Label(
            ticket_frame,
            text=" "
        ).grid(row=11, column=0, sticky=tk.W)
        # Ticket for Hatching
        ttk.Label(ticket_frame, text="HATCHING", takefocus=0).grid(
            row=12, column=0, sticky="w"
        )
        ttk.Checkbutton(
            ticket_frame,
            variable=self.apply_ticket_hatch
        ).grid(row=12, column=1, padx=(20, 0), sticky="w")
        self.golden_ticket_var = tk.IntVar(value=30)
        golden_spinbox = tk.Spinbox(
            ticket_frame,
            from_=30,
            to=9999,
            increment=30,
            textvariable=self.golden_ticket_var,
            width=4
        )
        golden_spinbox.grid(row=12, column=2, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(
            ticket_frame,
            text="mins"
        ).grid(row=12, column=3, sticky=tk.W)
        # Tab 2: Golden Ticket
        golden_tab = ttk.Frame(notebook, padding="10")
        notebook.add(golden_tab, text="Golden Ticket")
        golden_frame = ttk.LabelFrame(
        golden_tab, 
        text="Golden Ticket Settings", 
        padding="15"
        )
        golden_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.golden_ticket_var = tk.IntVar(value=30)
        ttk.Label(
            golden_frame, 
            text="Time"
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        golden_spinbox = tk.Spinbox(
            golden_frame,
            from_=30,
            to=9999,
            increment=30,
            textvariable=self.golden_ticket_var,
            width=10
        )
        golden_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Button(
            golden_frame,
            text="Apply Golden Ticket",
            command=self.apply_golden_ticket
        ).grid(row=1, column=0, columnspan=2, pady=(10, 0))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        notebook.enable_traversal()

    def apply_golden_ticket(self):
        minutes = self.golden_ticket_var.get()
        if minutes <= 0:
            return

        self.golden_delay_ms = minutes * 1000
        self.golden_running = True

        self.log_message(f"Golden Ticket: mỗi {minutes} phút")

        self._schedule_golden()
    def _schedule_golden(self):
        if not self.golden_running:
            return

        self.root.after(self.golden_delay_ms, self._run_golden)

    def _run_golden(self):
        if not self.golden_running:
            return

        if not self.golden_allowed:
            self.log_message("Golden skipped (auto busy)")
            self._schedule_golden()
            return

        try:
            use_ticket()   # 👈 hành động Golden (mày tự viết)
        except Exception as e:
            self.log_message(f"Golden error: {e}")

        self._schedule_golden()
    def stop_golden(self):
        self.golden_running = False


    def update_value(self, var_name, new_value):
        """
        Thay thế giá trị cũ bằng giá trị mới hoàn toàn.
        Ví dụ: HP từ 10 thay thẳng thành 100.
        """
        import eggtool #
        
        # Ép kiểu về int để đảm bảo tính toán không lỗi

        if var_name == 'hp':
            eggtool.min_hp = new_value #
            self.min_hp_var.set(str(new_value)) #
        elif var_name == 'atk':
            eggtool.min_atk = new_value #
            self.min_atk_var.set(str(new_value)) #
        elif var_name == 'speed':
            eggtool.min_speed = new_value #
            self.min_speed_var.set(str(new_value)) #

        # Sau khi thay thế thì cập nhật lại Level hiển thị và lưu file config
        self.calculate_lvl() #
        self.update_settings() #
    def decrease_value(self, var_name, step):
        #print(f"🔧 DEBUG: Giảm {var_name} với step {step}")
        import eggtool
        
        if var_name == 'hp':
            eggtool.min_hp = max(0, eggtool.min_hp - step)
            self.min_hp_var.set(str(eggtool.min_hp))
            #print(f"✅ DEBUG: HP giảm xuống {eggtool.min_hp}")
        elif var_name == 'atk':
            eggtool.min_atk = max(0, eggtool.min_atk - step)
            self.min_atk_var.set(str(eggtool.min_atk))
            #print(f"✅ DEBUG: ATK giảm xuống {eggtool.min_atk}")
        elif var_name == 'speed':
            eggtool.min_speed = max(0, eggtool.min_speed - step)
            self.min_speed_var.set(str(eggtool.min_speed))
            #print(f"✅ DEBUG: Speed giảm xuống {eggtool.min_speed}")
        self.calculate_lvl()
        # Tự động update và save
        self.update_settings()

    def increase_value(self, var_name, step):
        """Tăng giá trị biến global"""
        #print(f"🔧 DEBUG: Tăng {var_name} với step {step}")
        import eggtool
        
        if var_name == 'hp':
            eggtool.min_hp += step
            self.min_hp_var.set(str(eggtool.min_hp))
            #print(f"✅ DEBUG: HP tăng lên {eggtool.min_hp}")
        elif var_name == 'atk':
            eggtool.min_atk += step
            self.min_atk_var.set(str(eggtool.min_atk))
            #print(f"✅ DEBUG: ATK tăng lên {eggtool.min_atk}")
        elif var_name == 'speed':
            eggtool.min_speed += step
            self.min_speed_var.set(str(eggtool.min_speed))
            #print(f"✅ DEBUG: Speed tăng lên {eggtool.min_speed}")
        self.calculate_lvl()
        # Tự động update và save
        self.update_settings()
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def clear_log(self):
        """Clear the log text"""
        #print("🔧 DEBUG: Xóa log")
        self.log_text.delete(1.0, tk.END)
        
    def connect_device(self):
        """Connect to device in thread"""
        def connect_thread():
            #print("🔧 DEBUG: Bắt đầu kết nối device...")
            self.log_message("Connecting to device...")
            if connect_device():
                self.conn_status.config(text="Status: Connected", foreground="green")
                self.log_message("Device connected successfully!")
                #print("✅ DEBUG: Kết nối device thành công")
            else:
                self.conn_status.config(text="Status: Connection Failed", foreground="red")
                self.log_message("Device connection failed!")
                #print("❌ DEBUG: Kết nối device thất bại")
        self.update_settings()
        threading.Thread(target=connect_thread, daemon=True).start()
        
    # def update_settings(self):
    #     """Update the global settings và lưu vào file"""
    #     try:
    #         min_hp = int(self.min_hp_var.get())
    #         min_atk = int(self.min_atk_var.get())
    #         min_speed = int(self.min_speed_var.get())
            
    #         # Lưu vào file JSON
    #         self.save_config()
            
    #         self.log_message(f"Settings updated - HP: {min_hp}, ATK: {min_atk}, Speed: {min_speed}")
    #     except ValueError:
    #         messagebox.showerror("Error", "Please enter valid numbers for settings")
            
    def scan_team_stats(self):
        reset_count()
        self.update_count_display()
        return
    def calculate_lvl(self):
        """Tính toán Min Lvl dựa trên công thức: min_hp / 10 + atk + speed"""
        #print("🔧 DEBUG: Tính toán level...")
        try:
            import eggtool
            
            hp = eggtool.min_hp
            atk = eggtool.min_atk
            speed = eggtool.min_speed
            
            # Tính toán theo công thức: HP/10 + ATK + SPEED
            lvl = (hp // 10) + atk + speed
            self.min_lvl_label.config(text=str(lvl))
            #print(f"✅ DEBUG: Level tính toán: {lvl} (HP: {hp}, ATK: {atk}, Speed: {speed})")
            
        except Exception as e:
            #print(f"❌ DEBUG: Lỗi tính toán level: {e}")
            self.min_lvl_label.config(text="Error")
    def check_hatch(self):
        """Check hatch status"""
        def check_thread():
            #print("🔧 DEBUG: Kiểm tra hatch status...")
            self.log_message("Checking hatch status...")
            result = find_hatch()
            if result is True:
                self.log_message("✅ Egg ready to hatch!")
                #print("✅ DEBUG: Egg sẵn sàng nở")
            elif isinstance(result, int):
                self.log_message(f"⏰ Time until hatch: {result} seconds")
                #print(f"✅ DEBUG: Thời gian đến khi nở: {result} giây")
            else:
                self.log_message("❌ No egg ready to hatch")
                #print("❌ DEBUG: Không có egg sẵn sàng nở")
                
        threading.Thread(target=check_thread, daemon=True).start()
    def update_count_display(self):
        """Cập nhật hiển thị COUNT từ biến global trong eggtool.py"""
        # #print("🔧 DEBUG: Cập nhật COUNT display...")
        try:
            import eggtool
            
            # Cập nhật COUNT HP
            if hasattr(eggtool, 'hp_count'):
                self.hp_count_label.config(text=str(eggtool.hp_count))
            else:
                self.hp_count_label.config(text="N/A")
            
            # Cập nhật COUNT ATK
            if hasattr(eggtool, 'atk_count'):
                self.atk_count_label.config(text=str(eggtool.atk_count))
            else:
                self.atk_count_label.config(text="N/A")
            
            # Cập nhật COUNT SPEED
            if hasattr(eggtool, 'speed_count'):
                self.speed_count_label.config(text=str(eggtool.speed_count))
            else:
                self.speed_count_label.config(text="N/A")
                
            # #print(f"✅ DEBUG: COUNT updated - HP: {eggtool.hp_count}, ATK: {eggtool.atk_count}, SPEED: {eggtool.speed_count}")
            # self.log_message(f"COUNT updated - HP: {eggtool.hp_count}, ATK: {eggtool.atk_count}, SPEED: {eggtool.speed_count}")
            
        except Exception as e:
            #print(f"❌ DEBUG: Lỗi cập nhật COUNT: {e}")
            self.log_message(f"❌ Lỗi cập nhật COUNT: {e}")
            # Đặt giá trị mặc định nếu có lỗi
            self.hp_count_label.config(text="Error")
            self.atk_count_label.config(text="Error")
            self.speed_count_label.config(text="Error")
    def setup_auto_refresh(self):
        """Thiết lập tự động cập nhật COUNT mỗi giây"""
        #print("🔧 DEBUG: Thiết lập auto refresh...")
        def refresh_counts():
            if self.auto_mode:  # Chỉ cập nhật khi auto mode đang chạy
                self.update_count_display()
            self.root.after(60000, refresh_counts)  # Cập nhật mỗi giây
        
        self.root.after(60000, refresh_counts)
        #print("✅ DEBUG: Auto refresh setup completed")
    def open_egg(self):
        """Open a single egg"""
        def open_thread():
            #print("🔧 DEBUG: Mở egg...")
            self.log_message("Opening egg...")
            egg_loop()
            self.log_message("Egg opened!")
            #print("✅ DEBUG: Egg đã mở")
            
        threading.Thread(target=open_thread, daemon=True).start()
        
    def loot_egg(self):
        """Loot an egg"""
        def loot_thread():
            #print("🔧 DEBUG: Loot egg...")
            self.log_message("Looting egg...")
            loot_egg()
            self.log_message("Egg looted!")
            #print("✅ DEBUG: Egg đã loot")
            
        threading.Thread(target=loot_thread, daemon=True).start()
        
    def back_nests(self):
        """Return all dinos to nests"""
        def back_thread():
            #print("🔧 DEBUG: Trả dino về nests...")
            self.log_message("Returning dinos to nests...")
            back_all_nests()
            self.log_message("All dinos returned to nests!")
            #print("✅ DEBUG: Đã trả tất cả dino về nests")
            
        threading.Thread(target=back_thread, daemon=True).start()
        
    def check_gray(self):
        """Check and untap gray images"""
        def check_thread():
            #print("🔧 DEBUG: Kiểm tra gray images...")
            self.log_message("Checking for gray images...")
            check_and_untap_gray_image()
            self.log_message("Gray image check completed!")
            #print("✅ DEBUG: Kiểm tra gray images hoàn tất")
            
        threading.Thread(target=check_thread, daemon=True).start()
    def log_valid_dino(self, message):
        """Log dino hợp lệ với màu xanh lá"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        # Tô màu dòng cuối cùng thành xanh lá
        self.log_text.tag_add("valid", "end-2l", "end-1l")
        self.log_text.tag_config("valid", foreground="green")
        self.log_text.see(tk.END)
        self.root.update()

    def log_trash_dino(self, message):
        """Log dino rác với màu đỏ"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] 🔴 Dino cùi{message}\n")
        # Tô màu dòng cuối cùng thành đỏ
        self.log_text.tag_add("trash", "end-2l", "end-1l")
        self.log_text.tag_config("trash", foreground="red")
        self.log_text.see(tk.END)
        self.root.update()

    def log_waiting(self, message):
        """Log thời gian chờ với màu vàng"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] 🟡{message}\n")
        # Tô màu dòng cuối cùng thành vàng
        self.log_text.tag_add("waiting", "end-2l", "end-1l")
        self.log_text.tag_config("waiting", foreground="orange")
        self.log_text.see(tk.END)
        self.root.update() 
    def toggle_auto_mode(self):
        """Toggle auto mode on/off"""
        #print(f"🔧 DEBUG: Toggle auto mode, current: {self.auto_mode}")
        if not self.auto_mode:
            self.start_auto_mode()
        else:
            self.stop_auto_mode()
            
    def start_auto_mode(self):
        """Start auto mode"""
        #print("🔧 DEBUG: Bắt đầu auto mode")
        self.auto_mode = True
        # self.start_button.config(text="🛑 STOP AUTO MODE")
        self.log_message("🔄 Auto mode started!")
        self.thread = threading.Thread(target=self.auto_loop, daemon=True)
        self.thread.start()
        #print("✅ DEBUG: Auto mode đã bắt đầu")
        
    def stop_auto_mode(self):
        """Stop auto mode"""
        #print("🔧 DEBUG: Dừng auto mode")
        self.auto_mode = False
        # self.start_button.config(text="🚀 START AUTO MODE")
        self.log_message("⏹️ Auto mode stopped!")
        #print("✅ DEBUG: Auto mode đã dừng")
        
    def stop_all(self):
        """Stop all operations"""
        #print("🔧 DEBUG: Dừng tất cả hoạt động")
        self.stop_auto_mode()
        self.log_message("🛑 Tất cả hoạt động đã dừng!")
        #print("✅ DEBUG: Tất cả hoạt động đã dừng")
        
    def exit_app(self):
        """Exit the application"""
        #print("🔧 DEBUG: Thoát ứng dụng")
        if self.auto_mode:
            self.stop_auto_mode()
        self.log_message("Ứng dụng đang thoát...")
        self.root.quit()
        self.root.destroy()
        #print("✅ DEBUG: Ứng dụng đã thoát")
        
        
    def auto_loop(self):
        """Main auto loop"""
        while self.auto_mode:
            try:
                # check_and_untap_gray_image()  # THÊM DÒNG NÀY
                # self.log_message("Checking hatch status...")
                time.sleep(1)
                if not self.auto_mode: return
                hatch_status = find_hatch()
                check_and_untap_gray_image()
                if hatch_status is True:
                    #print("✅ DEBUG: Egg ready to open")
                    # self.log_message("Egg re99090ady! Opening...")
                    egg_loop()
                    self.load_config()
                    self.update_settings()
                    self.calculate_lvl()
                    self.update_count_display()
                    
                elif isinstance(hatch_status, int) and hatch_status > 0:
                    sleep_time = hatch_status - 13 # ĐỔI TÊN BIẾN
                    if sleep_time >= 120:
                        sleep_time = 120
                    self.log_message(f"Waiting {sleep_time} seconds for hatch...")

                    loot_egg()
                    start_time = time.time()
        
                    tap_x_to_close()
                    time.sleep(1)
                    check_and_untap_gray_image()
                    time.sleep(1)
                    if not self.auto_mode: return

                    if find_hatch() == True:

                        egg_loop()
                        
                else:

                    tap(2660, 3021)
                    time.sleep(0.5)
                    home()
                    time.sleep(0.5)
                    banish()
                    time.sleep(0.5) # Delay sau khi Banish
                    tap(1823, 2123) # Xác nhận Banish

            except Exception as e:
                #print(f"❌ DEBUG: Lỗi trong auto loop: {e}")
                self.log_message(f"Error in auto loop: {str(e)}")
                tap(3819, 3547)
                time.sleep(1)
                
def main():
    #print("🔧 DEBUG: Hàm main() được gọi")
    root = tk.Tk()
    app = EggToolGUI(root)
    #print("✅ DEBUG: Bắt đầu mainloop")
    root.mainloop()
    #print("✅ DEBUG: Mainloop kết thúc")

if __name__ == "__main__":
    #print("🔧 DEBUG: Script chạy trực tiếp")
    # back_all_nests()
    #print("✅ DEBUG: back_all_nests() completed")
    main()
    #print("✅ DEBUG: Script kết thúc")