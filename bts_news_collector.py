import os
import json
import requests
import google.generativeai as genai
import xml.etree.ElementTree as ET

# 1. 깃허브 비밀금고에서 Gemini 열쇠 꺼내기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ 에러: 구글 Gemini API Key가 없습니다!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_and_summarize_news():
    print("📡 구글 뉴스에서 BTS 최신 기사를 가져옵니다...")
    url = "https://news.google.com/rss/search?q=BTS+방탄소년단&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    root = ET.fromstring(response.content)
    
    news_list = []
    # 최신 기사 5개만 가져와서 요약하기
    for item in root.findall('./channel/item')[:5]:
        title = item.find('title').text
        link = item.find('link').text
        pub_date = item.find('pubDate').text
        source_elem = item.find('source')
        source = source_elem.text if source_elem is not None else "글로벌 언론사"
        
        print(f"-> 기사 발견: {title}")
        
        # Gemini AI에게 완벽한 6하원칙 요약 지시 (상투어 금지)
        prompt = f"""
        당신은 BTS 전문 뉴스 에디터입니다. 다음 기사 제목과 언론사를 분석하여 6하원칙(누가, 언제, 어디서, 무엇을, 어떻게, 왜)에 맞게 팩트만 번호를 매겨서 3~4줄로 상세히 요약해주세요. 
        절대로 '[원문 보도]', '[핵심 내용]' 같은 기계적인 안내 문구를 쓰지 마세요.
        
        기사 제목: {title}
        언론사: {source}
        """
        
        try:
            ai_response = model.generate_content(prompt)
            summary = ai_response.text.strip()
        except Exception as e:
            summary = "AI 요약을 불러오는 중 에러가 발생했습니다."
        
        news_list.append({
            "title": title,
            "link": link,
            "time": pub_date,
            "source": source,
            "summary": summary
        })
        
    # 요약된 데이터를 웹사이트가 읽을 수 있게 json 파일로 찰칵 저장!
    with open('news_data.json', 'w', encoding='utf-8') as f:
        json.dump(news_list, f, ensure_ascii=False, indent=4)
        
    print("✅ 뉴스 수집 및 6하원칙 AI 요약이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    get_and_summarize_news()
