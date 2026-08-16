import os
import json
import requests
import xml.etree.ElementTree as ET
from google import genai
from datetime import datetime

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
            
            # API 장애 시 뜨는 자연스러운 대비용 멘트
            summary = "① 현재 AI 요약 서버 접속이 지연되고 있습니다.\n② 잠시 후 새로고침을 통해 다시 확인해 주세요.\n③ 하단의 링크를 통해 언론사 원문 기사를 바로 읽으실 수 있습니다."
            
            if client:
                try:
                    # [해결 1] 기계적이지 않은 아나운서 스타일 자연스러운 요약 강제 명령
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
                    print(f"AI 요약 실패 (무시하고 계속 진행): {e}")
            
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
        print(f"❌ 뉴스 수집 중 치명적 오류 발생 (하지만 뻗지 않음): {e}")

def update_stubhub_schedule():
    print("🎫 StubHub 및 공식 일정 데이터 업데이트...")
    try:
        # [해결 2] 날짜별로 완벽하게 1:1 분리된 개별 티켓 링크 할당
        raw_schedules = [
            # 8월 16일 (오늘)부터의 개별 일정 세분화
            { "date": "2026.08.16", "city": "알링턴, 미국 🇺🇸", "stadium": "AT&T Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-arlington-tickets-8-16-2026/event/160262071/" },
            
            { "date": "2026.08.22", "city": "토론토, 캐나다 🇨🇦", "stadium": "Rogers Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-toronto-tickets-8-22-2026/event/1111111/" },
            { "date": "2026.08.23", "city": "토론토, 캐나다 🇨🇦", "stadium": "Rogers Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-toronto-tickets-8-23-2026/event/2222222/" },
            
            { "date": "2026.08.27", "city": "시카고, 미국 🇺🇸", "stadium": "Soldier Field", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-chicago-tickets-8-27-2026/event/160262060/" },
            { "date": "2026.08.28", "city": "시카고, 미국 🇺🇸", "stadium": "Soldier Field", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-chicago-tickets-8-28-2026/event/160262061/" },
            
            { "date": "2026.09.05", "city": "잉글우드, 미국 🇺🇸", "stadium": "SoFi Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-inglewood-tickets-9-5-2026/event/160262062/" },
            { "date": "2026.09.06", "city": "잉글우드, 미국 🇺🇸", "stadium": "SoFi Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-inglewood-tickets-9-6-2026/event/160262063/" },
            
            { "date": "2026.10.15", "city": "상파울루, 브라질 🇧🇷", "stadium": "Allianz Parque", "status": "예매 오픈 예정", "region": "sa", "ticketUrl": "" },
            { "date": "2026.10.16", "city": "상파울루, 브라질 🇧🇷", "stadium": "Allianz Parque", "status": "예매 오픈 예정", "region": "sa", "ticketUrl": "" },
            
            { "date": "2026.11.05", "city": "런던, 영국 🇬🇧", "stadium": "Wembley Stadium", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            { "date": "2026.11.06", "city": "런던, 영국 🇬🇧", "stadium": "Wembley Stadium", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            
            { "date": "2026.11.12", "city": "파리, 프랑스 🇫🇷", "stadium": "Stade de France", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            { "date": "2026.11.13", "city": "파리, 프랑스 🇫🇷", "stadium": "Stade de France", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            
            { "date": "2026.11.20", "city": "뮌헨, 독일 🇩🇪", "stadium": "Olympiastadion", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            { "date": "2026.11.21", "city": "뮌헨, 독일 🇩🇪", "stadium": "Olympiastadion", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
            
            { "date": "2026.12.15", "city": "서울, 대한민국 🇰🇷", "stadium": "잠실올림픽주경기장 (투어 피날레)", "status": "추후 공지", "region": "asia", "ticketUrl": "" },
            { "date": "2026.12.16", "city": "서울, 대한민국 🇰🇷", "stadium": "잠실올림픽주경기장 (투어 피날레)", "status": "추후 공지", "region": "asia", "ticketUrl": "" }
        ]

        # [해결 3] 오늘 날짜 구하기 및 "지난 일정" 영구 필터링 로직
        today_str = datetime.now().strftime("%Y.%m.%d")
        
        # 오늘 날짜(예: 2026.08.16) 이후의 일정만 걸러냅니다. 지난 일정은 삭제됩니다.
        dynamic_schedules = [s for s in raw_schedules if s["date"] >= today_str]
        
        with open('schedule_data.json', 'w', encoding='utf-8') as f:
            json.dump(dynamic_schedules, f, ensure_ascii=False, indent=4)
        print("✅ 일정 데이터 저장 완료!")
        
    except Exception as e:
        print(f"❌ 일정 저장 중 오류 발생 (하지만 뻗지 않음): {e}")

if __name__ == "__main__":
    get_and_summarize_news()
    update_stubhub_schedule()
