import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# model_path = "Mistral-7B-Instruct"
# # model_path = "./Mistral-7B-Instruct-v0.1"  # model weights 必须已经download到该directory


# tokenizer = AutoTokenizer.from_pretrained(model_path)
# # model = AutoModelForCausalLM.from_pretrained(
# #     model_path, torch_dtype=torch.float16, device_map="auto"
# # )  # GPU
# model = AutoModelForCausalLM.from_pretrained(model_path)  # CPU


# # Text prompt
# prompt = "Explain the concept of transformers in deep learning."

# # Tokenize input
# inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

# print("Hello")
# # Generate response
# with torch.no_grad():
#     output = model.generate(
#         **inputs, max_new_tokens=200, do_sample=True, temperature=0.7, top_p=0.95
#     )

# # Decode and print
# response = tokenizer.decode(output[0], skip_special_tokens=True)
# print(response)
