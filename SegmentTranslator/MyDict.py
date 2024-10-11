"""
SqlDict类, 有以下几个方法
1. 建数据库和表
2. 导入csv文件
3. 输入单词(word), 查询单词数据

csv数据来源: https://github.com/skywind3000/ECDICT

数据库字段
| 字段         | 解释                          |
| ------------ | ----------------------------- |
| word         | 单词名称                      |
| phonetic     | 音标                          |
| translation  | 中文释义                      |
| exchange     | 时态复数等变换, 使用 "/" 分割 |
| definition   | 英文释意                      |
| word_ignored | 是否忽略                      |

`exchange` 字段说明:
格式如下: "类型1:变换单词1/类型2:变换单词2", 比如good的exchange是"s:goods/0:good/1:s", 具体类型含义如下:
| 类型 | 说明                                                       |
| ---- | ---------------------------------------------------------- |
| p    | 过去式(did)                                                |
| d    | 过去分词(done)                                             |
| i    | 现在分词(doing)                                            |
| 3    | 第三人称单数(does)                                         |
| r    | 形容词比较级(-er)                                          |
| t    | 形容词最高级(-est)                                         |
| s    | 名词复数形式                                               |
| 0    | Lemma, 如 apples 的 Lemma 是 apple                         |
| 1    | Lemma 的变换形式, 比如 s 代表 apples 是其 lemma 的复数形式 |
"""

import csv
import sqlite3


class MyDict:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_table(self):
        self.connect()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS "sqldict" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
            "word" VARCHAR(64) COLLATE NOCASE NOT NULL UNIQUE,
            "phonetic" VARCHAR(64),
            "translation" TEXT,
            "exchange" TEXT,
            "definition" TEXT,
            "word_ignored" BOOLEAN DEFAULT FALSE
        );
        """)
        self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS "sqldict_1" ON sqldict (id);')
        self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS "sqldict_2" ON sqldict (word);')
        self.conn.commit()
        self.close()

    def import_csv(self, csv_file):
        self.connect()
        with open(csv_file, encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                self.cursor.execute(
                    """
                INSERT OR REPLACE INTO sqldict (word, phonetic, translation, exchange, definition)
                VALUES (?, ?, ?, ?, ?)
                """,
                    (row["word"], row["phonetic"], row["translation"], row["exchange"], row["definition"]),
                )
        self.conn.commit()
        self.close()

    def query_word(self, word):
        self.connect()
        self.cursor.execute("SELECT * FROM sqldict WHERE word = ?", (word,))
        result = self.cursor.fetchone()
        self.close()
        if result:
            return {
                "id": result[0],
                "word": result[1],
                "phonetic": result[2],
                "translation": result[3],
                "exchange": result[4],
                "definition": result[5],
                "word_ignored": result[6],
            }
        return None

    def update_ignore_status(self, word_id, word_ignored):
        self.connect()
        self.cursor.execute("UPDATE sqldict SET word_ignored = ? WHERE id = ?", (word_ignored, word_id))
        self.conn.commit()
        self.close()


def _transfer_csv(input_file, output_file, columns_to_keep):
    with open(input_file, encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            new_row = [row[i] for i in columns_to_keep]
            writer.writerow(new_row)


if __name__ == "__main__":
    # _transfer_csv("stardict.csv", "data.csv", [0, 1, 3, 10, 2])  # 修改源文件格式
    sql_dict = MyDict("sqldict.db")  # 打开数据库
    # sql_dict.create_table()  # 创建表
    # sql_dict.import_csv("data.csv")  # 导入数据
    # 查数据
    word_info = sql_dict.query_word("were")
    if word_info:
        print(f"单词: {word_info['word']}")
        print(f"音标: {word_info['phonetic']}")
        print("中文释义:")
        for line in word_info["translation"].split("\\n"):
            print(f"  {line}")
        print(f"变换: {word_info['exchange']}")
        print("英文释义:")
        for line in word_info["definition"].split("\\n"):
            print(f"  {line}")
        print(f"是否忽略: {bool(word_info['word_ignored'])}")
    else:
        print("未找到该单词")
