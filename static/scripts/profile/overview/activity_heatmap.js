// static/scripts/profile/overview/activity_heatmap.js
document.addEventListener('DOMContentLoaded', () => {
  const heatmapGrid = document.getElementById('activity-heatmap-grid');
  const heatmapDataScript = document.getElementById('heatmap-data-script');
  const yearSelect = document.getElementById('activity-year-select');
  const yearForm = document.getElementById('activity-year-form');
  const totalNotesSpan = document.getElementById('heatmap-total-notes');
  const monthsRow = document.querySelector('.heatmap-months-row');
  // const daysCol = document.querySelector('.heatmap-days-col'); // Уже есть в HTML

  if (!heatmapGrid || !heatmapDataScript || !yearSelect || !yearForm || !totalNotesSpan || !monthsRow) {
      console.warn('Heatmap elements not found. Activity heatmap will not be rendered.');
      return;
  }

  const activityData = JSON.parse(heatmapDataScript.textContent);
  const selectedYear = parseInt(yearSelect.value, 10);
  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const CELL_SIZE = 16;
  const CELL_GAP = 2;
  const NUM_WEEKS = 53;

  function getDayOfWeekMondayFirst(date) {
      let day = date.getDay(); // Sunday is 0, Monday is 1, etc.
      return (day === 0) ? 6 : day - 1;
  }

  function renderHeatmap(year, data) {
    heatmapGrid.innerHTML = '';
    monthsRow.innerHTML = '';

    const startDate = new Date(year, 0, 1);
    const firstDayOfYearIsMondayBased = getDayOfWeekMondayFirst(startDate);
    let totalContributions = 0;
    const cellsData = Array(NUM_WEEKS * 7).fill(null);
    
    for (let i = 0; i < NUM_WEEKS * 7; i++) {

        const dayOffset = i - firstDayOfYearIsMondayBased;
        const currentDate = new Date(year, 0, 1 + dayOffset);

        if (currentDate.getFullYear() === year) {
            const dateString = currentDate.toISOString().split('T')[0];
            const count = data[dateString] || 0;
            totalContributions += count;
            cellsData[i] = {
                date: dateString,
                count: count,
                dateObj: currentDate,
                active: true
            };
        } else {
            cellsData[i] = { active: false };
        }
    }

    cellsData.forEach(dayData => {
        const cell = document.createElement('div');
        cell.classList.add('heatmap-day-cell');
        if (dayData.active) {
            let level = 0;
            if (dayData.count > 0 && dayData.count <= 2) level = 1;
            else if (dayData.count > 2 && dayData.count <= 5) level = 2;
            else if (dayData.count > 5 && dayData.count <= 10) level = 3;
            else if (dayData.count > 10) level = 4;
            cell.classList.add(`level-${level}`);
            cell.dataset.date = dayData.date;
            cell.dataset.count = dayData.count;
            cell.title = `${dayData.count} contributions on ${dayData.dateObj.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}`;
        } else {
            cell.classList.add('level-0');
            cell.style.visibility = 'hidden';
        }
        heatmapGrid.appendChild(cell);
    });

    // Рендерим месяцы
    // Считаем, сколько недель занимает каждый месяц для позиционирования
    
    const monthWeekCounts = Array(12).fill(0);
    const firstWeekOfMonth = Array(12).fill(-1);

    for (let week = 0; week < NUM_WEEKS; week++) {
        // Проверяем, какой месяц доминирует в этой неделе или первый активный день недели
        let dominantMonth = -1;
        for (let day = 0; day < 7; day++) {
            const cellIndex = week * 7 + day;
            if (cellsData[cellIndex] && cellsData[cellIndex].active) {
                dominantMonth = cellsData[cellIndex].dateObj.getMonth();
                break; // Нашли первый активный день, его месяц считаем доминирующим для этой недели
            }
        }
        if (dominantMonth !== -1) {
            monthWeekCounts[dominantMonth]++;
            if (firstWeekOfMonth[dominantMonth] === -1) {
                firstWeekOfMonth[dominantMonth] = week;
            }
        }
    }
    
    monthsRow.innerHTML = '';
    const weekWidthWithGap = CELL_SIZE + CELL_GAP;

    // Найдем первую неделю каждого месяца
    const monthStartWeeks = Array(12).fill(-1);
    for (let i = 0; i < cellsData.length; i++) {
        if (cellsData[i] && cellsData[i].active) {
            const month = cellsData[i].dateObj.getMonth();
            const weekIndex = Math.floor(i / 7);
            if (monthStartWeeks[month] === -1) {
                monthStartWeeks[month] = weekIndex;
            }
        }
    }
    // Если какой-то месяц не найден (например, в очень коротком году), он не будет отображен
    // Для месяцев, которые не начались (например, если год неполный), заполним их начальной неделей следующего найденного
    for(let m = 11; m >=0; m--) {
        if(monthStartWeeks[m] === -1 && m < 11 && monthStartWeeks[m+1] !== -1) {
            // Если месяц не имеет активных дней, но следующий имеет,
            // ставим его "начало" туда же, где и у предыдущего нарисованного месяца,
            // или пробуем рассчитать примерно. Это сложный крайний случай.
            // Пока просто пропустим его, если он не имеет активных дней.
        }
    }


    for (let m = 0; m < 12; m++) {
        if (monthStartWeeks[m] === -1) continue; // Пропускаем месяцы без активных дней или если не смогли определить начало

        const monthDiv = document.createElement('div');
        monthDiv.textContent = monthNames[m];

        // Позиция 'left' для названия месяца
        // Это начальная неделя месяца * (ширина одной недельной колонки в сетке)
        const leftPosition = monthStartWeeks[m] * weekWidthWithGap;
        monthDiv.style.left = `${leftPosition}px`;
        
        // Ширина для названия месяца
        // От начала этого месяца до начала следующего (или до конца сетки для декабря)
        let nextMonthStartWeek;
        if (m < 11) {
            // Ищем следующую реальную стартовую неделю
            let foundNext = false;
            for(let next_m = m + 1; next_m < 12; next_m++) {
                if(monthStartWeeks[next_m] !== -1) {
                    nextMonthStartWeek = monthStartWeeks[next_m];
                    foundNext = true;
                    break;
                }
            }
            if(!foundNext) { // Если это последний отображаемый месяц перед концом года
                nextMonthStartWeek = NUM_WEEKS; // До конца сетки
            }
        } else { // Декабрь
            nextMonthStartWeek = NUM_WEEKS; // До конца сетки (53 недели)
        }
        
        const weeksInThisMonthDisplay = nextMonthStartWeek - monthStartWeeks[m];
        // Ширина = (кол-во недель * ширина недели) - один CELL_GAP (т.к. последний gap не нужен)
        const monthDisplayWidth = (weeksInThisMonthDisplay * weekWidthWithGap) - (weeksInThisMonthDisplay > 0 ? CELL_GAP : 0) ;
        
        // Ограничим минимальную ширину, чтобы текст влез
        monthDiv.style.width = `${Math.max(30, monthDisplayWidth)}px`; // Минимум 30px для текста

        monthsRow.appendChild(monthDiv);
    }

    if(totalNotesSpan) {
        totalNotesSpan.textContent = `${totalContributions} contributions in ${year}`;
    }
  }

  // Первоначальный рендер
  renderHeatmap(selectedYear, activityData);

  // Обработчик изменения года
  if (yearSelect && yearForm) {
      yearSelect.addEventListener('change', () => {
          yearForm.submit();
      });
  }
});