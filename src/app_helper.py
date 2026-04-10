import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import streamlit as st

# .env 로드 (로컬 환경용)
load_dotenv()

# Streamlit Cloud 배포 환경(st.secrets)과 로컬(.env) 모두 지원
def get_secret(key):
    # 1. Streamlit Secrets 확인
    if key in st.secrets:
        return st.secrets[key]
    # 2. 환경 변수(.env 등) 확인
    return os.getenv(key)

CLIENT_ID = get_secret("NAVER_CLIENT_ID")
CLIENT_SECRET = get_secret("NAVER_CLIENT_SECRET")

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
    "Content-Type": "application/json"
}

@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_datalab_trend(keywords_list, start_date, end_date):
    """
    여러 키워드를 한 번에 요청하여 동일 기준(Ratio) 상에서 비교 데이터를 가져옵니다.
    """
    if not keywords_list:
        return pd.DataFrame()

    url = "https://openapi.naver.com/v1/datalab/search"
    
    keyword_groups = []
    for kw in keywords_list:
        keyword_groups.append({
            "groupName": kw,
            "keywords": [kw]
        })

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": keyword_groups
    }
    
    response = requests.post(url, headers=HEADERS, json=body)
    
    if response.status_code == 200:
        data = response.json()
        all_dfs = []
        for result in data['results']:
            kw_name = result['title']
            if result['data']:
                df = pd.DataFrame(result['data'])
                df['keyword'] = kw_name
                df['period'] = pd.to_datetime(df['period'])
                all_dfs.append(df)
        
        if all_dfs:
            return pd.concat(all_dfs)
    else:
        st.error(f"데이터랩 API 오류: {response.status_code} - {response.text}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_shopping_insight(cat_id, start_date, end_date):
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    # 예시 cat_id: 50000000 (패션의류)
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "category": cat_id,
        "keyword": []
    }
    # 실제로는 카테고리 아이디를 정확히 알아야 함. 
    # 여기서는 검색 트렌드 위주로 먼저 구현.
    return pd.DataFrame()

@st.cache_data(ttl=1800)
def fetch_naver_search(category, keyword, display=100):
    url = f"https://openapi.naver.com/v1/search/{category}.json"
    params = {
        "query": keyword,
        "display": display,
        "start": 1,
        "sort": "sim" if category != "news" else "date"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        items = response.json().get('items', [])
        df = pd.DataFrame(items)
        return df
    return pd.DataFrame()

def get_word_frequency(df, text_col, top_n=30):
    if df.empty or text_col not in df.columns:
        return pd.DataFrame()
    
    # HTML 태그 제거 및 텍스트 정규화
    import re
    def clean_text(text):
        if not isinstance(text, str): return ""
        text = re.sub(r'<[^>]+>', '', text) # 태그 제거
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text) # 특수문자 제거
        return text

    all_text = " ".join(df[text_col].apply(clean_text))
    words = all_text.split()
    # 불용어(간단히) 처리 - 2글자 이상만
    words = [w for w in words if len(w) > 1]
    
    from collections import Counter
    counts = Counter(words).most_common(top_n)
    return pd.DataFrame(counts, columns=['word', 'count'])
