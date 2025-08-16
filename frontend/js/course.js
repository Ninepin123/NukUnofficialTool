// course.js - 排課系統功能

// 全域變數，避免重複初始化
let courseSystemInitialized = false;

function initializeCourseSystem() {
    if (courseSystemInitialized) return;
    courseSystemInitialized = true;
    
    // --- (ICONS, Constants, State) ---
    const ICONS = { info: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd" /></svg>` };
    const API_URL = '/api/courses';
    const DEPT_MAP = { "MI": "通識微學分", "GR": "共同必修系列", "CC": "核心通識", "LI": "通識人文科學類", "SC": "通識自然科學類", "SO": "通識社會科學類", "CD": "全民國防教育類", "IN": "興趣選修", "WL": "西洋語文學系", "KH": "運動健康與休閒學系", "CCD": "工藝與創意設計學系", "DA": "建築學系", "CDA": "創意設計與建築學系", "EL": "東亞語文學系", "DAP": "運動競技學系", "CHS": "人文社會科學院共同課程", "LA": "法律學系", "GL": "政治法律學系", "FL": "財經法律學系", "CCL": "法學院共同課程", "AE": "應用經濟學系", "FI": "財務金融學系", "IM": "資訊管理學系", "CCM": "管理學院共同課程", "AM": "應用數學系", "AC": "應用化學系", "AP": "應用物理學系", "CCS": "理學院共同課程", "EE": "電機工程學系", "CE": "土木與環境工程學系", "CS": "資訊工程學系", "CM": "化學工程及材料工程學系", "CCE": "工學院共同課程", "LS": "生命科學系", "AB": "亞太工商管理學系", "ISP": "國際學生系", "CPP": "華語先修班", "FIN": "財務金融學系(停用)", "IFD": "創新學院不分系" };
    const periodOrder = ['A', '1', '2', '3', '4', 'B', '5', '6', '7', '8', 'C', '9', '10', '11', '12', 'D'];
    
    // --- State for distinct color generation ---
    const GOLDEN_RATIO_CONJUGATE = 0.61803398875;
    let lastHue = Math.random() * 360;

    let allCourses = [], queryParams = {}, addedCourseIds = new Set(), timetableState = {};
    const courseListContainer = document.getElementById('courseList'), searchInput = document.getElementById('searchInput'), deptFilter = document.getElementById('deptFilter'), courseCountSpan = document.getElementById('courseCount'), timetableBody = document.querySelector('#timetable tbody'), clearTimetableBtn = document.getElementById('clearTimetableBtn'), modal = document.getElementById('courseModal'), modalBody = document.getElementById('modalBody'), closeModalBtn = document.querySelector('.close-btn'), totalCreditsSpan = document.getElementById('totalCredits'), exportTimetableBtn = document.getElementById('exportTimetableBtn');

    async function main() {
        initializeTimetable();
        try {
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            allCourses = data.courses;
            queryParams = data.query_params;
            loadTimetable();
            populateDeptFilter(allCourses);
            applyFilters();
        } catch (error) {
            courseListContainer.innerHTML = `<p style="color: red;">無法載入課程資料。請確認後端伺服器 (app.py) 正在執行，且 courses_final.json 已成功產生。</p><p>${error}</p>`;
        }
    }
    
    function saveTimetable() {
        const courseIdsToSave = Array.from(addedCourseIds);
        localStorage.setItem('myTimetable', JSON.stringify(courseIdsToSave));
    }

    function loadTimetable() {
        const savedCourseIds = JSON.parse(localStorage.getItem('myTimetable'));
        if (savedCourseIds && Array.isArray(savedCourseIds)) {
            savedCourseIds.forEach(courseId => {
                const course = allCourses.find(c => c.id === courseId);
                if (course) {
                    addCourseToTimetable(course, true); 
                }
            });
        }
    }

    function openModalWithCourseDetails(course) {
        const deptName = DEPT_MAP[course.department] || course.department;
        const detailUrl = `https://course.nuk.edu.tw/QueryCourse/tcontent.asp?OpenYear=${queryParams.OpenYear}&Helf=${queryParams.Helf}&Sclass=${course.department}&Cono=${course.code}`;
        const registrationCode = `${course.department}${course.code}`;
        modalBody.innerHTML = `
            <div class="modal-title-container">
                <h2>${course.name}</h2>
                <a href="${detailUrl}" target="_blank" class="detail-link" title="查看原始課程大綱">${ICONS.info}</a>
            </div>
            <table>
                <tr><td>課號</td><td>${course.code}</td></tr>
                <tr><td>選課代碼</td><td class="registration-code-cell"><span id="registrationCode">${registrationCode}</span><button id="copyCodeBtn" title="複製代碼">複製</button></td></tr>
                <tr><td>授課教師</td><td>${course.teacher}</td></tr>
                <tr><td>開課系所</td><td>${deptName}</td></tr>
                <tr><td>學分</td><td>${course.credits}</td></tr>
                <tr><td>限修人數</td><td>${course.limit}</td></tr>
                <tr><td>選課確定</td><td id="modal-confirmed">更新中...</td></tr>
                <tr><td>線上人數</td><td id="modal-online-count">更新中...</td></tr>
                <tr><td>餘額</td><td id="modal-remaining">更新中...</td></tr>
                <tr><td>上課教室</td><td>${course.classroom || '未定'}</td></tr>
                <tr><td>上課時間</td><td>${formatCourseTime(course.time)}</td></tr>
                <tr><td>先修/限修</td><td>${course.prerequisites || '無'}</td></tr>
                <tr><td>備註</td><td>${course.note || '無'}</td></tr>
            </table>
        `;
        modal.style.display = "block";
        document.getElementById('copyCodeBtn').addEventListener('click', () => copyRegistrationCode(registrationCode));
        fetchCourseUpdate(course);
    }

    async function fetchCourseUpdate(course) {
        try {
            const updateUrl = `/api/course-update?year=${queryParams.OpenYear}&helf=${queryParams.Helf}&sclass=${course.department}&cono=${course.code}&coname=${encodeURIComponent(course.name)}`;
            const response = await fetch(updateUrl);
            const updateData = await response.json();
            const confirmedCell = document.getElementById('modal-confirmed'), onlineCell = document.getElementById('modal-online-count'), remainingCell = document.getElementById('modal-remaining');
            if (response.ok && !updateData.error) {
                confirmedCell.textContent = updateData.confirmed;
                onlineCell.textContent = updateData.online_count;
                remainingCell.textContent = updateData.remaining;
            } else {
                console.error("Live update failed:", updateData.error);
                confirmedCell.textContent = '更新失敗'; onlineCell.textContent = '更新失敗'; remainingCell.textContent = '更新失敗';
            }
        } catch (error) {
            console.error("Error fetching course update:", error);
            document.getElementById('modal-confirmed').textContent = '網路錯誤'; document.getElementById('modal-online-count').textContent = '網路錯誤'; document.getElementById('modal-remaining').textContent = '網路錯誤';
        }
    }
    
    function copyRegistrationCode(code) {
        navigator.clipboard.writeText(code).then(() => {
            const copyBtn = document.getElementById('copyCodeBtn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '已複製!';
            setTimeout(() => { copyBtn.textContent = originalText; }, 2000);
        }).catch(err => { console.error('無法複製代碼: ', err); alert('複製失敗'); });
    }
    
    function populateDeptFilter(courses) { const depts = [...new Set(courses.map(course => course.department))]; depts.sort((a, b) => (DEPT_MAP[a] || a).localeCompare(DEPT_MAP[b] || b, 'zh-Hant')); depts.forEach(deptCode => { const option = document.createElement('option'); option.value = deptCode; option.textContent = DEPT_MAP[deptCode] || deptCode; deptFilter.appendChild(option); }); }
    function applyFilters() { const searchTerm = searchInput.value.toLowerCase().trim(); const selectedDept = deptFilter.value; let filteredCourses = allCourses; if (selectedDept) { filteredCourses = filteredCourses.filter(c => c.department === selectedDept); } if (searchTerm) { filteredCourses = filteredCourses.filter(c => c.name.toLowerCase().includes(searchTerm) || c.teacher.toLowerCase().includes(searchTerm) || c.code.toLowerCase().includes(searchTerm)); } renderCourseList(filteredCourses); }
    function renderCourseList(courses) { courseListContainer.innerHTML = ''; courseCountSpan.textContent = `共 ${courses.length} 筆`; if (courses.length === 0) { courseListContainer.innerHTML = '<p>沒有找到符合條件的課程。</p>'; return; } const fragment = document.createDocumentFragment(); courses.forEach(course => { const courseItem = document.createElement('div'); courseItem.className = 'course-item'; courseItem.id = `course-item-${course.id}`; const deptName = DEPT_MAP[course.department] || course.department; const courseTime = formatCourseTime(course.time); courseItem.innerHTML = `<div class="add-btn-container"><button class="add-btn" data-course-id="${course.id}">${addedCourseIds.has(course.id) ? '取消' : '加入'}</button></div><h3 class="course-title" data-course-id="${course.id}">${course.name}</h3><p><strong>系所:</strong> ${deptName}</p><p><strong>教師:</strong> ${course.teacher} | <strong>課號:</strong> ${course.code}</p><p><strong>時間:</strong> ${courseTime}</p> `; if (addedCourseIds.has(course.id)) { courseItem.querySelector('.add-btn').classList.add('added'); } fragment.appendChild(courseItem); }); courseListContainer.appendChild(fragment); }
    function initializeTimetable() { timetableBody.innerHTML = ''; periodOrder.forEach(period => { const row = document.createElement('tr'); if (['A', 'B', 'C', 'D'].includes(period)) { row.classList.add('break-period'); } row.innerHTML = `<td class="time-slot">${period}</td>`; for (let i = 0; i < 6; i++) { const day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][i]; row.innerHTML += `<td data-day="${day}" data-period="${period}"></td>`; } timetableBody.appendChild(row); }); }
    
    function getNextDistinctColor() {
        lastHue = (lastHue + GOLDEN_RATIO_CONJUGATE * 360) % 360;
        return `hsl(${lastHue}, 70%, 88%)`;
    }

    function addCourseToTimetable(course, isLoading = false) {
        if (addedCourseIds.has(course.id)) return;
        for (const day in course.time) {
            for (const period of course.time[day]) {
                const timeSlotKey = `${day}-${period}`;
                if (timetableState[timeSlotKey]) {
                    const existingCourseId = timetableState[timeSlotKey];
                    const existingCourse = allCourses.find(c => c.id === existingCourseId);
                    if (existingCourse) {
                        const dayMap = { Mon: "一", Tue: "二", Wed: "三", Thu: "四", Fri: "五", Sat: "六" };
                        const conflictingDay = dayMap[day] || day;
                        // --- KEY CHANGE: Updated alert message as requested ---
                        const alertMessage = `衝堂！\n"${course.name}"與課表中星期${conflictingDay}的"${existingCourse.name}"衝堂`;
                        alert(alertMessage);
                    } else {
                        alert(`衝堂！無法加入課程 "${course.name}"。`);
                    }
                    return;
                }
            }
        }
        addedCourseIds.add(course.id);
        const courseColor = getNextDistinctColor();
        let allSlots = [];
        for (const day in course.time) {
            for (const period of course.time[day]) { allSlots.push({ day, period }); }
        }
        allSlots.sort((a, b) => {
            const dayOrder = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
            if (dayOrder.indexOf(a.day) !== dayOrder.indexOf(b.day)) {
                return dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day);
            }
            return periodOrder.indexOf(a.period) - periodOrder.indexOf(b.period);
        });
        const primarySlot = allSlots.length > 0 ? allSlots[0] : null;
        allSlots.forEach(slot => {
            const cell = timetableBody.querySelector(`td[data-day="${slot.day}"][data-period="${slot.period}"]`);
            if (cell) {
                const isPrimaryCell = primarySlot && (slot.day === primarySlot.day && slot.period === primarySlot.period);
                const removeButtonHTML = isPrimaryCell ? `<span class="remove-btn" data-course-id="${course.id}" title="移除課程">×</span>` : '';
                cell.dataset.courseGroupId = course.id;
                cell.innerHTML = `<div class="course-cell-content">${course.name}<br><small>${course.teacher}</small></div>${removeButtonHTML}`;
                cell.className = 'course-cell';
                cell.style.backgroundColor = courseColor;
                timetableState[`${slot.day}-${slot.period}`] = course.id;
            }
        });
        updateAddButtonState(course.id, true);
        if (!isLoading) {
            scrollToCourseInList(course.id);
        }
        updateTotalCredits();
        if (!isLoading) {
            saveTimetable();
        }
    }
    
    function removeCourseFromTimetable(courseId) {
        if (!addedCourseIds.has(courseId)) return;
        addedCourseIds.delete(courseId);
        for (const key in timetableState) {
            if (timetableState[key] === courseId) {
                const [day, period] = key.split('-');
                const cell = timetableBody.querySelector(`td[data-day="${day}"][data-period="${period}"]`);
                if (cell) {
                    cell.innerHTML = '';
                    cell.className = '';
                    cell.style.backgroundColor = '';
                    delete cell.dataset.courseGroupId;
                }
                delete timetableState[key];
            }
        }
        updateAddButtonState(courseId, false);
        updateTotalCredits();
        saveTimetable();
    }
    
    function updateTotalCredits() {
        let totalCredits = 0;
        addedCourseIds.forEach(courseId => {
            const course = allCourses.find(c => c.id === courseId);
            if (course && course.credits) {
                totalCredits += Number(course.credits) || 0;
            }
        });
        totalCreditsSpan.textContent = `總學分數：${totalCredits}`;
    }
    
    function formatCourseTime(time) { const dayMap = { Mon: "一", Tue: "二", Wed: "三", Thu: "四", Fri: "五", Sat: "六", Sun: "日" }; let parts = []; for (const day in time) { if (time[day].length > 0) parts.push(`${dayMap[day]}[${time[day].join(',')}]`); } return parts.join(' ') || '時間未定'; }
    function updateAddButtonState(courseId, isAdded) { const btn = document.querySelector(`#course-item-${courseId} .add-btn`); if (btn) { btn.textContent = isAdded ? '取消' : '加入'; btn.classList.toggle('added', isAdded); } }
    function scrollToCourseInList(courseId) { const courseItem = document.getElementById(`course-item-${courseId}`); if (courseItem) { courseItem.scrollIntoView({ behavior: 'smooth', block: 'center' }); courseItem.classList.add('highlight'); setTimeout(() => courseItem.classList.remove('highlight'), 1500); } }
    function exportTimetable() { const exportBtn = document.getElementById('exportTimetableBtn'); const timetableElement = document.getElementById('timetable'); if (addedCourseIds.size === 0) { alert("您的課表是空的"); return; } exportBtn.textContent = "正在產生..."; exportBtn.disabled = true; html2canvas(timetableElement, { useCORS: true, scale: 2, backgroundColor: '#ffffff' }).then(canvas => { const imageUrl = canvas.toDataURL("image/png"); const a = document.createElement('a'); a.href = imageUrl; a.download = '我的課表.png'; document.body.appendChild(a); a.click(); document.body.removeChild(a); exportBtn.textContent = "匯出課表"; exportBtn.disabled = false; }).catch(error => { console.error("匯出錯誤:", error); alert("圖片產生失敗"); exportBtn.textContent = "匯出課表"; exportBtn.disabled = false; }); }

    // --- Event Listeners ---
    searchInput.addEventListener('input', applyFilters);
    deptFilter.addEventListener('change', applyFilters);
    courseListContainer.addEventListener('click', e => { const courseId = e.target.dataset.courseId; if (!courseId) return; const course = allCourses.find(c => c.id === courseId); if (!course) return; if (e.target.classList.contains('add-btn')) { if (addedCourseIds.has(courseId)) { removeCourseFromTimetable(courseId); } else { addCourseToTimetable(course); } } else if (e.target.classList.contains('course-title')) { openModalWithCourseDetails(course); } });
    timetableBody.addEventListener('click', e => { const target = e.target; if (target.classList.contains('remove-btn')) { removeCourseFromTimetable(target.dataset.courseId); } const contentCell = target.closest('.course-cell-content'); if (contentCell) { const courseId = target.closest('.course-cell').dataset.courseGroupId; const course = allCourses.find(c => c.id === courseId); if (course) { openModalWithCourseDetails(course); } } });
    timetableBody.addEventListener('mouseenter', e => { const cell = e.target.closest('.course-cell'); if (cell && cell.dataset.courseGroupId) { const courseId = cell.dataset.courseGroupId; document.querySelectorAll(`[data-course-group-id="${courseId}"]`).forEach(c => { c.classList.add('hover-highlight'); }); const removeBtn = document.querySelector(`.remove-btn[data-course-id="${courseId}"]`); if (removeBtn) { removeBtn.classList.add('show'); } } }, true);
    timetableBody.addEventListener('mouseleave', e => { const cell = e.target.closest('.course-cell'); if (cell && cell.dataset.courseGroupId) { const courseId = cell.dataset.courseGroupId; document.querySelectorAll(`[data-course-group-id="${courseId}"]`).forEach(c => { c.classList.remove('hover-highlight'); }); const removeBtn = document.querySelector(`.remove-btn[data-course-id="${courseId}"]`); if (removeBtn) { removeBtn.classList.remove('show'); } } }, true);
    
    clearTimetableBtn.addEventListener('click', () => {
        if (confirm('確定要清空整個課表嗎？')) {
            const idsToRemove = [...addedCourseIds];
            idsToRemove.forEach(id => removeCourseFromTimetable(id));
        }
    });

    exportTimetableBtn.addEventListener('click', exportTimetable);
    closeModalBtn.onclick = () => { modal.style.display = "none"; };
    window.onclick = (event) => { if (event.target == modal) { modal.style.display = "none"; } };

    // 啟動主要功能
    main();
}