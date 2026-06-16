import asyncio

class AsyncAIService:
    @staticmethod
    async def generate_text(prompt: str) -> str:
        # ⚠️ هنا يتم وضع كود الربط الحقيقي مع Gemini أو OpenAI API (مثل openai.ChatCompletion.acreate)
        # حالياً سنقوم بعمل محاكاة (Mock) لتجهيز البنية التحتية
        await asyncio.sleep(1.5) # محاكاة وقت الاتصال بـ API
        
        if "waiver" in prompt.lower():
            return '{"justification": "Local market constraints require this exception.", "control": "Quarterly audits will be enforced.", "probability": "75%"}'
        
        return '{"summary": "Project is viable but requires immediate mitigation on local content.", "actions": ["Hire local subcontractors", "Restructure payroll"]}'

ai_client = AsyncAIService()