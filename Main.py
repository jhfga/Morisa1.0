import os
import pickle
import random
import time
import tkinter
from tkinter import *
from tkinter import messagebox
from ttkbootstrap import Style
from flask import Flask, request
import requests
import subprocess
import asyncio
import datetime

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

# ======================part1=================================
style = Style(theme='lumen')
window = style.master
window.title('Claude to QQ')
# 添加菜单
menubar = Menu(window)

settings = []  # [certification=456, your name , AI's name,BOt_ID,User-token,language,yourQQ ]这是用来保存用户填写消息的变量


def cleanChatRecord():
    response = messagebox.askquestion("清除记忆",
                                      "这将会清除你们的聊天记录并导致她忘掉这些事情，你确定要这样做吗？\n（前6条聊天记录不会被删除，如果需要删除这些记录请手动删除！）")
    if response == "yes":

        print("Confirmed!")
        with open('memory/Chat_records.txt', 'r+', encoding='utf-8') as f:
            lines = [line.strip() for line in f]
        with open('memory/Chat_records.txt', 'w', encoding='utf-8') as f:
            for i in lines[0:6]:
                f.write(i + '\n')
        txt.insert(tkinter.END, "清除记忆成功\n")


menu1 = Menu(menubar, tearoff=0)
menu1.add_command(label='清除记忆', command=cleanChatRecord)

# 添加语言菜单并创建选项
language_menu = Menu(menubar, tearoff=0)
iv_default = IntVar()
language_menu.add_radiobutton(label='中文', command='', value=1, variable=iv_default)
language_menu.add_radiobutton(label='英语', command='', value=2, variable=iv_default)

menu1.add_cascade(label='回复的语言类型', menu=language_menu)

menubar.add_cascade(label='菜单', menu=menu1)
window.config(menu=menubar)

# 全局变量
start = False  # 用来记录用户是否点击启动
bid = ''  # 用来存储用户填写的Claude ID
yt = ''  # 用来存储用户填写的UserToken
qqNumber = ''  # 用来记录用户填写的QQ号
last_message = ''  # 用来记录用户上次发的消息
commands = []  # 存储指令


def startChatting():
    if txt_botid.get() == '' or txt_usertoken.get() == '':
        txt.insert(tkinter.END, "BotID 和 UserToken 都不能为空!\n")
        return False

    global start
    global bid
    global yt
    global qqNumber

    start = True
    settings[1] = txt_YName.get()
    settings[2] = txt_AIName.get()
    settings[3] = txt_botid.get()
    settings[4] = txt_usertoken.get()
    settings[5] = iv_default.get()
    settings[6] = txt_QQ.get()
    bid = txt_botid.get()
    yt = txt_usertoken.get()
    qqNumber = txt_QQ.get()
    with open('settings', 'wb') as f:  # 用户点击启动后就会存储当前填写的信息到本地文件
        pickle.dump(settings, f)

    window.destroy()
    print('本程序由 bilibili 嗷叫叫 制作,分享给大家研究学习。')


btn_start = Button(window, text='启动', command=startChatting, width=30, height=3)
btn_start.grid(row=0, column=0, pady=5, padx=5)

# 文本框
txt = Text(window, width=40, height=10)
txt.grid(row=1, column=0, pady=20, padx=20)

# 区域一:输入框和标签
frm_input = Frame(window)  # 框架frm_input代表区域一
frm_input.grid(row=0, column=1, pady=20, padx=20)

# UserToken输入框和标签
lbl_usertoken = Label(frm_input, text='UserToken:')
lbl_usertoken.pack()
txt_usertoken = Entry(frm_input, width=15)
txt_usertoken.pack()

# BotID输入框和标签
lbl_botid = Label(frm_input, text='Claude ID：')
lbl_botid.pack()
txt_botid = Entry(frm_input, width=15)
txt_botid.pack()

# 区域2:输入框和标签
frm_input1 = Frame(window)
frm_input1.grid(row=1, column=1, pady=20, padx=20)

