
// jsbuilder/search/search.js
var search = function (queryData, searchType) {
    var queryData = queryData ? queryData : {};
    var query = Object.assign({}, index.getQueryParams(), queryData);
    query.q = query.q == '' ? undefined : query.q;
    // if (query.filter) {
    //     query.filter = query.filter.filter(item => item.name != 'issueYear');
    // }
    $('#searchContainer')
        .empty()
        .render({
            data: query,
            template: [
                {
                    div: {
                        if: function () {
                            return searchType && searchType === 'advance';
                        },
                        then: {
                            div: function (e) {
                                search.advancedRender(e.container);
                            },
                            class: 'type_area'
                        },
                        else: {
                            div: {
                                div: [
                                    {
                                        input: 'q',
                                        value: '[[q]]'
                                    },
                                    {
                                        button: '检索',
                                        class: 'search_btn',
                                        click: function (para) {
                                            query.q = para.new_data.q;
                                            query.pageNo = 1;
                                            query.size = 10;
                                            search(query);
                                        }
                                    },
                                    {
                                        button: '高级检索',
                                        class: 'search_btn_advance',
                                        click: function () {
                                            window.open(index.ctxPath + '/search?searchType=advance');
                                        }
                                    }
                                ],
                                class: 'search_box type_area'
                            },
                            class: 'search_top search_container'
                        },
                    },
                },
                {
                    div: [
                        {
                            div: '',
                            id: 'resultFilter',
                            class: 'result_filter'
                        },
                        {
                            div: [
                                {
                                    div: '',
                                    class: 'filter_condition_container'
                                },
                                {
                                    div: '',
                                    class: 'result_list_container'
                                }
                            ],
                            class: 'result_right'
                        }
                    ],
                    class: 'type_area result_container'
                }
            ]
        });
    if (!searchType) {
        index.loading('.result_list_container');
        search.filter(query);
        search.condition(query);
        search.list(query);
    }
    $(document).click(function (event) {
        var _con = $('.start'); // 设置目标区域
        if (!_con.is(event.target) && _con.has(event.target).length === 0) {
            // Mark 1
            $('.startDate').fadeOut();
        }
        var _conend = $('.end'); // 设置目标区域
        if (!_conend.is(event.target) && _con.has(event.target).length === 0) {
            // Mark 1
            $('.endDate').fadeOut(); //淡出消失
        }
    });
};

// jsbuilder/search/moudles/saerch.filter.js
search.filter = function (query, searchType) {
    var queryData = {
        size: 0,
        profiles: [
            { name: 'year' },
            { name: 'core' },
            { name: 'oaj' },
            { name: 'organization' },
            { name: 'language' },
            { name: 'keyword' },
            { name: 'author' }
            // { name: 'source' },
        ]
    };
    var queryParams = Object.assign({}, query, queryData);
    function loadFilter() {
        wf.http.get(index.ctxPath + '/search/literature', queryParams, function (data) {
            if (data.status === 200) {
                renderFilter(data.result);
            } else {
                dialog.fail('检索接口异常');
                search.empty('.result_list_container');
            }
        });
    }

    function renderFilter(data) {
        $('.result_filter')
            .empty()
            .render({
                data: data.profile.list,
                template: {
                    ul: [
                        {
                            li: '[[title]]',
                            class: 'filter_title',
                            a: {
                                'data-en': function (para) {
                                    if (para.data.title == '年份') {
                                        return 'Years';
                                    } else if (para.data.title == '核心收录') {
                                        return 'Indexed by';
                                    } else if (para.data.title == '刊名') {
                                        return 'Journals';
                                    } else if (para.data.title == '作者单位') {
                                        return 'Affiliations';
                                    } else if (para.data.title == '语种') {
                                        return 'Languages';
                                    } else if (para.data.title == '关键词') {
                                        return 'Keywords';
                                    } else if (para.data.title == '作者') {
                                        return 'Authors';
                                    }
                                },
                                'data-cn': function (para) {
                                    return para.data.title;
                                }
                            }
                        },
                        {
                            li: [
                                {
                                    if: function (data) {
                                        return data.title !== ''
                                    },
                                    then: [
                                        {
                                            input: 'chk_filter',
                                            a: {
                                                type: 'checkbox',
                                                'data-type': '[[../name]]',
                                                'data-title': '[[title]]',
                                                'data-value': '[[value]]'
                                            },
                                            click: function (para) {
                                                if ($('input[name="chk_filter"]').is(':checked')) {
                                                    $('.filter_btn').fadeIn(500);
                                                } else {
                                                    $('.filter_btn').fadeOut(500);
                                                }
                                                translate.execute();
                                            }
                                        },
                                        {
                                            span: '[[title]]',
                                            class: 'filter_list_item_title'
                                        },
                                        {
                                            span: '（[[count]]）'
                                        }
                                    ]
                                }
                            ],
                            class: 'filter_list_item ignore',
                            datapath: 'list'
                        },
                        {
                            li: [
                                {
                                    if: function (para) {
                                        return para.data.list.length > 3;
                                    },
                                    then: {
                                        span: '更多...',
                                        class: 'filter_btn_more',
                                        click: function (para) {
                                            var sender = $(para.sender);
                                            if (sender.text() === '更多...') {
                                                sender.parents('.filter_item').find('.filter_list_item').css('display', 'flex');
                                                sender.text('收起');
                                            } else {
                                                sender.parents('.filter_item').find('.filter_list_item:gt(2)').hide();
                                                sender.text('更多...');
                                            }
                                            translate.execute();
                                        }
                                    },
                                    else: {
                                        span: '',
                                        class: 'filter_btn_more'
                                    }
                                },
                                {
                                    p: [
                                        {
                                            button: '排除',
                                            class: 'filter_btn_filterout',
                                            click: function () {
                                                var allCheck = $('input[name="chk_filter"]:checked');
                                                $.each(allCheck, function (i, ele) {
                                                    data.searchResult.query.filterOut.push({
                                                        name: $(ele).data().type,
                                                        values: $(ele).data().value,
                                                        title: $(ele).data().title
                                                    });
                                                });
                                                data.searchResult.query.size = 10;
                                                data.searchResult.query.pageNo = 1;
                                                if (searchType) {
                                                    index.loading('.result_list_container');
                                                    search.filter(data.searchResult.query, 'advance');
                                                    search.condition(data.searchResult.query, 'advance');
                                                    search.list(data.searchResult.query, 'advance');
                                                } else {
                                                    search(data.searchResult.query);
                                                }
                                            }
                                        },
                                        {
                                            button: '筛选',
                                            class: 'filter_btn_filter',
                                            click: function () {
                                                var allCheck = $('input[name="chk_filter"]:checked');
                                                $.each(allCheck, function (i, ele) {
                                                    data.searchResult.query.filter.push({
                                                        name: $(ele).data().type,
                                                        values: $(ele).data().value,
                                                        title: $(ele).data().title
                                                    });
                                                });
                                                data.searchResult.query.size = 10;
                                                data.searchResult.query.pageNo = 1;
                                                if (searchType) {
                                                    index.loading('.result_list_container');
                                                    search.filter(data.searchResult.query, 'advance');
                                                    search.condition(data.searchResult.query, 'advance');
                                                    search.list(data.searchResult.query, 'advance');
                                                } else {
                                                    search(data.searchResult.query);
                                                }
                                            }
                                        }
                                    ],
                                    class: 'filter_btn'
                                }
                            ],
                            class: 'filter_bottom'
                        }
                    ],
                    class: 'filter_item'
                }
            });
    }
    loadFilter();
};

