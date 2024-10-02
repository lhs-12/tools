import os
import random


def read_names():
    # :%s/\[//g | %s/\]//g | %s/", "/\r/g | %s/"//g
    # return ["小明", "小红", "小刚", "小李", "小王", "小张", "小赵", "小孙", "小周"]
    file_path = "lottery.txt"
    if not os.path.exists(file_path):
        return []
    with open(file_path, encoding="utf-8") as file:
        names = file.readlines()
    return [name.strip() for name in names]


def draw_lottery(names, num_winners):
    return random.sample(names, num_winners)


def main():
    # 输入奖项数量
    first_prize_count = int(input("请输入一等奖的数量: "))
    second_prize_count = int(input("请输入二等奖的数量: "))
    third_prize_count = int(input("请输入三等奖的数量: "))

    # 读取抽奖名单
    names = read_names()
    if len(names) < first_prize_count + second_prize_count + third_prize_count:
        print("名单中的人数为: ", len(names), ", 不足以抽取所有奖项!")
        return

    # 抽奖
    first_prize_winners = draw_lottery(names, first_prize_count)
    remaining_names = [name for name in names if name not in first_prize_winners]
    second_prize_winners = draw_lottery(remaining_names, second_prize_count)
    remaining_names = [name for name in remaining_names if name not in second_prize_winners]
    third_prize_winners = draw_lottery(remaining_names, third_prize_count)

    # 打印中奖名单
    print("===============")
    print("一等奖中奖名单:")
    for winner in first_prize_winners:
        print(winner)
    print("===============")
    print("二等奖中奖名单:")
    for winner in second_prize_winners:
        print(winner)
    print("===============")
    print("三等奖中奖名单:")
    for winner in third_prize_winners:
        print(winner)
    print("===============")


if __name__ == "__main__":
    main()
