import os
import json
import requests
import xml.etree.ElementTree as ET
from google import genai
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

def get_and_summarize_news():
    print("📡 구글 뉴스 수집 시작...")
    try:
        url = "https://news.google.com/rss/search?q=BTS+방탄소년단&hl=ko&gl=KR&ceid=KR:ko"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        root = ET.fromstring(response.content)
        
        news_list = []
        client = None
        if GEMINI_API_KEY:
            client = genai.Client(api_key=GEMINI_API_KEY)
        
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            source_elem = item.find('source')
            source = source_elem.text if source_elem is not None else "글로벌 언론사"
            
            summary = "① 현재 AI 요약 서버 접속이 지연되고 있습니다.\n② 잠시 후 새로고침을 통해 다시 확인해 주세요.\n③ 원문 기사는 정상적으로 확인 가능합니다."
            
            if client:
                try:
                    # [완벽 검증 1] 6하원칙 단어 절대 금지 + 자연스러운 아나운서 스타일 강제
                    prompt = f"""당신은 방탄소년단(BTS) 전문 뉴스 에디터입니다.
                    다음 기사를 읽고 독자가 가장 흥미로워할 핵심 내용만 딱 3줄로 요약하세요.
                    
                    [요약 규칙 - 절대 엄수]
                    1. '누가', '언제', '어디서', '무엇을' 같은 6하원칙 단어(레이블)는 절대로 문서에 쓰지 마세요. (예: "누가: 방탄소년단이" -> 금지)
                    2. 기사 내용을 실제 뉴스 아나운서가 브리핑하듯 아주 자연스럽고 매끄러운 한국어 문장으로 풀어쓰세요.
                    3. 반드시 ①, ②, ③ 기호로 시작하여 정확히 3줄로만 출력하세요. 줄바꿈을 확실히 하세요.
                    4. 번역기를 돌린 것 같은 어색한 문투를 피하고 한국인이 읽기 편하게 만드세요.
                    
                    제목: {title}
                    언론사: {source}"""
                    
                    interaction = client.interactions.create(
                        model="gemini-3.6-flash", 
                        input=prompt
                    )
                    summary = interaction.output_text.strip()
                except Exception as e:
                    print(f"AI 요약 실패: {e}")
            
            news_list.append({
                "title": title,
                "link": link,
                "time": pub_date,
                "source": source,
                "summary": summary
            })
            
        with open('news_data.json', 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=4)
        print("✅ 뉴스 데이터 저장 완료!")
        
    except Exception as e:
        print(f"❌ 뉴스 수집 중 오류: {e}")

def update_stubhub_schedule():
    print("🎫 진짜 StubHub 실시간 크롤링 시작 (꼼수/하드코딩 완전 제거)...")
    try:
        # 1. 봇 차단을 우회하기 위한 Cloudscraper 장착
        scraper = cloudscraper.create_scraper()
        
        dynamic_schedules = []
        today_str = datetime.now().strftime("%Y.%m.%d")
        
        # 2. Page 1부터 Page 9까지 샅샅이 순차 검색
        for page in range(1, 10):
            url = f"https://www.stubhub.com/bts-tickets/performer/1503185?restPage={page}"
            print(f"🔍 StubHub Page {page} 스캔 중...")
            
            response = scraper.get(url, timeout=15)
            
            # 스텁허브가 접근을 막으면 즉시 중단
            if response.status_code != 200:
                print(f"⚠️ Page {page} 접근 차단됨 (Status: {response.status_code})")
                break 
                
            # 3. BeautifulSoup으로 실제 웹페이지 해부
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 스텁허브 내부에 숨겨진 일정 데이터(JSON-LD) 파싱 시도
            scripts = soup.find_all('script', type='application/ld+json')
            page_has_events = False
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        if item.get('@type') in ['Event', 'MusicEvent']:
                            page_has_events = True
                            start_date_raw = item.get('startDate', '')
                            event_url = item.get('url', '')
                            location = item.get('location', {})
                            stadium = location.get('name', '공연장 미정')
                            address = location.get('address', {})
                            city = address.get('addressLocality', '도시 미정')
                            country = address.get('addressCountry', '')
                            
                            # 날짜 변환 및 지난 일정 필터링
                            if start_date_raw:
                                dt = datetime.fromisoformat(start_date_raw.replace('Z', '+00:00').split('T')[0])
                                date_str = dt.strftime("%Y.%m.%d")
                                
                                # [요청사항] 오늘 날짜보다 지난 일정은 절대 저장하지 않음!
                                if date_str >= today_str:
                                    dynamic_schedules.append({
                                        "date": date_str,
                                        "city": f"{city}, {country}",
                                        "stadium": stadium,
                                        "status": "예매 진행중",
                                        "region": "na", # 자동 파싱 기본값
                                        "ticketUrl": event_url
                                    })
                except Exception:
                    continue
                    
            # 4. 더 이상 이벤트 데이터가 없는 페이지면 시간 낭비 없이 스캔 종료
            if not page_has_events:
                print(f"ℹ️ Page {page}에 더 이상 일정이 없어 스캔을 마칩니다.")
                break
                
        # 5. 중복 티켓 URL 제거 및 날짜순 정렬
        unique_schedules = {v['ticketUrl']: v for v in dynamic_schedules}.values()
        final_schedules = sorted(list(unique_schedules), key=lambda x: x['date'])

        # 6. 진정한 개발자의 룰: 가짜 데이터를 넣지 않는다. 데이터가 없으면 빈 화면을 띄운다.
        if not final_schedules:
            print("⚠️ 수집된 일정이 없습니다. (스텁허브에 일정이 없거나 방화벽에 차단됨)")
        
        with open('schedule_data.json', 'w', encoding='utf-8') as f:
            json.dump(final_schedules, f, ensure_ascii=False, indent=4)
        print(f"✅ 실제 스텁허브 일정 {len(final_schedules)}개 크롤링 및 저장 완료!")
        
    except Exception as e:
        print(f"❌ 일정 크롤링 중 치명적 오류 발생: {e}")

if __name__ == "__main__":
    get_and_summarize_news()
    update_stubhub_schedule()