lbl_YName = Label(frm_input1, text='你的名字:')
lbl_YName.pack()
txt_YName = Entry(frm_input1, width=15)
txt_YName.pack()

lbl_AIName = Label(frm_input1, text='她的名字:')
lbl_AIName.pack()
txt_AIName = Entry(frm_input1, width=15)
txt_AIName.pack()

lbl_QQ = Label(frm_input1, text='你的QQ号:')
lbl_QQ.pack()
txt_QQ = Entry(frm_input1, width=15)
txt_QQ.pack()

try:
    with open('settings', 'rb') as f:
        data = pickle.load(f)
    if data[0] == 456:
        settings = data
    else:
        txt.insert(tkinter.END, "配置文件受损，已重置配置文件\n")
        settings = [456, 'Even', 'Ruby', '', '', 1, '']
        with open('settings', 'wb') as f:
            pickle.dump(settings, f)
except FileNotFoundError:
    txt.insert(tkinter.END, "配置文件不存在，已重置配置文件\n")
    settings = [456, 'Even', 'Ruby', '', '', 1, '']
    with open('settings', 'wb') as f:
        pickle.dump(settings, f)

txt_YName.insert(tkinter.END, settings[1])
txt_AIName.insert(tkinter.END, settings[2])
txt_botid.insert(tkinter.END, settings[3])
txt_usertoken.insert(tkinter.END, settings[4])
iv_default.set(settings[5])
txt_QQ.insert(tkinter.END, settings[6])
with open('commands/commands.pk', 'rb') as f:  # 读取基本指令
    commands = pickle.load(f)
# ==============================part2 监听QQ消息部分同时也在这里完成消息的中转=========================
app = Flask(__name__)


@app.route('/', methods=["POST"])
def post_data():
    global last_message
    if request.get_json().get('message_type') == 'private':
        qqNumber1 = request.get_json().get('sender').get('user_id')  # 获取对方的qq号
        message = request.get_json().get('raw_message')  # 获取对方发的消息
        if not last_message == message:
            last_message = message
            if str(qqNumber1) == qqNumber:
                now = datetime.datetime.now()
                writeUserMessage = message
                writeUserMessage = writeUserMessage.split('\n')
                for i2 in writeUserMessage:
                    item = '{User}:' + i2 + " time " + now.strftime("%Y-%m-%d %H:%M:%S") + '\n'
                    with open('memory/Chat_records.txt', 'a', encoding='utf-8') as f1:
                        f1.write(item)

                UM = '{User}:' + message + " time " + now.strftime("%Y-%m-%d %H:%M:%S")
                if int(settings[5]) == 1:
                    UM = commands[2] + UM + commands[4]
                else:
                    UM = commands[3] + UM + commands[4]

                UM = UM.format(AI=settings[2], User=settings[1])

                reply = asyncio.run(sendMessage(BotID=bid, UserToken=yt, Message1=UM))
                writeUserMessage = reply
                writeUserMessage = writeUserMessage.split('\n')
                isFirst = True  # AI回复的消息的第一行是序号所以要特殊处理
                choice = 1
                for i2 in writeUserMessage:
                    if isFirst:
                        try:
                            choice = int(i2)
                            isFirst = False
                            continue
                        except:
                            isFirst = False
                            continue
                    if i2 == '' or i2 == ' ':
                        continue
                    Reply(message=i2, targetQQ=qqNumber)
                    time.sleep(2)
                    item = '{AI}:' + i2 + " time " + now.strftime("%Y-%m-%d %H:%M:%S") + '\n'
                    with open('memory/Chat_records.txt', 'a', encoding='utf-8') as f1:
                        f1.write(item)

                isPicture = [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]  # 就是随机发送表情包，1就是要发，0就是不发
                random.shuffle(isPicture)
                ch = random.randint(0, 10)
                if isPicture[ch] == 1:
                    MyDict = {1: '高兴', 2: '信任', 3: '恐惧', 4: '惊讶', 5: '伤心', 6: '厌恶', 7: '生气',
                              8: '期待'}
                    fileNameList = os.listdir('data/images/' + MyDict[choice])
                    if len(fileNameList) >= 1:
                        choiceImage = random.randint(0, len(fileNameList) - 1)
                        theFile = MyDict[choice] + '/' + fileNameList[choiceImage]
                        Reply(message='[CQ:image,file=' + theFile + ']', targetQQ=qqNumber)

    return '0'


