import os
import datetime as dt
import panel as pn
import google.generativeai as genai

# Initialize Panel
pn.extension()

# Configure your Gemini API key
# Prefer environment variable if provided, otherwise fall back to existing key
_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDBLVUFfShN2RClhc5iF5oZ-Z9tkFwpDXo")
genai.configure(api_key=_api_key)

# Load Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Chat state
chat = model.start_chat(history=[])

# Instruction for bot (system message)
initial_instruction = """You are OrderBot, an automated service to collect orders for a pizza restaurant.
You first greet the customer, then collect the order and ask if it's pickup or delivery. 
You wait to collect the entire order, summarize it, and check for final additions. 
If delivery, you ask for an address. Finally, you collect the payment.
Menu:
- Pepperoni Pizza: Large 12.95, Medium 10.00, Small 7.00
- Cheese Pizza: Large 10.95, Medium 9.25, Small 6.50
- Eggplant Pizza: Large 11.95, Medium 9.75, Small 6.75
- Fries: Large 4.50, Small 3.50
- Greek Salad: 7.25
- Toppings: Extra Cheese 2.00, Mushrooms 1.50, Sausage 3.00, Canadian Bacon 3.50, AI Sauce 1.50, Peppers 1.00
- Drinks: Coke (Large 3.00, Medium 2.00, Small 1.00), Sprite (Large 3.00, Medium 2.00, Small 1.00), Bottled Water 5.00
Respond in a friendly, conversational style."""

# --- UI: Chat container and helpers ---
message_container = pn.Column(
    height=520,
    scroll=True,
    align='center',
    sizing_mode="stretch_width",
    styles={'width': '700px', 'margin': '0 auto'}
)

def _timestamp():
    return dt.datetime.now().strftime("%I:%M %p")

def _bubble(content: str, role: str):
    is_user = role == "user"
    bubble_bg = "#F4F6F8" if is_user else "#E7F1FF"
    text_align = 'right' if is_user else 'left'
    bubble = pn.pane.Markdown(
        content,
        sizing_mode=None,
        styles={
            'background': bubble_bg,
            'padding': '12px 14px',
            'border-radius': '14px',
            'border': '1px solid #E2E8F0',
            'line-height': '1.45',
            'text-align': text_align,
            'color': '#0F172A',
            'display': 'inline-block',
            'max-width': '80%',
            'overflow-wrap': 'anywhere',
            'word-wrap': 'break-word',
            'white-space': 'pre-wrap'
        }
    )
    meta = pn.pane.Markdown(
        f"<span style='color:#64748B;font-size:11px'>{_timestamp()}</span>",
        styles={'margin': '4px 6px'}
    )
    if is_user:
        row = pn.Column(
            pn.Row(pn.Spacer(), bubble, width=700, sizing_mode='fixed'),
            meta,
        )
    else:
        row = pn.Column(
            pn.Row(bubble, pn.Spacer(), width=700, sizing_mode='fixed'),
            meta,
        )
    return row

# Function to collect messages and respond
def collect_messages(_):
    prompt = inp.value.strip()
    inp.value = ''
    if not prompt:
        return
    send_controls(False)
    try:
        if len(chat.history) == 0:
            chat.send_message(initial_instruction)

        message_container.append(_bubble(prompt, "user"))
        typing_indicator.visible = True
        response = chat.send_message(prompt)
        typing_indicator.visible = False
        bot_text = getattr(response, 'text', None) or "Sorry, I couldn't generate a response."
        message_container.append(_bubble(bot_text, "bot"))
    except Exception as e:
        typing_indicator.visible = False
        message_container.append(_bubble(f"Error: {e}", "bot"))
    finally:
        send_controls(True)
        message_container.scroll_to_bottom = True

# UI Components
inp = pn.widgets.TextInput(value="", placeholder="Type a message... (Enter to send)", width=700)
button_conversation = pn.widgets.Button(
    name="➤",  # Arrow symbol
    button_type="warning",
    width=40,
    height=40,
    css_classes=['custom-button']
)
typing_indicator = pn.indicators.LoadingSpinner(value=False, size=24)

