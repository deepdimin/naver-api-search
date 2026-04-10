import streamlit as st  # Streamlit 라이브러리 임포트
import pandas as pd  # Pandas 라이브러리 임포트
import plotly.express as px  # Plotly Express 라이브러리 임포트
import plotly.graph_objects as go  # Plotly Graph Objects 라이브러리 임포트
from datetime import datetime, timedelta  # 날짜 계산을 위한 모듈 임포트
from app_helper import get_datalab_trend, fetch_naver_search, get_word_frequency  # 헬퍼 함수 임포트

# 대시보드 페이지의 기본 설정 (타이틀, 아이콘, 레이아웃 등)
st.set_page_config(
    page_title="네이버 API 통합 실시간 분석 대시보드",  # 웹 브라우저 탭에 표시될 제목
    page_icon="📊",  # 페이지 아이콘 설정
    layout="wide",  # 화면을 넓게 사용하는 와이드 모드 설정
    initial_sidebar_state="expanded"  # 시작 시 사이드바를 펼친 상태로 설정
)

# 대시보드 디자인 개선을 위한 커스텀 CSS 마크다운
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;  /* 메인 배경색 설정 */
    }
    .stMetric {
        background-color: #ffffff;  /* 지표 카드의 배경색 */
        padding: 15px;  /* 내부 여백 */
        border-radius: 10px;  /* 모서리 둥글게 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);  /* 입체감을 위한 그림자 효과 */
    }
    h1, h2, h3 {
        color: #1e1e1e;  /* 헤더 텍스트 색상 */
        font-family: 'Outfit', sans-serif;  /* 헤더 폰트 설정 */
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;  /* 탭 사이의 간격 설정 */
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;  /* 탭 버튼 높이 */
        white-space: pre-wrap;  /* 텍스트 줄바꿈 허용 */
        background-color: #f0f2f6;  /* 비활성 탭 배경색 */
        border-radius: 5px;  /* 탭 모서리 둥글게 */
        gap: 1px;  /* 내부 요소 간격 */
        padding-top: 10px;  /* 상단 여백 */
        padding-bottom: 10px;  /* 하단 여백 */
    }
    .stTabs [aria-selected="true"] {
        background-color: #2e7d32;  /* 활성화된 탭의 배경색 (녹색) */
        color: white;  /* 활성화된 탭의 글자색 */
    }
    </style>
    """, unsafe_allow_html=True)  # HTML 태그 직접 사용 허용

# --- 사이드바 구성 시작 ---
st.sidebar.title("🔍 분석 설정")  # 사이드바 타이틀 표시
st.sidebar.markdown("---")  # 구분선 추가

# 분석할 키워드를 입력받는 텍스트 박스 (기본값 설정)
keyword = st.sidebar.text_input("분석 키워드 입력", value="핫팩, 선풍기")
# 쉼표를 기준으로 키워드를 분리하고 양쪽 공백 제거
keywords = [k.strip() for k in keyword.split(",") if k.strip()]

# 분석 기간을 선택하는 날짜 입력 위젯
date_range = st.sidebar.date_input(
    "분석 기간",
    value=(datetime.now() - timedelta(days=30), datetime.now() - timedelta(days=1)),  # 최근 30일 기본 설정
    max_value=datetime.now() - timedelta(days=1)  # 최대 어제 날짜까지만 선택 가능
)

# 선택된 날짜 범위가 시작일과 종료일을 모두 포함하는지 확인
if len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")  # 시작일 포맷팅
    end_date = date_range[1].strftime("%Y-%m-%d")  # 종료일 포맷팅
else:
    # 날짜가 하나만 선택된 경우 기본 30일 범위로 설정
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# 각 검색 카테고리별로 가져올 아이템 개수 설정 슬라이더
search_display = st.sidebar.slider("검색 결과 수 (각 카테고리)", 10, 100, 50)

st.sidebar.markdown("---")  # 하단 구분선
st.sidebar.info("네이버 API를 통해 실시간 데이터를 수집합니다.")  # 안내 메시지 표시

# --- 메인 본문 영역 시작 ---
st.title("🚀 네이버 API 통합 실시간 데이터 분석")  # 메인 타이틀
# 선택된 키워드와 분석 기간 요약을 마크다운으로 표시
st.markdown(f"**분석 키워드**: {', '.join(keywords)} | **기간**: {start_date} ~ {end_date}")

# 입력된 키워드가 없는 경우 경고 메시지 표시 후 중단
if not keywords:
    st.warning("분석할 키워드를 입력해 주세요.")
    st.stop()

# 네이버 API를 통한 실시간 데이터 수집 진행
with st.spinner("데이터를 수집하고 있습니다..."):
    # 네이버 데이터랩 검색어 트렌드 데이터 수집 (통합 호출)
    trend_df_all = get_datalab_trend(keywords, start_date, end_date)
    
    # 쇼핑, 블로그, 카페, 뉴스 데이터 수집을 위한 구조 정의
    all_search_data = {cat: {} for cat in ["shop", "blog", "cafearticle", "news"]}
    # 각 키워드별로 카테고리별 검색 데이터 수집 반복
    for kw in keywords:
        for cat in all_search_data.keys():
            all_search_data[cat][kw] = fetch_naver_search(cat, kw, display=search_display)

# 분석 결과를 보여줄 5개의 탭 정의
tabs = st.tabs(["📊 통합 트렌드", "🛒 쇼핑 분석", "📱 소셜/뉴스 인사이트", "🔬 데이터 프로파일링", "📁 원본 데이터"])

# --- 첫 번째 탭: 통합 트렌드 분석 ---
with tabs[0]:
    st.subheader("📈 검색어 트렌드 비교")  # 탭 서브 헤더
    # 수집된 트렌드 데이터가 비어있지 않은 경우 시각화 진행
    if not trend_df_all.empty:
        # Plotly를 사용한 라인 차트 생성
        fig = px.line(trend_df_all, x='period', y='ratio', color='keyword',
                     title="기간별 상대적 검색량 추이 (동일 기준 비교)",  # 차트 제목
                     template="plotly_white",  # 차트 템플릿 설정
                     labels={'ratio': '검색량 (상대값)', 'period': '날짜'})  # 축 라벨 설정
        fig.update_layout(hovermode="x unified")  # 마우스 오버 시 정보를 수직선으로 통합 표시
        st.plotly_chart(fig, use_container_width=True)  # 생성된 차트를 화면에 표시
        
        # 각 키워드별 상단 요약 통계(Metric) 표시
        kw_list = trend_df_all['keyword'].unique()
        cols = st.columns(len(kw_list))  # 키워드 개수만큼 컬럼 생성
        for i, kw in enumerate(kw_list):
            kw_data = trend_df_all[trend_df_all['keyword'] == kw]  # 특정 키워드 데이터 필터링
            avg_ratio = kw_data['ratio'].mean()  # 평균 검색량 계산
            max_ratio = kw_data['ratio'].max()  # 최대 검색량 계산
            cols[i].metric(f"{kw} 평균 검색량", f"{avg_ratio:.1f}", delta=f"최대 {max_ratio:.1f}")  # 통계 카드 렌더링
    else:
        # 데이터가 없을 경우 안내 문구 표시
        st.info("해당 기간의 트렌드 데이터가 없습니다. 키워드나 기간을 확인해 주세요.")

# --- 두 번째 탭: 쇼핑 분석 ---
with tabs[1]:
    st.subheader("🛒 네이버 쇼핑 데이터 분석")
    
    # 분석할 특정 키워드 선택을 위한 셀렉트 박스
    selected_kw_shop = st.selectbox("집중 분석 키워드 (쇼핑)", keywords, key="shop_kw")
    # 선택된 키워드에 해당하는 쇼핑 데이터 가져오기
    df_shop = all_search_data['shop'][selected_kw_shop]
    
    # 데이터가 존재하는 경우 분석 진행
    if not df_shop.empty:
        # 가격 데이터(lprice)를 숫자형으로 변환 (오류 발생 시 NaN 처리)
        df_shop['lprice'] = pd.to_numeric(df_shop['lprice'], errors='coerce')
        
        # 화면을 좌우 2칸으로 분할
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 🏷️ 카테고리 구성 (Treemap)")
            # 카테고리 계층 정보를 포함하는 컬럼 리스트 추출
            cat_cols = [col for col in ['category1', 'category2', 'category3', 'category4'] if col in df_shop.columns]
            # 트리맵(계층 구조 영역 차트) 생성
            fig_tree = px.treemap(df_shop, path=cat_cols, values='lprice', 
                                 title=f"'{selected_kw_shop}' 카테고리 및 가격 분포",
                                 color='lprice', color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with c2:
            st.markdown("### 💰 가격 분포")
            # 가격 분포를 보여주는 박스 플롯 생성
            fig_box = px.box(df_shop, y='lprice', points="all", 
                            title=f"'{selected_kw_shop}' 상품 가격 분포",
                            color_discrete_sequence=['#2e7d32'])
            st.plotly_chart(fig_box, use_container_width=True)
            
        # 브랜드 및 판매처 빈도 분석 섹션
        st.markdown("### 🏢 브랜드 및 판매처 현황")
        bc1, bc2 = st.columns(2)  # 화면 분할
        with bc1:
            # 상위 10개 브랜드 추출 및 카운트
            brand_counts = df_shop['brand'].value_counts().reset_index().head(10)
            brand_counts.columns = ['brand', 'count']
            # 데이터에 브랜드가 없는 경우 예외 처리
            brand_counts['brand'] = brand_counts['brand'].replace('', '기타/미지정')
            # 브랜드 점유율 파이 차트 생성
            fig_brand = px.pie(brand_counts, values='count', names='brand', title="상위 브랜드 점유율")
            st.plotly_chart(fig_brand, use_container_width=True)
            
        with bc2:
            # 상위 10개 판매처(몰) 추출 및 카운트
            mall_counts = df_shop['mallName'].value_counts().reset_index().head(10)
            mall_counts.columns = ['mallName', 'count']
            # 판매처 분포 가로 막대 그래프 생성
            fig_mall = px.bar(mall_counts, x='count', y='mallName', orientation='h', 
                             title="주요 판매처(Mall) Top 10", color='count',
                            color_continuous_scale='Greens')
            st.plotly_chart(fig_mall, use_container_width=True)
    else:
        st.info("쇼핑 데이터를 불러올 수 없습니다.")  # 데이터 부재 시 안내

# --- 세 번째 탭: 소셜/뉴스 인사이트 ---
with tabs[2]:
    st.subheader("📱 블로그, 카페, 뉴스 관심사 분석")
    
    # 소셜 분석용 특정 키워드 선택
    selected_kw_social = st.selectbox("집중 분석 키워드 (소셜/뉴스)", keywords, key="social_kw")
    
    # 블로그, 카페, 뉴스 데이터를 하나로 병합하여 분석
    social_dfs = []
    for cat in ["blog", "cafearticle", "news"]:
        if not all_search_data[cat][selected_kw_social].empty:
            temp = all_search_data[cat][selected_kw_social].copy()
            temp['source'] = cat  # 데이터 출처 표시 컬럼 추가
            social_dfs.append(temp)
            
    if social_dfs:
        combined_social = pd.concat(social_dfs)  # 리스트 내 모든 데이터프레임 병합
        
        # 제목 데이터의 단어 빈도 분석 (상위 30개 단어 추출)
        st.markdown("### 🔠 핵심 키워드 빈도 (Top 30)")
        freq_df = get_word_frequency(combined_social, 'title', top_n=30)
        
        if not freq_df.empty:
            # 단어 빈도 막대 그래프 생성
            fig_freq = px.bar(freq_df, x='count', y='word', orientation='h',
                             title=f"'{selected_kw_social}' 관련 소셜 데이터 주요 단어",
                             color='count', color_continuous_scale='Blues')
            fig_freq.update_layout(yaxis={'categoryorder':'total ascending'})  # 빈도 순 정렬
            st.plotly_chart(fig_freq, use_container_width=True)
        
        # 전체 데이터 중 채널별(블로그/카페/뉴스) 비중 분포
        st.markdown("### 📢 채널별 데이터 비중")
        source_counts = combined_social['source'].value_counts().reset_index()
        source_counts.columns = ['source', 'count']
        # 선버스트 차트(도넛 형태의 계층 시각화) 사용
        fig_source = px.sunburst(source_counts, path=['source'], values='count', title="데이터 출처 분포")
        st.plotly_chart(fig_source, use_container_width=True)
    else:
        st.info("소셜 데이터를 불러올 수 없습니다.")

# --- 네 번째 탭: 데이터 프로파일링 ---
with tabs[3]:
    st.subheader("🔬 수집 데이터 기초 프로파일링")
    
    # 프로파일링 대상을 선택하기 위한 UI
    prof_kw = st.selectbox("분석 대상 키워드", keywords, key="prof_kw")
    prof_cat = st.selectbox("분석 대상 카테고리", ["shop", "blog", "cafearticle", "news"], key="prof_cat")
    
    # 선택된 데이터 불러오기
    df_prof = all_search_data[prof_cat][prof_kw]
    
    if not df_prof.empty:
        col1, col2 = st.columns(2)  # 좌우 분할
        with col1:
            st.markdown("**기초 정보**")  # 행/열 개수 등 표시
            st.write(f"- 전체 데이터 수: {len(df_prof)}")
            st.write(f"- 컬럼 수: {len(df_prof.columns)}")
            st.write(f"- 컬럼 목록: {', '.join(df_prof.columns)}")
        
        with col2:
            st.markdown("**결측치 현황**")  # 데이터의 누락값 확인
            missing = df_prof.isnull().sum().reset_index()
            missing.columns = ['Column', 'Missing Count']
            # 결측치가 있는 컬럼만 표 형식으로 표시
            st.table(missing[missing['Missing Count'] > 0] if not missing[missing['Missing Count'] == 0].empty else missing)
            
        st.markdown("**기술 통계 (수치형)**")  # 평균, 편차 등 수치 통계 표시
        st.write(df_prof.describe(include='all').fillna('-'))
    else:
        st.info("프로파일링할 데이터가 없습니다.")

# --- 다섯 번째 탭: 원본 데이터 상세 조회 및 다운로드 ---
with tabs[4]:
    st.subheader("📁 수집된 데이터 상세 보기")
    
    # 각 키워드별로 접고 펼칠 수 있는 Expander 섹션 생성
    for kw in keywords:
        with st.expander(f"'{kw}' 데이터 상세보기"):
            # 블로그, 뉴스 등 모든 카테고리 데이터 조회
            for cat in ["shop", "blog", "cafearticle", "news"]:
                st.write(f"**[{cat.upper()}]**")
                st.dataframe(all_search_data[cat][kw], use_container_width=True)  # 데이터프레임 렌더링
                # CSV 파일 다운로드 버튼 생성 (Excel 호환을 위해 utf-8-sig 인코딩 적용)
                st.download_button(
                    label=f"{kw}_{cat} 데이터 다운로드",
                    data=all_search_data[cat][kw].to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"naver_{kw}_{cat}.csv",
                    mime='text/csv'
                )
