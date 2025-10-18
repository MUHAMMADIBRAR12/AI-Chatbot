import { NextResponse } from 'next/server';

export async function POST() {
  try {
    // In a real application, you'd clear from a database
    // For this demo, we'll just return success
    // The actual clearing would be handled by the chat endpoint
    
    return NextResponse.json({
      detail: 'Chat history cleared.'
    });

  } catch (error) {
    console.error('Error clearing history:', error);
    return NextResponse.json(
      { error: 'Failed to clear chat history' },
      { status: 500 }
    );
  }
}