def Reply(message, targetQQ):  # 发信息给你自己的函数
    put = 'http://127.0.0.1:5700/send_private_msg?user_id={0}&message={1}&auto_escape=false'.format(targetQQ, message)
    requests.get(url=put)


# =================================part3 和claude交互的部分====================================
class SlackClient(AsyncWebClient):
    def __init__(self, token, BotID):
        super().__init__(token=token)
        self.LAST_TS = None
        self.CHANNEL_ID = None
        self.CLAUDE_BOT_ID = BotID

    async def open_channel(self):
        response = await self.conversations_open(users=self.CLAUDE_BOT_ID)
        self.CHANNEL_ID = response["channel"]["id"]

    async def chat(self, text):
        if not self.CHANNEL_ID:
            raise Exception("Channel not found.")

        resp = await self.chat_postMessage(channel=self.CHANNEL_ID, text=text)
        self.LAST_TS = resp["ts"]

    async def get_reply(self):
        for _ in range(150):
            try:
                resp = await self.conversations_history(channel=self.CHANNEL_ID, oldest=self.LAST_TS, limit=2)
                msg = [msg["text"] for msg in resp["messages"] if msg["user"] == self.CLAUDE_BOT_ID]
                if msg and not msg[-1].endswith("Typing…_"):
                    return msg[-1]
            except (SlackApiError, KeyError) as e:
                print(f"Get reply error: {e}")

            await asyncio.sleep(2)

        raise Exception("Get replay timeout")


async def sendMessage(BotID, UserToken, Message1):  # 开始聊天后给claude发消息的函数
    client = SlackClient(token=UserToken, BotID=BotID)
    await client.open_channel()
    await client.chat(Message1)
    reply = await client.get_reply()
    return reply


async def sendMessageOne(BotID, UserToken, Message1):  # 这是第一次启动时给claude发信息的函数
    client = SlackClient(token=UserToken, BotID=BotID)
    await client.open_channel()
    await client.chat('/reset')
    await client.chat(Message1)


if __name__ == '__main__':
    window.mainloop()
    if start:
        InitialMessage = commands[0]
        with open('memory/Setting_And_Hobbies.txt', 'r+', encoding='utf-8') as f:
            lines = f.readlines()
        InitialMessage += "\n{AI}'s hobbies and Setting:\n```"
        for i in lines:
            InitialMessage += i
        InitialMessage += "```\n"

        with open('memory/Chat_records.txt', 'r+', encoding='utf-8') as f:
            lines = f.readlines()
        InitialMessage += "\nThe chat records of {AI} and {User}:\n```"
        for i in lines:
            InitialMessage += i
        InitialMessage += "```\n"
        InitialMessage += commands[1]

        InitialMessage = InitialMessage.format(AI=settings[2], User=settings[1])
        idOK = False
        try:
            # 如果第一次发信息给claude就报错，说明有问题
            asyncio.run(sendMessageOne(BotID=bid, UserToken=yt, Message1=InitialMessage))
            idOK = True
        except:
            response = messagebox.askokcancel("错误!",
                                              "你填写的 Claude ID 或者 User Token 是错误的，或者当前网络有问题，请仔细检查！")
        if idOK:
            # 使用一个子进程来运行go-cqhttp.exe 来登陆QQ号并可以同时运行下面的监听QQ消息的部分
            subprocess.Popen('go-cqhttp/go-cqhttp.exe')
            app.run(debug=False, host='127.0.0.1', port=8788)
