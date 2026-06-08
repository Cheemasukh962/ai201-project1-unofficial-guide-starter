"""
app.py -- Gradio web UI for the ASSIST Transfer Chatbot.

Run: python app.py
Then open: http://localhost:7860
"""

import gradio as gr
from query import ask

def handle_query(question, cc_name, uc_name):
    if not question.strip():
        return "", ""
    result   = ask(question, cc_name=cc_name, uc_name=uc_name)
    answer   = result["answer"]
    src_list = "\n".join(f"• {s}" for s in result["sources"])
    return answer, src_list

with gr.Blocks(title="ASSIST Transfer Chatbot") as demo:
    gr.Markdown("## ASSIST Transfer Chatbot\nAsk about course articulation between California community colleges and UC campuses.")

    with gr.Row():
        cc_input = gr.Textbox(value="American River College", label="Community College")
        uc_input = gr.Textbox(value="UC Davis",              label="UC Campus")

    question_input = gr.Textbox(
        label="Your question",
        placeholder="e.g. Does MATH 400 count for MAT 021B at UC Davis?",
        lines=2,
    )
    ask_btn = gr.Button("Ask", variant="primary")

    answer_output  = gr.Textbox(label="Answer",        lines=8)
    sources_output = gr.Textbox(label="Retrieved from", lines=4)

    ask_btn.click(handle_query,
                  inputs=[question_input, cc_input, uc_input],
                  outputs=[answer_output, sources_output])
    question_input.submit(handle_query,
                          inputs=[question_input, cc_input, uc_input],
                          outputs=[answer_output, sources_output])

if __name__ == "__main__":
    demo.launch()
