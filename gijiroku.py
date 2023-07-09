import os

import requests

import pandas as pd

class Gijiroku():
    def __init__(self, threash_num_token_in_facts, enc):
        self.threash_num_token_in_facts = threash_num_token_in_facts
        self.enc = enc

    def count_tokens(self, string):
        token = self.enc.encode(string)
        return len(token)
    
    def get_facts(self, keywords):
        '''
        1. 国会議事録検索システムのAPIからkeywordsを検索語として引っ張ってくる。
        2. 点数(score)化。keywordsが全て含まれる発言を6点、keyword1 + keyword2 = 5点、keyword2 + keyword3 = 4点、keyword1のみ3点、keyword2のみ2点、keyword3のみ1点
        3. 発言を改行でlist化し、それぞれの要素のトークン数(numtoken)を付与
        4. 同じ発言のものはユニーク化。その残す優先順位はscore列の値が大きさが大きいほど高い。もしもsocre列の値が同じならば、num_token列の値が大きい方が優先順位が高い。
        5. 優先順位高いものを選んでいく。合計のトークン数がthreash_num_token以下となるように残す。
        '''

        search_strs = [" ".join(keywords), keywords[0]+" "+keywords[1], keywords[1]+" "+keywords[2], keywords[0], keywords[1], keywords[2] ]
        scores = [3+2+1, 3+2, 3+1, 3, 2, 1]

        dfs = []
        print("Searching in 国会会議録検索システム")
        for search_str, score in zip(search_strs, scores):
            numberOfRecords, speeches, num_tokens = self._search_speeches_from_Gijiroku(search_str)
            if numberOfRecords == 0:
                continue
            _df = pd.DataFrame(columns=['score', 'num_token', 'speech'])
            _df["num_token"] = num_tokens
            _df["speech"] = speeches
            _df['score'] = score
            dfs.append(_df)
        _df = pd.concat(dfs,  ignore_index=True)

        '''
        4. speech列の値が重複をしたレコードを削除して単一のものを残したい。
        その残す優先順位はscore列の値が大きさが大きいほど高い。
        もしもsocre列の値が同じならば、num_token列の値が大きい方が優先順位が高い。
        '''
        # 重複したspeech列を削除して、score列を降順、num_token列を昇順にソートする
        _df = _df.drop_duplicates(subset=['speech']).sort_values(by=['score', 'num_token'], ascending=[False, False])
        '''
        5. 優先順位高いものを選んでいく。合計のトークン数がthreash_num_token以下となるように残す。
        '''
        # sum_num_token列を追加
        _df['sum_num_token'] = _df['num_token'].cumsum()
        # threash_sum_num_tokenよりも大きい行を削除
        df = _df[_df['sum_num_token'] <= self.threash_num_token_in_facts]
        
        facts = df["speech"].values
        return facts
    
    def _search_speeches_from_Gijiroku(self, search_str):
        '''
        Pramaeters
        ----------
        search_str: str
            "any" parameter used in API. Ex. "企業 主導"
        '''
        # getメソッドでURLに対してGETリクエストを送る
        url = "https://kokkai.ndl.go.jp/api/speech?"
        params = {"any": search_str, "speaker":"安倍晋三", "recordPacking":"json"}
        #records = requests.get("https://kokkai.ndl.go.jp/api/speech?any=企業 主導 型 保育 検討 委員会 児童 育成 協会&speaker=%E5%AE%89%E5%80%8D")
        records = requests.get(url, params=params)
        records = records.json()
        numberOfRecords = records["numberOfRecords"]
        print(numberOfRecords, " records found")
        if numberOfRecords == 0:
            return numberOfRecords, [], []
        #
        speeches = []
        for elem in records["speechRecord"]:
            speech = elem["speech"]
            ### （拍手）以下を削除: cleaning
            speech = speech.split("（拍手）")[0]
            ###
            _speeches = speech.split('\u3000')
            ### # <= ○安倍内閣総理大臣を削除: cleaning
            _speeches.pop(0)
            ###
            speeches+=_speeches
        speeches = [speech.replace("\r\n", "") for speech in speeches] # cleaning
        ## search_str にある単語が一つでも使われているものを探して、それに該当する要素をspeechesとする。
        list_string_search = search_str.split()
        speeches = [s for s in speeches if any(xs in s for xs in list_string_search)]
        ##
        num_tokens = []
        for speech in speeches:
            num_tokens.append(self.count_tokens(speech))
        ##
        # print("Num of sentences =", len(speeches))
        return numberOfRecords, speeches, num_tokens

