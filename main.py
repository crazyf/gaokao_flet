import os
import sys

import flet as ft

from utils.db_helper import get_university_details, search_by_score

# 将项目根目录添加到 Python 路径，以便找到 utils 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main(page: ft.Page):
    page.title = "高考志愿查询系统"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.window_width = None
    page.window_height = None
    page.scroll = ft.ScrollMode.AUTO

    # 存储状态
    current_query_params = {
        "score": None,
        "rank": None,
        "year": "2025",
        "float_range": 10,
    }

    # ========== 左侧面板控件 ==========
    score_input = ft.TextField(
        label="分数",
        hint_text="输入分数",
        width=140,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    rank_input = ft.TextField(
        label="排位",
        hint_text="输入排位",
        width=140,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    # 院校类型复选框
    c9_check = ft.Checkbox(label="985", value=False)
    c211_check = ft.Checkbox(label="211", value=False)
    double_first_check = ft.Checkbox(label="双一流", value=False)

    # 年份单选
    year_group = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="2024", label="2024年"),
                ft.Radio(value="2025", label="2025年"),
            ]
        ),
        value="2025",
    )

    # 地区列表容器
    locations_container = ft.Column(spacing=8)

    # 右侧面板引用
    right_panel_content = ft.Column(
        [
            ft.Text("请选择院校查看详情", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("", size=12, color=ft.Colors.BLUE_600),
            ft.Text(
                "请从左侧选择地区后，再点击院校名称查看专业详情",
                color=ft.Colors.GREY_500,
                size=13,
            ),
        ],
        spacing=15,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    right_panel = ft.Card(
        content=ft.Container(content=right_panel_content, padding=15, height=None),
        elevation=5,
        expand=True,
    )

    # ========== 定义函数 ==========
    def clear_score(e):
        if score_input.value:
            rank_input.value = ""
            page.update()

    def clear_rank(e):
        if rank_input.value:
            score_input.value = ""
            page.update()

    score_input.on_change = clear_score
    rank_input.on_change = clear_rank

    def show_university_list(location, universities):
        """在右侧显示院校列表"""
        uni_list = ft.Column(spacing=10)

        for uni in universities:
            uni_card = ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    uni["name"], size=15, weight=ft.FontWeight.W_500
                                ),
                                ft.Text(uni["type"], size=10, color=ft.Colors.GREY_600),
                            ],
                            spacing=5,
                            expand=True,
                        ),
                        ft.Text(">", size=16, color=ft.Colors.GREY_400),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.GREY_200),
                ink=True,
                on_click=lambda e, name=uni["name"]: show_major_details(name),
            )
            uni_list.controls.append(uni_card)

        right_panel.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"📋 {location} - 院校列表", size=16, weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([uni_list], scroll=ft.ScrollMode.AUTO),
                        height=450,
                    ),
                ],
                spacing=12,
            ),
            padding=15,
        )
        page.update()

    def show_major_details(university_name):
        """显示专业详情"""
        # 显示加载状态
        right_panel.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text("加载中...", size=16, color=ft.Colors.GREY_500),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=15,
            height=400,
        )
        page.update()

        # 获取专业详情（真实数据库）
        try:
            result = get_university_details(
                university_name=university_name,
                year=current_query_params["year"],
                score=current_query_params["score"],
                rank=current_query_params["rank"],
                float_range=current_query_params["float_range"],
            )
        except Exception as e:
            result = []
            print(f"查询出错: {e}")

        if not result:
            right_panel.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text("暂无专业数据", size=16, color=ft.Colors.GREY_500),
                        ft.TextButton(
                            content=ft.Text("← 返回"),
                            on_click=lambda e: (
                                show_university_list_for_current_location()
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=15,
            )
            page.update()
            return

        # 创建表格
        columns = [
            ft.DataColumn(ft.Text("序号", weight=ft.FontWeight.BOLD, size=12)),
            ft.DataColumn(ft.Text("专业名称", weight=ft.FontWeight.BOLD, size=12)),
            ft.DataColumn(ft.Text("2024录取人数", weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("2025录取人数", weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("投档最低位次", weight=ft.FontWeight.BOLD, size=11)),
            ft.DataColumn(ft.Text("投档最低分", weight=ft.FontWeight.BOLD, size=11)),
        ]

        rows = []
        for item in result:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item["序号"]), size=11)),
                        ft.DataCell(ft.Text(item["专业名称"], size=11)),
                        ft.DataCell(ft.Text(str(item["2024录取人数"]), size=11)),
                        ft.DataCell(ft.Text(str(item["2025录取人数"]), size=11)),
                        ft.DataCell(ft.Text(str(item["投档最低位次"]), size=11)),
                        ft.DataCell(ft.Text(str(item["投档最低分"]), size=11)),
                    ]
                )
            )

        detail_table = ft.DataTable(columns=columns, rows=rows, column_spacing=12)

        back_button = ft.TextButton(
            content=ft.Text("← 返回"),
            on_click=lambda e: show_university_list_for_current_location(),
            style=ft.ButtonStyle(
                color=ft.Colors.BLUE_600, bgcolor=ft.Colors.TRANSPARENT
            ),
        )

        # 显示筛选信息
        filter_text = ""
        if current_query_params["score"]:
            min_score = (
                current_query_params["score"] - current_query_params["float_range"]
            )
            max_score = (
                current_query_params["score"] + current_query_params["float_range"]
            )
            filter_text = f"📌 分数范围: {min_score} - {max_score} 分"
        elif current_query_params["rank"]:
            min_rank = current_query_params["rank"] - 1000
            max_rank = current_query_params["rank"] + 1000
            filter_text = f"📌 排位范围: {min_rank} - {max_rank}"

        right_panel.content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [back_button],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Text(
                        f"📖 {university_name}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        filter_text,
                        size=11,
                        color=ft.Colors.BLUE_600,
                    )
                    if filter_text
                    else ft.Container(),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([detail_table], scroll=ft.ScrollMode.AUTO),
                        height=400,
                    ),
                ],
                spacing=10,
            ),
            padding=15,
        )
        page.update()

    def show_university_list_for_current_location():
        """显示当前地区的院校列表（用于返回）"""
        if hasattr(page, "current_location") and hasattr(page, "current_universities"):
            show_university_list(page.current_location, page.current_universities)

    def select_location(location):
        """选择地区，在右侧显示院校列表"""
        if not hasattr(page, "locations_data"):
            return

        location_data = None
        for item in page.locations_data:
            if item["location"] == location:
                location_data = item
                break

        if location_data:
            page.current_location = location
            page.current_universities = location_data["universities"]
            show_university_list(location, location_data["universities"])

    def render_locations(data):
        """渲染地区列表"""
        locations_container.controls.clear()
        for item in data:
            location_card = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(item["location"], weight=ft.FontWeight.W_500, size=14),
                        ft.Container(
                            content=ft.Text(
                                f"{item['count']}", size=11, color=ft.Colors.WHITE
                            ),
                            bgcolor=ft.Colors.BLUE_600,
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.GREY_100,
                border_radius=10,
                ink=True,
                on_click=lambda e, loc=item["location"]: select_location(loc),
            )
            locations_container.controls.append(location_card)

        page.locations_data = data
        page.update()

    def on_search_click(e):
        """查询按钮点击事件"""
        score = score_input.value
        rank = rank_input.value
        year = year_group.value
        university_types = []
        if double_first_check.value:
            university_types.append("双一流")
        if c9_check.value:
            university_types.append("985")
        if c211_check.value:
            university_types.append("211")

        # 验证输入
        if (not score and not rank) or (score and rank):
            page.snack_bar = ft.SnackBar(
                content=ft.Text("请且仅输入分数或排位中的一项")
            )
            page.snack_bar.open = True
            page.update()
            return

        if not year:
            page.snack_bar = ft.SnackBar(content=ft.Text("请选择年份"))
            page.snack_bar.open = True
            page.update()
            return

        # 保存查询参数
        current_query_params["score"] = int(score) if score else None
        current_query_params["rank"] = int(rank) if rank else None
        current_query_params["year"] = year

        # 显示加载状态
        locations_container.controls.clear()
        locations_container.controls.append(
            ft.Text("查询中...", color=ft.Colors.GREY_500)
        )
        page.update()

        # 执行查询（真实数据库）
        try:
            if score:
                result = search_by_score(
                    score=int(score),
                    year=year,
                    university_types=university_types,
                    float_range=10,
                )
            else:
                # 按排位查询（需要单独实现，暂时用分数估算）
                result = search_by_score(
                    score=int(rank) // 10,
                    year=year,
                    university_types=university_types,
                    float_range=50,
                )
        except Exception as e:
            print(f"查询出错: {e}")
            result = []

        if result:
            render_locations(result)
            # 重置右侧面板
            right_panel.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "请选择院校查看详情", size=18, weight=ft.FontWeight.BOLD
                        ),
                        ft.Text("", size=12, color=ft.Colors.BLUE_600),
                        ft.Text(
                            "请从左侧选择地区后，再点击院校名称查看专业详情",
                            color=ft.Colors.GREY_500,
                            size=13,
                        ),
                    ],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=15,
            )
        else:
            locations_container.controls.clear()
            locations_container.controls.append(
                ft.Text("未找到相关院校", color=ft.Colors.RED_600)
            )
            page.update()

    # ========== 构建UI ==========
    # 左侧查询面板
    query_panel = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("🔍 查询条件", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([score_input, rank_input]),
                    ft.Text("院校类型", size=13, weight=ft.FontWeight.W_500),
                    ft.Row([double_first_check, c9_check, c211_check]),
                    ft.Divider(height=5),
                    ft.Text("年份", size=13, weight=ft.FontWeight.W_500),
                    year_group,
                    ft.FilledButton(
                        content=ft.Text("查询"), on_click=on_search_click, width=120
                    ),
                ],
                spacing=12,
            ),
            padding=15,
        ),
        elevation=3,
    )

    # 左侧地区面板
    location_panel = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("📊 院校地区分布", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column(
                            [locations_container], scroll=ft.ScrollMode.AUTO
                        ),
                        height=350,
                    ),
                ],
                spacing=10,
            ),
            padding=15,
        ),
        elevation=3,
        expand=True,
    )

    # 左侧面板
    left_panel = ft.Container(
        width=None,
        expand=True,
        content=ft.Column(
            [
                query_panel,
                location_panel,
            ],
            spacing=12,
            expand=True,
        ),
    )

    # 主布局 - 上下排列（手机优化）
    main_column = ft.Column(
        [
            left_panel,
            ft.Divider(height=1, visible=False),
            right_panel,
        ],
        spacing=12,
        expand=True,
    )
    page.add(main_column)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
