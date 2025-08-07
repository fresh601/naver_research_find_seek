import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs
import time

st.set_page_config(layout="wide")
st.title("📊 네이버 리서치 리포트 크롤러")

# 🔹 사용자 입력
item_name = st.text_input("📝 종목명 입력", value="삼성전자")
code = st.text_input("🔑 종목 코드 입력", value="005930")

# 🔍 검색 버튼
if st.button("🔍 검색 시작") and item_name and code:
    encoded_name = quote(item_name.encode('euc-kr'))

    headers = {
        'Referer': f'https://finance.naver.com/research/company_list.naver?keyword=&brokerCode=&writeFromDate=&writeToDate=&searchType=itemCode&itemName={encoded_name}&itemCode={code}&x=28&y=16',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    # 🔎 리서치 목록 요청
    response = requests.get(
        f'https://finance.naver.com/research/company_list.naver?keyword=&brokerCode=&writeFromDate=&writeToDate=&searchType=itemCode&itemName={encoded_name}&itemCode={code}&x=27&y=19',
        headers=headers,
    )

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.select_one('table.type_1')
    rows = table.select('tr') if table else []

    if not rows:
        st.warning("리서치 테이블이 존재하지 않습니다.")
    else:
        for idx, row in enumerate(rows):
            cols = row.find_all('td')
            if len(cols) >= 6:
                try:
                    report_item_name = cols[0].select_one('a.stock_item').get_text(strip=True)
                    title = cols[1].select_one('a').get_text(strip=True)
                    company = cols[2].get_text(strip=True)
                    date = cols[4].get_text(strip=True)

                    st.markdown("---")
                    st.markdown(f"### 📄 {report_item_name} | {title} | {company} | {date}")

                    # ▶ nid 추출
                    href = cols[1].select_one('a')['href']
                    nid = parse_qs(urlparse(href).query).get('nid', [''])[0]

                    # ▶ 상세 페이지 요청
                    response_detail = requests.get(
                        f'https://finance.naver.com/research/company_read.naver?nid={nid}'
                    )
                    soup_detail = BeautifulSoup(response_detail.text, 'html.parser')

                    sub_table = soup_detail.select_one('table.type_1')
                    if not sub_table:
                        st.warning("세부 테이블이 없습니다.")
                        continue

                    # ▶ 텍스트 정보 추출
                    money = sub_table.select_one(".money").text.strip()
                    coment = sub_table.select_one(".coment").text.strip()

                    th_tag = sub_table.select_one('.view_sbj')
                    text_parts = [t for t in th_tag.contents if t.name is None and t.strip()]
                    sub_title = text_parts[0].strip() if text_parts else ''

                    p_tags = sub_table.select('.view_cnt > div > p')
                    sub_content1 = p_tags[0].text.strip() if len(p_tags) > 0 else ''
                    sub_content2 = '\n'.join(p.text.strip() for p in p_tags[1:]) if len(p_tags) > 1 else ''

                    # ▶ PDF 링크 추출
                    pdf_link_tag = soup_detail.select_one('a[href$=".pdf"]')
                    pdf_link = pdf_link_tag['href'] if pdf_link_tag else None

                    # ▶ 출력
                    st.markdown(f"**🎯 목표가:** {money}")
                    st.markdown(f"**🧭 투자의견:** {coment}")
                    st.markdown(f"**🔹 제목:** {sub_title}")
                    st.markdown(f"**🔸 소제목:** {sub_content1}")
                    st.markdown("**📑 본문:**")
                    st.write(sub_content2)

                    if pdf_link:
                        st.markdown("---")
                        st.markdown(f"[📎 리포트 원문 다운로드]({pdf_link})", unsafe_allow_html=True)

                    time.sleep(0.5)

                except Exception as e:
                    st.error(f"⚠️ 예외 발생: {e}")
                    continue
