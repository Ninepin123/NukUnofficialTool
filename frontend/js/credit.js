// credit.js - 學分分析功能

document.addEventListener('DOMContentLoaded', function() {
    initializeCreditSystem();
});

function initializeCreditSystem() {
    const startButton = document.getElementById('startCreditAnalysis');
    const statusDiv = document.getElementById('creditStatus');
    const resultsContainer = document.getElementById('creditResults');

    if (startButton) {
        startButton.addEventListener('click', startCreditAnalysis);
    }

    async function startCreditAnalysis() {
        startButton.disabled = true;
        resultsContainer.innerHTML = '';
        showMessage(statusDiv, '處理中，請在開啟的瀏覽器視窗中登入...', 'processing');

        try {
            const data = await apiRequest('/api/start-credit-analysis', { method: 'POST' });
            
            if (data.status === 'success') {
                showMessage(statusDiv, data.message, 'success');
                renderCreditResults(data.data);
            } else {
                showMessage(statusDiv, '錯誤：' + data.message, 'error');
            }
        } catch (error) {
            console.error('Credit analysis error:', error);
            showMessage(statusDiv, '前端請求失敗，請檢查網路連線。', 'error');
        } finally {
            startButton.disabled = false;
        }
    }

    function renderCreditResults(data) {
        resultsContainer.innerHTML = '';
        
        // 顯示學分缺額摘要
        renderDeficitSummary(data);
        
        // 顯示詳細成績
        renderDetailedGrades(data);
    }

    function renderDeficitSummary(data) {
        if (!data.deficit_analysis || data.deficit_analysis.status !== 'success') {
            if (data.deficit_analysis && data.deficit_analysis.message) {
                const warningDiv = document.createElement('div');
                warningDiv.className = 'deficit-summary';
                warningDiv.innerHTML = `
                    <div class="deficit-title">學分缺額分析</div>
                    <p style="color: #856404;">${data.deficit_analysis.message}</p>
                `;
                resultsContainer.appendChild(warningDiv);
            }
            return;
        }

        const deficitInfo = data.deficit_analysis;
        const deficitDiv = document.createElement('div');
        deficitDiv.className = 'deficit-summary';

        let deficitDetailsHtml = '';
        for (const category in deficitInfo.deficit_details) {
            const detail = deficitInfo.deficit_details[category];
            const statusClass = detail.缺額 > 0 ? 'deficit-needed' : 'deficit-satisfied';
            deficitDetailsHtml += `
                <div class="deficit-item">
                    <h4>${category}</h4>
                    <div>需要：${detail.需要} 學分</div>
                    <div>已修：${detail.已修} 學分</div>
                    <div class="${statusClass}">${detail.狀態}</div>
                </div>
            `;
        }

        let recommendationsHtml = '';
        if (deficitInfo.recommendations && deficitInfo.recommendations.length > 0) {
            recommendationsHtml = `
                <div class="recommendations">
                    <h4>修課建議</h4>
                    <ul>
                        ${deficitInfo.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        deficitDiv.innerHTML = `
            <div class="deficit-title">學分缺額分析 - ${deficitInfo.department}</div>
            <div class="deficit-details">${deficitDetailsHtml}</div>
            <div style="text-align: center; padding: 10px; background-color: white; border-radius: 5px; margin-bottom: 15px;">
                <strong>總學分狀況：</strong>
                <span style="margin: 0 15px;">需求 ${deficitInfo.total_summary.總需求學分} 學分</span>
                <span style="margin: 0 15px;">已修 ${deficitInfo.total_summary.目前總學分} 學分</span>
                <span style="margin: 0 15px; color: ${deficitInfo.total_summary.總缺額 > 0 ? '#dc3545' : '#28a745'};">
                    缺額 ${deficitInfo.total_summary.總缺額} 學分
                </span>
                <div style="margin-top: 8px; font-size: 1.1em;">
                    <span style="color: ${deficitInfo.total_summary.畢業狀態.includes('符合') ? '#28a745' : '#dc3545'};">
                        ${deficitInfo.total_summary.畢業狀態}
                    </span>
                </div>
            </div>
            ${recommendationsHtml}
        `;

        resultsContainer.appendChild(deficitDiv);
    }

    function renderDetailedGrades(data) {
        const categorizedData = data.categorized_credits || data;
        if (!categorizedData || Object.keys(categorizedData).length === 0) {
            resultsContainer.innerHTML += '<p>沒有找到成績資料。</p>';
            return;
        }

        for (const categoryName in categorizedData) {
            const category = categorizedData[categoryName];
            
            if ((categoryName === '核心通識' || categoryName === '博雅通識') && category.subcategories) {
                renderHierarchicalCategory(categoryName, category);
            } else {
                renderSimpleCategory(categoryName, category);
            }
        }
    }

    function renderHierarchicalCategory(categoryName, category) {
        const mainCategoryDiv = document.createElement('div');
        mainCategoryDiv.className = 'category-block';

        const mainTitle = document.createElement('h2');
        mainTitle.className = 'category-title';
        mainTitle.textContent = `${categoryName} (總計已獲學分: ${category.earned_credits.toFixed(1)})`;
        mainCategoryDiv.appendChild(mainTitle);

        for (const subcatName in category.subcategories) {
            const subcategory = category.subcategories[subcatName];
            
            const subcatTotalCredits = subcategory['必修'].earned_credits + subcategory['選修'].earned_credits;
            
            if (subcatTotalCredits > 0 || subcategory['必修'].courses.length > 0 || subcategory['選修'].courses.length > 0) {
                const subcatTitle = document.createElement('h3');
                subcatTitle.style.marginTop = '25px';
                subcatTitle.style.marginBottom = '15px';
                subcatTitle.style.color = '#0084d1';
                subcatTitle.style.fontSize = '1.2em';
                subcatTitle.textContent = `${subcatName} (已獲學分: ${subcatTotalCredits.toFixed(1)})`;
                mainCategoryDiv.appendChild(subcatTitle);

                ['必修', '選修'].forEach(type => {
                    const typeData = subcategory[type];
                    if (typeData.courses.length > 0) {
                        const typeTitle = document.createElement('h4');
                        typeTitle.style.margin = '15px 0 10px 0';
                        typeTitle.style.color = '#666';
                        typeTitle.textContent = `${type} (${typeData.earned_credits.toFixed(1)}學分)`;
                        mainCategoryDiv.appendChild(typeTitle);

                        const table = createGradesTable(typeData.courses, false);
                        mainCategoryDiv.appendChild(table);
                    }
                });
            }
        }
        
        resultsContainer.appendChild(mainCategoryDiv);
    }

    function renderSimpleCategory(categoryName, category) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-block';

        const title = document.createElement('h2');
        title.className = 'category-title';
        title.textContent = `${categoryName} (已獲學分: ${category.earned_credits.toFixed(1)})`;
        categoryDiv.appendChild(title);

        const table = createGradesTable(category.courses, true);
        categoryDiv.appendChild(table);

        resultsContainer.appendChild(categoryDiv);
    }

    function createGradesTable(courses, includeType) {
        const table = document.createElement('table');
        table.className = 'grades-table';
        
        const headers = ['課號', '課程名稱', '學分數'];
        if (includeType) headers.push('修別');
        headers.push('期中成績', '學期成績', '備註');
        
        table.innerHTML = `
            <thead>
                <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
            </thead>
        `;

        const tbody = document.createElement('tbody');
        courses.forEach(course => {
            const row = document.createElement('tr');
            
            const isFailedOrDropped = course.remark.includes('棄選') || parseFloat(course.final_score) < 60;
            if (isFailedOrDropped) {
                row.className = 'failed-course';
            }

            const cells = [
                course.id,
                course.name,
                course.credits
            ];
            if (includeType) cells.push(course.type);
            cells.push(
                course.midterm_score,
                `<b>${course.final_score}</b>`,
                course.remark
            );

            row.innerHTML = cells.map((cell, index) => 
                `<td${index === 1 ? ' class="course-name"' : ''}>${cell}</td>`
            ).join('');
            
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        return table;
    }
}