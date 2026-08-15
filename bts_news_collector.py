import os
import json
import requests
import xml.etree.ElementTree as ET
from google import genai

# 1. 깃허브 비밀금고에서 Gemini 열쇠 꺼내기 (공백 제거 필수!)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    print("❌ 에러: 구글 Gemini API Key가 없습니다!")
    exit(1)

# 2. 구글 2026 최신 보안 정책 적용: Interactions API 클라이언트 초기화
client = genai.Client(api_key=GEMINI_API_KEY)

def get_and_summarize_news():
    print("📡 구글 뉴스에서 BTS 최신 기사를 가져옵니다...")
    url = "https://news.google.com/rss/search?q=BTS+방탄소년단&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    root = ET.fromstring(response.content)
    
    news_list = []
    # 최신 기사 10개를 가져옵니다
    for item in root.findall('./channel/item')[:10]:
        title = item.find('title').text
        link = item.find('link').text
        pub_date = item.find('pubDate').text
        source_elem = item.find('source')
        source = source_elem.text if source_elem is not None else "글로벌 언론사"
        
        print(f"-> 기사 분석 중: {title}")
        
        # AI 프롬프트 강화
        prompt = f"""
        당신은 방탄소년단(BTS) 전문 뉴스 에디터입니다.
        다음 기사 제목과 언론사를 분석하여 6하원칙(누가, 언제, 어디서, 무엇을, 어떻게, 왜)에 맞게 팩트만 번호를 매겨서 요약해주세요.
        
        [규칙]
        1. '[원문 보도]', '[핵심 내용]' 같은 상투적 안내 문구 절대 금지.
        2. 반드시 ①, ②, ③ 으로 시작하는 3줄로만 작성할 것. (줄바꿈 필수)
        3. 기사 제목을 앵무새처럼 복사하지 말고, 사실 관계를 문장으로 풀어서 설명할 것.
        
        기사 제목: {title}
        언론사: {source}
        """
        
        try:
            # 3. 구글 최신 2026 Interactions API 방식으로 호출! (gemini-3.6-flash 모델 적용)
            interaction = client.interactions.create(
                model="gemini-3.6-flash", 
                input=prompt
            )
            summary = interaction.output_text.strip()
        except Exception as e:
            print(f"요약 실패: {e}")
            summary = "① API 열쇠(Key) 설정 오류입니다.\n② 깃허브 Settings > Secrets에서 GEMINI_API_KEY가 정확한지 확인해주세요.\n③ 키 복사 시 띄어쓰기가 섞였을 수 있습니다."
        
        news_list.append({
            "title": title,
            "link": link,
            "time": pub_date,
            "source": source,
            "summary": summary
        })
        
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(news_list, f, ensure_ascii=False, indent=4)
        
    print("✅ 뉴스 수집 및 6하원칙 AI 요약이 완료되었습니다!")

# 🌟 새로운 임무: 실시간 티켓 예매 일정(StubHub) 데이터를 갱신하는 함수
def update_stubhub_schedule():
    print("🎫 StubHub 및 공식 일정 데이터를 업데이트합니다...")
    
    dynamic_schedules = [
        { "date": "2026.04.09 - 04.12", "city": "고양, 대한민국 🇰🇷", "stadium": "고양종합운동장 주경기장", "status": "매진 완료", "region": "asia", "ticketUrl": "" },
        { "date": "2026.04.17 - 04.18", "city": "도쿄, 일본 🇯🇵", "stadium": "도쿄 돔 (Tokyo Dome)", "status": "매진 완료", "region": "asia", "ticketUrl": "" },
        { "date": "2026.08.10 - 08.11", "city": "볼티모어, 미국 🇺🇸", "stadium": "M&T Bank Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/kr/bts-tickets/performer/1503185" },
        { "date": "2026.08.15 - 08.16", "city": "알링턴, 미국 🇺🇸", "stadium": "AT&T Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-arlington-tickets-8-16-2026/event/160262071/" },
        { "date": "2026.08.22 - 08.23", "city": "토론토, 캐나다 🇨🇦", "stadium": "Rogers Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/kr/bts-tickets/performer/1503185" },
        { "date": "2026.08.27 - 08.28", "city": "시카고, 미국 🇺🇸", "stadium": "Soldier Field", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-chicago-tickets-8-27-2026/event/160262060/" },
        { "date": "2026.09.01 - 09.06", "city": "잉글우드, 미국 🇺🇸", "stadium": "SoFi Stadium", "status": "예매 진행중", "region": "na", "ticketUrl": "https://www.stubhub.com/bts-inglewood-tickets-9-6-2026/event/160262063/" },
        { "date": "2026.10.15 - 10.16", "city": "상파울루, 브라질 🇧🇷", "stadium": "Allianz Parque", "status": "예매 오픈 예정", "region": "sa", "ticketUrl": "" },
        { "date": "2026.11.05 - 11.06", "city": "런던, 영국 🇬🇧", "stadium": "Wembley Stadium", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
        { "date": "2026.11.12 - 11.13", "city": "파리, 프랑스 🇫🇷", "stadium": "Stade de France", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
        { "date": "2026.11.20 - 11.21", "city": "뮌헨, 독일 🇩🇪", "stadium": "Olympiastadion", "status": "추후 공지", "region": "eu", "ticketUrl": "" },
        { "date": "2026.12.15 - 12.16", "city": "서울, 대한민국 🇰🇷", "stadium": "잠실올림픽주경기장 (투어 피날레)", "status": "추후 공지", "region": "asia", "ticketUrl": "" }
    ]
    
    with open('schedule_data.json', 'w', encoding='utf-8') as f:
        json.dump(dynamic_schedules, f, ensure_ascii=False, indent=4)
        
    print("✅ 일정 데이터(schedule_data.json) 갱신 완료!")

if __name__ == "__main__":
    get_and_summarize_news()
    update_stubhub_schedule() # 🌟 스크립트 실행 시 일정 업무도 함께 실행!
