import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os 
import winsound
import json
import queue
import sys
from PIL import Image, ImageTk

# Import các hàm core
from eggtool import (
    connect_device, find_hatch, egg_loop, loot_egg, back_all_nests, banish, home,claim, send_telegram_msg, check_and_untap_gray_image, ticket_boosting_hatch, ticket_boosting_grow_hp, ticket_boosting_grow_atk, scan,replace_lower_atk_position,replace_lower_hp_position,smart_tap,
    min_atk, min_hp, min_speed, hp_count, atk_count, speed_count, atk_gap, hp_gap
)
from license import check_license
from hunttool import tap_x_to_close,check_and_tap_gray_image,check_and_untap_gray_image
from hunt import screenshot, merge_color_regions, get_filtered_centroids_and_contours, get_region_centroids,find_large_green_regions,extract_and_sort_final_red_locations,remove_nearby_red_regions_optimized,find_color_regions,find_large_red_regions,highlight_color_path,highlight_color_regions

if not check_license():
    sys.exit(1)

class EggToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Egg Tool - Double Queue Architecture")
                
        # --- 1. TÁCH BIỆT QUEUE ---
        self.task_queue = queue.PriorityQueue()  # Lệnh cho Worker
        self.gui_queue = queue.Queue()   # Lệnh cho GUI
        
        self.auto_mode = False
        self.config_file = "config.json"
        self.current_task_name = tk.StringVar(value="Idle")
        self.trigger_flag = False
        self.hunting_flag = False
        # Load Assets
        self._load_assets()
        
        # --- 2. KHỞI TẠO GUI ---
        self.setup_gui()
        self.load_config()

        # --- 3. KHỞI CHẠY HỆ THỐNG LUỒNG ---
        # Worker duy nhất xử lý ADB
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Loop lắng nghe cập nhật giao diện (GUI Thread)
        self._listen_gui_queue()
        
        # Loop cập nhật thanh Debug (GUI Thread)
        self._update_debug_bar()
        
        self.target_colors = [
                            (230, 230, 230), (187, 187, 187)
                        ]
        self.target_colors_path = [(126, 216, 217)]
        self.CROP_BOX = (1200, 1200, 3000, 3000)
        self.OFFSET_X, self.OFFSET_Y = self.CROP_BOX[0], self.CROP_BOX[1]
        self.MIN_AREA_THRESHOLD = 50
        self.NEARBY_DISTANCE_THRESHOLD = 200
        self.AIM_CENTER = (2048, 2048) # Tâm cố định cho việc sắp xếp

        # Đường dẫn tệp kết quả
        self.RED_PATH = "bubuchachalalala/large_red_regions_filtered.png"
        self.GREEN_PATH = "bubuchachalalala/large_green_regions_filtered.png"
        self.FINAL_MERGED_PATH = "bubuchachalalala/merged_regions_final.png"
        self.FINAL_FILTERED_PATH = "bubuchachalalala/filtered_final_result_optimized.png"
        self.count = 0
        # self.atk_gap = 0
        # self.hp_gap = 0
        # self.play_welcome_sound()
    def _load_assets(self):
        try:
            self.pho_icon = ImageTk.PhotoImage(Image.open("Graphics/pho.png").resize((24, 24)))
            self.tik_icon = ImageTk.PhotoImage(Image.open("Graphics/tik.png").resize((24, 24)))
        except:
            self.pho_icon = self.tik_icon = None
    def play_welcome_sound(self):
        """Phát âm thanh chào mừng khi khởi động ứng dụng"""
        try:
            # Tần số thấp (300-400Hz) nghe sẽ rất êm
            winsound.Beep(330, 150) # Mi (E4)
            winsound.Beep(392, 150) # Sol (G4)
            winsound.Beep(523, 200) # Đô (C5)
        except:
            pass
    def play_soft_success(self):
        try:
            # Hai nốt quãng cao nhưng thời gian rất ngắn (100ms)
            winsound.Beep(784, 100) # Nốt Sol (G5)
            winsound.Beep(1046, 150) # Nốt Đô (C6)
        except:
            pass
    
    def _worker_loop(self):
        # flag = 0
        while True:
            try:
                # Lấy item từ PriorityQueue
                item = self.task_queue.get(block=True)
                
                # Kiểm tra nếu item là tuple (đúng chuẩn PriorityQueue)
                if isinstance(item, tuple) and len(item) > 1:
                    task = item[1]
                else:
                    # Phòng hờ trường hợp dữ liệu cũ vẫn còn trong queue
                    task = item
                
                t_type = task.get("type")
                self.current_task_name.set(t_type)

                if t_type == "CONNECT":
                    self.gui_queue.put({"type": "STATUS", "msg": "Connecting...", "color": "orange"})
                    
                    # Thực hiện kết nối (hàm này từ eggtool.py)
                    is_connected = connect_device() 
                    
                    if is_connected:
                        self.gui_queue.put({"type": "LOG", "msg": "✅ Connected to device successfully!"})
                        self.gui_queue.put({"type": "STATUS", "msg": "Connected", "color": "green"})
                    else:
                        self.gui_queue.put({"type": "LOG", "msg": "❌ Connection failed. Check ADB/Port!"})
                        self.gui_queue.put({"type": "STATUS", "msg": "Failed", "color": "red"})
                elif t_type == "SCAN_STATS":
                    scan()

                elif t_type == "HATCHING_EGG":
                    if self.auto_mode:
                        self._execute_HATCHING_EGG()
                elif self.is_hunt.get() and t_type == "HUNTING":
                    if self.auto_mode:
                        self._execute_HUNTING()
                        # self.hunting_flag = False
                        time.sleep(3)
                        check_and_untap_gray_image()
                        time.sleep(3)

                        self._retrigger_hunting()
                elif self.is_ticket_hatching.get() and t_type == "TICKET_HATCHING":
                    if self.auto_mode:
                        self._execute_TICKET_HATCHING()

                elif t_type == "TICKET_GROWING":
                    if self.auto_mode:
                        self._execute_TICKET_GROWING(task.get("m_type"), task.get("m_val"))
                elif t_type == "REPLACE_DINO":
                    if self.auto_mode:
                        self._execute_REPLACE_DINO(task.get("d_type"))
                elif t_type == "ACTION":
                    task.get("func")()
                # if(flag == 1):
                #     check_and_untap_gray_image()
                self.current_task_name.set("Idle")
                self.task_queue.task_done()
                time.sleep(0.5)
            except Exception as e:
                self.gui_queue.put({"type": "LOG", "msg": f"Worker Error: {str(e)}"})

    # --- AUTO LOGIC (NON-BLOCKING) ---