// jsbuilder/search/moudles/search.advancedRender.js
search.advancedRender = function (container) {
    var query = {};
    $(container).empty().render({
        data: {},
        template: {
            multiview: [
                {
                    div: {
                        e: 'tab',
                        t: [
                            {
                                e: 'tab-nav',
                                t: '高级检索',
                                a: {
                                    view: 'advanced',
                                    class: 'active'
                                }
                            },
                            {
                                e: 'tab-nav',
                                t: '专业检索',
                                a: {
                                    view: 'professional',
                                }
                            }
                        ]
                    },
                    class: 'tab_container'
                },
                {
                    view: [
                        {
                            div: [
                                {
                                    div: [
                                        // 检索信息
                                        {
                                            div: [
                                                {
                                                    div: '检索信息：',
                                                    class: 'advanced_title'
                                                },
                                                {
                                                    div: [
                                                        {
                                                            div: [
                                                                {
                                                                    span: '',
                                                                    class: 'bool_value',
                                                                    style: {
                                                                        border: 'none'
                                                                    }
                                                                },
                                                                {
                                                                    e: 'select',
                                                                    a: {
                                                                        class: 'selectId',
                                                                        name: 'selectId',
                                                                        value: '标题'
                                                                    },
                                                                    t: [
                                                                        {
                                                                            e: 'option',
                                                                            a: {
                                                                                value: '[[val]]'
                                                                            },
                                                                            t: '[[name]]',
                                                                            data: search.mapping.searchFields
                                                                        }
                                                                    ]
                                                                },
                                                                {
                                                                    e: 'input',
                                                                    a: {
                                                                        type: 'text',
                                                                        class: 'textTitle',
                                                                        name: 'textTitle',
                                                                        value: ''
                                                                    }
                                                                },
                                                                {
                                                                    e: 'select',
                                                                    a: {
                                                                        class: 'vague_accurate',
                                                                        name: 'vague_accurate',
                                                                        value: function (e) {
                                                                            var accurate = null;
                                                                            if (accurate == 'accurate') {
                                                                                $(e.container).val('accurate');
                                                                            } else {
                                                                                $(e.container).val('vague');
                                                                            }
                                                                        }
                                                                    },
                                                                    t: [
                                                                        "<option value='vague' selected='selected'>模糊</option>",
                                                                        "<option value='accurate' >精确</option>"
                                                                    ]
                                                                },
                                                                {
                                                                    div: function (params) {
                                                                        renderButton(params);
                                                                    }
                                                                }
                                                            ],
                                                            class: 'info'
                                                        },
                                                        function () {
                                                            renderFilter({}, 'new');
                                                            renderFilter({}, 'new');
                                                        }
                                                    ],
                                                    class: 'search_condition'
                                                }
                                            ],
                                            class: 'search'
                                        },
                                        // 出版年
                                        {
                                            div: function (params) {
                                                renderPubYear(params);
                                            },
                                            class: 'search_time '
                                        },
                                        // 检索
                                        {
                                            div: {
                                                button: '检索',
                                                click: function (p) {
                                                    let info = $('.info');
                                                    let data = '';
                                                    let title = '';
                                                    let startDate = $('.start').val();
                                                    var endDate = $('.end').val();
                                                    var dateRange = '';
                                                    let advanced = new Array();
    
                                                    // 时间;
                                                    if (startDate != '' || endDate != '') {
                                                        if (endDate == '' && startDate !== '') {
                                                            dateRange = startDate + '-' + new Date().getFullYear();
                                                            $('.end').val(new Date().getFullYear());
                                                        } else if (startDate == '' && endDate !== '') {
                                                            dateRange = 1900 + '-' + endDate;
                                                            $('.start').val(1900);
                                                        } else {
                                                            dateRange = startDate + '-' + endDate;
                                                        }
                                                        query.filter = [{name: 'issueYear', values: dateRange}];
                                                    }
                                                    $.each(info, function (index, value) {
                                                        var map = {};
                                                        if ($(value).find('.textTitle').val() != '') {
                                                            let textTitle = $(value).find('.textTitle').val();
                                                            title = textTitle;
                                                            let selectId = $(value).find('.selectId').val();
                                                            let bool_value = $(value).find('.bool_value').val();
                                                            let vague_accurate = $(value).find('.vague_accurate').val();
                                                            map['bool_value'] = bool_value || '';
                                                            map['selectId'] = selectId;
                                                            map['textTitle'] = textTitle;
                                                            map['vague_accurate'] = vague_accurate;
                                                            const isAccurate = map['vague_accurate'] === 'accurate';
                                                            if (bool_value && bool_value !== '') {
                                                                if (isAccurate) {
                                                                    data = data + bool_value + selectId + ':"' + textTitle.trim() + '"';
                                                                } else {
                                                                    data = data + bool_value + selectId + ':' + textTitle.trim();
                                                                }
                                                            } else {
                                                                if (isAccurate) {
                                                                    data = data + selectId + ':"' + textTitle.trim() + '"';
                                                                } else {
                                                                    data = data + selectId + ':' + textTitle.trim();
                                                                }
                                                            }
                                                            advanced.push(map);
                                                        }
                                                    });
                                                    if (title === '') {
                                                        return alert('请输入检索项');
                                                    }
                                                    query.q = data;
                                                    index.loading('.result_list_container');
                                                    search.filter(query, 'advance');
                                                    search.condition(query, 'advance');
                                                    search.list(query, 'advance');
                                                }
                                            },
                                            class: 'search_btn'
                                        }
                                    ],
                                    class: 'advanced_search_main'
                                },
                                {
                                    div: [
                                        {
                                            div: '<strong>温馨提示</strong>'
                                        },
                                        {
                                            div: '1. 高级检索支持选择检索词精确或模糊匹配。'
                                        },
                                        {
                                            div: '2. 运算符含义:'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; AND: 逻辑与, 所有词同时出现在文献中。'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; OR: 逻辑或, 至少一个词出现在文献中。'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; NOT:逻辑非, 后面的词不出现在文献中。'
                                        },
    
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; " ":精确匹配, 引号内容作为整体进行检索。'
                                        },
    
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; (): 限定检索顺序, 括号内容作为一个子查询'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; ?: 通配符, 一个问号代表一个字符。'
                                        },
                                        {
                                            div: '3. 逻辑运算优先级顺序：'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; () > NOT > AND > OR。'
                                        },
                                        {
                                            div: '4. 运算符建议使用英文半角输入形式。'
                                        }
                                    ],
                                    class: 'advanced_search_tip'
                                }
                            ],
                            class: 'advanced_view'
                        }
                    ],
                    id: 'advanced',
                    a: {
                        class: 'active'
                    }
                },
                {
                    view: [
                        {
                            div: [
                                {
                                    div: [
                                        {
                                            div: [
                                                {
                                                    div: [
                                                        {
                                                            div: '字段标识',
                                                            class: 'title_item'
                                                        },
                                                        function (e) {
                                                            var arr = [
                                                                { name: '标题', value: '标题' },
                                                                { name: '作者', value: '作者' },
                                                                { name: '关键词', value: '关键词' },
                                                                { name: '摘要', value: '摘要' },
                                                            ];
                                                            $(e.container).render({
                                                                data: arr,
                                                                template: {
                                                                    e: 'div',
                                                                    class: 'keyword_item',
                                                                    t: '[[name]]',
                                                                    click: function (d) {
                                                                        let textareaEle = document.getElementById('expressionvalue');
                                                                        let start = textareaEle.selectionStart;
                                                                        let end = textareaEle.selectionEnd;
                                                                        let curVal = textareaEle.value;
                                                                        let appendVal = ' ' + d.org_data.value + '=';
                                                                        let operator = ['AND', 'and', 'OR', 'or', 'NOT', 'not'];
                                                                        let preWords = curVal
                                                                            .substring(0, start)
                                                                            .trimEnd()
                                                                            .split(' ')
                                                                            .filter(function (item) {
                                                                                if (item && item != ' ') {
                                                                                    return item;
                                                                                }
                                                                            });
                                                                        if (preWords.length > 0 && !operator.includes(preWords.pop())) {
                                                                            appendVal = ' AND ' + appendVal;
                                                                        }
                                                                        let afterWords = curVal
                                                                            .substring(end)
                                                                            .trimStart()
                                                                            .split(' ')
                                                                            .filter(function (item) {
                                                                                if (item && item != ' ') {
                                                                                    return item;
                                                                                }
                                                                            });
                                                                        let pos = start + appendVal.length;
                                                                        if (afterWords.length > 0 && !operator.includes(afterWords[0])) {
                                                                            appendVal = appendVal + ' AND ';
                                                                        }
                                                                        textareaEle.value =
                                                                            curVal.substring(0, start) + appendVal + curVal.substring(end);
                                                                        textareaEle.focus();
                                                                        textareaEle.setSelectionRange(pos, pos);
                                                                    }
                                                                }
                                                            });
                                                        }
                                                    ],
                                                    class: 'list_wrapper'
                                                },
                                                {
                                                    div: [
                                                        {
                                                            div: '逻辑关系',
                                                            class: 'title_item'
                                                        },
                                                        function (e) {
                                                            var arr = [
                                                                { name: 'AND(与)', value: 'AND' },
                                                                { name: 'OR(或)', value: 'OR' },
                                                                { name: 'NOT(非)', value: 'NOT' }
                                                            ];
                                                            $(e.container).render({
                                                                data: arr,
                                                                template: {
                                                                    e: 'div',
                                                                    class: 'keyword_item',
                                                                    t: '[[name]]',
                                                                    click: function (d) {
                                                                        let textareaEle = document.getElementById('expressionvalue');
                                                                        let start = textareaEle.selectionStart;
                                                                        let end = textareaEle.selectionEnd;
                                                                        let curVal = textareaEle.value;
                                                                        textareaEle.value =
                                                                            curVal.substring(0, start) +
                                                                            ' ' +
                                                                            d.org_data.value +
                                                                            ' ' +
                                                                            curVal.substring(end);
                                                                    }
                                                                }
                                                            });
                                                        }
                                                    ],
                                                    class: 'list_wrapper'
                                                }
                                            ],
                                            class: 'keyword_tips'
                                        },
                                        {
                                            div: [
                                                {
                                                    textarea: 'expressionvalue',
                                                    a: {
                                                        class: 'expressionvalue',
                                                        autocomplete: 'off',
                                                        spellcheck: 'false',
                                                        wrap: 'soft',
                                                        maxlength: '800'
                                                    },
                                                    t: ''
                                                }
                                            ],
                                            class: 'major'
                                        },
                                        // 出版年
                                        {
                                            div: function (params) {
                                                renderPubYear(params);
                                            },
                                            class: 'search_time '
                                        },
                                        // 专业检索
                                        {
                                            div: {
                                                button: '检索',
                                                click: function (p) {
                                                    let startDate = $('.start').val();
                                                    var endDate = $('.end').val();
                                                    var dateRange = '';
                                                    var dataMajor = p.new_data.expressionvalue;
                                                    let data = ''; //最后拼接字符串
                                                    if (dataMajor == '') {
                                                        return alert('请输入检索项');
                                                    } else {
                                                        const regexp = /[AND|and|OR|or|NOT|not]+/g;
                                                        const str = p.new_data.expressionvalue;
                                                        const array = [...str.matchAll(regexp)];
                                                        let data_major_array = new Array();
                                                        data_major_array = dataMajor.split(/[AND|and|OR|or|NOT|not]+/); //出现关键词就分割
    
                                                        data_major_array.forEach(function (item, index) {
                                                            var num = item.indexOf('='); //查找=号第一次出现的位置
                                                            var item_first = item
                                                                .substring(0, num + 1)
                                                                .replace(/\标题=/g, 'title:')
                                                                .replace(/\关键词=/g, 'subject:')
                                                                .replace(/\作者=/g, 'creator:')
                                                                .replace(/\摘要=/g, 'description:')
                                                                .replace(/\作者单位=/g, '作者单位:');
                                                            var item_last = item.slice(num + 1);
                                                            item = item_first + item_last;
    
                                                            if (index != data_major_array.length - 1) {
                                                                data = data + item + array[index][0];
                                                            } else {
                                                                data = data + item;
                                                            }
                                                        });
                                                    }
                                                    // 时间;
                                                    if (startDate != '' || endDate != '') {
                                                        if (endDate == '' && startDate !== '') {
                                                            dateRange = startDate + '-' + new Date().getFullYear();
                                                            $('.end').val(new Date().getFullYear());
                                                        } else if (startDate == '' && endDate !== '') {
                                                            dateRange = 1900 + '-' + endDate;
                                                            $('.start').val(1900);
                                                        } else {
                                                            dateRange = startDate + '-' + endDate;
                                                        }
                                                        query.filter = [{name: 'issueYear', values: dateRange}];
                                                    }
                                                    query.q = data;
                                                    index.loading('.result_list_container');
                                                    search.filter(query, 'advance');
                                                    search.condition(query, 'advance');
                                                    search.list(query, 'advance');
                                                }
                                            },
                                            class: 'search_btn'
                                        }
                                    ],
                                    class: 'advanced_search_main'
                                },
                                {
                                    div: [
                                        {
                                            div: '<strong>温馨提示</strong>'
                                        },
                                        {
                                            div: '1. 选择资源类型后, 可使用对应资源的独有字段检索。'
                                        },
                                        {
                                            div: '2. 运算符含义:'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; AND: 逻辑与, 所有词同时出现在文献中。'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; OR: 逻辑或, 至少一个词出现在文献中。'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; NOT:逻辑非, 后面的词不出现在文献中。'
                                        },
    
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; " ":精确匹配, 引号内容作为整体进行检索。'
                                        },
    
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; (): 限定检索顺序, 括号内容作为一个子查询'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; ?: 通配符, 一个问号代表一个字符。'
                                        },
                                        {
                                            div: '3. 逻辑运算优先级顺序：'
                                        },
                                        {
                                            div: '&nbsp;&nbsp;&nbsp; () > NOT > AND > OR。'
                                        },
                                        {
                                            div: '4. 运算符建议使用英文半角输入形式。'
                                        }
                                    ],
                                    class: 'advanced_search_tip'
                                }
                            ],
                            class: 'professional_view'
                        }
                    ],
                    id: 'professional',
                }
            ]
        }
    })


    // 渲染检索信息
    function renderFilter (data, type) {
        $('.search_condition').render({
            data: data,
            template: {
                e: 'div',
                a: { class: 'info' },
                t: [
                    {
                        e: 'select',
                        a: {
                            class: 'bool_value',
                            name: 'bool_value',
                            value: function (e) {
                                if (type == 'new') {
                                    return '';
                                }
    
                                if (e.data.bool_value) {
                                    $(e.container).val(e.data.bool_value);
                                    return e.data.bool_value;
                                } else {
                                    $(e.container).val(' AND ');
                                    return ' AND ';
                                }
                            }
                        },
                        t: ['<option value=" AND ">与</option>', '<option value=" OR ">或</option>', '<option value=" NOT ">非</option>']
                    },
                    {
                        e: 'select',
                        a: {
                            class: 'selectId',
                            name: 'selectId',
                            value: function (e) {
                                if (e.data.selectId) {
                                    $(e.container).val(e.data.selectId);
                                    return e.data.selectId;
                                } else {
                                    return '标题';
                                }
                            }
                        },
                        t: [
                            {
                                e: 'option',
                                a: {
                                    value: '[[val]]'
                                },
                                t: '[[name]]',
                                data: search.mapping.searchFields
                            }
                        ]
                    },
                    {
                        e: 'input',
                        a: {
                            type: 'text',
                            class: 'textTitle',
                            name: 'textTitle',
                            value: function (e) {
                                if (type == 'new') {
                                    return '';
                                }
                                if (e.data.textTitle) {
                                    return e.data.textTitle;
                                } else {
                                    return '';
                                }
                            }
                        }
                    },
                    {
                        e: 'select',
                        a: { class: 'vague_accurate', name: 'vague_accurate' },
                        t: [
                            "<option value='vague' selected='selected'>模糊</option>",
                            "<option value='accurate'>精确</option>",
                            function (e) {
                                if (type == 'new') {
                                    $(e.container).val('vague');
                                    return 'vague';
                                }
                                var accurate = e.data.vague_accurate;
                                if (accurate == 'accurate') {
                                    $(e.container).val('accurate');
                                } else {
                                    $(e.container).val('vague');
                                }
                            }
                        ]
                    },
                    {
                        div: function (params) {
                            renderButton(params);
                        }
                    }
                ]
            }
        });
    };

    // 每条检索信息后的加减按钮
    function renderButton (data) {
        $(data.container).render({
            template: {
                div: [
                    {
                        span: '',
                        class: 'add_condition fa fa-plus-circle',
                        click: function (p) {
                            let num = $('.info').length;
                            if (num < 5) {
                                renderFilter('new');
                            }
                            if (num == 4) {
                                $('.add_condition').hide();
                            }
                            $('.remove_condition').show();
                        }
                    },
                    {
                        sapn: '',
                        class: 'remove_condition  fa fa-minus-circle',
                        click: function (p) {
                            let num = $('.info').length;
                            if (num > 3) {
                                $('.info').last().remove();
                            }
                            if (num == 4) {
                                $('.remove_condition').hide();
                            }
                            $('.add_condition').show();
                        }
                    }
                ],
                class: 'add_sub_btn'
            }
        });
    }

    // 起始年份渲染
    function renderPubYear(e) {
        $(e.container)
            .empty()
            .render({
                data: e.data,
                template: [
                    {
                        div: '出版年：',
                        class: 'advanced_title'
                    },
                    {
                        div: [
                            {
                                e: 'input',
                                a: {
                                    name: 'start',
                                    class: 'start',
                                    autocomplete: 'off',
                                    value: '',
                                    placeholder: '起始日期'
                                },
                                click: function () {
                                    $('.dateTime .endDate').fadeOut();
                                    if ($('.dateTime .startDate').css('display') == 'none') {
                                        $('.dateTime .startDate').fadeIn();
                                    } else {
                                        $('.dateTime .startDate').fadeOut();
                                    }
                                }
                            },
                            {
                                div: function (p) {
                                    $(p.container).render({
                                        data: index.generateYears(),
                                        template: {
                                            div: '[[.]]',
                                            class: 'year',
                                            click: function (p) {
                                                if ($("[name='end']").val() == '') {
                                                    $('.start').val(p.org_data);
                                                    $('.startDate').fadeOut();
                                                } else {
                                                    if (p.org_data <= Number($("[name='end']").val())) {
                                                        $('.start').val(p.org_data);
                                                        $('.startDate').fadeOut();
                                                    }
                                                }
                                            }
                                        }
                                    });
                                },
                                class: 'startDate'
                            },
                            ' &nbsp;&nbsp;-&nbsp;&nbsp; ',
                            {
                                e: 'input',
                                a: {
                                    name: 'end',
                                    class: 'end',
                                    autocomplete: 'off',
                                    value: '',
                                    placeholder: '结束日期'
                                },
                                click: function () {
                                    $('.dateTime .startDate').fadeOut();
                                    if ($('.dateTime .endDate').css('display') == 'none') {
                                        $('.dateTime .endDate').fadeIn();
                                    } else {
                                        $('.dateTime .endDate').fadeOut();
                                    }
                                }
                            },
                            {
                                div: function (p) {
                                    $(p.container).render({
                                        data: index.generateYears(),
                                        template: {
                                            div: '[[.]]',
                                            class: 'year',
                                            click: function (p) {
                                                if (p.org_data >= Number($("[name='start']").val())) {
                                                    $('.end').val(p.org_data);
                                                    $('.endDate').fadeOut();
                                                }
                                            }
                                        }
                                    });
                                },
                                class: 'endDate'
                            }
                        ],
                        class: 'dateTime'
                    }
                ]
            });
    }

    
};

