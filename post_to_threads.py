"""毎朝1本、posts.json から Threads に投稿する。標準ライブラリだけで動く。

環境変数:
  THREADS_ACCESS_TOKEN  Threads のアクセストークン(GitHub Secrets から渡す)
  DRY_RUN               "1" のときは投稿せず、内容の表示だけ行う
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.threads.net/v1.0"
MAX_LEN = 500  # Threads の1投稿の上限文字数
JST = datetime.timezone(datetime.timedelta(hours=9))


def load_config():
    with open(os.path.join(os.path.dirname(__file__), "posts.json"), encoding="utf-8") as f:
        return json.load(f)


def pick_post(config, today):
    """開始日からの日数で、今日の1本を決める(状態ファイル不要)。"""
    start = datetime.date.fromisoformat(config["start_date"])
    days = (today - start).days
    if days < 0:
        return None
    posts = config["posts"]
    return posts[days % len(posts)]


def build_text(post, urls):
    text = post["text"]
    url = urls.get(str(post["article"]), "").strip()
    if url:
        text += "\n\n" + url
    return text


def call(path, params):
    # トークンを URL に載せないよう、POST の本文で送る
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        # エラー本文にトークンは含まれない。内容だけ表示する
        sys.exit(f"Threads API エラー {e.code}: {e.read().decode(errors='replace')}")


def main():
    config = load_config()
    today = datetime.datetime.now(JST).date()
    post = pick_post(config, today)
    if post is None:
        print(f"開始日 {config['start_date']} より前なので投稿しません。")
        return

    text = build_text(post, config["urls"])
    if len(text) > MAX_LEN:
        sys.exit(f"文字数オーバー({len(text)}/{MAX_LEN}): {text[:30]}...")

    print(f"--- {today} の投稿({len(text)}文字) ---\n{text}\n")
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN のため投稿しませんでした。")
        return

    token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not token:
        sys.exit("THREADS_ACCESS_TOKEN が設定されていません。")

    created = call("me/threads", {"media_type": "TEXT", "text": text, "access_token": token})
    result = call("me/threads_publish", {"creation_id": created["id"], "access_token": token})
    print(f"投稿しました。id={result.get('id')}")


if __name__ == "__main__":
    main()
