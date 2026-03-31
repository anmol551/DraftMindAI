from openai import OpenAI
import os 
# from dotenv import load_dotenv
# load_dotenv()
# key = os.getenv("GROK_API_KEY")
# key = os.getenv("OPENAI_API_KEY")

import streamlit as st
key = st.secrets["GROK_API_KEY"]

def generate_content(prompt):

  api_key = key
  
  client = OpenAI(
      api_key=api_key,
      base_url="https://api.x.ai/v1"
  )

  chat_completion = client.chat.completions.create(
      model="grok-3-mini", #"gpt-4o-mini", "grok-3-mini"
      messages=[
          {
              "role": "user",
              "content": prompt
          }
      ],
  )

  return chat_completion.choices[0].message.content

# print(generate_content("What is AI"))


# # save in txt

# with open("InputFiles/example.txt", "w") as file:
#             file.write("Examples:\n")
#             file.write(a + "\n\n")
            
# print("Bani Gayo File")
