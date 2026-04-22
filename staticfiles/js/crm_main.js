/**
 * CRM Main Logic Module
 */

$(document).ready(function() {
    let currentRecordType = '';
    let currentDealType = '';
    let isEditMode = false;
    let editRecordId = null;
    
    // Кастомные фильтры
    let activeFilters = { 
        ranges: {},
        dates: {},
        selects: {}
    };

    // --- Функции сохранения и восстановления фильтров ---
    function saveFiltersState() {
        const state = {
            ranges: activeFilters.ranges,
            dates: activeFilters.dates,
            selects: activeFilters.selects,
            search: $('#customGlobalSearch').val() || '',
            page: $('.table').DataTable().page()
        };
        sessionStorage.setItem('crmFiltersState', JSON.stringify(state));
    }

    function restoreFiltersState() {
        const saved = sessionStorage.getItem('crmFiltersState');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                activeFilters = {
                    ranges: state.ranges || {},
                    dates: state.dates || {},
                    selects: state.selects || {}
                };
                $('#customGlobalSearch').val(state.search || '');
                sessionStorage.removeItem('crmFiltersState');
                return true;
            } catch(e) {
                return false;
            }
        }
        return false;
    }

    // Сохраняем фильтры перед уходом со страницы
    $(window).on('beforeunload', function() {
        if (isEditMode) {
            saveFiltersState();
        }
    });

    // Восстанавливаем фильтры после загрузки
    const wasRestored = restoreFiltersState();

    // Инициализация Bootstrap модальных окон
    const modalSelectElement = document.getElementById('addRecordModal');
    const modalFormElement = document.getElementById('addFormModal');
    
    let modalSelect, modalForm;
    if (modalSelectElement) modalSelect = new bootstrap.Modal(modalSelectElement);
    if (modalFormElement) modalForm = new bootstrap.Modal(modalFormElement);

    // --- Логика открытия модального окна добавления ---
    $('#btnOpenAddModal').click(function() { 
        isEditMode = false; 
        editRecordId = null;
        $('#btnBackToSelection').show(); 
        $('#btnDeleteRecord').hide();
        $('#btnSaveRecord').html('СОХРАНИТЬ В БАЗУ');
        $('#formPropertyView')[0].reset(); 
        $('#formClientView')[0].reset();
        if (modalSelect) modalSelect.show(); 
    });
    
    $('input[name="recordType"]').on('change', function() {
        const type = $(this).val();
        $('input[name="dealType"]').prop('checked', false);
        $('#continueAddBtn').hide();
        if (type === 'property') {
            $('#dealAction1').val('sale'); 
            $('#labelAction1').html('<i class="bi bi-cash-coin me-2"></i>Продать');
            $('#dealAction2').val('rent'); 
            $('#labelAction2').html('<i class="bi bi-key-fill me-2"></i>Сдать');
        } else if (type === 'client') {
            $('#dealAction1').val('buy'); 
            $('#labelAction1').html('<i class="bi bi-bag-check me-2"></i>Купить');
            $('#dealAction2').val('rent'); 
            $('#labelAction2').html('<i class="bi bi-house-door me-2"></i>Снять');
        }
        $('#step2Block').slideDown(200);
    });

    $('input[name="dealType"]').on('change', function() { 
        $('#continueAddBtn').fadeIn(200); 
    });

    $('#continueAddBtn').click(function() {
        currentRecordType = $('input[name="recordType"]:checked').val();
        currentDealType = $('input[name="dealType"]:checked').val();
        $('#formPropertyView, #formClientView').hide();

        if (currentRecordType === 'property') {
            const titleText = currentDealType === 'sale' ? 'Новый объект: На продажу' : 'Новый объект: В аренду';
            $('#addFormModalTitle').html('<i class="bi bi-building-add text-warning me-2" style="color:#D7B56D!important;"></i>' + titleText);
            $('#formPropertyView').show();
        } else {
            const titleText = currentDealType === 'buy' ? 'Новый клиент: Покупка' : 'Новый клиент: Аренда';
            $('#addFormModalTitle').html('<i class="bi bi-person-add text-warning me-2" style="color:#D7B56D!important;"></i>' + titleText);
            $('#formClientView').show();
        }
        if (modalSelect) modalSelect.hide(); 
        if (modalForm) modalForm.show();
    });

    $('#btnBackToSelection').click(function() { 
        if (modalForm) modalForm.hide(); 
        if (modalSelect) modalSelect.show(); 
    });

    // --- Клик по строке (Редактирование) ---
    $('tbody').on('click', 'td', function() {
        const colIdx = $(this).index();
        const totalCols = $(this).closest('tr').children('td').length;
        if (colIdx >= totalCols - 2) return;

        const tr = $(this).closest('tr');
        const recId = tr.data('id');
        const recType = tr.data('type');

        if (!recId || !recType) return;

        $.ajax({
            url: '/get-record/', 
            type: 'POST',
            data: { 
                'record_id': recId, 
                'record_type': recType, 
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val() 
            },
            success: function(res) {
                if (res.status === 'denied') return; 
                if (res.status === 'error') { alert(res.message); return; }

                isEditMode = true; 
                editRecordId = recId; 
                currentRecordType = recType; 
                currentDealType = res.data.dealType;

                $('#btnBackToSelection').hide(); 
                if (window.CRM_CONFIG.isStaff) {
                    $('#btnDeleteRecord').show();
                } else {
                    $('#btnDeleteRecord').hide();
                }

                $('#btnSaveRecord').html('СОХРАНИТЬ ИЗМЕНЕНИЯ');

                const formId = recType === 'property' ? '#formPropertyView' : '#formClientView';
                const form = $(formId); 
                form[0].reset();

                $.each(res.data, function(key, val) {
                    const input = form.find('[name="'+key+'"]');
                    if (input.length) { input.val(val); }
                });

                $('#formPropertyView, #formClientView').hide();
                const icon = '<i class="bi bi-pencil-square text-warning me-2" style="color:#D7B56D!important;"></i>';
                if (recType === 'property') {
                    const titleText = currentDealType === 'sale' ? 'Редактирование (Продажа)' : 'Редактирование (Аренда)';
                    $('#addFormModalTitle').html(icon + titleText);
                    $('#formPropertyView').show();
                } else {
                    const titleText = currentDealType === 'buy' ? 'Редактирование (Покупка)' : 'Редактирование (Аренда)';
                    $('#addFormModalTitle').html(icon + titleText);
                    $('#formClientView').show();
                }
                if (modalForm) modalForm.show();
            }
        });
    });

    // --- Сохранение записи ---
    $('#btnSaveRecord').click(function(e) {
        e.preventDefault();
        const btn = $(this);
        const formId = currentRecordType === 'property' ? '#formPropertyView' : '#formClientView';
        let formData = $(formId).serialize(); 
        formData += '&recordType=' + currentRecordType + '&dealType=' + currentDealType + '&csrfmiddlewaretoken=' + $('input[name=csrfmiddlewaretoken]').val();
        const ajaxUrl = isEditMode ? '/edit-record/' : '/add-record/';
        if (isEditMode) formData += '&record_id=' + editRecordId;

        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>СОХРАНЕНИЕ...');
        
        $.ajax({
            url: ajaxUrl, 
            type: 'POST', 
            data: formData,
            success: function(response) {
                if(response.status === 'ok') {
                    // Сохраняем состояние фильтров перед перезагрузкой
                    saveFiltersState();
                    // Перезагружаем страницу
                    location.reload();
                } else { 
                    alert('Ошибка: ' + response.message); 
                    btn.prop('disabled', false).html(isEditMode ? 'СОХРАНИТЬ ИЗМЕНЕНИЯ' : 'СОХРАНИТЬ В БАЗУ'); 
                }
            },
            error: function() {
                alert('Ошибка соединения с сервером');
                btn.prop('disabled', false).html(isEditMode ? 'СОХРАНИТЬ ИЗМЕНЕНИЯ' : 'СОХРАНИТЬ В БАЗУ');
            }
        });
    });

    // --- Удаление записи ---
    $('#btnDeleteRecord').click(function(e) {
        e.preventDefault();
        if (!confirm('Вы уверены, что хотите навсегда удалить эту запись?')) return;
        const btn = $(this); 
        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');
        
        $.ajax({
            url: '/delete-record/', 
            type: 'POST',
            data: { 
                'record_id': editRecordId, 
                'record_type': currentRecordType, 
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val() 
            },
            success: function(response) {
                if (response.status === 'ok') {
                    saveFiltersState();
                    location.reload();
                } else { 
                    alert('Ошибка: ' + response.message); 
                    btn.prop('disabled', false).html('УДАЛИТЬ'); 
                }
            }
        });
    });

    // --- Быстрое переключение статуса ---
    $('tbody').on('click', '.status-toggle', function(e) {
        e.stopPropagation(); 
        const badge = $(this); 
        const tr = badge.closest('tr');
        
        badge.html('<span class="spinner-border spinner-border-sm" style="width: 1rem; height: 1rem;"></span>');
        
        $.ajax({
            url: '/toggle-status/', 
            type: 'POST',
            data: { 
                'record_id': tr.data('id'), 
                'record_type': tr.data('type'), 
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val() 
            },
            success: function(response) {
                if (response.status === 'ok') {
                    saveFiltersState();
                    location.reload();
                } else { 
                    alert('Ошибка: ' + response.message); 
                }
            }
        });
    });

    // --- Быстрое обновление даты ---
    $('tbody').on('click', '.date-toggle', function(e) {
        e.stopPropagation(); 
        const badge = $(this); 
        const tr = badge.closest('tr');
        
        badge.html('<span class="spinner-border spinner-border-sm" style="width: 0.8rem; height: 0.8rem;"></span>').removeClass('date-green date-red');
        
        $.ajax({
            url: '/update-date/', 
            type: 'POST',
            data: { 
                'record_id': tr.data('id'), 
                'record_type': tr.data('type'), 
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val() 
            },
            success: function(response) {
                if (response.status === 'ok') {
                    saveFiltersState();
                    location.reload();
                } else { 
                    alert('Ошибка: ' + response.message); 
                }
            }
        });
    });

    // --- КОМБИНИРОВАННЫЙ ФИЛЬТР DataTables ---
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        for (let colIdx in activeFilters.ranges) {
            const filter = activeFilters.ranges[colIdx];
            if (filter.min !== null || filter.max !== null) {
                let cellVal = parseFloat(String(data[colIdx]).replace(/<[^>]*>?/gm, '').replace(/\s/g, '').replace('&nbsp;', ''));
                if (isNaN(cellVal)) return false;
                if (filter.min !== null && cellVal < filter.min) return false;
                if (filter.max !== null && cellVal > filter.max) return false;
            }
        }
        
        for (let colIdx in activeFilters.dates) {
            const dFilter = activeFilters.dates[colIdx];
            if (dFilter.active) {
                const cellStr = String(data[colIdx]).replace(/<[^>]*>?/gm, '').trim();
                const parts = cellStr.split('.');
                if (parts.length === 3) {
                    const cDate = new Date(parts[2], parts[1] - 1, parts[0]).getTime();
                    if (dFilter.exact && cDate !== dFilter.min) return false;
                    if (!dFilter.exact && (cDate < dFilter.min || cDate > dFilter.max)) return false;
                } else { 
                    return false; 
                }
            }
        }
        
        for (let colIdx in activeFilters.selects) {
            const val = activeFilters.selects[colIdx];
            if (val) {
                let cellData = data[colIdx];
                let cellText = $('<div>').html(cellData).text().replace(/\s+/g, ' ').trim();
                if (cellText !== val) return false;
            }
        }
        
        return true;
    });

    // --- Инициализация ОСНОВНЫХ ТАБЛИЦ ---
    const tableElement = $('.table:not(#reportTable)');
    if (tableElement.length > 0) {
        tableElement.find('thead tr').clone(true).addClass('filters').appendTo(tableElement.find('thead'));
        
        const table = tableElement.DataTable({
            "language": { "url": "https://cdn.datatables.net/plug-ins/1.13.6/i18n/ru.json" },
            "paging": true, 
            "pageLength": 100, 
            "lengthMenu": [[100, 200, 500, -1],[100, 200, 500, "Все"]],
            "deferRender": true, 
            "info": false, 
            "dom": "t<'d-flex justify-content-between align-items-center mt-2'lp>",
            "orderCellsTop": true, 
            "autoWidth": false,
            "drawCallback": function(settings) {
                const api = this.api(); 
                const pageInfo = api.page.info(); 
                const wrapper = $(settings.nTableWrapper);
                if (pageInfo.pages <= 1) wrapper.find('.dataTables_paginate').hide(); 
                else wrapper.find('.dataTables_paginate').show();
                if (pageInfo.recordsDisplay <= 100) wrapper.find('.dataTables_length').hide(); 
                else wrapper.find('.dataTables_length').show();
            },
            initComplete: function () {
                const api = this.api();
                
                // Восстанавливаем значения фильтров из activeFilters
                api.columns().eq(0).each(function (colIdx) {
                    const cell = tableElement.find('.filters th').eq(colIdx);
                    const title = tableElement.find('thead tr:first th').eq(colIdx).text().trim().toLowerCase();
                    const headCell = $(api.column(colIdx).header());
                    
                    if (colIdx === 0 || title === '№' || title === '#') { 
                        headCell.addClass('col-number'); 
                        cell.addClass('col-number'); 
                    }
                    else if (title.includes('примечание') || title.includes('комментарий')) { 
                        headCell.addClass('truncate-text'); 
                        cell.addClass('truncate-text'); 
                    }
                    else if (title.includes('дата') || title.includes('этаж') || title.includes('уровн') || 
                             title.includes('площадь') || title.includes('цена') || title.includes('стоимость') || 
                             title.includes('бюджет')) { 
                        headCell.addClass('narrow-col'); 
                        cell.addClass('narrow-col'); 
                    }

                    if (colIdx === 0 || title === '№' || title === '#') { 
                        cell.html(''); 
                    }
                    else if (title.includes('площадь') || title.includes('цена') || title.includes('бюджет') || title.includes('стоимость')) {
                        cell.html('<div class="d-flex gap-1"><input type="number" class="min-range" placeholder="От" /><input type="number" class="max-range" placeholder="До" /></div>');
                        
                        // Восстанавливаем значения если были сохранены
                        if (activeFilters.ranges[colIdx]) {
                            const filter = activeFilters.ranges[colIdx];
                            if (filter.min !== null) cell.find('.min-range').val(filter.min);
                            if (filter.max !== null) cell.find('.max-range').val(filter.max);
                        }
                        
                        $('input', cell).on('keyup change', function () { 
                            const minV = parseFloat(cell.find('.min-range').val()); 
                            const maxV = parseFloat(cell.find('.max-range').val());
                            activeFilters.ranges[colIdx] = { 
                                min: isNaN(minV) ? null : minV, 
                                max: isNaN(maxV) ? null : maxV 
                            };
                            table.draw(); 
                        });
                    } 
                    else if (title.includes('статус') || title.includes('менеджер')) {
                        const select = $('<select><option value="">Все</option></select>'); 
                        cell.html(select);
                        
                        let uniqueVals = [];
                        api.column(colIdx).data().each(function (d) { 
                            let val = $('<div>').html(d).text();
                            val = val.replace(/\u00A0/g, ' ').replace(/\s+/g, ' ').trim();
                            if (val && val !== '-' && uniqueVals.indexOf(val) === -1) {
                                uniqueVals.push(val); 
                            }
                        });
                        uniqueVals.sort(); 
                        
                        $.each(uniqueVals, function(i, val) { 
                            select.append('<option value="' + val + '">' + val + '</option>'); 
                        });
                        
                        // Восстанавливаем значение если было сохранено
                        if (activeFilters.selects[colIdx]) {
                            select.val(activeFilters.selects[colIdx]);
                        }
                        
                        select.on('change', function () { 
                            const val = $(this).val();
                            if (val) {
                                activeFilters.selects[colIdx] = val;
                            } else {
                                delete activeFilters.selects[colIdx];
                            }
                            table.draw();
                        });
                    } 
                    else if (title.includes('дата')) {
                        const $input = $('<input type="text" class="date-range-filter" placeholder="Даты..." readonly="readonly" />');
                        cell.html($input);
                        
                        const fp = flatpickr($input[0], { 
                            mode: "range", dateFormat: "d.m.Y", locale: "ru", 
                            onChange: function(selectedDates) { 
                                if (selectedDates.length > 0) {
                                    const minD = selectedDates[0].setHours(0,0,0,0);
                                    if (selectedDates.length === 1) {
                                        activeFilters.dates[colIdx] = { active: true, exact: true, min: minD };
                                    } else if (selectedDates.length === 2) {
                                        activeFilters.dates[colIdx] = { 
                                            active: true, 
                                            exact: false, 
                                            min: minD, 
                                            max: selectedDates[1].setHours(0,0,0,0) 
                                        };
                                    }
                                } else { 
                                    delete activeFilters.dates[colIdx];
                                }
                                table.draw(); 
                            }
                        });
                        
                        // Восстанавливаем дату если была сохранена
                        if (activeFilters.dates[colIdx] && activeFilters.dates[colIdx].active) {
                            const df = activeFilters.dates[colIdx];
                            if (df.exact) {
                                fp.setDate(new Date(df.min));
                            } else {
                                fp.setDate([new Date(df.min), new Date(df.max)]);
                            }
                        }
                    } else {
                        cell.html('<input type="text" placeholder="Поиск..." />');
                        $('input', cell).on('keyup change', function () { 
                            api.column(colIdx).search(this.value).draw();
                        });
                    }
                });
                
                setTimeout(function() { 
                    $('#table-loader').hide(); 
                    $('#table-wrapper').addClass('visible'); 
                }, 50);
            }
        });

        $('#customGlobalSearch').on('keyup change', function() { 
            table.search(this.value).draw(); 
        });
        
        // Восстанавливаем глобальный поиск
        if (wasRestored) {
            const savedSearch = sessionStorage.getItem('crmSearchValue');
            if (savedSearch) {
                $('#customGlobalSearch').val(savedSearch);
                table.search(savedSearch);
                sessionStorage.removeItem('crmSearchValue');
            }
        }
        
        $('#customClearBtn').on('click', function() {
            activeFilters = { ranges: {}, dates: {}, selects: {} };
            table.search(''); 
            $('#customGlobalSearch').val(''); 
            $('.filters input:not(.date-range-filter), .filters select').val(''); 
            $('.date-range-filter').each(function() { 
                if(this._flatpickr) this._flatpickr.clear(); 
            });
            table.columns().search('').draw();
        });
        
        tableElement.wrap('<div class="custom-table-scroll"></div>');
    } else {
        $('#table-loader').hide(); 
        $('#table-wrapper').addClass('visible');
    }
});