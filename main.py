from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, MessageAction, ConfirmTemplate, FollowEvent,
    QuickReply, QuickReplyButton, MessageAction, ImageSendMessage
)
import os

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import re

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

#画像の参照元パス
SRC_IMAGE_PATH = "static/images/letter.jpg"
MAIN_IMAGE_PATH = "static/images/main_letter.jpg"
PREVIEW_IMAGE_PATH = "static/images/preview_letter.jpg"
li = []
stage = "accepter"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print(body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
@handler.add(FollowEvent)
def handle_follow(event):
    confirm_template = ConfirmTemplate(text='手紙を書きますか？', actions=[
        MessageAction(label='書きたい！', text='書きたい！'),
        MessageAction(label='書きたくない', text='書きたくない'),
    ])
    template_message = TemplateSendMessage(
        alt_text='Confirm alt text', template=confirm_template)
    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text="友達追加ありがとうございます！\nこのトークでは、簡単なやり取りを通して手紙を書くことが出来ます！"),
            template_message
        ]
     )
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global stage
    global li
    reply = event.message.text
    if reply == "書きたくない":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                    text="分かりました！\nまた書きたくなったら話かけてくださいね〜😁"))
        
    elif stage == "accepter":
        stage = "sender"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                    text="ありがとうございます！\n素敵な手紙を書いてくださいね😊\n\n誰に手紙を書きますか？"))
    elif stage == "sender":
        stage = "reason" 
        li.append(reply)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                    text=li[0]+"さんですね！\nきっと喜びますね！\nあなたの名前は何ですか？"))
    elif stage == "reason":
        stage = "detail"
        li.append(reply)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=li[1]+"さんですね！\nありがとうございます！\n今回"+li[0]+"さんに手紙を書こうと思った理由は何ですか？\n\n例）大切な気持ちを伝えたい",
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="感謝を伝えたい", text="感謝を伝えたい")
                         ),
                         QuickReplyButton(
                            action=MessageAction(label="謝りたい", text="謝りたい")
                          ),
                         QuickReplyButton(
                            action=MessageAction(label="自分の気持ちを伝えたい", text="自分の気持ちを伝えたい")
                         ),
                 ])))
    elif stage == "detail":
        stage = "addition"
        if reply == "感謝を伝えたい":
            li.append("今日は" + li[0] + "さんにお礼を言いたくてこの手紙を書くことにしました。")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ステキですね✨\n" + li[0] + "さんへの感謝の気持ちを伝えたいか教えてください！\n\n例）落ち込んでいるときにそっと声を掛けてくれてありがとう"))
        elif reply == "謝りたい":
            li.append("今日は謝りたくてこの手紙を書くことにしました。")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="なかなか言えない気持ちを伝えるのはすごい勇気が入りますよね...でもきっと気持ちは伝わりますよ！\n" + li[0] +
                                "さんに伝えたいその気持ちを教えてください！\n\n例）この間は太郎くんの気持ちを考えないであんなこと言ってごめんね"))
        elif reply == "自分の気持ちを伝えたい":
            li.append("今日は伝えたいことがあって、この手紙を書くことにしました。") 
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="あなたの気持ちは必ず伝わりますよ！\n" + li[0] + "さんに伝えたいその気持ちを教えてください！\n\n例"+
                                " ）実はあのときテニス部に入る気はなかったんです"))
    elif stage == "addition":
        stage = "complete"
        li.append(reply)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="最後に何か一言どうぞ！\n\n例）これからもよろしくね！"))
    elif stage == "complete":
        sentences=""
        li.append(reply)
        for i,j in enumerate(li):
            if i == 0:
                sentences += j + "さんへ" + "\n\n"
            elif i == 1:
                continue
            elif i == len(li) - 1:
                sentences += j + "\n\n" + li[1] + "より"
            else:
                for ix, va in enumerate(range(0, len(j), 14)):
                    sentences += j[va:va+14] + "\n"
        print("wow",sentences)
                
        stage = "accepter"
        li = []
        src_image_path = Path(SRC_IMAGE_PATH).absolute()
        main_image_path = MAIN_IMAGE_PATH
        preview_image_path = PREVIEW_IMAGE_PATH

        date_the_image(src=src_image_path, desc=Path(main_image_path).absolute(), sentences=sentences)
        date_the_image(src=src_image_path, desc=Path(preview_image_path).absolute(), sentences=sentences)

        # 画像の送信
        image_message = ImageSendMessage(
            original_content_url=f"https://line-bot-letter.herokuapp.com/{main_image_path}",
            preview_image_url=f"https://line-bot-letter.herokuapp.com/{preview_image_path}"
         )
        #ログの取得
        app.logger.info(f"https://line-bot-letter.herokuapp.com/{main_image_path}")

        confirm_template = ConfirmTemplate(text='また手紙を書きますか？?', actions=[
            MessageAction(label='書きたい', text='書きたい！'),
            MessageAction(label='書きたくない', text='書きたくない'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="お疲れ様でした！こちらが手紙の文章です！"),
                image_message,
                template_message
            ]
        )

def date_the_image(src: str, desc: str, sentences: str, size=800) -> None:
    """日付を付けて、保存する
    :params src:
        読み込む画像のパス
    :params desc:
        保存先のパス
    :params size:
        変換後の画像のサイズ
    """
    # 開く
    im = Image.open(src)

    # 800 x Height の比率にする
    if im.width > size:
        proportion = size / im.width
        im = im.resize((int(im.width * proportion), int(im.height * proportion)))

    draw = ImageDraw.Draw(im)

    font = ImageFont.truetype("./fonts/TakaoPMincho.ttf", 45)
    text = sentences
    # 図形を描画
    x = 100
    y = 120
    margin = 5
    text_width = draw.textsize(text, font=font)[0] + margin
    text_height = draw.textsize(text, font=font)[1] + margin
    draw.rectangle(
        (x - margin, y - margin, x + text_width, y + text_height), fill=(255, 255, 255)
    )

    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    # 保存
    im.save(desc)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