# --- AUTO LOGIC (NON-BLOCKING) ---
    def _execute_HUNTING(self):
        if not self.is_hunt.get(): return
        self.gui_queue.put({"type": "LOG", "msg": "Hunting ARK 3-5 times"})

        time.sleep(1)

        try:
            check_and_tap_gray_image()
            while self.count <= 3:
                time.sleep(1); screenshot()
                img = Image.open("screenshot.png").crop(box=self.CROP_BOX)
                bbox = find_color_regions(img, self.target_colors, tolerance=5)
                if bbox:
                    highlight_color_regions(img, self.target_colors, tolerance=5, output_path="bubuchachalalala/highlighted_color.png")
                    highlight_color_path(img, self.target_colors_path, tolerance=5, output_path="bubuchachalalala/highlighted_color_path.png")
                    find_large_red_regions("bubuchachalalala/highlighted_color.png", min_area=self.MIN_AREA_THRESHOLD, erosion_kernel_size=5, output_path=self.RED_PATH)
                    find_large_green_regions("bubuchachalalala/highlighted_color_path.png", min_area=10, erosion_kernel_size=3, output_path=self.GREEN_PATH)
                    r_data, g_data, shape = get_filtered_centroids_and_contours(self.RED_PATH, self.GREEN_PATH)
                    merge_color_regions(self.RED_PATH, self.GREEN_PATH, output_path=self.FINAL_MERGED_PATH) 
                    if r_data or g_data:
                        remove_nearby_red_regions_optimized(r_data, g_data, shape, self.NEARBY_DISTANCE_THRESHOLD, self.FINAL_FILTERED_PATH)
                    
                    coords = extract_and_sort_final_red_locations(self.FINAL_FILTERED_PATH, self.OFFSET_X, self.OFFSET_Y, self.AIM_CENTER)
                    while coords:
                        hit_cX, hit_cY = coords[0]["Centroid (X, Y)"]
                        if not self.is_hunt.get(): return
                        smart_tap(hit_cX, hit_cY); time.sleep(1)
                        smart_tap(hit_cX, hit_cY - 350); time.sleep(1) # -350 -> -175
                        smart_tap(2174, 3562); time.sleep(1) # 2049, 3598
                        tap_x_to_close(); time.sleep(1); tap_x_to_close()
                        coords.pop(0); time.sleep(1); self.count += 1
                        if not self.auto_mode: return
                        if self.count == 4:
                            if not self.is_hunt.get():
                                return
                            smart_tap(3927, 3086)
                            time.sleep(1)
                            smart_tap(2608, 2964)
                            time.sleep(1)
                            smart_tap(2040, 2636)
                            time.sleep(1)
                            smart_tap(3925, 3348)
                            smart_tap(3925, 3348)

            self.count = 0

            time.sleep(1)
            # while not check_and_untap_gray_image():
            #     if check_and_untap_gray_image(): break
            #     time.sleep(1)
        except Exception as e: self.gui_queue.put({"type": "LOG", "msg": f"❌ Lỗi HUNTING: {str(e)}"})
    def _execute_TICKET_HATCHING(self):
        """Sử dụng Ticket và lên lịch kiểm tra lại dựa trên thời gian giảm trừ"""
        if not self.is_ticket_hatching.get(): return
        try:
            if self.is_ticket_hatching.get():
                # 1. Lấy giá trị phút từ Spinbox trên giao diện (mặc định 30, 45, ...)
                minutes_reduced = self.golden_ticket_var.get()
                self.gui_queue.put({"type": "LOG", "msg": f"🎫 Kích hoạt Ticket Hatching (Giảm {minutes_reduced} phút)..."})
                
                # 2. Gọi hàm core thực hiện thao tác tap trong game
                ticket_boosting_hatch()
                
                self.gui_queue.put({"type": "LOG", "msg": "✅ Đã dùng Ticket. Chờ xử lý quả trứng tiếp theo..."})

                # 3. Tính toán thời gian delay (chuyển từ phút sang miliseconds)
                # Chúng ta trừ đi 10 giây (10000ms) để trừ hao thời gian load animation của game
                delay_ms = max(1000, (minutes_reduced * 60 * 1000) + 15000)
                
                # 4. Lên lịch tự động quay lại kiểm tra trứng (Retrigger)
                self.root.after(delay_ms, self._retrigger_auto_ticket)
            else:
                # Nếu không dùng ticket, thực hiện kiểm tra định kỳ mặc định (ví dụ 5 giây)
                self.root.after(10000, self._retrigger_auto_ticket)
                
        except Exception as e:
            self.gui_queue.put({"type": "LOG", "msg": f"❌ Lỗi Ticket Hatching: {str(e)}"})
            # Thử lại sau 5 giây nếu có lỗi xảy ra
            self.root.after(10000, self._retrigger_auto_ticket)

    def _execute_TICKET_GROWING(self, mutation_type, mutation_value):
        """
        Xử lý sự kiện dùng Ticket để tăng chỉ số nhanh (Boosting)
        mutation_type: 'ATK' hoặc 'HP'
        mutation_value: Giá trị đột biến (1, 2, hoặc 3) để lấy số lần tap tương ứng từ UI
        """
        timestamp = time.strftime("%H:%M:%S")
        try:
            # Kiểm tra checkbox tổng cho Growing Ticket
            if not self.apply_ticket_grow.get():
                return

            # Xác định số lần cần tap dựa trên mức độ đột biến (+1, +2, hoặc +3)
            # Dữ liệu lấy từ các Spinbox trên UI
            n_times = 1
            if mutation_type == 'ATK':
                i = 1
                if mutation_value == 1: n_times = self.number_of_atk_1.get()
                elif mutation_value == 2: n_times = self.number_of_atk_2.get()
                else: n_times = self.number_of_atk_3.get()
            else: # HP
                if mutation_value == 1: n_times = self.number_of_hp_1.get()
                elif mutation_value == 2: n_times = self.number_of_hp_2.get()
                else: n_times = self.number_of_hp_3.get()
                i = 0

            self.gui_queue.put({"type": "LOG", "msg": f"🚀 Boosting {mutation_type} (+{mutation_value}) x{n_times} time(s)..."})
            
            # Gọi hàm core từ eggtool.py với tham số n_times
            if i == 1:
                time_grow = ticket_boosting_grow_atk(n_times)
                send_telegram_msg(f"[ {timestamp} ] ♻️ 🗡️ in {time_grow}s")
            else:
                time_grow = ticket_boosting_grow_hp(n_times)
                send_telegram_msg(f"[ {timestamp} ] ♻️ ❤️ in {time_grow}s")
 
            
            self.log_valid_dino({f"✅ Boosted {mutation_type}."})
            if time_grow and time_grow > 0:
                self.gui_queue.put({
                    "type": "LOG", 
                    "msg": f"⏳ WAITING {time_grow}s for replacing dino..."
                })
                self.root.after((int(time_grow*102.58/100)) * 1000, lambda: self.task_queue.put((2, {"type": "REPLACE_DINO","d_type": i})))
            else:
                self.log_trash_dino("⏳ [ERROR] CANNOT DEFINE THE BOOSTED DINO - REPLACE CANCELED")
            # Sau khi dùng ticket xong, cập nhật lại giao diện số lượng (nếu có biến đếm)
            self.gui_queue.put({"type": "REFRESH"})
            
        except Exception as e:
            self.gui_queue.put({"type": "LOG", "msg": f"❌ Lỗi Ticket Growing: {str(e)}"})
    def _execute_REPLACE_DINO(self, dino_type): #1 for atk and 0 for hp
        try:
            timestamp = time.strftime("%H:%M:%S")

            if dino_type == 1:
                message = f"[ {timestamp} ] ♻️ 🗡️ Replacing ATK nest"
                self.log_valid_dino(message)
                send_telegram_msg(message)
                # self.play_soft_success()
                # replace_lower_atk_position()

            else:
                message = f"[ {timestamp} ] ♻️ ❤️ Replacing HP nest"
                self.log_valid_dino(message)
                send_telegram_msg(message)
                # self.play_soft_success()
                # replace_lower_hp_position()
        except Exception as e:
            self.gui_queue.put({"type": "LOG", "msg": f"⚠️ Auto Error: {str(e)}"})
    def _execute_HATCHING_EGG(self):
        check_and_untap_gray_image()
        try:
            h_status = find_hatch()
            if h_status is True:
                entity = egg_loop(); self.gui_queue.put({"type": "REFRESH"})
                if entity:
                    m_type = "ATK" if entity.atk_or_hp else "HP"
                    m_val = entity.atk_increase if m_type=="ATK" else entity.hp_increase
                    # self.play_soft_success()
                    # import eggtool
                    # timestamp = time.strftime("%H:%M:%S")
                    # if m_type == "ATK":
                    #     message = (
                    #         f"[ {timestamp} ] 🗡️🔺 \n"
                    #         f"━━━━━━━━━━━━━━━━━━\n"
                    #         f"Max_ATK: {eggtool.min_atk}\n"
                    #         f"Min_ATK: {eggtool.min_min_atk}\n"
                    #         f"Mutation(s): + {m_val}"
                    #     )
                    #     send_telegram_msg(message)

                    # else:
                    #     message = (
                    #         f"[ {timestamp} ] ❤️🔺 \n"
                    #         f"━━━━━━━━━━━━━━━━━━\n"
                    #         f"Max_HP: {eggtool.min_hp}\n"
                    #         f"Min_HP: {eggtool.min_min_hp}\n"
                    #         f"Mutation(s): + {m_val}"
                    #     )
                    #     send_telegram_msg(message)

                self.root.after(0, lambda: self.task_queue.put((0, {"type": "HATCHING_EGG"})))
                if entity: self.root.after(5000, lambda: self.task_queue.put((2, {"type": "TICKET_GROWING", "m_type": m_type, "m_val": m_val})))
            elif isinstance(h_status, int) and h_status > 0:
                wait_s = min(h_status, 150)
                wait_s -= 13
                self.gui_queue.put({"type": "LOG", "msg": f"Egg breaks in {wait_s}s..."})
                loot_egg(); tap_x_to_close(); time.sleep(1); check_and_untap_gray_image()
                if not self.hunting_flag and self.is_hunt.get():
                    self.hunting_flag = True
                    self.task_queue.put((5, {"type": "HUNTING"}))
                self.root.after(wait_s * 1000, self._retrigger_auto)
            else:
                smart_tap(1330, 1510); time.sleep(1); home(); time.sleep(1); claim(); time.sleep(0.5); banish()
                self.root.after(20000, lambda: self.task_queue.put((0, {"type": "HATCHING_EGG"})))
        except Exception as e:
            self.gui_queue.put({"type": "LOG", "msg": f"⚠️ Auto Error: {str(e)}"})
            self.task_queue.put((1, {"type": "ACTION", "func": lambda: smart_tap(1910, 1774)})) # 3819, 3547
            self.root.after(5000, lambda: self.task_queue.put((0, {"type": "HATCHING_EGG"})))

    def _retrigger_auto(self):
        if self.auto_mode:
            self.task_queue.put((0,{"type": "HATCHING_EGG"}))
    def _retrigger_auto_ticket(self):
        if self.auto_mode:
            self.task_queue.put((3,{"type": "TICKET_HATCHING"}))
    def _retrigger_hunting(self):
        if self.auto_mode:
            self.task_queue.put((5,{"type": "HUNTING"}))
    # --- GUI QUEUE LISTENER ---
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
            
            #self.log_message(f"Settings updated - HP: {new_min_hp}, ATK: {new_min_atk}, Speed: {new_min_speed}")
        except ValueError as e:
            #print(f"❌ DEBUG: Lỗi giá trị khi update settings: {e}")
            messagebox.showerror("Error", "Please enter valid numbers for settings")
    def _listen_gui_queue(self):
        try:
            while True:
                task = self.gui_queue.get_nowait()
                t_type = task.get("type")
                
                if t_type == "LOG":
                    self._append_log(task['msg'])
                elif t_type == "REFRESH":
                    self.load_config()
                    self.update_count_display()
                elif t_type == "STATUS":
                    self.conn_status.config(text=f"Status: {task['msg']}", foreground=task['color'])
                
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._listen_gui_queue)

    def _update_debug_bar(self):
        q_size = self.task_queue.qsize()
        self.queue_label.config(text=f"Task Queue: {q_size} | Active: {self.current_task_name.get()}")
        self.root.after(300, self._update_debug_bar)

    # --- UI COMPONENTS ---
    def setup_gui(self):
        self.root.geometry("500x600")
        self.hp_gap_var = tk.StringVar(value="0")
        self.atk_gap_var = tk.StringVar(value="0")
        # Notebook
        nb = ttk.Notebook(self.root)
        nb.pack(expand=True, fill="both", padx=5, pady=5)
        
        main_tab = ttk.Frame(nb, padding=10)
        nb.add(main_tab, text="Main")

        # Connection
        c_frame = ttk.LabelFrame(main_tab, text="Connection")
        c_frame.pack(fill="x", pady=5)
        self.port_var = tk.StringVar(value="5555")
        ttk.Entry(c_frame, textvariable=self.port_var, width=10).pack(side="left", padx=5)
        ttk.Button(c_frame, text="Connect Device", 
                   command=lambda: self.task_queue.put((1,{"type": "CONNECT"}))).pack(side="left")
        self.conn_status = ttk.Label(c_frame, text="Status: Disconnected", foreground="red")
        self.conn_status.pack(side="left", padx=10)

        # Settings
        s_frame = ttk.LabelFrame(main_tab, text="Dino Settings")
        s_frame.pack(fill="x", pady=5)
        
        self.min_hp_var = tk.StringVar(value="0")
        self.min_atk_var = tk.StringVar(value="0")
        self.min_speed_var = tk.StringVar(value="0")

        self._create_stat_row(s_frame, "HP:", self.min_hp_var, 'hp', 0)
        self._create_stat_row(s_frame, "ATK:", self.min_atk_var, 'atk', 1)
        self._create_stat_row(s_frame, "SPD:", self.min_speed_var, 'speed', 2)
        ttk.Label(
            s_frame,
            text="Count:",
            takefocus=0
        ).grid(row=0, column=4, sticky="w")
        ttk.Label(
            s_frame,
            text="Count:",
            takefocus=0
        ).grid(row=1, column=4, sticky="w")
        ttk.Button(
            s_frame, 
            text="Scan Stats", 
            command=lambda: self.task_queue.put((1, {
                "type": "ACTION", 
                "func": lambda: scan()
            }))
        ).grid(row=4, column=0, columnspan=4, pady=(10, 0), sticky="ew")
        ttk.Label(
            s_frame,
            text="Count:",
            takefocus=0
        ).grid(row=2, column=4, sticky="w")
        
        self.hp_count_label = ttk.Label(s_frame, text="0", background="white",width=2)
        self.hp_count_label.grid(row=0, column=5, padx=5)
        self.atk_count_label = ttk.Label(s_frame, text="0", background="white",width=2)
        self.atk_count_label.grid(row=1, column=5, padx=5)
        self.speed_count_label = ttk.Label(s_frame, text="0", background="white",width=2)
        self.speed_count_label.grid(row=2, column=5, padx=5)
        ttk.Button(s_frame, text="Reset Count", 
                  command=self.reset_counts).grid(row=3, column=4, columnspan=2, pady=(10, 0))
        # ttk.Button(s_frame, text="Test", 
        #           command=self.test).grid(row=3, column=5, columnspan=2, pady=(10, 0))
        ttk.Label(s_frame, text="Max level:").grid(row=3, column=0)
        self.min_lvl_label = ttk.Label(s_frame, text="0", font=("Arial", 10, "bold"))
        self.min_lvl_label.grid(row=3, column=1)

        # Controls
        ctrl = ttk.Frame(main_tab)
        ctrl.pack(pady=10)
        ttk.Button(ctrl, text="🚀 START", command=self.toggle_auto_mode).pack(side="left", padx=5)
        ttk.Button(ctrl, text="🛑 STOP", command=self.stop_all).pack(side="left", padx=5)

        # Log
        self.log_text = tk.Text(main_tab, height=12, width=55)
        self.log_text.pack(fill="both", expand=True)

        # Debug Bar
        self.queue_label = ttk.Label(self.root, text="Queue: 0", font=("Consolas", 9))
        self.queue_label.pack(side="bottom", fill="x")
        ##########################################
        apply_tap = ttk.Frame(nb, padding="10")
        nb.add(apply_tap, text="Application")

        # biến trạng thái
        self.is_hunt = tk.BooleanVar(value=False) # Khởi tạo ở đây
        # label "Enable application" ở bên trái
        phero_frame = ttk.LabelFrame(
            apply_tap,
            text="Hunting",
            padding="10"
        )
        phero_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # self.apply_phoromone_hp = tk.BooleanVar(value=False)
        # ttk.Label(
        #     phero_frame,
        #     image=self.pho_icon,
        #     takefocus=0
        # ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            phero_frame,
            text="",
            takefocus=0
        ).grid(row=1, column=0, sticky="w")
        
        ttk.Checkbutton(
            phero_frame,
            variable=self.is_hunt
        ).grid(row=1, column=1, padx=(20, 0), sticky="w")
        # ttk.Label(
        #     phero_frame,
        #     text="HP",
        #     takefocus=0
        # ).grid(row=2, column=0, sticky="w")
        
        # ttk.Checkbutton(
        #     phero_frame,
        #     variable=self.apply_phoromone_hp
        # ).grid(row=2, column=1, padx=(20, 0), sticky="w")
        # #ticket
        ticket_frame = ttk.LabelFrame(
            apply_tap,
            text="Ticket",
            padding="10"
        )
        ticket_frame.grid(row=1, column=0, sticky="w")

        self.apply_ticket_grow = tk.BooleanVar(value=True)

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
        self.number_of_atk_1 = tk.IntVar(value=2)
        self.number_of_atk_2 = tk.IntVar(value=2)
        self.number_of_atk_3 = tk.IntVar(value=2)
        ttk.Label(ticket_frame, text="for ATK:", takefocus=0).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(ticket_frame, text ="+1:", takefocus=0).grid(
            row=3, column=1, sticky="w"
        )

        atk_nums = tk.Spinbox(
            ticket_frame,
            from_=0,
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
        self.number_of_hp_1 = tk.IntVar(value=2)
        self.number_of_hp_2 = tk.IntVar(value=2)
        self.number_of_hp_3 = tk.IntVar(value=2)

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=0,
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

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=0,
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

        hp_nums = tk.Spinbox(
            ticket_frame,
            from_=0,
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
        self.is_ticket_hatching = tk.BooleanVar(value=True)
        ttk.Label(ticket_frame, text="HATCHING", takefocus=0).grid(
            row=12, column=0, sticky="w"
        )
        ttk.Checkbutton(
            ticket_frame,
            variable=self.is_ticket_hatching
        ).grid(row=12, column=1, padx=(20, 0), sticky="w")
        self.golden_ticket_var = tk.IntVar(value=30)
        golden_spinbox = tk.Spinbox(
            ticket_frame,
            from_=30,
            to=9999,
            increment=15,
            textvariable=self.golden_ticket_var,
            width=4
        )
        golden_spinbox.grid(row=12, column=2, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(
            ticket_frame,
            text="mins"
        ).grid(row=12, column=3, sticky=tk.W)
    def _create_stat_row(self, frame, txt, var, stype, r):
        ttk.Label(frame, text=txt).grid(row=r, column=0)
        ttk.Entry(frame, textvariable=var, width=8).grid(row=r, column=1)
        ttk.Button(frame, text="➖", width=3, command=lambda: self.adjust_val(stype, -1)).grid(row=r, column=2)
        ttk.Button(frame, text="➕", width=3, command=lambda: self.adjust_val(stype, 1)).grid(row=r, column=3)

    # --- LOGIC HELPER ---
    def adjust_val(self, stype, delta):
        import eggtool
        if stype == 'hp': eggtool.min_min_hp = max(0, eggtool.min_min_hp + delta*10); self.min_hp_var.set(str(eggtool.min_min_hp))
        elif stype == 'atk': eggtool.min_min_atk = max(0, eggtool.min_min_atk + delta); self.min_atk_var.set(str(eggtool.min_min_atk))
        elif stype == 'speed': eggtool.min_speed = max(0, eggtool.min_speed + delta); self.min_speed_var.set(str(eggtool.min_speed))
        self.calculate_lvl()
        self.save_config()
    def test(self):
        self.root.after(1000, lambda: self.task_queue.put((2, {"type": "REPLACE_DINO","d_type": 1})))

    def toggle_auto_mode(self):
        if not self.auto_mode and not self.trigger_flag:
            self.auto_mode = True
            self.trigger_flag = True
            self.hunting_flag = False

            # self.task_queue.put((0,{"type": "CONNECT"}))
            self.gui_queue.put({"type": "LOG", "msg": "🚀 Auto Mode ON"})
            self.task_queue.put((0, {"type": "HATCHING_EGG"}))
            self.task_queue.put((3, {"type": "TICKET_HATCHING"}))
            return
        if not self.auto_mode:
            self.auto_mode = True
            self.gui_queue.put({"type": "LOG", "msg": "🚀 Auto Mode ON"})
            self.task_queue.put((0, {"type": "HATCHING_EGG"}))
            return

        else:
            self.auto_mode = False
            self.gui_queue.put({"type": "LOG", "msg": "⏹️ Auto Mode OFF"})
    def stop_all(self):
        """Dừng ngay lập tức và dọn dẹp hàng chờ"""
        self.auto_mode = False
        self.hunting_flag = False
        
        # 1. Dọn dẹp Task Queue (Xóa hết các lệnh đang xếp hàng)
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break
        
        # 2. Log thông báo
        self.gui_queue.put({"type": "LOG", "msg": "🛑 STOPPED"})
    def _append_log(self, msg):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)

    def calculate_lvl(self):
        import eggtool
        lvl = (eggtool.min_hp // 10) + eggtool.min_atk + eggtool.min_speed
        self.min_lvl_label.config(text=str(lvl))

    def update_count_display(self):
        import eggtool
        self.hp_count_label.config(text=str(getattr(eggtool, 'hp_count', 0)))
        self.atk_count_label.config(text=str(getattr(eggtool, 'atk_count', 0)))
        self.speed_count_label.config(text=str(getattr(eggtool, 'speed_count', 0)))

    def save_config(self):
        try:
            import eggtool
            # Đọc dữ liệu cũ để giữ lại các trường min_min nếu GUI không sửa
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    current_cfg = json.load(f)
            else:
                current_cfg = {}

            # Lấy dữ liệu từ các ô nhập liệu trên GUI
            current_cfg["port"] = self.port_var.get()
            current_cfg["min_hp"] = int(self.min_hp_var.get())
            current_cfg["min_atk"] = int(self.min_atk_var.get())
            current_cfg["min_speed"] = int(self.min_speed_var.get())
            
            # Cập nhật các trường min_min và gap từ biến global (do scan tạo ra)
            current_cfg["min_min_hp"] = getattr(eggtool, 'min_min_hp', current_cfg.get("min_min_hp", 0))
            current_cfg["min_min_atk"] = getattr(eggtool, 'min_min_atk', current_cfg.get("min_min_atk", 0))
            current_cfg["hp_gap"] = eggtool.hp_gap
            current_cfg["atk_gap"] = eggtool.atk_gap

            with open(self.config_file, 'w') as f:
                json.dump(current_cfg, f, indent=2)
        except Exception as e:
            self._append_log(f"⚠️ Lỗi lưu config: {e}")
    def load_config(self):

        import eggtool
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                c = json.load(f)
                # Cập nhật biến global bên eggtool
                eggtool.min_hp = c.get('min_hp', 0)
                eggtool.min_min_hp = c.get('min_min_hp', 0)
                eggtool.min_atk = c.get('min_atk', 0)
                eggtool.min_min_atk = c.get('min_min_atk', 0)
                eggtool.min_speed = c.get('min_speed', 0)
                eggtool.hp_gap = c.get('hp_gap', 0)
                eggtool.atk_gap = c.get('atk_gap', 0)

                # Cập nhật giao diện
                self.min_hp_var.set(str(eggtool.min_min_hp))
                self.min_atk_var.set(str(eggtool.min_min_atk))
                self.min_speed_var.set(str(eggtool.min_speed))
                self.hp_gap_var.set(str(eggtool.hp_gap))   # Cập nhật gap
                self.atk_gap_var.set(str(eggtool.atk_gap))
                
                # Gán giá trị atk_gap vào biến a như bạn muốn

        self.calculate_lvl()
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
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
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        # Tô màu dòng cuối cùng thành đỏ
        self.log_text.tag_add("trash", "end-2l", "end-1l")
        self.log_text.tag_config("trash", foreground="red")
        self.log_text.see(tk.END)
        self.root.update()
    def reset_counts(self):
        """Đặt lại toàn bộ bộ đếm chỉ số về 0"""
        import eggtool
        # 1. Reset các biến trong file eggtool
        eggtool.hp_count = 0
        eggtool.atk_count = 0
        eggtool.speed_count = 0
        
        # 2. Ghi log để người dùng biết
        self._append_log("♻️")
        
        # 3. Cập nhật hiển thị lên giao diện
        self.update_count_display()
        
        # 4. (Tùy chọn) Lưu vào file nếu bạn muốn lưu trạng thái reset
        # self.save_config()
    
def main():
    root = tk.Tk()
    app = EggToolGUI(root)
    import eggtool
    eggtool.gui_logger = app
    root.mainloop()

if __name__ == "__main__":
    main()