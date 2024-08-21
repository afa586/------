from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import json
import pandas as pd
import os
from PIL import Image, ImageTk


class LotteryApp(ttk.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill=BOTH, expand=YES)
        self.is_all_participants = ttk.BooleanVar(value=False) # 是否所有人都参加
        self.is_allow_reserve = ttk.BooleanVar(value=False) # 是否允许内定
        self.participants = pd.DataFrame(columns=['Name']) # 所有抽奖参与者
        self.participants_not_win = pd.DataFrame(columns=['Name']) # 尚未中奖参与者        
        self.awards = pd.DataFrame(columns=['Award', 'Quota']) # 奖项信息
        self.winners = pd.DataFrame(columns=['Award', 'Name']) # 获奖者
        self.winners_reserve = pd.DataFrame(columns=['Award', 'Name']) # 内定获奖者
        self.display_interval = 100 # 随机名单切换时间， 可修改
        self.in_progress = False # 是否正在抽奖， 用于决定抽奖按钮功能
        self.selected_participants = None # 随机抽取的参与者
        self.current_winners = None # 随机抽取的参与者数组
        self.draw_count = 1 # 一次抽取人数
        self.current_award = None # 选中奖项
        self.current_award_quota = 0 # 选中奖项配额
        self.current_award_remain_quota = 0 # 选中奖项剩余配额  
        self.load_settings()
        self.setup_ui()
        self.load_data()
 
    def load_settings(self):
        self.param_file_path = Path('config.json')
        if not self.param_file_path.exists():
            # 如果文件不存在，创建默认参数文件
            default_params = {
                "software_name": "抽奖软件",
                "title": "年会抽奖软件",
                "width": "1024",
                "height": "768",
                "data_folder": "data",            
                "default_count": 1,
                "display_interval": 50,
                "is_allow_reserve": False
            }
            with open(self.param_file_path, 'w', encoding='utf-8') as f:
                json.dump(default_params, f)

        # 读取 JSON 参数文件
        with open(self.param_file_path, encoding='utf-8') as f:
            self.config = json.load(f)

        self.software_name = self.config.get('software_name', '抽奖软件')  #软件名称      
        self.title = self.config.get('title', '年会抽奖软件')   #标题     
        self.data_folder = self.config.get('data_folder', 'data') #数据文件夹名称
        self.bg_imge_path = os.path.join(self.data_folder, 'background.jpg') #背景图片路
        self.default_count = self.config.get('default_count', 1) #默认抽取人数
        self.display_interval = self.config.get('display_interval', 100) #名单切换时间
        self.is_allow_reserve.set(self.config.get('is_allow_reserve', False)) #是否允许内定

        
    def apply_settings(self):    
        self.master.geometry(f"{self.config.get('width', 1024)}x{self.config.get('height', 768)}")
        self.update_draw_count_entry(self.default_count) 
        self.draw_count_scale.set(self.default_count)
        self.title_label.config(text=self.title)
        self.master.title(self.software_name)
        self.is_allow_reserve_checkbutton.config()
        
    
    def setup_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True)

        # 抽奖标签
        self.lottery_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.lottery_tab, text='抽奖')
        self.load_background_image()
        self.setup_lottery_ui()        


        # 抽奖结果标签
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text='抽奖结果')
        self.setup_result_ui()


        # 设置标签
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text='设置')
        self.setup_settings_ui()


        # 使用说明
        self.about_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.about_tab, text='使用说明')
        self.setup_about_ui()

        self.notebook.bind("<<NotebookTabChanged>>", self.refresh_results_if_needed)      

 
    def load_background_image(self):
        if os.path.exists(self.bg_imge_path):
            self.bg_image = Image.open(self.bg_imge_path)
            self.bg_image = self.bg_image.resize((self.master.winfo_width(), self.master.winfo_height()),
                                                  Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.lottery_tab, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            # 绑定窗口大小变化事件
            self.master.bind("<Configure>", self.resize_background)


    def resize_background(self, event):
        if os.path.exists(self.bg_imge_path):
            self.bg_image = Image.open(self.bg_imge_path)
            self.bg_image = self.bg_image.resize((event.width, event.height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label.config(image=self.bg_photo)


    def setup_lottery_ui(self):
        # 重置按钮
        self.reset_button = ttk.Button(self.lottery_tab, text="重置", command=self.reset_lottery, bootstyle=DANGER)
        self.lottery_tab.pack_propagate(False)  # 防止框架根据子控件调整大小
        self.reset_button.grid(row=0, column=0,padx=10,pady=10)  # 放在右上角) 

        # 软件名称显示
        self.title_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 30),bootstyle='danger')
        self.title_label.pack(side=ttk.TOP, pady=20)   
        

        # 正在抽取奖项显示
        self.current_awards_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 20), bootstyle=DANGER)
        self.current_awards_label.pack(side=ttk.TOP, pady=10)
        self.current_awards_label.config(text='')

        # 所有奖项信息显示
        self.awards_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 20),bootstyle='default',background='pink')
        self.awards_label.pack(side=ttk.TOP, pady=10)
        # 绑定Notebook的<TabChanged>事件
        # self.notebook.bind("<<NotebookTabChanged>>", self.refresh_results_if_needed)          

        # 奖项选择下拉菜单
        self.draw_option_row_frame = ttk.Frame(self.lottery_tab)
        self.draw_option_row_frame.pack()
        self.award_option_label = ttk.Label(self.draw_option_row_frame, text="奖项:", font=("FangSong", 16), bootstyle='primary')
        self.award_option_label.pack(side=ttk.LEFT, padx=5)
        self.award_var = ttk.StringVar()
        self.award_option_menu = ttk.Combobox(self.draw_option_row_frame, textvariable=self.award_var, font=("Arial", 16), state='readonly')
        self.award_option_menu.pack(side=ttk.LEFT, padx=5)
        self.award_option_menu.bind('<<ComboboxSelected>>', self.check_award_selected)

        # 待抽奖名字显示文本框
        self.name_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 25),bootstyle="danger")
        self.name_label.pack(side=ttk.TOP, pady=50)      

        # 是否所有人参与， 默认只有未中奖人员参与
        self.is_all_participants_checkbutton = ttk.Checkbutton(self.lottery_tab, text="所有人员参与抽奖",
                                      variable=self.is_all_participants,
                                      offvalue=False,
                                      onvalue=True)
        self.is_all_participants_checkbutton.pack(side=ttk.TOP, pady=20)        

        # 每次抽取人数输入
        self.draw_count_row_frame = ttk.Frame(self.lottery_tab)
        self.draw_count_row_frame.pack()

        self.draw_count_label = ttk.Label(self.draw_count_row_frame, text="抽取人数:", font=("FangSong", 16), bootstyle='primary')
        self.draw_count_label.pack(side=ttk.LEFT, padx=5)

        self.draw_count_entry = ttk.Entry(self.draw_count_row_frame, font=("FangSong", 16), width=5, bootstyle='primary',justify='center')
        self.draw_count_entry.pack(side=ttk.LEFT, padx=5)
   

        self.draw_count_scale = ttk.Scale(self.draw_count_row_frame, from_=1, to=10, orient='horizontal', command=self.update_draw_count_entry)  
        self.draw_count_scale.pack(side=ttk.LEFT, padx=5)

        # 抽奖按钮
        self.draw_button = ttk.Button(self.lottery_tab, text="开始", bootstyle='primary', command=self.start_pick)
        self.draw_button.pack(side=ttk.TOP, pady=10)
        # 绑定空格和回车键按下事件到 start_pick 方法
        self.master.bind('<Return>', self.start_pick)  # 回车键
        # self.root.bind('<space>', self.start_pick)   # 空格键

        # 结果显示
        self.result_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 15), bootstyle=DANGER)
        self.result_label.pack(side=ttk.TOP, pady=20)  
        self.result_label.config(text='') 
        

    def load_data(self):    
        participants_path = os.path.join(self.data_folder, 'participants.xlsx')
        awards_path = os.path.join(self.data_folder, 'awards.xlsx')
        winners_path = os.path.join(self.data_folder, 'winners.xlsx')
        winners_reserve_path = os.path.join(self.data_folder, 'winners_reserve.xlsx')
        
        # 检查是否为VIP
        try:
            with open('SN.txt', 'r', encoding='utf-8' ) as file:
                SN = file.read()
        except FileNotFoundError:
            SN = None
        if SN == '天王盖地虎':
            self.is_VIP = True
            # print(SN)
        else:
            self.is_VIP = False
            self.is_allow_reserve.set(False) #不允许内定 

        # 加载或创建Excel文件
        self.load_or_create_excel(participants_path, {'Name': ['参与者1', '参与者2', '参与者3']})
        self.load_or_create_excel(awards_path, {'Award': ['一等奖', '二等奖', '三等奖'], 'Quota': [1, 2, 3]})            

        self.awards = pd.read_excel(awards_path)
        if os.path.exists(winners_path):
            self.winners = pd.read_excel(winners_path)
        self.participants = pd.read_excel(participants_path)  
        # print(self.is_allow_reserve.get())
        if self.is_allow_reserve.get():
            self.load_or_create_excel(winners_reserve_path, {'Award': [], 'Name': []})     
            self.winners_reserve = pd.read_excel(winners_reserve_path)  
        else:
            if os.path.exists(winners_reserve_path):
                os.remove(winners_reserve_path)     
        self.award_option_menu['values'] = self.awards['Award'].unique().tolist()
        self.update_award_status()
        self.apply_settings()
 


    def update_draw_count_entry(self,value):
        int_value = int(float(value))
        self.draw_count_entry.config(state='normal')  # 临时允许修改
        self.draw_count_entry.delete(0, 'end')  # 清空原有内容
        self.draw_count_entry.insert(0, str(int(int_value)))  # 插入新值
        self.draw_count_entry.config(state='readonly')  # 恢复只读状态


    def load_or_create_excel(self, file_path, data):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists(file_path):
            pd.DataFrame(data).to_excel(file_path, index=False, engine='openpyxl')


    def reset_lottery(self):
         # 重置抽取人数输入框
        self.update_draw_count_entry(self.default_count)

        # 重置中奖者名单
        self.winners = pd.DataFrame(columns=['Award', 'Name'])

        # 重命名现有的winners文件（如果存在）
        winners_path = os.path.join(self.data_folder, 'winners.xlsx')
        new_winners_path = os.path.join(self.data_folder, 'winners_old.xlsx')
        if os.path.exists(new_winners_path):
            os.remove(new_winners_path)
        if os.path.exists(winners_path):
            os.rename(winners_path, new_winners_path)        

        # 清空界面上的显示
        self.name_label.config(text='')
        self.result_label.config(text='')
        # self.award_option_menu.set('请选择奖项')  # 重置奖项选择下拉菜单

        # 重新加载数据
        self.load_data()

        # 显示重置成功的消息
        messagebox.showinfo("重置", "抽奖已重置！")
        self.draw_count_scale.focus_set()


    def update_award_status(self, event = None):
        self.participants_not_win = self.participants[~self.participants['Name'].isin(self.winners['Name'])]
        label_text = ''        
        total_awards =  len(self.awards['Award'].unique().tolist())
        total_participants = len(self.participants['Name'].unique().tolist())
        winner_number = len(self.winners['Name'].unique().tolist())
        participants_not_win_count = 0 if self.participants_not_win.empty else len(self.participants_not_win['Name'].unique().tolist())
        label_text += f"总奖项{total_awards},总人数{total_participants},已中奖{winner_number}人,未中奖{participants_not_win_count}人"             
        for index, row in self.awards.iterrows():
            award_name = row['Award']
            quota = row['Quota']
            used_quota = self.winners[(self.winners['Award'] == award_name) & (self.winners['Name'].notnull())]['Name'].count()
            remain_quota = quota - used_quota
            label_text +=  f"\n{award_name} {quota}/{remain_quota}"       
        self.awards_label.config(text=label_text)


    def check_award_selected(self, event=None):
        try:
            self.draw_count = int(self.draw_count_entry.get())
        except ValueError:
            return {'status':False, 'message':'错误：请输入有效的人数! \n'}
        self.current_award = self.award_var.get()
        if not self.current_award or self.current_award  == '请选择奖项':
           return {'status':False, 'message':'请选择奖项!\n'} 
        else:
            self.current_awards_label.config(text=f"正在抽取{self.current_award}")
         # 检查奖项的剩余数量
        award_index = self.awards[self.awards['Award'] == self.current_award].index
        self.current_award_quota = self.awards.loc[award_index, 'Quota'].item()
        used_quota = self.winners[(self.winners['Award'] == self.current_award) & (self.winners['Name'].notnull())]['Name'].count()
        # used_quota = self.winners[self.winners['Award'] == self.current_award]['Name'].count()
        self.current_award_remain_quota = self.current_award_quota - used_quota
        self.update_award_status()        
        if self.current_award_remain_quota >= self.draw_count:            
            return {'status':True, 'message':'没发现错误'}
        else:
            return {'status':False, 'message':f'奖项({self.current_award})剩余配额不足！'}
        
        

    def get_winners(self):
        if self.is_all_participants.get():
            get_sample_from = self.participants
        else:
            get_sample_from = self.participants_not_win
        

    # 循环显示名字，直到再次按下抽奖按钮            
        if self.in_progress:    
            self.selected_participants = get_sample_from.sample(n=self.draw_count)
            self.current_winners = self.selected_participants['Name'].tolist()                                    
            self.name_label.config(text=','.join(self.current_winners))
            # 设置定时器，用于快速轮流显示名字
            self.master.after(self.display_interval, self.get_winners)
        else:  
            # 检查是否开启内定功能   
            if self.is_allow_reserve.get():
                get_sample_from = get_sample_from[~get_sample_from['Name'].isin(self.winners_reserve['Name'])]
                match_reserves = self.winners_reserve[(self.winners_reserve['Award'] == self.current_award) & (~self.winners_reserve['Name'].isin(self.winners['Name']))]
                match_reserves_count = match_reserves['Name'].count()
                if match_reserves_count > 0:
                    if match_reserves_count >= self.draw_count:
                        self.selected_participants = match_reserves.sample(n=self.draw_count)
                    else:
                        other_winners = get_sample_from.sample(n=self.draw_count - match_reserves_count)
                        self.selected_participants =  pd.concat([other_winners, match_reserves], ignore_index=True)
                else:
                    self.selected_participants = get_sample_from.sample(n=self.draw_count) 
            else:
                self.selected_participants = get_sample_from.sample(n=self.draw_count)
            self.current_winners = self.selected_participants['Name'].tolist()
            self.name_label.config(text=','.join(self.current_winners))  
            self.result_label.config(text=f"恭喜 {', '.join(self.current_winners)} 获得{self.current_award}") 
            # 更新中奖者名单
            new_winners = pd.DataFrame({'Award': [self.current_award]*len(self.current_winners), 'Name': self.current_winners})
            self.winners = pd.concat([self.winners, new_winners], ignore_index=True)
            self.check_award_selected()
            # 保存更新后的中奖者名单
            self.winners.to_excel(os.path.join(self.data_folder, 'winners.xlsx'), index=False)
    

    

    def start_pick(self, event = None):
        # print(f'全体人员参与开关状态： {self.is_all_participants.get()}')
        result = self.check_award_selected()
        if result['status']:
            if self.in_progress:
                self.in_progress = False
                self.draw_button.config(text='开始')
            else:
                self.in_progress = True
                self.draw_button.config(text='结束')
                self.get_winners() 
        else:
             self.result_label.config(text=f"注意：{result['message']}")   



    def setup_result_ui(self):
        # 创建结果表格
        self.results_table = ttk.Treeview(self.result_tab, columns=('Award', 'Name'), show='headings', selectmode='browse', bootstyle='info')
        self.results_table.heading('Award', text='奖项')
        self.results_table.heading('Name', text='获奖者')
        self.results_table.column('Award', width=100)
        self.results_table.column('Name', width=100)
        self.results_table.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)

        # 滚动条
        self.vsb = ttk.Scrollbar(self.result_tab, orient='vertical', command=self.results_table.yview)
        self.results_table.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side=ttk.RIGHT, fill='y')

        self.hsb = ttk.Scrollbar(self.result_tab, orient='horizontal', command=self.results_table.xview)
        self.results_table.configure(xscrollcommand=self.hsb.set)
        self.hsb.pack(side=ttk.BOTTOM, fill='x')

        # 绑定 Treeview 的选中事件
        self.results_table.bind('<<TreeviewSelect>>', self.on_selection_changed)

        # 撤销按钮
        self.revoke_button = ttk.Button(self.result_tab, text="撤销选中", command=self.revoke_selected_winner)
        self.revoke_button.pack(side=ttk.BOTTOM, pady=10)
        self.revoke_button['state'] = 'disabled'  # 禁用点击

        # 确保表格在Notebook中正确显示
        # self.notebook.select(self.result_tab)

    def refresh_results_if_needed(self, event):
        # 检查当前激活的标签页是否是结果页
        if self.notebook.index(self.notebook.select()) == 1:  # 索引1对应于 "抽奖结果" 标签页
            # 更新结果数据
            self.show_results()

    def on_selection_changed(self, event):
        # 当选中的行发生变化时，更新撤销按钮的状态
        selection = self.results_table.selection()
        if selection:
            self.revoke_button['state'] = 'normal'  # 允许点击
        else:
            self.revoke_button['state'] = 'disabled'  # 禁用点击

    
    def action_when_change_tab(self, event):
        # 检查当前激活的标签页是否是结果页
        if self.notebook.index(self.notebook.select()) == 1:  # 索引1对应于 "抽奖结果" 标签页
            # 更新结果数据
            self.show_results()

    def show_results(self):
         # 清空结果表格
        for i in self.results_table.get_children():
            self.results_table.delete(i)
        # 插入抽奖结果
        for index, row in self.winners.iterrows():
            self.results_table.insert('', 'end', values=(row['Award'], row['Name']))   

    def revoke_selected_winner(self):
        # 获取选中的行
        selected_row = self.results_table.selection()
        if not selected_row:
            messagebox.showerror("错误", "请先选中一个中奖者")
            return

        # 获取选中行的奖项和名字
        award = self.results_table.item(selected_row, 'values')[0]
        name = self.results_table.item(selected_row, 'values')[1]

        # 根据奖项和名字查找中奖者并从 winners DataFrame 中删除
        to_revoke = self.winners[(self.winners['Award'] == award) & (self.winners['Name'] == name)]
        if to_revoke.empty:
            messagebox.showerror("错误", "未找到匹配的中奖者")
            return

        # 删除匹配的行
        self.winners = self.winners.drop(to_revoke.index)

        # 刷新显示结果
        self.update_award_status()
        self.show_results()

        # 保存更新后的中奖者名单
        self.winners.to_excel(os.path.join(self.data_folder, 'winners.xlsx'), index=False)
        messagebox.showinfo("操作成功", f"已撤销 {award} - {name}")



    def setup_settings_ui(self):
        # 配置信息
        self.setting_info = ttk.Labelframe(self.settings_tab, text='配置信息', padding=10)
        self.setting_info.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)
        # self.setting_info.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)

        self.entries_info = [
            ('软件名称', 'software_name'),
            ('抽奖标题', 'title'),
            ('窗体宽度', 'width'),
            ('窗体高度', 'height'),
            ('数据文件夹名', 'data_folder'),
            ('默认抽取人数', 'default_count'),
            ('滚动间隔时间(ms)', 'display_interval')
        ]

        row = 0
        col = 0
        for desc, conf_key in self.entries_info:
            # 配置项描述标签
            ttk.Label(self.setting_info, text=desc).grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)

            # 配置项输入框
            entry_var = tk.StringVar()
            entry = ttk.Entry(self.setting_info, textvariable=entry_var)
            entry.grid(row=row, column=col+1, padx=5, pady=2, sticky=tk.W+tk.E)
            entry.insert(0, self.config.get(conf_key, ''))
            
            # 保存每个entry_var的引用，以便在save_settings中使用
            setattr(self, f'setting_{conf_key}_entry', entry_var)
            row += 1

        self.is_allow_reserve_checkbutton = ttk.Checkbutton(self.setting_info, text="高级功能",
                                        variable=self.is_allow_reserve,
                                        command=self.check_vip_and_update_checkbutton,
                                        offvalue=False,
                                        onvalue=True)
        self.is_allow_reserve_checkbutton.grid(row=row, columnspan=len(self.entries_info)+2, padx=5, pady=10)

        # 保存按钮
        self.settings_save_button = ttk.Button(self.setting_info, text="保存", command=self.save_settings)
        self.settings_save_button.grid(row=row+1, columnspan=len(self.entries_info)+2, padx=5, pady=10)

    
    def check_vip_and_update_checkbutton(self):
        if self.is_allow_reserve.get() and not self.is_VIP:
            self.is_allow_reserve.set(False)
            messagebox.showwarning('注意','高级功能可以通过发红包， 请吃饭等方式获得!')
 

    def save_settings(self):
        setting_params = {}
        errors = []
    
        for desc, conf_key in self.entries_info:
            entry_var = getattr(self, f'setting_{conf_key}_entry')
            value = entry_var.get()
            if conf_key in ['width', 'height', 'default_count', 'display_interval']:
                # 尝试转换为整数，并检查是否在合理范围内
                try:
                    value = int(value)
                    if value <= 0:
                        errors.append(f"{desc} 必须大于0")
                except ValueError:
                    errors.append(f"{desc} 必须是数字")
            
            setting_params[conf_key] = value

        if errors:
            messagebox.showerror("错误", "\n".join(errors))
        else:
            setting_params['is_allow_reserve'] = self.is_allow_reserve.get()
            try:
                with open(self.param_file_path, 'w', encoding='utf-8') as f:
                    json.dump(setting_params, f)
                messagebox.showinfo("保存", "保存成功")
                self.load_settings()
                self.load_data()    
            except Exception as e:
                messagebox.showerror("错误", str(e))


    def setup_about_ui(self):
        # 配置信息
        self.about_info = ttk.Labelframe(self.about_tab, text='使用说明', padding=10)
        self.about_info.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)
        # 使用说明标签
        about_string = f'''
        1. 可以通过设置页修改标题， 窗口大小，数据文件夹名称，默认抽取人数，滚动间隔时间等信息。\n
        2. 重启软件不会清空中奖者名单， 重新抽奖需要点击左上角的重置按钮来清空中奖者名单。\n
        3. 可以替换{self.data_folder}文件夹中的background.jpg来更换背景图片。\n        
        4. 通过更新 {os.path.join(self.data_folder, 'awards.xlsx')} 文件来更新奖项信息。\n
        5. 通过更新 {os.path.join(self.data_folder, 'participants.xlsx')} 文件来更新参与抽奖人员信息。\n
        6. 拖动滑块可以修改一次抽取人数。\n
        7. 默认仅未中奖人员参与抽奖， 如果需要所有人员参加抽奖可勾选 {self.is_all_participants_checkbutton.cget("text")} 开关。\n
        8. 点击开始按钮（或者按回车键）人员名单开始随机滚动， 点击结束按钮（或者按回车键）名单停止滚动并显示中奖者名单。\n
        9. 抽奖结果页可以查看或者撤销中奖名单。\n        
        '''
        self.description_label = ttk.Label(self.about_info, text=about_string)
        self.description_label.pack()

        # 版本和作者信息
        self.version_author_label = ttk.Label(self.about_tab, text="版本：1.1  作者：Tom Wu", font=("FangSong", 12), bootstyle='info')
        self.version_author_label.pack(side=ttk.BOTTOM, anchor=ttk.SE, pady=10) 
    
    

if __name__ == '__main__':    
    app = ttk.Window('', "cosmo")    
    LotteryApp(app)
    app.mainloop()