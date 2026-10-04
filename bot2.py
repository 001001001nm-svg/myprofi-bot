def ask_ai(prompt, system_instruction):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Barsbek Bot"
    }
    
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",  # Самая надежная бесплатная модель
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        res_data = response.json()
        
        # Печатаем в консоль Render реальную ошибку, если она возникнет
        if 'choices' in res_data and len(res_data['choices']) > 0:
            return res_data['choices'][0]['message']['content']
        else:
            print(f"OpenRouter Raw Error: {res_data}")
            return f"Ошибка OpenRouter: {res_data.get('error', {}).get('message', 'Неизвестная ошибка')}"
    except Exception as e:
        print(f"Request exception: {e}")
        return "Ошибка соединения с ИИ. Попробуй позже."