def send_controls(enabled: bool):
    inp.disabled = not enabled
    button_conversation.disabled = not enabled
    quick_pickup.disabled = not enabled
    quick_delivery.disabled = not enabled
    quick_menu.disabled = not enabled

# Add custom CSS for the button and container
pn.config.raw_css = """
.fast-title { font-weight: 700; }
/* Input bar */
.input-bar { background:#ffffff; border:1px solid #E2E8F0; border-radius:12px; padding:10px; }
.pn-TextInput input { text-align: left !important; }
.chip { margin: 2px 4px; }

/* Custom button for arrow */
.custom-button {
    background-color: transparent !important;
    color: black !important;
    border: none !important;
    font-size: 20px !important;
    font-weight: bold !important;
    padding: 0 !important;
    /* Removed absolute positioning, right, top, and z-index */
    transform: rotate(-60deg) !important; /* Keep rotation, but without translateY */
    transition: all 0.3s ease !important;
}
.custom-button:hover {
    color: #333 !important;
    transform: rotate(-60deg) scale(1.1) !important;
}
"""

# Function to handle input changes
def on_input_change(event):
    if event.new and event.new.endswith('\n'):
        inp.value = event.new.rstrip('\n')
        collect_messages(None)

# Bind events
inp.param.watch(on_input_change, 'value') # Re-enabled this line
# inp.on_submit(collect_messages) # Use on_submit for Enter key functionality # Removed this line
button_conversation.on_click(collect_messages)

# Quick replies
def send_quick(text: str):
    inp.value = text
    collect_messages(None)

quick_pickup = pn.widgets.Button(name="Pickup", button_type="success", width=120, height=34, css_classes=["chip"])
quick_delivery = pn.widgets.Button(name="Delivery", button_type="warning", width=120, height=34, css_classes=["chip"])
quick_menu = pn.widgets.Button(name="Show Menu", button_type="light", width=120, height=34, css_classes=["chip"])

quick_pickup.on_click(lambda e: send_quick("I'd like pickup"))
quick_delivery.on_click(lambda e: send_quick("I'd like delivery"))
quick_menu.on_click(lambda e: send_quick("Show me the menu"))

quick_replies = pn.Row(quick_pickup, quick_delivery, quick_menu)

# Collapsible menu
menu_md = f"""
### Menu
- Pepperoni Pizza: Large 12.95, Medium 10.00, Small 7.00
- Cheese Pizza: Large 10.95, Medium 9.25, Small 6.50
- Eggplant Pizza: Large 11.95, Medium 9.75, Small 6.75
- Fries: Large 4.50, Small 3.50
- Greek Salad: 7.25
- Toppings: Extra Cheese 2.00, Mushrooms 1.50, Sausage 3.00, Canadian Bacon 3.50, AI Sauce 1.50, Peppers 1.00
- Drinks: Coke (Large 3.00, Medium 2.00, Small 1.00), Sprite (Large 3.00, Medium 2.00, Small 1.00), Bottled Water 5.00
"""
menu_card = pn.Accordion(("Menu", pn.pane.Markdown(menu_md, sizing_mode='stretch_width')), active=[])

# Clear chat
def clear_chat(event=None):
    global chat
    chat = model.start_chat(history=[])
    message_container.objects = []

clear_btn = pn.widgets.Button(name="Clear Chat", button_type="danger", width=120, height=34)
clear_btn.on_click(clear_chat)

# Layout - messages on top, input box below
# Template layout
template = pn.template.FastListTemplate(
    title="🍕 Pizza OrderBot",
    sidebar=[menu_card, pn.layout.Divider(), pn.pane.Markdown("#### Quick Replies"), quick_replies, pn.Spacer(height=10), clear_btn],
    main=[
        message_container,
        pn.Row(
            pn.Column(inp, sizing_mode='stretch_width'),
            pn.Column(button_conversation, typing_indicator, sizing_mode='fixed'),
            sizing_mode='stretch_width',
            css_classes=["input-bar"]
        ),
    ],
    accent_base_color="#2563EB",
    header_background="#0F172A",
)

# Make app visible
template.servable()