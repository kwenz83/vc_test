from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random
import re
import os
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_123'


# 初始化词典数据
def init_dictionary():
    try:
        conn = sqlite3.connect('stardict.db')
        cur = conn.cursor()

        # 加载单词翻译映射
        cur.execute("SELECT LOWER(word), translation FROM stardict")
        word_translations = {row[0]: row[1] for row in cur.fetchall()}

        # 加载所有翻译选项
        cur.execute("SELECT translation FROM stardict WHERE translation IS NOT NULL")
        all_translations = [row[0] for row in cur.fetchall()]

        conn.close()
        return word_translations, all_translations
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        return {}, []


# 预加载词典数据
word_translations, all_translations = init_dictionary()


def load_test_words():
    """从testword.txt加载测试单词"""
    try:
        with open('testword.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("测试单词文件testword.txt未找到")
        return []


@app.route('/')
def home():
    session.clear()
    word_list = load_test_words()
    return render_template('index.html',word_count=len(word_list))


@app.route('/start', methods=['POST'])
def start_test():
    # 加载测试单词
    word_list = load_test_words()
    if not word_list:
        return jsonify({'error': '测试单词文件未找到或内容为空'})

    # 初始化测试参数
    test_size = min(int(request.form.get('test_size', 10)), len(word_list))
    session.update({
        'words': random.sample(word_list, test_size),
        'total': test_size,
        'current': 0,
        'correct': 0,
        'wrong': []
    })
    return jsonify({'redirect': '/test'})


@app.route('/test')
def test_interface():
    return render_template('test.html')


@app.route('/next')
def get_next_question():
    if session['current'] >= session['total']:
        return jsonify({'redirect': '/results'})

    current_word = session['words'][session['current']]

    # 获取正确翻译
    correct_trans = get_translation(current_word)

    # 生成选项
    options = [correct_trans]
    while len(options) < 4:
        rand_trans = random.choice(all_translations)
        if rand_trans not in options:
            options.append(rand_trans)
    random.shuffle(options)

    # 保存正确索引
    session['correct_idx'] = options.index(correct_trans)

    # 获取例句
    example = fetch_example(current_word)

    response = {
        'word': current_word,
        'example': example,
        'options': options,
        'current_question': session['current'],
        'total_questions': session['total'],
        'progress': f"{session['current'] + 1}/{session['total']}"
    }

    session['current'] += 1
    return jsonify(response)


@app.route('/submit', methods=['POST'])
def check_answer():
    user_choice = int(request.json.get('choice'))
    current_index = session['current'] + 1
    is_correct = (user_choice == session['correct_idx'])

    if is_correct:
        session['correct'] += 1
    else:
        wrong_data = {
            'word': session['words'][current_index],  # 使用修正后的索引
            'correct': session['correct_idx'],
            'user_choice': user_choice
        }
        session['wrong'].append(wrong_data)

    return jsonify({'correct': is_correct})


@app.route('/results')
def show_results():
    # 新增验证逻辑
    total = session.get('total', 0)
    correct = session.get('correct', 0)

    if total == 0:
        return redirect(url_for('home'))

    accuracy = (correct / total) * 100
    return render_template('results.html',
                           accuracy=f"{accuracy:.1f}%",
                           correct=correct,
                           total=total,
                           wrong_list=session.get('wrong', []))


# 工具函数
def get_translation(word):
    translation = word_translations.get(word.lower(), "未找到翻译")
    return format_translation(translation)


def format_translation(text):
    if not text:
        return "无可用翻译"
    return text.split('\n')[0][:150].strip() + '...'


def fetch_example(word):
    try:
        url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, 'html.parser')

        for div in soup.find_all('div', {'class': 'examp'}):
            example = div.get_text(strip=True)
            clean_example = re.sub(r'[\u4e00-\u9fff]', '', example)  # 去中文
            clean_example = re.sub(r'\s+', ' ', clean_example).strip()
            if len(clean_example) > 10:
                return clean_example
        return "暂无可用例句"
    except Exception as e:
        print(f"例句获取失败: {str(e)}")
        return "例句获取失败"


@app.route('/session_status')
def show_session_status():
    return jsonify({
        'current_index': session.get('current', 0) - 1,
        'correct_idx': session.get('correct_idx', 0),
        'total_questions': session.get('total', 0),
        'correct_count': session.get('correct', 0),
        'current_word': session.get('words', [])[session.get('current', 0)-1] if session.get('current',0)>0 else None
    })

if __name__ == '__main__':
    app.run(debug=True)