// jsbuilder/search/moudles/search.condition.js
search.condition = function (data, searchType) {
    if (data.filter && data.filter.length == 1 && data.filter[0].name == 'issueYear' && !(data.filterOut && data.filterOut.length > 0)) {
        $('.filter_condition_container').empty();
    } else if ((data.filter && data.filter.length > 0) || (data.filterOut && data.filterOut.length > 0)) {
        $('.filter_condition_container')
            .empty()
            .render({
                data: data,
                template: {
                    div: [
                        {
                            div: [
                                {
                                    label: '限定条件：'
                                },
                                {
                                    span: [
                                        function (para) {
                                            return para.data.name == 'issueYear' ? '' : search.mapping.filter[para.data.name] + '：' + (para.data.title || para.data.values);
                                        },
                                        {
                                            i: '',
                                            class: 'fa fa-times-circle',
                                            click: function (para) {
                                                data.filter = data.filter.filter((item) => {
                                                    return item.values !== para.org_data.values || item.name !== para.org_data.name;
                                                });
                                                data.pageNo = 1;
                                                data.size = 10;
                                                if (searchType) {
                                                    index.loading('.result_list_container');
                                                    search.filter(data, 'advance');
                                                    search.condition(data, 'advance');
                                                    search.list(data, 'advance');
                                                } else {
                                                    search(data);
                                                }
                                            },
                                            when: function (e) {
                                                return e.data.name == 'issueYear' ? false : true;
                                            }
                                        }
                                    ],
                                    class: 'condition_item',
                                    datapath: 'filter'
                                },
                                {
                                    span: [
                                        function (para) {
                                            return '非 ' + search.mapping.filter[para.data.name] + '：<span class="ignore">' + para.data.values + '</span>';
                                        },
                                        {
                                            i: '',
                                            class: 'fa fa-times-circle',
                                            click: function (para) {
                                                data.filterOut = data.filterOut.filter((item) => {
                                                    return item.values !== para.org_data.values || item.name !== para.org_data.name;
                                                });
                                                data.pageNo = 1;
                                                data.size = 10;
                                                if (searchType) {
                                                    index.loading('.result_list_container');
                                                    search.filter(data, 'advance');
                                                    search.condition(data, 'advance');
                                                    search.list(data, 'advance');
                                                } else {
                                                    search(data);
                                                }
                                            }
                                        }
                                    ],
                                    class: 'condition_item',
                                    datapath: 'filterOut'
                                }
                            ],
                            class: 'condition_contianer'
                        },
                        {
                            button: '重置',
                            class: 'reset_btn',
                            click: function () {
                                data.filter = undefined;
                                data.filterOut = undefined;
                                if (searchType) {
                                    index.loading('.result_list_container');
                                    search.filter(data, 'advance');
                                    search.condition(data, 'advance');
                                    search.list(data, 'advance');
                                } else {
                                    search(data);
                                }
                            }
                        }
                    ]
                }
            });
    }
};

