document.addEventListener('DOMContentLoaded', () => {
    // 首页表单提交
    if (window.location.pathname === '/test') {
        loadNextQuestion();
    }

    const configForm = document.getElementById('testConfig');
    if (configForm) {
        configForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const testSize = document.getElementById('testSize').value;

            try {
                const response = await fetch('/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `test_size=${testSize}`
                });

                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    window.location.href = data.redirect;
                }
            } catch (error) {
                console.error('请求失败:', error);
            }
        });
    }
});

let selectedOption = null;

// 修改选项点击处理逻辑
function handleOptionClick(optionElem, index) {
    // 移除所有激活状态
    document.querySelectorAll('.option-item').forEach(item => {
        item.classList.remove('active');
    });

    // 添加当前激活状态
    optionElem.classList.add('active');

    // 显示确认按钮
    document.querySelector('.nav-btn').disabled = false;
    selectedOption = index;
}

// 在动态创建选项时绑定事件
data.options.forEach((option, index) => {
    const optionElem = document.createElement('div');
    optionElem.className = 'option-item';
    optionElem.innerHTML = `...`;

    // 绑定点击事件（新增）
    optionElem.addEventListener('click', () => {
        handleOptionClick(optionElem, index);
    });
});

async function handleNext() {

    const status = await (await fetch('/session_status')).json();

    console.log('[DEBUG] 提交前状态:', {
        "当前题号": status.current_index + 1,
        "正确答案位置": status.correct_idx + 1,
        "用户选择位置": selectedOption + 1
    });

    if (!selectedOption && document.querySelector('.option-item.active')) {
        const choice = document.querySelector('.option-item.active').dataset.index;

        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ choice })
            });

            const result = await response.json();
            loadNextQuestion();
        } catch (error) {
            console.error('提交答案失败:', error);
        }
    } else {
        loadNextQuestion();
    }
}

async function loadNextQuestion() {
    try {
        const response = await fetch('/next');
        const data = await response.json();

        if (data.redirect) {
            window.location.href = data.redirect;
            return;
        }

        updateProgress(data.current_question+1, data.total_questions);

        // 更新界面
        document.getElementById('currentWord').textContent = data.word;
        document.getElementById('exampleText').textContent = data.example || '暂无例句';

        const optionsContainer = document.getElementById('options');
        optionsContainer.innerHTML = '';

        data.options.forEach((option, index) => {
            const optionElem = document.createElement('div');
            optionElem.className = 'option-item';
            optionElem.innerHTML = `
                <span class="option-letter">${String.fromCharCode(65 + index)}</span>
                <span class="option-text">${option}</span>
            `;
            optionElem.dataset.index = index;

            optionElem.addEventListener('click', () => {
                document.querySelectorAll('.option-item').forEach(item => {
                    item.classList.remove('active');
                });
                optionElem.classList.add('active');
                selectedOption = index;
            });

            optionsContainer.appendChild(optionElem);
        });
    } catch (error) {
        console.error('加载题目失败:', error);
    }
}

function createOptionElement(option, index) {
    const optionElem = document.createElement('div');
    optionElem.className = 'option-item';
    optionElem.innerHTML = `
        <div class="option-index">${index + 1}</div>
        <div class="option-content">${option}</div>
    `;

    optionElem.addEventListener('click', () => {
        // 清除其他选项状态
        document.querySelectorAll('.option-item').forEach(item => {
            item.classList.remove('active');
        });
        // 设置当前选中状态
        optionElem.classList.add('active');
        selectedOption = index;
    });

    return optionElem;
}

function updateProgress(current, total) {
    // 文本进度
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = `${current}/${total}`;
    }

    // 进度条动画
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        const percent = (current / total) * 100;
        progressBar.style.width = `${percent}%`;
    }
}