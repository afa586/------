import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import configparser


class LotteryApp:
    def __init__(self, root):
        self.root = root
        self.participants = pd.DataFrame(columns=['Name']) # 所有抽奖参与者
        self.participants_not_win = None # 尚未中奖参与者
        self.is_all_participants = tk.BooleanVar(value=False) # 是否所有人都参加
        self.awards = pd.DataFrame(columns=['Award', 'Quota']) # 奖项信息
        self.winners = pd.DataFrame(columns=['Award', 'Name']) # 获奖者
        self.display_interval = 100 # 随机名单切换时间， 可修改
        self.in_progress = False # 是否正在抽奖， 用于觉得抽奖按钮功能
        self.selected_participants = None # 随机抽取的参与者
        self.current_winners = None # 随机抽取的参与者数组
        self.data_folder = 'data' # 数据文件夹名称
        self.load_config()      
        self.draw_count = 0 # 抽取人数
        self.current_award = None # 选中奖项
        self.current_award_quota = 0 # 选中奖项配额
        self.current_award_remain_quota = 0 # 选中奖项剩余配额
        self.selected_award = '' # 选择奖项
        self.bg_imge_path = os.path.join(self.data_folder, 'background.jpg') #背景图片路径
        self.setup_ui()
        self.root.bind("<Configure>", self.resize_background)  # 绑定窗口大小改变事件
               

    def setup_ui(self):
        style = ttk.Style("cosmo")

        self.root.title(self.title)

        # 设置窗口大小
        self.root.geometry("1024x768")

        # 创建Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # 创建抽奖标签页
        self.lottery_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.lottery_tab, text='抽奖')

        # 设置抽奖页背景图片
        self.load_background_image()  

        # 重置按钮
        self.reset_button = ttk.Button(self.lottery_tab, text="重置", command=self.reset_lottery, bootstyle=DANGER)
        self.lottery_tab.pack_propagate(False)  # 防止框架根据子控件调整大小
        self.reset_button.grid(row=0, column=0,padx=10,pady=10)  # 放在右上角) 

        # 软件名称显示
        self.title_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 30),bootstyle='danger')
        self.title_label.pack(side=tk.TOP, pady=20)
        self.title_label.config(text=self.title)   

        # 正在抽取奖项显示
        self.current_awards_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 20), bootstyle=DANGER)
        self.current_awards_label.pack(side=tk.TOP, pady=10)
        self.current_awards_label.config(text='')

        # 所有奖项信息显示
        self.awards_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 20),bootstyle='default',background='pink')
        self.awards_label.pack(side=tk.TOP, pady=10)
        # 绑定Notebook的<TabChanged>事件
        self.notebook.bind("<<NotebookTabChanged>>", self.refresh_results_if_needed)          

        # 奖项选择下拉菜单
        self.draw_option_row_frame = tk.Frame(self.lottery_tab)
        self.draw_option_row_frame.pack()
        self.award_option_label = ttk.Label(self.draw_option_row_frame, text="奖项:", font=("FangSong", 16), bootstyle='primary')
        self.award_option_label.pack(side=tk.LEFT, padx=5)
        self.award_var = tk.StringVar()
        self.award_option_menu = ttk.Combobox(self.draw_option_row_frame, textvariable=self.award_var, font=("Arial", 16), state='readonly')
        self.award_option_menu.pack(side=tk.LEFT, padx=5)
        self.award_option_menu.bind('<<ComboboxSelected>>', self.check_award_selected)

        # 待抽奖名字显示文本框
        self.name_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 25),bootstyle="danger")
        self.name_label.pack(side=tk.TOP, pady=50)      

        # 是否所有人参与， 默认只有未中奖人员参与
        self.is_all_participants_checkbutton = ttk.Checkbutton(self.lottery_tab, text="所有人员参与抽奖",
                                      variable=self.is_all_participants,
                                      offvalue=False,
                                      onvalue=True)
        self.is_all_participants_checkbutton.pack(side=tk.TOP, pady=20)        

        # 每次抽取人数输入
        self.draw_count_row_frame = tk.Frame(self.lottery_tab)
        self.draw_count_row_frame.pack()

        self.draw_count_label = ttk.Label(self.draw_count_row_frame, text="抽取人数:", font=("FangSong", 16), bootstyle='primary')
        self.draw_count_label.pack(side=tk.LEFT, padx=5)

        self.draw_count_entry = ttk.Entry(self.draw_count_row_frame, font=("FangSong", 16), width=5, bootstyle='primary',justify='center')
        self.draw_count_entry.pack(side=tk.LEFT, padx=5)
        self.update_draw_count_entry(1)     

        self.draw_count_scale = ttk.Scale(self.draw_count_row_frame, from_=1, to=10, orient='horizontal', command=self.update_draw_count_entry)  
        self.draw_count_scale.pack(side=tk.LEFT, padx=5)

        # 抽奖按钮
        self.draw_button = ttk.Button(self.lottery_tab, text="开始", command=self.start_pick)
        self.draw_button.pack(side=tk.TOP, pady=10)
        # 绑定空格和回车键按下事件到 start_pick 方法
        self.root.bind('<Return>', self.start_pick)  # 回车键
        self.root.bind('<space>', self.start_pick)   # 空格键

        # 结果显示
        self.result_label = ttk.Label(self.lottery_tab, text="", font=("FangSong", 15), bootstyle=DANGER)
        self.result_label.pack(side=tk.TOP, pady=20)  
        self.result_label.config(text='') 

        # 版本和作者信息
        self.version_author_label = ttk.Label(self.lottery_tab, text="版本：1.0  作者：Tom Wu", font=("FangSong", 12), bootstyle='info')
        self.version_author_label.pack(side=tk.BOTTOM, anchor=tk.SE, pady=10) 



    # 创建结果标签页
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text='抽奖结果')
        self.create_results_table() 



        # 创建使用说明标签页
        self.about_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.about_tab, text='使用说明')

        # 标题设置栏
        self.title_setting_row_frame = tk.Frame(self.about_tab)
        self.title_setting_row_frame.grid(row=0, column=0, padx=10, pady=10)

        # 设置标题的Label和Entry
        self.title_label1 = ttk.Label(self.title_setting_row_frame, text="标题信息：")
        self.title_label1.pack(side=ttk.LEFT)        

        self.title_entry = ttk.Entry(self.title_setting_row_frame)
        self.title_entry.pack(side=ttk.LEFT)
        self.title_entry.insert(0, self.title)  # 插入新值

        # 保存标题信息的按钮
        self.save_button = ttk.Button(self.title_setting_row_frame, text="保存标题", command=self.save_config)
        self.save_button.pack(side=ttk.LEFT)  

        # 使用说明标签
        description_string = f'''
        使用说明:\n
        1. 如果需要修改标题信息， 在上面标题信息框输入标题然后点击保存。\n
        2. 修改 {os.path.join(self.data_folder, 'awards.xlsx')} 文件中的奖项信息。\n
        3. 修改 {os.path.join(self.data_folder, 'participants.xlsx')} 文件中的参与抽奖人员信息。\n
        4. 拖动滑块来修改一次抽取人数。\n
        5. 默认仅未中奖人员参与抽奖， 如果需要所有人员参加抽奖可勾选 {self.is_all_participants_checkbutton.cget("text")} 开关。\n
        6. 点击开始按钮（也可以按回车或者空格键）人员名单开始随机滚动， 点击结束按钮（也可以按回车或者空格键）名单停止滚动并显示中奖者名单。\n
        7. 重启软件不会清空中奖者名单， 重新抽奖需要点击左上角的重置按钮来清空中奖者名单。
        '''
        self.description_label = ttk.Label(self.about_tab, text=description_string)
        self.description_label.grid(row=1, column=0, padx=10, pady=10)       

        self.load_data()


    def load_config(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)  # 创建data文件夹
        self.config_file_path = os.path.join(self.data_folder, 'config.ini') #配置文件路径
        # 检查配置文件是否存在
        config = configparser.ConfigParser()
        # 如果配置文件不存在，创建一个新的配置文件并设置默认值           
        if not os.path.exists(self.config_file_path):                 
            # 添加默认的配置节和键值对
            config['Settings'] = {
                'Title': '年会抽奖软件',
            }
            
            # 写入配置文件
            with open(self.config_file_path, 'w') as config_file:
                config.write(config_file)
        config.read(self.config_file_path)
        self.title = config.get('Settings', 'Title')


    def save_config(self):
        config = configparser.ConfigParser()
         # 获取标题输入框的内容
        new_title = self.title_entry.get()
        if new_title:
            # 更新标题
            config['Settings'] = {
                'Title': new_title,
            }
                
            # 写入配置文件
            with open(self.config_file_path, 'w') as config_file:
                config.write(config_file)
            config.read(self.config_file_path)
            self.title = config.get('Settings', 'Title')
            self.root.title(self.title)
            self.title_label.config(text=self.title)
            messagebox.showinfo("操作成功", "标题已保存")
        else:
            messagebox.showwarning("警告", "标题不能为空")           
        

    def load_background_image(self):
        if os.path.exists(self.bg_imge_path):
            self.bg_image = Image.open(self.bg_imge_path)
            self.bg_image = self.bg_image.resize((self.root.winfo_width(), self.root.winfo_height()), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = tk.Label(self.lottery_tab, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)


    def resize_background(self, event):
        if os.path.exists(self.bg_imge_path):
            self.bg_image = Image.open(self.bg_imge_path)
            self.bg_image = self.bg_image.resize((event.width, event.height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label.config(image=self.bg_photo)     
        


    def load_data(self):      
        participants_path = os.path.join(self.data_folder, 'participants.xlsx')
        awards_path = os.path.join(self.data_folder, 'awards.xlsx')
        winners_path = os.path.join(self.data_folder, 'winners.xlsx')

        # 加载或创建Excel文件
        self.load_or_create_excel(participants_path, {'Name': ['参与者1', '参与者2', '参与者3']})
        self.load_or_create_excel(awards_path, {'Award': ['一等奖', '二等奖', '三等奖'], 'Quota': [1, 2, 3]})

        if os.path.exists(winners_path):
            self.winners = pd.read_excel(winners_path)
        else:
            self.winners = pd.DataFrame(columns=['Award', 'Name'])
        self.awards = pd.read_excel(awards_path)
        if os.path.exists(winners_path):
            self.winners = pd.read_excel(winners_path)
        self.participants = pd.read_excel(participants_path)       
        self.award_option_menu['values'] = self.awards['Award'].unique().tolist()
        self.update_award_status()


    def update_draw_count_entry(self,value):
        int_value = int(float(value))
        self.draw_count_entry.config(state='normal')  # 临时允许修改
        self.draw_count_entry.delete(0, 'end')  # 清空原有内容
        self.draw_count_entry.insert(0, str(int(int_value)))  # 插入新值
        self.draw_count_entry.config(state='readonly')  # 恢复只读状态


    def load_or_create_excel(self, file_path, data):
        if not os.path.exists(file_path):
            pd.DataFrame(data).to_excel(file_path, index=False, engine='openpyxl')


    def reset_lottery(self):
        self.update_draw_count_entry(1)

        # 如果winners文件存在，则重命名
        winners_path = os.path.join(self.data_folder, 'winners.xlsx')
        new_winners_path = os.path.join(self.data_folder, 'winners_old.xlsx')
        if os.path.exists(winners_path):
            if os.path.exists(new_winners_path):
                os.remove(new_winners_path)
            os.rename(winners_path, new_winners_path)
        self.load_data()
        self.result_label.config(text='------------------抽奖已重置！------------------')
        self.name_label.config(text='')
        self.draw_button.focus_set()


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
            self.selected_participants = self.participants.sample(n=self.draw_count)
        else:
            self.selected_participants = self.participants_not_win.sample(n=self.draw_count)
        self.current_winners = self.selected_participants['Name'].tolist()

        # 如果名单不为空，循环显示名字，直到再次按下抽奖按钮
        if self.current_winners:
            self.name_label.config(text=','.join(self.current_winners))
            if self.in_progress:                             
                # 设置定时器，用于快速轮流显示名字
                self.root.after(self.display_interval, self.get_winners)
            else:   
                self.result_label.config(text=f"恭喜 {', '.join(self.current_winners)} 中{self.current_award}") 
                # 更新中奖者名单
                new_winners = pd.DataFrame({'Award': [self.current_award]*len(self.current_winners), 'Name': self.current_winners})
                self.winners = pd.concat([self.winners, new_winners], ignore_index=True)
                self.check_award_selected()
                # 保存更新后的中奖者名单
                self.winners.to_excel(os.path.join(self.data_folder, 'winners.xlsx'), index=False)
        else:
             self.result_label.config(text=f"错误：未获得中奖者名单！") 

    

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


    def create_results_table(self):
        self.results_table = ttk.Treeview(self.result_tab, columns=('Award', 'Name'), show='headings',bootstyle='info')
        self.results_table.heading('Award', text='奖项')
        self.results_table.heading('Name', text='获奖者')
        self.results_table.column('Award', width=100)
        self.results_table.column('Name', width=100)
        self.results_table.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 滚动条
        self.vsb = ttk.Scrollbar(self.result_tab, orient='vertical', command=self.results_table.yview)
        self.results_table.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side=tk.RIGHT, fill='y')

        self.hsb = ttk.Scrollbar(self.result_tab, orient='horizontal', command=self.results_table.xview)
        self.results_table.configure(xscrollcommand=self.hsb.set)
        self.hsb.pack(side=tk.BOTTOM, fill='x')

        # 确保表格在Notebook中正确显示
        # self.notebook.select(self.result_tab)
    
    def refresh_results_if_needed(self, event):
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



         
 
            

# 主程序
root = tk.Tk()
app = LotteryApp(root)
root.mainloop()