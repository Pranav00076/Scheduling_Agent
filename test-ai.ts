import { GoogleGenAI } from '@google/genai';

async function test() {
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    console.log("API Key exists:", !!apiKey);
    const ai = new GoogleGenAI({ apiKey });
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: 'Hello',
    });
    console.log("Success:", response.text);
  } catch (e: any) {
    console.error("Error:", e.message);
    if (e.status) console.error("Status:", e.status);
    if (e.details) console.error("Details:", JSON.stringify(e.details, null, 2));
  }
}

test();
