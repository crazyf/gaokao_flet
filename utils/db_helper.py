import os
import sqlite3
import sys

# 数据库路径（相对于 main.py）
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "gaokao.db")

def get_db_path():
    """获取数据库路径（兼容安卓打包）"""
    import os
    # 如果是打包后的环境
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, 'database', 'gaokao.db')

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def search_by_score(
    score, year, university_types=None, float_range=10, max_results=500
):
    """
    根据分数搜索院校
    返回：地区分布统计数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    min_score = score - float_range
    max_score = score + float_range

    table_name = f"{year}年普通类本科批投档情况"

    # 查询符合条件的投档记录
    query = f"""
        SELECT DISTINCT 院校名称 
        FROM "{table_name}"
        WHERE 投档最低分 BETWEEN ? AND ?
        LIMIT ?
    """
    cursor.execute(query, (min_score, max_score, max_results))
    records = cursor.fetchall()

    if not records:
        conn.close()
        return []

    university_names = [r["院校名称"] for r in records]

    # 构建院校查询条件
    placeholders = ",".join(["?" for _ in university_names])
    uni_query = f"""
        SELECT 院校名称, 院校所在地, 是否双一流, 是否211, 是否985
        FROM "院校信息"
        WHERE 院校名称 IN ({placeholders})
    """

    # 添加院校类型筛选
    if university_types:
        type_conditions = []
        if "双一流" in university_types:
            type_conditions.append("是否双一流 = '是'")
        if "985" in university_types:
            type_conditions.append("是否985 = '是'")
        if "211" in university_types:
            type_conditions.append("是否211 = '是'")
        if type_conditions:
            uni_query += " AND (" + " OR ".join(type_conditions) + ")"

    cursor.execute(uni_query, university_names)
    universities = cursor.fetchall()
    conn.close()

    # 按地区分组统计
    location_stats = {}
    for uni in universities:
        location = uni["院校所在地"]
        if location and location.strip():
            location = location.strip()
            if location not in location_stats:
                location_stats[location] = {"count": 0, "universities": []}
            location_stats[location]["count"] += 1
            location_stats[location]["universities"].append(
                {"name": uni["院校名称"], "type": get_university_type_labels(uni)}
            )

    # 转换为列表并排序
    result = [
        {
            "location": loc,
            "count": stats["count"],
            "universities": stats["universities"],
        }
        for loc, stats in sorted(
            location_stats.items(), key=lambda x: x[1]["count"], reverse=True
        )
    ]

    return result


def get_university_details(
    university_name, year, score=None, rank=None, float_range=10
):
    """
    获取院校两年专业对比详情（带分数筛选）
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    majors = {}

    # 处理2024年数据
    query_2024 = """
        SELECT 专业名称, 投档人数, 投档最低分, 投档最低位次
        FROM "2024年普通类本科批投档情况"
        WHERE 院校名称 = ?
    """
    params_2024 = [university_name]

    if year == "2024" and score:
        min_score = score - float_range
        max_score = score + float_range
        query_2024 += " AND 投档最低分 BETWEEN ? AND ?"
        params_2024.extend([min_score, max_score])
    elif year == "2024" and rank:
        min_rank = rank - 1000
        max_rank = rank + 1000
        query_2024 += " AND 投档最低位次 BETWEEN ? AND ?"
        params_2024.extend([min_rank, max_rank])

    cursor.execute(query_2024, params_2024)
    data_2024 = cursor.fetchall()

    for record in data_2024:
        major_name = record["专业名称"]
        if not major_name:
            continue
        major_name = major_name.strip()
        if major_name not in majors:
            majors[major_name] = {
                "专业名称": major_name,
                "2024录取人数": record["投档人数"] or 0,
                "2025录取人数": 0,
                "投档最低位次": record["投档最低位次"] or "",
                "投档最低分": record["投档最低分"] or "",
            }
        else:
            majors[major_name]["2024录取人数"] += record["投档人数"] or 0
            if record["投档最低分"] and (
                not majors[major_name]["投档最低分"]
                or record["投档最低分"] < majors[major_name]["投档最低分"]
            ):
                majors[major_name]["投档最低分"] = record["投档最低分"]
            if record["投档最低位次"] and (
                not majors[major_name]["投档最低位次"]
                or record["投档最低位次"] < majors[major_name]["投档最低位次"]
            ):
                majors[major_name]["投档最低位次"] = record["投档最低位次"]

    # 处理2025年数据
    query_2025 = """
        SELECT 专业名称, 投档人数, 投档最低分, 投档最低位次
        FROM "2025年普通类本科批投档情况"
        WHERE 院校名称 = ?
    """
    params_2025 = [university_name]

    if year == "2025" and score:
        min_score = score - float_range
        max_score = score + float_range
        query_2025 += " AND 投档最低分 BETWEEN ? AND ?"
        params_2025.extend([min_score, max_score])
    elif year == "2025" and rank:
        min_rank = rank - 1000
        max_rank = rank + 1000
        query_2025 += " AND 投档最低位次 BETWEEN ? AND ?"
        params_2025.extend([min_rank, max_rank])

    cursor.execute(query_2025, params_2025)
    data_2025 = cursor.fetchall()

    for record in data_2025:
        major_name = record["专业名称"]
        if not major_name:
            continue
        major_name = major_name.strip()
        if major_name not in majors:
            majors[major_name] = {
                "专业名称": major_name,
                "2024录取人数": 0,
                "2025录取人数": record["投档人数"] or 0,
                "投档最低位次": record["投档最低位次"] or "",
                "投档最低分": record["投档最低分"] or "",
            }
        else:
            majors[major_name]["2025录取人数"] += record["投档人数"] or 0
            if record["投档最低分"] and (
                not majors[major_name]["投档最低分"]
                or record["投档最低分"] < majors[major_name]["投档最低分"]
            ):
                majors[major_name]["投档最低分"] = record["投档最低分"]
            if record["投档最低位次"] and (
                not majors[major_name]["投档最低位次"]
                or record["投档最低位次"] < majors[major_name]["投档最低位次"]
            ):
                majors[major_name]["投档最低位次"] = record["投档最低位次"]

    conn.close()

    # 转换为列表并排序
    result = []
    for idx, (major_name, details) in enumerate(
        sorted(
            majors.items(),
            key=lambda x: x[1]["2025录取人数"] if x[1]["2025录取人数"] else 0,
            reverse=True,
        ),
        1,
    ):
        result.append(
            {
                "序号": idx,
                "专业名称": details["专业名称"],
                "2024录取人数": details["2024录取人数"]
                if details["2024录取人数"] > 0
                else "",
                "2025录取人数": details["2025录取人数"]
                if details["2025录取人数"] > 0
                else "",
                "投档最低位次": details["投档最低位次"]
                if details["投档最低位次"]
                else "",
                "投档最低分": details["投档最低分"] if details["投档最低分"] else "",
            }
        )

    return result


def get_university_type_labels(uni):
    """获取院校类型标签"""
    labels = []
    if uni["是否985"] == "是":
        labels.append("985")
    if uni["是否211"] == "是":
        labels.append("211")
    if uni["是否双一流"] == "是":
        labels.append("双一流")
    return "、".join(labels) if labels else "普通"