// jsbuilder/search/moudles/search.empty.js
search.empty = function (container) {
    $(container)
        .empty()
        .render({
            data: '',
            template: {
                p: [
                    {
                        img: index.ctxPath + '/images/warning.png'
                    },
                    '没有命中的记录，请重试或修改检索表达式'
                ],
                class: 'empty_tips'
            }
        });
};

// jsbuilder/search/moudles/search.list.js
search.list = function (query, searchType) {
  var queryData = {
    profiles: undefined
  };
  var queryParams = Object.assign({}, query, queryData);
  function loadList() {
    wf.http.get(index.ctxPath + '/search/literature', queryParams, function (data) {
      if (data.status === 200) {
        if (data.result.searchResult.list.length > 0) {
          renderList(data.result.searchResult);
        } else {
          search.empty('.result_list_container');
        }
      } else {
        dialog.fail(data.message || '检索接口异常');
        search.empty('.result_list_container');
      }
    });
  }

  function renderList(data) {
    $('.result_list_container')
      .empty()
      .render({
        data: data,
        template: [
          {
            div: [
              {
                div: function (para) {
                  var arr = [
                    { title: '相关度', value: '' },
                    { title: '发表时间', value: 'issueYear' }
                  ];
                  index.select(para.container, arr, query.sort ? query.sort[0].by : '', 'sortSelect', function (val) {
                    if (val === '') {
                      query.sort = undefined;
                    } else {
                      if ($('.long_arrow').hasClass('fa-sort-amount-down')) {
                        query.sort = [{ by: val, order: 'desc' }];
                      } else {
                        query.sort = [{ by: val, order: 'asc' }];
                      }
                    }
                    if (searchType) {
                      index.loading('.result_list_container');
                      search.filter(query, 'advance');
                      search.condition(query, 'advance');
                      search.list(query, 'advance');
                    } else {
                      search(query);
                    }
                  });
                },
                class: 'sort_item'
              },
              {
                i: '',
                a: {
                  class: function () {
                    if (query.sort) {
                      if (query.sort[0].order === 'asc') {
                        return 'fa fa-sort-amount-up long_arrow';
                      } else {
                        return 'fa fa-sort-amount-down long_arrow';
                      }
                    } else {
                      return 'fa fa-sort-amount-down long_arrow';
                    }
                  }
                },
                click: function (para) {
                  var sortSelect = $('#sortSelect').data().val;
                  var sender = $(para.sender);
                  if (sortSelect !== '') {
                    if (sender.hasClass('fa-sort-amount-down')) {
                      sender.removeClass('fa-sort-amount-down').addClass('fa-sort-amount-up');
                      query.sort = [{ by: sortSelect, order: 'asc' }];
                    } else {
                      sender.removeClass('fa-sort-amount-up').addClass('fa-sort-amount-down');
                      query.sort = [{ by: sortSelect, order: 'desc' }];
                    }
                    if (searchType) {
                      index.loading('.result_list_container');
                      search.filter(query, 'advance');
                      search.condition(query, 'advance');
                      search.list(query, 'advance');
                    } else {
                      search(query);
                    }
                  }
                }
              },
              {
                div: function (para) {
                  var arr = [
                    { title: '每页显示10条', value: 10 },
                    { title: '每页显示20条', value: 20 },
                    { title: '每页显示30条', value: 30 }
                  ];
                  var size;
                  if (query.size && query.size != 0) {
                    size = query.size;
                  } else {
                    size = 10;
                  }
                  index.select(para.container, arr, size, 'sizeSelect', function (val) {
                    query.size = val;
                    if (searchType) {
                      index.loading('.result_list_container');
                      search.filter(query, 'advance');
                      search.condition(query, 'advance');
                      search.list(query, 'advance');
                    } else {
                      search(query);
                    }
                  });
                },
                class: 'sort_item sort_size'
              },
              {
                div: [
                  '<span class="en_hide">共找到</span>',
                  {
                    strong: ' [[total]] '
                  },
                  '条结果'
                ],
                class: 'total_count'
              }
            ],
            class: 'filter_sort_container'
          },
          {
            ul: {
              li: [
                {
                  span: [
                    {
                      e: 'a',
                      a: {
                        href: index.ctxPath + '/periodicalArticle/[[identifier/id]]',
                        class: 'ignore'
                      },
                      t: '[[title/HL]]'
                    },
                    {
                      e: 'span',
                      class: 'tag_container ignore',
                      t: {
                        e: 'span',
                        a: {
                          class: function (e) {
                            var classStr = '';
                            switch (e.data.name) {
                              case '北大核心':
                                classStr = 'BDHX';
                                break;
                              default:
                                classStr = e.data.name;
                                break;
                            }
                            return classStr;
                          }
                        },
                        t: '[[name]]',
                        datapath: 'metric/cores'
                      }
                    }
                  ],
                  class: 'result_title'
                },
                {
                  div: [
                    {
                      div: [
                        {
                          div: [
                            {
                              label: '作者：'
                            },
                            {
                              span: {
                                e: 'a',
                                a: {
                                  href: '/search?q=作者："[[name]]"'
                                },
                                t: '[[nameHL]]'
                              },
                              class: 'mul_item ignore',
                              datapath: 'creators'
                            }
                          ],
                          class: 'result_creator'
                        },
                        {
                          div: [
                            {
                              span: {
                                e: 'a',
                                a: {
                                  href: function (e) {
                                    return `/search?q=刊名："${e.data.publication.name.zh || e.data.publication.name.en}"`;
                                  }
                                },
                                t: '《[[publication/name/HL]]》 [[publication/year]]年[[publication/issue]]期'
                              },
                              class: 'mul_item en_hide ignore'
                            },
                            {
                              span: {
                                e: 'a',
                                a: {
                                  href: function (e) {
                                    return `/search?q=刊名："${e.data.publication.name.zh || e.data.publication.name.en}"`;
                                  }
                                },
                                t: '<span class="ignore">《[[publication/name/HL]]》</span> Issue [[publication/issue]],[[publication/year]]</span>'
                              },
                              class: 'mul_item en_show'
                            }
                          ],
                          class: 'result_item publication_name_container'
                        }
                      ],
                      class: 'result_item result_creator_time'
                    },
                    {
                      div: [
                        {
                          label: '关键词：'
                        },
                        {
                          span: {
                            e: 'a',
                            a: {
                              href: '/search?q=关键词："[[name]]"'
                            },
                            t: '[[nameHL]]'
                          },
                          class: 'mul_item ignore',
                          datapath: 'keyWordsCN'
                        }
                      ],
                      when: function (para) {
                        return para.data.keywords.keyWordsCN.length > 0;
                      },
                      class: 'result_keywords result_item',
                      datapath: 'keywords'
                    },
                    {
                      div: [
                        {
                          font: '摘要：',
                          class: 'label'
                        },
                        {
                          span: '[[abstract/HL]]',
                          class: 'ellipsis_content ignore'
                        },
                        {
                          span: '',
                          class: 'ellipsis_btn'
                        }
                      ],
                      when: function (para) {
                        return para.data.abstract.HL;
                      },
                      class: 'result_item ellipsis'
                    }
                    // {
                    //     div: [
                    //         {
                    //             label: '来源：'
                    //         },
                    //         {
                    //             span: {
                    //                 e: 'a',
                    //                 a: {
                    //                     href: '[[url]]'
                    //                 },
                    //                 t: [
                    //                     {
                    //                         e: 'img',
                    //                         a: {
                    //                             src: '[[logo]]'
                    //                         }
                    //                     },
                    //                     '[[name]]'
                    //                 ]
                    //             },
                    //             class: 'source_item',
                    //             datapath: 'sources'
                    //         }
                    //     ],
                    //     class: 'result_source result_item'
                    // }
                  ]
                }
              ],
              datapath: 'list'
            },
            class: 'result_list'
          },
          {
            div: function (para) {
              var params = {
                container: para.container,
                data: {
                  countNum: para.data.total,
                  page: parseInt(para.data.query.pageNo),
                  pageSize: parseInt(para.data.query.size)
                }
              };
              index.searchPagination(params, function (workCase, pageData) {
                para.data.query.pageNo = pageData.page;
                if (searchType) {
                  index.loading('.result_list_container');
                  search.filter(para.data.query, 'advance');
                  search.condition(para.data.query, 'advance');
                  search.list(para.data.query, 'advance');
                } else {
                  search(para.data.query);
                }
              });
            },
            class: 'page_container'
          }
        ]
      });
    window.journalIndex.init();
  }

  loadList(query);
};

// jsbuilder/search/moudles/search.mapping.js
search.mapping = {
    filter: {
        author: '作者',
        core: '核心收录',
        keyword: '关键词',
        language: '语种',
        oaj: '刊名',
        organization: '作者单位',
        year: '年份',
    },
    searchFields: [
        {
            name: '标题',
            val: 'title'
        },
        {
            name: '作者',
            val: 'creator'
        },
        {
            name: '关键词',
            val: 'subject'
        },
        {
            name: '摘要',
            val: 'description'
        }
    ],
    queryStr: ''
};
