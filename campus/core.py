"""AGPL-3.0. Deterministic terminology layer; no text is stored or logged."""
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

DATA = Path(__file__).with_name('terms.json')

def terms():
    return json.loads(DATA.read_text(encoding='utf-8'))

def translate(text, source, target, engine, preserve=(), glossary=True):
    if (source, target) not in [('zh', 'ru'), ('ru', 'zh')]:
        raise ValueError('仅支持中文与俄语互译')
    if not isinstance(text, str) or not text.strip() or len(text) > 5000:
        raise ValueError('请输入 1–5000 字符')
    if not isinstance(preserve, list) and preserve != ():
        raise ValueError('保留词必须是列表')
    if len(preserve) > 30 or any(not isinstance(x, str) or len(x)>100 for x in preserve):
        raise ValueError('最多 30 个保留词，每个不超过 100 字符')
    mapping = {}
    if glossary:
        mapping = {t[source]: (t[target], t['id']) for t in terms()}
    for value in preserve:
        if value.strip():
            mapping[value] = (value, 'protected')
    # Course identifiers are preserved exactly, rather than guessed or transliterated.
    for value in re.findall(r'\b[A-Z]{2,8}[- ]?\d{2,6}\b', text):
        mapping[value] = (value, 'course-code')
    keys = sorted(mapping, key=len, reverse=True)
    patterns = []
    for key in keys:
        escaped = re.escape(key)
        if re.match(r'[A-Za-zА-Яа-яЁё]', key):
            escaped = r'(?<!\w)' + escaped
        if re.search(r'[A-Za-zА-Яа-яЁё0-9]$', key):
            escaped += r'(?!\w)'
        patterns.append(escaped)
    matches = list(re.finditer('|'.join(patterns), text)) if patterns else []
    out, hits, pos = [], [], 0
    def segment(value):
        if not value.strip() or not re.search(r'[A-Za-zА-Яа-яЁё\u4e00-\u9fff]', value):
            return value
        leading = value[:len(value)-len(value.lstrip())]
        trailing = value[len(value.rstrip()):]
        return leading + engine(value.strip(), source, target) + trailing
    for match in matches:
        out.append(segment(text[pos:match.start()]))
        replacement, term_id = mapping[match.group()]
        out.append(replacement)
        hits.append({'source': match.group(), 'target': replacement, 'id': term_id})
        pos = match.end()
    out.append(segment(text[pos:]))
    return {'sourceText': text, 'translatedText': ''.join(out), 'hits': hits,
            'warnings': ['术语采用分段锁定，可能影响俄语变格和句子衔接；正式发布前请人工复核。',
                         '内置术语是项目种子示例，尚未经学校或俄语教师审定。']}

class LibreEngine:
    def __init__(self, base='http://127.0.0.1:5000', api_key=''):
        self.base, self.api_key = base.rstrip('/'), api_key

    def request(self, path, payload=None, timeout=25):
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(self.base + path, body, {'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise RuntimeError('本地翻译引擎不可用，请启动 LibreTranslate 并安装中俄语言模型。') from exc

    def __call__(self, text, source, target):
        payload = {'q': text, 'source': source, 'target': target, 'format': 'text'}
        if self.api_key:
            payload['api_key'] = self.api_key
        result = self.request('/translate', payload)
        if not isinstance(result, dict) or not isinstance(result.get('translatedText'), str):
            raise RuntimeError('翻译引擎返回的数据无效')
        return result['translatedText']

def render_template(kind, fields):
    required = {'notice': ['course_zh', 'course_ru', 'date', 'time', 'room'],
                'email': ['teacher_zh', 'teacher_ru', 'course_zh', 'course_ru', 'date'],
                'title': ['course_zh', 'course_ru', 'topic_zh', 'topic_ru']}
    if kind not in required or not isinstance(fields, dict):
        raise ValueError('模板类型或字段无效')
    for key in required[kind]:
        if not isinstance(fields.get(key), str) or not fields[key].strip() or len(fields[key]) > 150:
            raise ValueError('请填写所有模板字段，单项不超过 150 字符')
    f = fields
    if kind == 'notice':
        zh = f"课程通知\n《{f['course_zh']}》课程将于 {f['date']} {f['time']} 在 {f['room']} 上课。请同学们准时参加。"
        ru = f"Объявление\nЗанятие по дисциплине «{f['course_ru']}» состоится {f['date']} в {f['time']}, аудитория {f['room']}. Просим студентов прийти вовремя."
    elif kind == 'email':
        zh = f"主题：《{f['course_zh']}》课程答疑预约\n{f['teacher_zh']}老师，您好！\n我希望于 {f['date']} 就《{f['course_zh']}》课程的问题向您请教。请问您何时方便？谢谢！"
        ru = f"Тема: Консультация по дисциплине «{f['course_ru']}»\nЗдравствуйте, {f['teacher_ru']}!\nМожно ли записаться на консультацию по дисциплине «{f['course_ru']}» на {f['date']}? Подскажите, пожалуйста, в какое время Вам будет удобно. Спасибо!"
    else:
        zh, ru = f"{f['course_zh']}\n{f['topic_zh']}", f"{f['course_ru']}\n{f['topic_ru']}"
    return {'sourceText': zh, 'translatedText': ru, 'hits': [], 'warnings': ['模板中的课程、姓名和主题需自行提供中俄写法；本结果为模板生成，非机器翻译。']}
