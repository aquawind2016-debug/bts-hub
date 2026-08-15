import os
import json
import requests
import xml.etree.ElementTree as ET

# 깃허브 비밀금고에서 Gemini 열쇠 꺼내기 (앞뒤 공백 제거로 에러 방지)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
# 가장 안정적인 다이렉트 통신(REST API) 주소 사용
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        }
        
        try:
            # AI 서버에 요청 보내기
            res = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
            if res.status_code == 200:
                result = res.json()
                summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                print(f"API Error: {res.text}")
                summary = "① API 열쇠(Key) 설정 오류입니다.\n② 깃허브 Settings > Secrets에서 GEMINI_API_KEY가 정확한지 확인해주세요.\n③ 키 복사 시 띄어쓰기가 섞였을 수 있습니다."
        except Exception as e:
            print(f"요약 실패: {e}")
            summary = "① AI 요약을 생성하는 중 연결 오류가 발생했습니다.\n② 5분 뒤 자동 새로고침 시 해결될 수 있습니다."
        
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

if __name__ == "__main__":
    get_and_summarize_news()
