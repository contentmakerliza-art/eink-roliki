# Добавляет в schedule.json готовые запросы для Buffer (TikTok + Pinterest).
import json, re, random
TT = "6ac344af6a5c39ccb61bd437"; PIN = "6ac344686a5c39ccb61bd27f"
BOARDS = {"main": "1141521905491005624", "estetika": "1141521905491064869", "svoe_foto": "1141521905491064863",
          "gadzhety": "1141521905491064872", "romantika": "1141521905491064868", "nahodki": "1141521905491787605",
          "devushke": "1141521905491064886", "ng2027": "1141521905491787607", "idei": "1141521905491064866"}
BOARD_BY_ID = {"04_seryi_anime": "estetika", "05_seryi_podstavka": "main", "06_semya": "svoe_foto",
               "07_zaichik": "gadzhety", "08_nadpisi": "romantika"}
Q = "mutation($i:CreatePostInput!){createPost(input:$i){__typename ... on PostActionSuccess{post{id status dueAt}} ... on MutationError{message}}}"
QB = ("mutation($t:CreatePostInput!,$p:CreatePostInput!){"
      "tiktok:createPost(input:$t){__typename ... on PostActionSuccess{post{id status dueAt}} ... on MutationError{message}} "
      "pinterest:createPost(input:$p){__typename ... on PostActionSuccess{post{id status dueAt}} ... on MutationError{message}}}")
QP = ("mutation($p:CreatePostInput!){"
      "pinterest:createPost(input:$p){__typename ... on PostActionSuccess{post{id status dueAt}} ... on MutationError{message}}}")
def body(inp): return json.dumps({"query": Q, "variables": {"i": inp}}, ensure_ascii=False)
d = json.load(open("queue/schedule.json"))
for e in d:
    rnd = random.Random(e["id"])
    if "tiktok_at" not in e:
        e["tiktok_at"] = f'{e["date"]}T{rnd.randint(19,20)}:{rnd.randint(0,59):02d}:00+03:00'
        e["pinterest_at"] = f'{e["date"]}T{rnd.randint(20,21)}:{rnd.randint(0,59):02d}:00+03:00'
    art = re.search(r"арт\.\s*(?:WB\s*)?(\d+)", e["description"]).group(1)
    title = e["title"].replace("#shorts", "").strip()
    board = e.get("board") or BOARD_BY_ID.get(e["id"], "main"); e["board"] = board
    e["buffer_tiktok"] = body({"channelId": TT, "text": e["description"], "assets": [{"video": {"url": e["file_url"]}}],
        "mode": "customScheduled", "dueAt": e["tiktok_at"], "schedulingType": "automatic",
        "metadata": {"tiktok": {"isAiGenerated": False}}})
    e["buffer_pinterest"] = body({"channelId": PIN, "text": e["description"], "assets": [{"video": {"url": e["file_url"]}}],
        "mode": "customScheduled", "dueAt": e["pinterest_at"], "schedulingType": "automatic",
        "metadata": {"pinterest": dict({"boardServiceId": BOARDS[board], "title": title[:100]},
                     **({"url": f"https://www.wildberries.ru/catalog/{art}/detail.aspx"} if e.get("pin_link", True) else {}))}})
    tt=json.loads(e["buffer_tiktok"])["variables"]["i"]; pn=json.loads(e["buffer_pinterest"])["variables"]["i"]
    if e.get("tiktok_via") == "studio":
        # TikTok публикуется вручную/через TikTok Studio — в Buffer уходит только Pinterest
        e["buffer_tiktok"] = json.dumps({"query": "query{__typename}"})
        e["buffer_both"] = json.dumps({"query": QP, "variables": {"p": pn}}, ensure_ascii=False)
    else:
        e["buffer_both"] = json.dumps({"query": QB, "variables": {"t": tt, "p": pn}}, ensure_ascii=False)
json.dump(d, open("queue/schedule.json", "w"), ensure_ascii=False, indent=1)
for e in d: print(e["id"], e["date"], "TT", e["tiktok_at"][11:16], "PIN", e["pinterest_at"][11:16], e["board"])
