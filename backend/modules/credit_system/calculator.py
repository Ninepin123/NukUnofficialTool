# calculator.py

from .config import CC_SUBCATEGORY_MAPPING, GENERAL_SUBCATEGORY_MAPPING, COURSE_CODE_MAPPING
from .credit_deficit_calculator import calculate_credit_deficit

def categorize_and_calculate_credits(all_semesters_data, mapping):
    categorized_data = {}
    processed_categories = set()
    for category in mapping.values():
        if category in processed_categories:
            continue
        processed_categories.add(category)
        
        if category == '核心通識':
            # 為核心通識建立階層結構
            categorized_data['核心通識'] = {
                'subcategories': {},
                'courses': [],
                'earned_credits': 0.0,
                'total_credits': {
                    '必修': 0.0,
                    '選修': 0.0
                }
            }
            # 建立子分類
            for subcat in CC_SUBCATEGORY_MAPPING.values():
                categorized_data['核心通識']['subcategories'][subcat] = {
                    '必修': {'courses': [], 'earned_credits': 0.0},
                    '選修': {'courses': [], 'earned_credits': 0.0}
                }
            # 其他無法辨識的核心通識課程
            categorized_data['核心通識']['subcategories']['其他'] = {
                '必修': {'courses': [], 'earned_credits': 0.0},
                '選修': {'courses': [], 'earned_credits': 0.0}
            }
        elif category == '博雅通識':
            # 為博雅通識建立階層結構
            categorized_data['博雅通識'] = {
                'subcategories': {},
                'courses': [],
                'earned_credits': 0.0,
                'total_credits': {
                    '必修': 0.0,
                    '選修': 0.0
                }
            }
            # 建立子分類
            for subcat in GENERAL_SUBCATEGORY_MAPPING.values():
                categorized_data['博雅通識']['subcategories'][subcat] = {
                    '必修': {'courses': [], 'earned_credits': 0.0},
                    '選修': {'courses': [], 'earned_credits': 0.0}
                }
        else:
            categorized_data[f"{category} - 必修"] = {'courses': [], 'earned_credits': 0.0}
            categorized_data[f"{category} - 選修"] = {'courses': [], 'earned_credits': 0.0}
    
    categorized_data['其他 (無法辨識) - 必修'] = {'courses': [], 'earned_credits': 0.0}
    categorized_data['其他 (無法辨識) - 選修'] = {'courses': [], 'earned_credits': 0.0}
    
    sorted_prefixes = sorted(mapping.keys(), key=len, reverse=True)

    all_courses = [course for semester in all_semesters_data for course in semester['courses']]

    for course in all_courses:
        course_id = course.get('id', '')
        course_type = course.get('type', '').strip()
        matched_category = None

        for prefix in sorted_prefixes:
            if course_id.startswith(prefix):
                matched_category = mapping[prefix]
                break
        
        if not matched_category:
            matched_category = '其他 (無法辨識)'
        
        # 特殊處理核心通識課程
        if matched_category == '核心通識' and course_id.startswith('CC'):
            # 檢查是否有子分類
            subcategory_found = False
            target_subcat = '其他'
            
            for subcode, subname in CC_SUBCATEGORY_MAPPING.items():
                if len(course_id) > 2 and course_id[2:2+len(subcode)] == subcode:
                    target_subcat = subname
                    subcategory_found = True
                    break
            
            # 決定課程類型
            course_type_key = '必修' if course_type == '必修' else '選修'
            
            # 將課程添加到對應的子分類中
            categorized_data['核心通識']['subcategories'][target_subcat][course_type_key]['courses'].append(course)
            
        # 特殊處理博雅通識課程
        elif matched_category == '博雅通識':
            # 根據課程代碼前綴確定子分類
            target_subcat = None
            for prefix, subname in GENERAL_SUBCATEGORY_MAPPING.items():
                if course_id.startswith(prefix):
                    target_subcat = subname
                    break
            
            if target_subcat:
                # 決定課程類型
                course_type_key = '必修' if course_type == '必修' else '選修'
                
                # 將課程添加到對應的子分類中
                categorized_data['博雅通識']['subcategories'][target_subcat][course_type_key]['courses'].append(course)
            
        else:
            # 非核心通識課程的一般處理
            if course_type == '必修':
                category_key = f"{matched_category} - 必修"
            elif course_type == '選修':
                category_key = f"{matched_category} - 選修"
            else:
                category_key = f"{matched_category} - 選修"
            
            categorized_data[category_key]['courses'].append(course)

        try:
            if '棄選' in course.get('remark', ''):
                continue
                
            final_score = float(course.get('final_score', '0'))
            credits = float(course.get('credits', '0'))

            if final_score >= 60:
                if matched_category == '核心通識' and course_id.startswith('CC'):
                    # 核心通識課程學分計算
                    categorized_data['核心通識']['subcategories'][target_subcat][course_type_key]['earned_credits'] += credits
                    categorized_data['核心通識']['earned_credits'] += credits
                    categorized_data['核心通識']['total_credits'][course_type_key] += credits
                elif matched_category == '博雅通識' and target_subcat:
                    # 博雅通識課程學分計算
                    categorized_data['博雅通識']['subcategories'][target_subcat][course_type_key]['earned_credits'] += credits
                    categorized_data['博雅通識']['earned_credits'] += credits
                    categorized_data['博雅通識']['total_credits'][course_type_key] += credits
                else:
                    # 其他課程學分計算
                    categorized_data[category_key]['earned_credits'] += credits
        except (ValueError, TypeError):
            continue
            
    # 過濾掉沒有課程的分類
    final_data = {}
    for k, v in categorized_data.items():
        if k in ['核心通識', '博雅通識']:
            # 檢查階層分類是否有課程
            has_courses = False
            filtered_subcats = {}
            for subcat_name, subcat_data in v['subcategories'].items():
                if subcat_data['必修']['courses'] or subcat_data['選修']['courses']:
                    filtered_subcats[subcat_name] = subcat_data
                    has_courses = True
            
            if has_courses:
                final_data[k] = v.copy()
                final_data[k]['subcategories'] = filtered_subcats
        else:
            # 其他分類的一般處理
            if v['courses']:
                final_data[k] = v
    
    return final_data

