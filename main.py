"""
Gaokao Query System - Kivy Version
"""
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

from utils.db_helper import search_by_score, get_university_details

Window.size = (360, 600)


class MainScreen(Screen):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # Title
        layout.add_widget(Label(
            text='Gaokao Query System',
            size_hint_y=0.08,
            font_size=18
        ))
        
        # Input row
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)
        self.score_input = TextInput(hint_text='Score', multiline=False, input_filter='int')
        self.rank_input = TextInput(hint_text='Rank', multiline=False, input_filter='int')
        input_layout.add_widget(self.score_input)
        input_layout.add_widget(self.rank_input)
        layout.add_widget(input_layout)
        
        # University type options
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=8)
        self.c9_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='985', size_hint_x=0.2))
        type_layout.add_widget(self.c9_check)
        
        self.c211_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='211', size_hint_x=0.2))
        type_layout.add_widget(self.c211_check)
        
        self.double_check = CheckBox(active=False, size_hint_x=0.1)
        type_layout.add_widget(Label(text='Double First', size_hint_x=0.3))
        type_layout.add_widget(self.double_check)
        layout.add_widget(type_layout)
        
        # Year selection
        from kivy.uix.togglebutton import ToggleButton
        year_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        year_layout.add_widget(Label(text='Year:', size_hint_x=0.2))
        self.year_2024 = ToggleButton(text='2024', group='year', state='normal')
        self.year_2025 = ToggleButton(text='2025', group='year', state='down')
        year_layout.add_widget(self.year_2024)
        year_layout.add_widget(self.year_2025)
        layout.add_widget(year_layout)
        
        # Search button
        self.search_btn = Button(text='Search', size_hint_y=0.08, background_color=(0.2, 0.4, 0.8, 1))
        self.search_btn.bind(on_press=self.on_search)
        layout.add_widget(self.search_btn)
        
        # Loading indicator
        self.loading_label = Label(text='Searching...', size_hint_y=0.05, color=(0.5, 0.5, 0.5, 1))
        self.loading_label.opacity = 0
        layout.add_widget(self.loading_label)
        
        # Results area
        self.result_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.result_layout)
        layout.add_widget(scroll)
        
        self.locations_data = []
        self.add_widget(layout)
    
    def show_loading(self, show=True):
        self.loading_label.opacity = 1 if show else 0
        self.search_btn.disabled = show
    
    def on_search(self, instance):
        score = self.score_input.text
        rank = self.rank_input.text
        year = '2025' if self.year_2025.state == 'down' else '2024'
        
        types = []
        if self.c9_check.active:
            types.append('985')
        if self.c211_check.active:
            types.append('211')
        if self.double_check.active:
            types.append('Double First')
        
        if (not score and not rank) or (score and rank):
            self.show_result_error('Please enter score OR rank only')
            return
        
        self.show_loading(True)
        self.result_layout.clear_widgets()
        Clock.schedule_once(lambda dt: self.do_search(score, rank, year, types), 0.1)
    
    def do_search(self, score, rank, year, types):
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
            Clock.schedule_once(lambda dt: self.render_result(result), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_result_error(str(e)), 0)
    
    def render_result(self, data):
        self.show_loading(False)
        
        if not data:
            self.show_result_error('No universities found')
            return
        
        self.locations_data = data
        total = sum(item['count'] for item in data)
        self.result_layout.add_widget(Label(
            text=f'{len(data)} regions, {total} universities',
            size_hint_y=None,
            height=30,
        ))
        
        for item in data:
            btn = Button(
                text=f"{item['location']} ({item['count']})",
                size_hint_y=None,
                height=45,
            )
            btn.bind(on_press=lambda x, loc=item['location'], uni=item['universities']: 
                     self.show_university_list(loc, uni))
            self.result_layout.add_widget(btn)
    
    def show_result_error(self, msg):
        self.show_loading(False)
        self.result_layout.clear_widgets()
        self.result_layout.add_widget(Label(text=msg))
    
    def show_university_list(self, location, universities):
        self.result_layout.clear_widgets()
        """显示院校列表"""
        self.current_location = location  # 保存
        self.current_universities = universities  # 保存

        back_btn = Button(text='< Back', size_hint_y=None, height=40)
        back_btn.bind(on_press=lambda x: self.render_result(self.locations_data))
        self.result_layout.add_widget(back_btn)
        
        self.result_layout.add_widget(Label(text=f'{location} Universities', size_hint_y=None, height=35))
        
        for uni in universities:
            btn_text = f"{uni['name']} ({uni['type']})" if uni['type'] else uni['name']
            btn = Button(text=btn_text, size_hint_y=None, height=50)
            btn.bind(on_press=lambda x, name=uni['name']: self.show_major_details(name))
            self.result_layout.add_widget(btn)
    
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
    
    def show_university_list_for_current(self):
        """返回到当前地区的院校列表"""
        if hasattr(self, 'current_location') and hasattr(self, 'current_universities'):
            self.show_university_list(self.current_location, self.current_universities)


class GaokaoApp(App):
    def build(self):
        self.title = 'Gaokao Query'
        return MainScreen()


if __name__ == '__main__':
    GaokaoApp().run()