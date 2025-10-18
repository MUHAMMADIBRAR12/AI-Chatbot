import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

const INITIAL_INSTRUCTION = `You are OrderBot, an automated service to collect orders for a pizza restaurant. 
You first greet the customer, then collect the order and ask if it's pickup or delivery. 
You wait to collect the entire order, summarize it, and check for final additions. 
If delivery, you ask for an address. Finally, you collect the payment. 
Menu: Pepperoni Pizza (L 12.95, M 10.00, S 7.00), Cheese Pizza (L 10.95, M 9.25, S 6.50), 
Eggplant Pizza (L 11.95, M 9.75, S 6.75), Fries (L 4.50, S 3.50), Greek Salad 7.25, 
Toppings: Extra Cheese 2.00, Mushrooms 1.50, Sausage 3.00, Canadian Bacon 3.50, AI Sauce 1.50, Peppers 1.00, 
Drinks: Coke (L 3.00, M 2.00, S 1.00), Sprite (L 3.00, M 2.00, S 1.00), Bottled Water 5.00. 
Respond in a friendly, conversational style.`;

interface Message {
  role: string;
  text: string;
}

interface ChatRequest {
  message: string;
  history?: Message[];
}

function toGeminiHistory(messages: Message[]) {
  return messages.map(m => ({
    role: m.role === 'user' ? 'user' : 'model',
    parts: [{ text: m.text }]
  }));
}

export async function POST(request: NextRequest) {
  try {
    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json({
        reply: '❌ Server Error: GEMINI_API_KEY is not configured. Please set the GEMINI_API_KEY environment variable.',
        history: []
      });
    }

    const body: ChatRequest = await request.json();
    const { message, history = [] } = body;

    // Configure the model with system instruction
    const model = genAI.getGenerativeModel({
      model: 'gemini-2.0-flash',
      systemInstruction: INITIAL_INSTRUCTION,
    });

    // Build conversation history
    const conversationHistory = [...history];
    conversationHistory.push({ role: 'user', text: message });

    try {
      // Start chat with history
      const chat = model.startChat({
        history: toGeminiHistory(conversationHistory.filter(m => m.role !== 'system'))
      });

      // Send message with timeout
      const result = await chat.sendMessage(message);
      const reply = result.response.text();

      // Add bot response to history
      conversationHistory.push({ role: 'bot', text: reply });

      return NextResponse.json({
        reply,
        history: conversationHistory
      });

    } catch (error) {
      console.error('Gemini API Error:', error);
      const errorReply = `❌ AI Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your GEMINI_API_KEY and try again.`;
      
      conversationHistory.push({ role: 'bot', text: errorReply });
      
      return NextResponse.json({
        reply: errorReply,
        history: conversationHistory
      });
    }

  } catch (error) {
    console.error('Server error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
