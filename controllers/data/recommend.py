import os

os.environ['KERAS_BACKEND'] = 'tensorflow'
from keras.models import load_model
import heapq
import numpy as np
import json
import time

## 加载模型
model = load_model("NeuMF_1546507199.h5")

def evaluate_model(model, uid, predata, K):
    global _model
    global _predata
    global _K
    _model = model
    _predata = predata
    _K = K

    u = uid
    items = _predata
    map_item_score = {}
    users = np.full(len(items), u, dtype='int32')
    predictions = _model.predict([users, np.array(items)], batch_size=100, verbose=0)
    for i in range(len(items)):
        item = items[i]
        map_item_score[item] = predictions[i]
    items.pop()

    # Evaluate top rank list
    ranklist = heapq.nlargest(_K, map_item_score, key=map_item_score.get)
    return ranklist


def recommend(filepath, savepath, user):
    ###读取json文件，获取直播ID列表，建立ID和信息之间的字典
    Idlist = []
    dydata = {}
    with open(filepath, "r", encoding="utf-8") as load_f:
        read_file = load_f.read()
        load_dict = read_file.split('}{')
        item = ""
        for i in range(len(load_dict)):
            if i != 0:
                item = "{"+load_dict[i]
            try:
                p = item.index("{")
            except Exception as e:
                print(e)  # 报错则重新推荐
            else:
                if i != len(load_dict)-1:
                    info = str(item[p:] + "}")
                else:
                    info = str(item[p:])
                dic = eval(info)
                if dic["platformIcon"][-5] == '1':
                    id = str(dic["url"]).split("/")
                    if id[-1].isdigit():
                        Idlist.append(id[-1])
                        dydata[id[-1]] = dic
    ## 直播ID转换字典
    zbid_dic = {}
    with open("ZBID.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            zbid = line.split(" : ")
            zbid_dic[zbid[0]] = int(zbid[1])
    ## 得到转换后的候选直播ID
    candList = []
    cand_dic = {}
    for id in Idlist:
        if id in zbid_dic.keys():
            candList.append(zbid_dic[id])
            cand_dic[zbid_dic[id]] = id
    ## 获得推荐ID
    recommendlist = evaluate_model(model, user, candList, 4)
    print("推荐列表：", recommendlist)
    ## 存储推荐列表ID下的直播房间信息
    with open(savepath, "w", encoding="utf-8") as f:
        for id in recommendlist:
            f.write(json.dumps(dydata[cand_dic[id]]))
    return recommendlist


def get_FileUpdateTime(filePath):
    t = os.path.getmtime(filePath)
    return t


if __name__ == '__main__':
    dirs = "users/"
    dir_time = {}
    users = {"admin":1206,"huster":904,"huster2":1109}
    dir_all = os.listdir(dirs)
    for dir in dir_all:
        dir_time[dir] = time.time()
    while True:
        try:
            dir_all = os.listdir(dirs)
            for dir in dir_all:
                if dir != "游客":
                    t = get_FileUpdateTime(dirs+dir+"/dylive.json")
                    if abs(t - dir_time[dir]) > 5:
                        while not recommend(dirs+dir+"/dylive.json", dirs+dir+"/recommend.txt", users[dir]):
                            print("重新推荐中...")
                dir_time[dir] = t
        except Exception as e:
            print(e)
        time.sleep(0.5)