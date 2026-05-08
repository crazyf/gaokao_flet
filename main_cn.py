"""
高考志愿查询系统 - Kivy 版本
"""
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock

from kivy.config import Config
# 导入你的数据库模块
from utils.db_helper import search_by_score, get_university_details

# 设置应用窗口大小（手机适配）
Window.size = (360, 600)

# 设置默认字体为中文字体（解决乱码）
Config.set('kivy', 'default_font', ['/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'])

class MainScreen(Screen):
    """主查询界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 主布局
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # 标题
        self.layout.add_widget(Label(
            text='高考志愿查询系统',
            size_hint_y=0.08,
            font_size=20
        ))
        
        # 分数和排位输入行
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)
        self.score_input = TextInput(
            hint_text='输入分数',
            multiline=False,
            input_filter='int',
            font_size=14
        )
        self.rank_input = TextInput(
            hint_text='输入排位',
            multiline=False,
            input_filter='int',
            font_size=14
        )
        input_layout.add_widget(self.score_input)
        input_layout.add_widget(self.rank_input)
        self.layout.add_widget(input_layout)
        
        # 院校类型选项
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=8)
        self.c9_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='985', size_hint_x=0.2))
        type_layout.add_widget(self.c9_check)
        
        self.c211_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='211', size_hint_x=0.2))
        type_layout.add_widget(self.c211_check)
        
        self.double_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='双一流', size_hint_x=0.3))
        type_layout.add_widget(self.double_check)
        self.layout.add_widget(type_layout)
        
        # 年份选择
        year_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        year_layout.add_widget(Label(text='年份:', size_hint_x=0.2))
        
        from kivy.uix.togglebutton import ToggleButton
        self.year_2024 = ToggleButton(text='2024年', group='year', state='normal')
        self.year_2025 = ToggleButton(text='2025年', group='year', state='down')
        year_layout.add_widget(self.year_2024)
        year_layout.add_widget(self.year_2025)
        self.layout.add_widget(year_layout)
        
        # 查询按钮
        self.search_btn = Button(text='查 询', size_hint_y=0.08, background_color=(0.2, 0.4, 0.8, 1))
        self.search_btn.bind(on_press=self.on_search)
        self.layout.add_widget(self.search_btn)
        
        # 进度提示（初始隐藏）
        self.loading_label = Label(text='查询中...', size_hint_y=0.05, color=(0.5, 0.5, 0.5, 1))
        self.loading_label.opacity = 0
        self.layout.add_widget(self.loading_label)
        
        # 结果区域（可滚动）
        self.result_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.result_layout)
        self.layout.add_widget(scroll)
        
        # 存储查询结果
        self.locations_data = []
        
        self.add_widget(self.layout)
    
    def show_loading(self, show=True):
        """显示/隐藏加载状态"""
        self.loading_label.opacity = 1 if show else 0
        self.search_btn.disabled = show
        Clock.schedule_once(lambda dt: None, 0)
    
    def on_search(self, instance):
        """查询按钮点击事件"""
        score = self.score_input.text
        rank = self.rank_input.text
        year = '2025' if self.year_2025.state == 'down' else '2024'
        
        # 收集院校类型
        types = []
        if self.c9_check.active:
            types.append('985')
        if self.c211_check.active:
            types.append('211')
        if self.double_check.active:
            types.append('双一流')
        
        # 验证输入
        if (not score and not rank) or (score and rank):
            self.show_result_error('请且仅输入分数或排位中的一项')
            return
        
        # 显示加载状态
        self.show_loading(True)
        self.result_layout.clear_widgets()
        
        # 在后台线程中查询
        Clock.schedule_once(lambda dt: self.do_search(score, rank, year, types), 0.1)
    
    def do_search(self, score, rank, year, types):
        """执行查询"""
        try:
            if score:
                result = search_by_score(
                    score=int(score),
                    year=year,
                    university_types=types,
                    float_range=10
                )
            else:
                result = search_by_score(
                    score=int(rank) // 10,
                    year=year,
                    university_types=types,
                    float_range=50
                )
            
            # 在主线程中更新界面
            Clock.schedule_once(lambda dt: self.render_result(result), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_result_error(str(e)), 0)
    
    def render_result(self, data):
        """显示查询结果"""
        self.show_loading(False)
        
        if not data:
            self.show_result_error('未找到相关院校')
            return
        
        self.locations_data = data
        
        # 显示统计信息
        total = sum(item['count'] for item in data)
        info_label = Label(
            text=f'找到 {len(data)} 个地区，共 {total} 所院校',
            size_hint_y=None,
            height=30,
            color=(0.3, 0.3, 0.3, 1)
        )
        self.result_layout.add_widget(info_label)
        
        # 显示各地区按钮
        for item in data:
            btn = Button(
                text=f"{item['location']} ({item['count']})",
                size_hint_y=None,
                height=45,
                background_color=(0.4, 0.6, 0.9, 1) if item['count'] > 0 else (0.5, 0.5, 0.5, 1)
            )
            btn.bind(on_press=lambda x, loc=item['location'], uni=item['universities']: 
                     self.show_university_list(loc, uni))
            self.result_layout.add_widget(btn)
    
    def show_result_error(self, msg):
        """显示错误信息"""
        self.show_loading(False)
        self.result_layout.clear_widgets()
        self.result_layout.add_widget(Label(text=msg, color=(0.8, 0.2, 0.2, 1)))
    
    def show_university_list(self, location, universities):
        """显示院校列表"""
        # 清空结果区域
        self.result_layout.clear_widgets()
        
        # 返回按钮
        back_btn = Button(text='← 返回', size_hint_y=None, height=40, background_color=(0.6, 0.6, 0.6, 1))
        back_btn.bind(on_press=lambda x: self.render_result(self.locations_data))
        self.result_layout.add_widget(back_btn)
        
        # 标题
        title = Label(text=f'{location} 的院校', size_hint_y=None, height=35, font_size=16)
        self.result_layout.add_widget(title)
        
        # 院校列表
        for uni in universities:
            btn_text = f"{uni['name']} ({uni['type']})" if uni['type'] else uni['name']
            btn = Button(text=btn_text, size_hint_y=None, height=50)
            btn.bind(on_press=lambda x, name=uni['name']: self.show_major_details(name))
            self.result_layout.add_widget(btn)
    
    def show_university_list_for_current(self):
        """返回到当前地区的院校列表"""
        if hasattr(self, 'current_location') and hasattr(self, 'current_universities'):
            self.show_university_list(self.current_location, self.current_universities)

    def show_major_details(self, university_name):
        """显示专业详情"""
        self.result_layout.clear_widgets()
        
        # 返回按钮
        back_btn = Button(text='< Back to Universities', size_hint_y=None, height=40)
        back_btn.bind(on_press=lambda x: self.show_university_list_for_current())
        self.result_layout.add_widget(back_btn)
        
        self.result_layout.add_widget(Label(text=f'{university_name}\nMajors', size_hint_y=None, height=50))
        
        try:
            year = '2025' if self.year_2025.state == 'down' else '2024'
            result = get_university_details(university_name=university_name, year=year)
        except Exception as e:
            self.result_layout.add_widget(Label(text=f'Error: {e}'))
            return
        
        if not result:
            self.result_layout.add_widget(Label(text='No data available'))
            return
        
        # 显示表头
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=5)
        header_layout.add_widget(Label(text='Major Name', bold=True, size_hint_x=0.4))
        header_layout.add_widget(Label(text='2024', bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text='2025', bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text='Rank', bold=True, size_hint_x=0.15))
        header_layout.add_widget(Label(text='Score', bold=True, size_hint_x=0.15))
        self.result_layout.add_widget(header_layout)
        
        # 显示数据行
        for item in result[:30]:  # 限制显示30条
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=5)
            
            major_name = item.get('专业名称', 'Unknown')
            enrollment_2024 = item.get('2024录取人数', '')
            enrollment_2025 = item.get('2025录取人数', '')
            rank = item.get('投档最低位次', '')
            score = item.get('投档最低分', '')
            
            # 处理 None 值
            enrollment_2024 = enrollment_2024 if enrollment_2024 else '0'
            enrollment_2025 = enrollment_2025 if enrollment_2025 else '0'
            rank = rank if rank else '-'
            score = score if score else '-'
            
            row.add_widget(Label(text=major_name[:12], size_hint_x=0.4, font_size=11))
            row.add_widget(Label(text=str(enrollment_2024), size_hint_x=0.15, font_size=11))
            row.add_widget(Label(text=str(enrollment_2025), size_hint_x=0.15, font_size=11))
            row.add_widget(Label(text=str(rank), size_hint_x=0.15, font_size=11))
            row.add_widget(Label(text=str(score), size_hint_x=0.15, font_size=11))
            
            self.result_layout.add_widget(row)
    
    def go_back_to_universities(self):
        """返回院校列表"""
        # 需要保存当前选中的地区数据，这里简化
        pass


class GaokaoApp(App):
    """应用主类"""
    
    def build(self):
        self.title = '高考志愿查询'
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    GaokaoApp().run()