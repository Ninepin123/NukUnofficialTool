# parser.py

from bs4 import BeautifulSoup


def parse_grades_html(html_source):
    soup = BeautifulSoup(html_source, 'lxml')
    all_semesters_data = []
    semester_titles = soup.find_all('font', {'face': '標楷體', 'color': '#0000FF'})
    for title_tag in semester_titles:
        semester_data = {"semester_name": title_tag.b.get_text(strip=True), "courses": [], "summary": {}}
        courses_table = title_tag.find_parent('p').find_next_sibling('table')
        if not courses_table: continue
        course_rows = courses_table.find_all('tr')[1:]
        for row in course_rows:
            cells = row.find_all('td')
            if len(cells) == 7:
                course_info = {"id": cells[0].get_text(strip=True), "name": cells[1].get_text(strip=True), "credits": cells[2].get_text(strip=True), "type": cells[3].get_text(strip=True), "midterm_score": cells[4].get_text(strip=True), "final_score": cells[5].get_text(strip=True), "remark": cells[6].get_text(strip=True)}
                semester_data["courses"].append(course_info)
        summary_table = courses_table.find_next_sibling('p').find('table')
        if summary_table:
            summary_cells = summary_table.find_all('td')
            for cell in summary_cells:
                text = cell.get_text(strip=True)
                if '：' in text:
                    key, value = text.split('：', 1)
                    semester_data["summary"][key] = value
        all_semesters_data.append(semester_data)
    return all_semesters_data