def extract_current_credits_from_categorized_data(categorized_data):
    """
    從分類後的學分資料中提取各類別的已修學分數
    用於學分缺額計算
    """
    current_credits = {
        '系必修': 0,
        '領域選修': 0,
        '校定必修': 0,
        '通識選修': 0,
        '其他': 0
    }
    
    for category, data in categorized_data.items():
        if isinstance(data, dict) and 'earned_credits' in data:
            credits = data['earned_credits']
            
            # 根據分類名稱判斷學分類型
            if '共同必修' in category or '校定必修' in category or category.startswith('共同必修系列'):
                current_credits['校定必修'] += credits
            elif category == '核心通識' or category == '博雅通識':
                # 通識選修只計算核心通識和博雅通識
                current_credits['通識選修'] += credits
            elif '必修' in category and '共同' not in category and '通識' not in category:
                current_credits['系必修'] += credits
            elif '選修' in category and '共同' not in category and '通識' not in category:
                current_credits['領域選修'] += credits
            elif '其他' in category:
                current_credits['其他'] += credits
    
    # 注意：這裡已經在上面的迴圈中處理了階層結構的通識課程
    # 不需要重複計算
    
    return current_credits

def calculate_deficit_with_department(all_semesters_data, department_name, mapping=COURSE_CODE_MAPPING):
    """
    整合函數：分析學分並計算缺額
    
    Args:
        all_semesters_data: 所有學期的課程資料
        department_name: 科系名稱
        mapping: 課程代碼對應表
    
    Returns:
        dict: 包含分類學分資料和缺額資訊
    """
    # 先進行學分分類計算
    categorized_data = categorize_and_calculate_credits(all_semesters_data, mapping)
    
    # 提取各類別已修學分
    current_credits = extract_current_credits_from_categorized_data(categorized_data)
    
    # 計算學分缺額
    deficit_info = calculate_credit_deficit(department_name, current_credits)
    
    # 整合結果
    result = {
        'categorized_credits': categorized_data,
        'current_credits_summary': current_credits,
        'deficit_analysis': deficit_info
    }
    
    return result