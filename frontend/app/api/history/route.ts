import { NextRequest, NextResponse } from 'next/server';

interface HistoryMessage {
  role: string;
  text: string;
  timestamp?: string;
}

// In a real application, you'd use a database
// For this demo, we'll use a simple in-memory store
const historyStore: HistoryMessage[] = [];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const year = parseInt(searchParams.get('year') || new Date().getFullYear().toString());
    const month = parseInt(searchParams.get('month') || (new Date().getMonth() + 1).toString());
    const day = parseInt(searchParams.get('day') || new Date().getDate().toString());

    const targetDate = new Date(year, month - 1, day);
    const startOfDay = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
    const endOfDay = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate() + 1);

    // Filter messages for the target date
    const filteredMessages = historyStore.filter(msg => {
      if (!msg.timestamp) return false;
      const msgDate = new Date(msg.timestamp);
      return msgDate >= startOfDay && msgDate < endOfDay;
    });

    return NextResponse.json(filteredMessages.map(msg => ({
      role: msg.role,
      text: msg.text
    })));

  } catch (error) {
    console.error('Error loading history:', error);
    return NextResponse.json(
      { error: 'Invalid date provided' },
      { status: 400 }
    );
  }
}

// Store messages (called from chat endpoint)
export function storeMessage(role: string, text: string) {
  historyStore.push({
    role,
    text,
    timestamp: new Date().toISOString()
  });
}
