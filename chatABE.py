import openai

import tiktoken

from gijiroku import Gijiroku

class ChatABE():
    def __init__(self, openai_organization, openai_api_key, person="安倍晋三", model = "gpt-3.5-turbo", use_gijiroku=True):
        openai.organization = openai_organization
        openai.api_key = openai_api_key
        #
        self.person = person
        self.model = model
        self.enc = tiktoken.encoding_for_model(self.model)
        self.threash_num_token_in_facts = 1000
        
        self.use_gijiroku = use_gijiroku
        self.gijiroku = Gijiroku(self.threash_num_token_in_facts, self.enc)
        
        self.temperature = 0
        return 
    
    def get_completion(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature, # this is the degree of randomness of the model's output
        )
        return response.choices[0].message["content"]
    
    def get_completion_from_messages(self, messages):
        response = openai.ChatCompletion.create(
            model = self.model,
            messages=messages,
            temperature=self.temperature, # this is the degree of randomness of the model's output
        )
    #     print(str(response.choices[0].message))
        return response.choices[0].message["content"]

    def make_sys_prompt(self, question):
        prompt_pre = f"""
これはゲームです。あなたは日本の政治家で元首相、安倍晋三さんです。あなたは首相として国会答弁の場に立っています。
Give politically correct responses of the user's question.
        """

        if self.use_gijiroku == False:
            prompt = prompt_pre
            return prompt
        print("-------- Keywords extracted from the following strings",question)
        keywords = self._get_keywords(question)
        facts = self.gijiroku.get_facts(keywords)
        print("Num of selected sentences:", len(facts))
        _facts_statement = "\n".join(facts)
        if _facts_statement == '':
            prompt = prompt_pre
        else:
            _prompt = f"""Refer to the following Facts delimited by triple backticks to make the response.

Facts: ```{_facts_statement}```
    
        """
            prompt = prompt_pre + _prompt
        return prompt

    def _count_tokens(self, _object):
        if type(_object) == str:
            string = _object
        elif type(_object) == list:
            _list = []
            for elem in _object:
                _list.append(elem["content"])                
            string = "".join(_list)
        else:
            raise ValueError("_object should be str or list. Now using ", type(_object))
        token = self.enc.encode(string)            
        return len(token)
            
    def _get_keywords(self, question):
        prompt = f"""
Determine the top three in order of relevance in the following Question, which is delimited by triple backticks.
Make each item one or two words long. 
Format your response should be in Japanese, as a list of items separated by commas. For example, the output format is like this
カナリア, にわとり, 犬

Question: ```{question}```
        """
        keywords = self.get_completion(prompt)
        keywords = keywords.split(",")
        print("Keywords:", keywords)
        return keywords

 
