from .operations import *
from groq import Groq
def process_analysis(file_path,):
    text = read_txt_file(file_path)
    chunk = chunk_text(text,max_length=5000)
    selected_chunks = select_chunks(chunk, num_samples=20)
    client = Groq(
        api_key="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",
        )
    summary = process_raw_analysis(client, selected_chunks)
    merged_output = merge_responses(summary)
    raw_json_output = process_final_analysis(merged_output, client)
    final_analysis = extract_json(raw_json_output)
