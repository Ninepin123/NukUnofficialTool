# credit_deficit_calculator.py

import json
import os
import sys

def get_resource_path(relative_path):
    """獲取資源檔案的正確路徑，支援PyInstaller打包後的環境"""
    try:
        # PyInstaller 打包後的路徑
        base_path = sys._MEIPASS
    except Exception:
        # 開發環境的路徑
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_department_requirements():
    """
    從 score.json 讀取各科系的學分要求
    """
    try:
        # 使用get_resource_path獲取正確的檔案路徑
        score_file_path = get_resource_path('data/score.json')
        
        with open(score_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        requirements = {}
        for dept_info in data:
            dept_name = dept_info.get('科系', '')
            if dept_name:
                requirements[dept_name] = {
                    '系必修': dept_info.get('系必修', 0),
                    '領域選修': dept_info.get('領域選修', 0),
                    '校定必修': dept_info.get('校定必修', 0),
                    '通識選修': dept_info.get('通識選修', 0),
                    '總學分': dept_info.get('畢業學分', 0)
                }
        
        return requirements
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"讀取學分要求檔案時發生錯誤: {e}")
        return {}

# 科系代碼前綴對應表
DEPARTMENT_PREFIX_MAPPING = {
    'cs': '資訊工程學系',
    'ee': '電機工程學系',
    'am': '應用數學系',
    'ac': '應用化學系',
    'ap': '應用物理學系',
    'ce': '土木與環境工程學系',
    'cm': '化學工程及材料工程學系',
    'ls': '生命科學系',
    'ae': '應用經濟學系',
    'fi': '財務金融學系',
    'im': '資訊管理學系',
    'ab': '亞太工商管理學系',
    'la': '法律學系',
    'gl': '政治法律學系',
    'fl': '財經法律學系',
    'wl': '西洋語文學系',
    'el': '東亞語文學系',
    'kh': '運動健康與休閒學系',
    'dap': '運動競技學系',
    'da': '建築學系',
    'ccd': '工藝與創意設計學系',
    'cda': '創意設計與建築學系'
}

def get_department_from_course_prefix(course_data):
    """
    根據課程資料推測學生所屬科系
    優先級：系必修課程數量 > 系選修課程數量
    """
    department_scores = {}
    
    # 統計各科系的相關課程數量
    for category, data in course_data.items():
        if isinstance(data, dict) and 'courses' in data:
            for course in data['courses']:
                course_id = course.get('id', '')
                
                # 根據課程代碼前綴判斷可能的科系
                for prefix, dept_name in DEPARTMENT_PREFIX_MAPPING.items():
                    if course_id.lower().startswith(prefix.lower()):
                        if dept_name not in department_scores:
                            department_scores[dept_name] = {'必修': 0, '選修': 0}
                        
                        course_type = course.get('type', '選修')
                        if '必修' in category and course_type == '必修':
                            department_scores[dept_name]['必修'] += 1
                        else:
                            department_scores[dept_name]['選修'] += 1
    
    # 找出最可能的科系（優先考慮必修課程數量）
    best_dept = None
    best_score = 0
    
    for dept, scores in department_scores.items():
        # 必修課程權重較高
        total_score = scores['必修'] * 3 + scores['選修']
        if total_score > best_score:
            best_score = total_score
            best_dept = dept
    
    return best_dept

def calculate_credit_deficit(department_name, current_credits):
    """
    計算學分缺額
    
    Args:
        department_name: 科系名稱
        current_credits: 目前各類別已修學分數
        
    Returns:
        dict: 包含缺額資訊的字典
    """
    # 載入學分要求
    requirements_data = load_department_requirements()
    
    if department_name not in requirements_data:
        return {
            'status': 'unknown_department',
            'message': f'未找到科系：{department_name} 的學分要求資料',
            'department': department_name,
            'deficit_details': {}
        }
    
    requirements = requirements_data[department_name]
    deficit_details = {}
    total_deficit = 0
    
    # 計算各類別缺額
    for category in ['系必修', '領域選修', '校定必修', '通識選修']:
        required = requirements.get(category, 0)
        current = current_credits.get(category, 0)
        deficit = max(0, required - current)
        
        deficit_details[category] = {
            '需要': required,
            '已修': current,
            '缺額': deficit,
            '狀態': '已滿足' if deficit == 0 else f'還需 {deficit} 學分'
        }
        
        total_deficit += deficit
    
    # 計算總學分狀況
    total_earned = sum(current_credits.values())
    total_required = requirements['總學分']
    total_gap = max(0, total_required - total_earned)
    
    return {
        'status': 'success',
        'department': department_name,
        'deficit_details': deficit_details,
        'total_summary': {
            '總需求學分': total_required,
            '目前總學分': total_earned,
            '總缺額': total_gap,
            '各類別缺額合計': total_deficit,
            '畢業狀態': '符合畢業條件' if total_gap == 0 and total_deficit == 0 else '尚未符合畢業條件'
        },
        'recommendations': generate_recommendations(deficit_details)
    }

def generate_recommendations(deficit_details):
    """
    根據缺額情況生成修課建議
    """
    recommendations = []
    
    # 按優先級排序缺額項目
    priority_order = ['系必修', '校定必修', '通識選修', '領域選修']
    
    for category in priority_order:
        if category in deficit_details and deficit_details[category]['缺額'] > 0:
            deficit = deficit_details[category]['缺額']
            if category == '系必修':
                recommendations.append(f"優先修習系必修課程，還需 {deficit} 學分")
            elif category == '校定必修':
                recommendations.append(f"儘快修習校定必修課程（如國文、英文等），還需 {deficit} 學分")
            elif category == '通識選修':
                recommendations.append(f"可修習核心通識或博雅通識課程，還需 {deficit} 學分")
            elif category == '領域選修':
                recommendations.append(f"修習系上的選修課程，還需 {deficit} 學分")
    
    if not recommendations:
        recommendations.append("恭喜！您已符合所有學分要求")
    
    return recommendations