import re
import sys

from MyDict import MyDict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# pyinstaller -n SegmentTranslator --add-data "sqldict.db;." --add-data "MyDict.py;." -F -w .\SegmentTranslator.py

FORM_NAMES = {
    "p": "过去式",
    "d": "过去分词",
    "i": "现在分词",
    "3": "三单",
    "r": "比较级",
    "t": "最高级",
    "s": "复数",
    "0": "原型",
    "1": "变体",
}

UNCHECKED_SYMBOL = "☐"  # 未勾选符号
CHECKED_SYMBOL = "☑"  # 已勾选符号


STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #fdf6e3;
    font-family: '微软雅黑';
    font-size: 11pt;
}
QTextEdit, QTreeWidget {
    background-color: #1d1d1d;
    border: 1px solid #646464;
    font-size: 12pt;
}
QTreeWidget::item {
    border: 1px solid #646464;
}
QPushButton {
    background-color: #365880;
    border: 1px solid #4b6eaf;
    padding: 5px;
}
QPushButton:hover {
    background-color: #4b6eaf;
}
QHeaderView::section {
    background-color: #353739;
    color: #fdf6e3;
    padding: 4px;
    border: 1px solid #646464;
}
"""


class SegmentTranslator(QMainWindow):
    def __init__(self, dict: MyDict):
        super().__init__()
        self.setWindowTitle("分词翻译")
        self.setGeometry(280, 200, 1200, 800)
        self.setStyleSheet(STYLE)
        self.create_widgets()

        self.sql_dict = dict
        self.ignored_words = set()

    def create_widgets(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)  # 设置主窗口的中央部件
        layout = QVBoxLayout(main_widget)  # 设置为中央部件的布局为垂直布局

        # 创建输入框
        self.input_field = QTextEdit()
        self.input_field.setFixedHeight(200)  # 设置输入框的高度
        self.input_field.setAcceptRichText(False)  # 禁用富文本
        layout.addWidget(self.input_field)  # 将输入框添加到布局中

        # 创建按钮框架
        button_layout = QHBoxLayout()  # 创建一个水平布局管理器
        button_layout.addStretch(1)  # 弹性空间布局, 使按钮居中

        self.search_button = QPushButton("查询")  # 创建查询按钮
        self.search_button.setFixedSize(160, 30)  # 设置按钮大小
        self.search_button.clicked.connect(self.search_words)  # 将按钮的点击事件连接到search_words方法
        button_layout.addWidget(self.search_button)  # 将查询按钮添加到布局中

        self.show_ignored_words_checkbox = QCheckBox("显示忽略的单词")  # 创建一个复选框，文本为"显示忽略的单词"
        self.show_ignored_words_checkbox.stateChanged.connect(lambda: self.search_words())  # 将复选框的选中状态绑定事件
        button_layout.addWidget(self.show_ignored_words_checkbox)  # 将复选框添加到布局中
        button_layout.addStretch(1)  # 弹性空间布局, 使复选框居中
        layout.addLayout(button_layout)  # 将按钮布局添加到布局中

        # 创建翻译结果表格
        self.translation_table = CustomTreeWidget(self)  # 创建表格
        layout.addWidget(self.translation_table)

        # 创建未知单词显示框
        self.unknown_words_display = QTextEdit()
        self.unknown_words_display.setFixedHeight(80)
        self.unknown_words_display.setVisible(False)
        layout.addWidget(self.unknown_words_display)

    def tokenize_and_deduplicate(self, sentence):
        # 匹配一个或多个字母,数字,下划线,连字符的组合, 后面可接一个's(全角/半角)或'(全角/半角)
        words = re.findall(r"\b[\w-]+(?:'s?|’s?)?(?=\s|\b)", sentence)
        processed_words = []
        for word in words:
            # 去掉's(全角/半角)或'(全角/半角)
            word = re.sub(r"'s?$|’s?$", "", word)
            if "_" in word or "-" in word:
                # 如果单词包含下划线或连字符，则分割
                processed_words.extend(re.split(r"[_-]", word))
            elif re.search(r"[A-Z]", word):
                # 如果单词包含大写字母，则分割成多个单词
                processed_words.extend(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", word))
            else:
                processed_words.append(word)
        # 返回去重后的单词列表
        return list(dict.fromkeys(word.lower() for word in processed_words))

    def search_words(self):
        # 获取输入框中的文本
        sentence = self.input_field.toPlainText().strip()
        # 对输入的文本进行分词和去重
        words = self.tokenize_and_deduplicate(sentence)
        # 清除旧的翻译结果
        self.translation_table.clear()
        self.unknown_words_display.clear()
        self.unknown_words_display.setVisible(False)

        unknown_words = []
        for word in words:
            show_ignore_words = self.show_ignored_words_checkbox.isChecked()
            if show_ignore_words or word not in self.ignored_words:
                word_info = self.sql_dict.query_word(word)
                if word_info:
                    # 如果找到单词信息，添加到表格中
                    self.add_word_to_table(word_info)
                else:
                    # 如果没有找到单词信息，添加到未知单词列表
                    unknown_words.append(word)

        if unknown_words:
            # 如果有未知单词，显示它们
            self.unknown_words_display.setText("未知单词: " + ", ".join(unknown_words))
            self.unknown_words_display.setVisible(True)

    def add_word_to_table(self, word_info):
        item = QTreeWidgetItem(self.translation_table)
        item.setText(0, word_info["word"])
        item.setText(1, word_info["phonetic"])
        item.setText(2, word_info["translation"].replace("\\n", "\n").replace("\\r", ""))

        # 处理变形列
        exchange_parts = word_info["exchange"].split("/")
        formatted_exchange = []
        for part in exchange_parts:
            if ":" not in part:
                formatted_exchange.append(part)
                continue
            form, value = part.split(":", 1)
            form = form.strip()
            value = value.strip()
            form = FORM_NAMES.get(form, form)
            value = ";".join([FORM_NAMES.get(f, f) for f in list(value)]) if form == "变体" else value
            formatted_exchange.append(f"{form}:{value}")

        item.setText(3, "\n".join(formatted_exchange))
        item.setText(4, CHECKED_SYMBOL if word_info["word"].lower() in self.ignored_words else UNCHECKED_SYMBOL)
        self.translation_table.addTopLevelItem(item)


class CustomTreeWidget(QTreeWidget):
    def __init__(self, segment_translator: SegmentTranslator):
        super().__init__()
        self.segment_translator = segment_translator
        self.setAlternatingRowColors(False)
        self.setHeaderLabels(["单词", "音标", "翻译", "变形", "忽略"])  # 设置表头
        self.setColumnWidth(0, 160)  # 设置列宽
        self.setColumnWidth(1, 160)
        self.setColumnWidth(2, 600)
        self.setColumnWidth(3, 200)
        self.setColumnWidth(4, 30)
        self.setIndentation(0)  # 设置不缩进
        # 绑定点击"忽略"按钮的事件
        self.itemClicked.connect(lambda item, column: self.toggle_ignore_word(item) if column == 4 else None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            item = self.currentItem()
            if item:
                self.toggle_ignore_word(item)
        else:
            super().keyPressEvent(event)

    def toggle_ignore_word(self, item):
        word = item.text(0).lower()
        current_status = item.text(4)
        if current_status == UNCHECKED_SYMBOL:
            self.segment_translator.ignored_words.add(word)
            new_status = CHECKED_SYMBOL
        else:
            self.segment_translator.ignored_words.discard(word)
            new_status = UNCHECKED_SYMBOL
        item.setText(4, new_status)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    dictionary_app = SegmentTranslator(MyDict("sqldict.db"))
    dictionary_app.show()
    sys.exit(app.exec())
