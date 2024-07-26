import json
import math
import random
import os
import streamlit as st
import lyricsgenius
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM



st.set_page_config(page_title="BIG PP")


st.title("VIRTUOSOS")
st.sidebar.markdown(
    """
<style>
.aligncenter {
    text-align: center;
}

</style>
<p class="aligncenter">
    <img src="https://raw.githubusercontent.com/abishek1802/lyric-generation/main/images/pic.png" width="420" />
</p>
""",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    """
<style>
.aligncenter {
    text-align: center;
}
</style>

    """,
    unsafe_allow_html=True,
)



st.sidebar.header("Generation settings:")
num_sequences = st.sidebar.number_input(
    "Number of sequences to generate",
    min_value=1,
    value=5,
    help="The amount of generated texts",
)
min_length = st.sidebar.number_input(
    "Minimum length of the sequence",
    min_value=1,
    value=100,
    help="The minimum length of the sequence to be generated",
)
max_length= st.sidebar.number_input(
    "Maximum length of the sequence",
    min_value=1,
    value=160,
    help="The maximum length of the sequence to be generated",
)
temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=3.0,
    step=0.01,
    value=1.0,
    help="The value used to module the next token probabilities",
)
top_p = st.sidebar.slider(
    "Top-P",
    min_value=0.0,
    max_value=1.0,
    step=0.01,
    value=0.95,
    help="If set to float < 1, only the most probable tokens with probabilities that add up to top_p or higher are kept for generation.",
)

top_k= st.sidebar.number_input(
    "Top-K",
    min_value=0,
    value=50,
    step=1,
    help="The number of highest probability vocabulary tokens to keep for top-k-filtering.",
)

caption = (" വയലാർ എഴുതുമോ ഇതുപോലെ ? ")

st.markdown(caption)

st.subheader("Settings:")
artist_name = st.text_input("Artist name:", "Eminem")
start = st.text_input("Beginning of the song:", "But for me to rap like a computer")

TOKEN = "q_JK_BFy9OMiG7fGTzL-nUto9JDv3iXI24aYRrQnkOvjSCSbY4BuFIindweRsr5I"
genius = lyricsgenius.Genius(TOKEN)

model_html = """

<div class="inline-flex flex-col" style="line-height: 1.5;">
    <div class="flex">
        <div
\t\t\tstyle="display:DISPLAY_1; margin-left: auto; margin-right: auto; width: 92px; height:92px; border-radius: 50%; background-size: cover; background-image: url(&#39;USER_PROFILE&#39;)">
        </div>
    </div>
    <div style="text-align: center; margin-top: 3px; font-size: 16px; font-weight: 800"></div>
    <div style="text-align: center; font-size: 16px; font-weight: 800">USER_NAME</div>
    <a href="https://genius.com/artists/USER_HANDLE">
    \t<div style="text-align: center; font-size: 14px;">@USER_HANDLE</div>
    </a>
</div>
"""


def post_process(output_sequences):
    predictions = []
    generated_sequences = []

    max_repeat = 2

    # decode prediction
    for generated_sequence_idx, generated_sequence in enumerate(output_sequences):
        generated_sequence = generated_sequence.tolist()
        text = tokenizer.decode(generated_sequence, clean_up_tokenization_spaces=True, skip_special_tokens=True)
        generated_sequences.append(text.strip())
                    
    for i, g in enumerate(generated_sequences):
        res = str(g).replace('\n\n\n', '\n').replace('\n\n', '\n')
        lines = res.split('\n')
        # print(lines)
        # i = max_repeat
        # while i != len(lines):
        #   remove_count = 0
        #   for index in range(0, max_repeat):
        #     # print(i - index - 1, i - index)
        #     if lines[i - index - 1] == lines[i - index]:
        #       remove_count += 1
        #   if remove_count == max_repeat:
        #     lines.pop(i)
        #     i -= 1
        #   else:
        #     i += 1
        predictions.append('\n'.join(lines))

    return predictions

if st.button("Run"):
    model_name = None
    with st.spinner(text=f"Searching for {artist_name } in Genius..."):
        artist = genius.search_artist(artist_name, max_songs=0, get_full_info=False)
        if artist is not None:
            artist_dict = genius.artist(artist.id)['artist']
            artist_url = str(artist_dict['url'])
            model_name = artist_url[artist_url.rfind('/') + 1:].lower()
            st.markdown(model_html.replace("USER_PROFILE",artist.image_url).replace("USER_NAME",artist.name).replace("USER_HANDLE",model_name), unsafe_allow_html=True)
        else:
            st.markdown(f"Could not find {artist_name}! Be sure that he/she exists in [Genius](https://genius.com/).")
    if model_name is not None:
        with st.spinner(text=f"Downloading the model of {artist_name }..."):
            model = None
            tokenizer = None
            try:
                tokenizer = AutoTokenizer.from_pretrained(f"huggingartists/{model_name}")
                model = AutoModelForCausalLM.from_pretrained(f"huggingartists/{model_name}")
            except Exception as ex:
                # st.markdown(ex)
                st.markdown(f"Model for this artist does not exist yet.")
                st.markdown(
                        """
                    <style>
                    .aligncenter {
                        text-align: center;
                    }
                    </style>
                    <p class="aligncenter">
                      
                    </p>
                        """,
                        unsafe_allow_html=True,
                    )
                
    if model is not None:
        with st.spinner(text=f"Generating lyrics..."):
            encoded_prompt = tokenizer(start, add_special_tokens=False, return_tensors="pt").input_ids
            encoded_prompt = encoded_prompt.to(model.device)
            # prediction
            output_sequences = model.generate(
                                    input_ids=encoded_prompt,
                                    max_length=max_length,
                                    min_length=min_length,
                                    temperature=float(temperature),
                                    top_p=float(top_p),
                                    top_k=int(top_k),
                                    do_sample=True,
                                    repetition_penalty=1.0,
                                    num_return_sequences=num_sequences
                                    )
            # Post-processing
            predictions = post_process(output_sequences)
            st.subheader("Results")
            for prediction in predictions:
                st.text(prediction)
            